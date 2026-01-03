"""Background graph executor for LangGraph Studio."""

from __future__ import annotations

import threading
import time
from typing import Any, Callable

from ..models.execution import ExecutionState, ExecutionStatus, StepResult, ToolCallInfo


class GraphExecutor:
    """Background thread executor for LangGraph.

    Executes a compiled LangGraph in a background thread, providing
    real-time updates to the UI via callbacks. Supports:
    - Continuous execution (run)
    - Step-by-step execution (step)
    - Pause/resume
    - Stop
    """

    def __init__(
        self,
        on_state_update: Callable[[ExecutionState], None],
    ):
        """Initialize the executor.

        Args:
            on_state_update: Callback for execution state updates.
                Called from background thread, but Castella's State.set()
                is thread-safe.
        """
        self._on_state_update = on_state_update
        self._compiled_graph: Any = None

        # Threading state
        self._thread: threading.Thread | None = None
        self._stop_requested = False
        self._pause_requested = False
        self._step_mode = False
        self._step_event = threading.Event()

        # Execution state
        self._state = ExecutionState()

    def set_graph(self, compiled_graph: Any) -> None:
        """Set the graph to execute.

        Args:
            compiled_graph: A LangGraph CompiledGraph instance.
        """
        # Stop any running execution first
        self.stop()

        self._compiled_graph = compiled_graph
        self._state = ExecutionState()
        self._notify_update()

    def run(self, initial_state: dict[str, Any] | None = None) -> None:
        """Start continuous execution in background thread.

        Args:
            initial_state: Initial graph state dictionary.
        """
        if self._thread and self._thread.is_alive():
            return  # Already running

        if self._compiled_graph is None:
            return

        self._stop_requested = False
        self._pause_requested = False
        self._step_mode = False

        self._thread = threading.Thread(
            target=self._execute_loop,
            args=(initial_state or {},),
            daemon=True,
        )
        self._thread.start()

    def step(self, initial_state: dict[str, Any] | None = None) -> None:
        """Execute a single step.

        If already running, triggers one step. Otherwise starts
        execution in step mode.

        Args:
            initial_state: Initial graph state dictionary.
        """
        if self._thread and self._thread.is_alive():
            # Already running - trigger one step
            self._step_event.set()
            return

        if self._compiled_graph is None:
            return

        # Start in step mode
        self._stop_requested = False
        self._pause_requested = False
        self._step_mode = True
        self._step_event.clear()

        self._thread = threading.Thread(
            target=self._execute_loop,
            args=(initial_state or {},),
            daemon=True,
        )
        self._thread.start()

    def stop(self) -> None:
        """Stop execution."""
        self._stop_requested = True
        self._step_event.set()  # Unblock if waiting

        if self._thread:
            self._thread.join(timeout=2.0)
            self._thread = None

    def pause(self) -> None:
        """Pause execution."""
        self._pause_requested = True

    def resume(self) -> None:
        """Resume execution after pause."""
        self._pause_requested = False

    def continue_execution(self) -> None:
        """Continue execution after pause or breakpoint.

        This unblocks the execution thread if it's waiting at a pause
        or breakpoint.
        """
        self._pause_requested = False
        self._state.paused_at_breakpoint = False
        self._step_event.set()

    def reset(self) -> None:
        """Reset execution state."""
        self.stop()
        # Preserve breakpoints when resetting
        breakpoints = self._state.breakpoints.copy()
        self._state = ExecutionState(breakpoints=breakpoints)
        self._notify_update()

    def toggle_breakpoint(self, node_id: str) -> None:
        """Toggle a breakpoint on a node.

        Args:
            node_id: The node ID to toggle breakpoint on.
        """
        if node_id in self._state.breakpoints:
            self._state.breakpoints.discard(node_id)
        else:
            self._state.breakpoints.add(node_id)
        self._notify_update()

    def set_breakpoints(self, node_ids: set[str]) -> None:
        """Set breakpoints to the given set of node IDs.

        Args:
            node_ids: Set of node IDs to set breakpoints on.
        """
        self._state.breakpoints = node_ids.copy()
        self._notify_update()

    @property
    def is_running(self) -> bool:
        """Check if executor is currently running."""
        return self._thread is not None and self._thread.is_alive()

    @property
    def current_state(self) -> ExecutionState:
        """Get current execution state."""
        return self._state

    def _execute_loop(self, initial_state: dict) -> None:
        """Main execution loop (runs in background thread).

        Args:
            initial_state: Initial graph state.
        """
        if self._compiled_graph is None:
            return

        # Preserve breakpoints when starting new execution
        breakpoints = self._state.breakpoints.copy()
        self._state = ExecutionState(
            status=ExecutionStatus.RUNNING,
            current_state=initial_state.copy(),
            current_node_id="__start__",  # Start at __start__ node
            breakpoints=breakpoints,
        )
        self._notify_update()

        # Brief pause to show __start__ highlighted
        time.sleep(0.2)

        try:
            # Use LangGraph's stream() for step-by-step execution
            for event in self._compiled_graph.stream(initial_state):
                if self._stop_requested:
                    break

                # Get the node name from the event for breakpoint checking
                node_name = next(iter(event.keys()), None)

                # Check for breakpoint BEFORE processing
                if node_name and node_name in self._state.breakpoints:
                    self._state.status = ExecutionStatus.PAUSED
                    self._state.paused_at_breakpoint = True
                    self._state.current_node_id = node_name
                    self._notify_update()

                    # Wait for continue signal
                    self._step_event.wait()
                    self._step_event.clear()

                    if self._stop_requested:
                        break

                    self._state.paused_at_breakpoint = False
                    self._state.status = ExecutionStatus.RUNNING

                # Wait while paused (manual pause)
                while self._pause_requested and not self._stop_requested:
                    self._state.status = ExecutionStatus.PAUSED
                    self._notify_update()
                    time.sleep(0.1)

                if self._stop_requested:
                    break

                # Resume running status after pause
                if self._state.status == ExecutionStatus.PAUSED:
                    self._state.status = ExecutionStatus.RUNNING

                # In step mode, wait for step signal
                if self._step_mode:
                    self._state.status = ExecutionStatus.PAUSED
                    self._notify_update()
                    self._step_event.wait()
                    self._step_event.clear()

                    if self._stop_requested:
                        break

                    self._state.status = ExecutionStatus.RUNNING

                # Process the step event
                self._process_step_event(event)

            # Record edge to __end__ and show __end__ node highlighted
            previous_node = self._state.current_node_id
            if previous_node and previous_node != "__end__":
                self._state.executed_edges.append((previous_node, "__end__"))
            self._state.current_node_id = "__end__"
            self._notify_update()
            time.sleep(0.3)

            # Execution completed successfully
            self._state.status = ExecutionStatus.COMPLETED
            self._state.current_node_id = None
            self._state.paused_at_breakpoint = False

        except Exception as e:
            self._state.status = ExecutionStatus.ERROR
            self._state.error_message = str(e)

        self._notify_update()

    def _process_step_event(self, event: dict) -> None:
        """Process a single step event from the graph.

        LangGraph stream events have the format:
        {node_name: {state_key: value, ...}}

        Args:
            event: Step event dictionary.
        """
        start_time = time.perf_counter()

        for node_name, node_output in event.items():
            # Record edge transition (from previous node to this node)
            previous_node = self._state.current_node_id
            if previous_node and previous_node != node_name:
                self._state.executed_edges.append((previous_node, node_name))

            # Update current node
            self._state.current_node_id = node_name

            # Record state before
            state_before = self._state.current_state.copy()

            # Merge node output into state
            if isinstance(node_output, dict):
                self._state.current_state.update(node_output)

            # Extract tool calls from current state
            tool_calls = self._extract_tool_calls(self._state.current_state)

            # Record step
            duration_ms = (time.perf_counter() - start_time) * 1000
            step_result = StepResult(
                node_id=node_name,
                state_before=state_before,
                state_after=self._state.current_state.copy(),
                duration_ms=duration_ms,
                tool_calls=tool_calls,
            )
            self._state.step_history.append(step_result)
            self._state.total_steps += 1

            self._notify_update()

            # Small delay for visualization
            time.sleep(0.1)

    def _extract_tool_calls(self, state: dict[str, Any]) -> list[ToolCallInfo]:
        """Extract tool call information from LangGraph state.

        LangGraph agents typically store messages in a 'messages' key,
        where AIMessage objects may contain tool_calls, and ToolMessage
        objects contain the results.

        Args:
            state: Current graph state.

        Returns:
            List of ToolCallInfo objects.
        """
        tool_calls: list[ToolCallInfo] = []

        try:
            # Try to import LangChain message types
            from langchain_core.messages import AIMessage, ToolMessage
        except ImportError:
            # LangChain not installed, skip tool extraction
            return tool_calls

        messages = state.get("messages", [])
        if not isinstance(messages, list):
            return tool_calls

        # Map tool call IDs to their results
        tool_results: dict[str, Any] = {}
        for msg in messages:
            if isinstance(msg, ToolMessage):
                tool_results[msg.tool_call_id] = msg.content

        # Extract tool calls from AIMessages
        for msg in messages:
            if isinstance(msg, AIMessage) and hasattr(msg, "tool_calls"):
                for tc in msg.tool_calls:
                    if isinstance(tc, dict):
                        tool_calls.append(
                            ToolCallInfo(
                                tool_call_id=tc.get("id", ""),
                                tool_name=tc.get("name", "unknown"),
                                arguments=tc.get("args", {}),
                                result=tool_results.get(tc.get("id")),
                            )
                        )

        return tool_calls

    def _notify_update(self) -> None:
        """Notify UI of state update.

        Creates a deep copy to ensure thread safety.
        """
        # Create a copy to avoid threading issues
        state_copy = self._state.model_copy(deep=True)
        self._on_state_update(state_copy)
