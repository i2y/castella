"""Background graph executor for LangGraph Studio.

Uses the shared BaseWorkflowExecutor for common threading logic.
"""

from __future__ import annotations

import time
from typing import Any

from castella.studio.executor.base import BaseWorkflowExecutor
from castella.studio.models.execution import ExecutionStatus

from ..models.execution import ExecutionState, StepResult, ToolCallInfo


class GraphExecutor(BaseWorkflowExecutor):
    """Background thread executor for LangGraph.

    Executes a compiled LangGraph in a background thread, providing
    real-time updates to the UI via callbacks. Supports:
    - Continuous execution (run)
    - Step-by-step execution (step)
    - Pause/resume
    - Stop
    - Breakpoints
    """

    def __init__(self, on_state_update):
        """Initialize the executor.

        Args:
            on_state_update: Callback for execution state updates.
        """
        self._compiled_graph: Any = None
        super().__init__(on_state_update)

    def _create_initial_state(self) -> ExecutionState:
        """Create the initial execution state."""
        return ExecutionState()

    def set_workflow(self, workflow: Any) -> None:
        """Set the workflow to execute (alias for set_graph).

        Args:
            workflow: A LangGraph CompiledGraph instance.
        """
        self.set_graph(workflow)

    def set_graph(self, compiled_graph: Any) -> None:
        """Set the graph to execute.

        Args:
            compiled_graph: A LangGraph CompiledGraph instance.
        """
        # Stop any running execution first
        self.stop()

        self._compiled_graph = compiled_graph
        self._state = self._create_initial_state()
        self._notify_update()

    def run(self, initial_state: dict[str, Any] | None = None) -> None:
        """Start continuous execution in background thread.

        Args:
            initial_state: Initial graph state dictionary.
        """
        if self._compiled_graph is None:
            return
        super().run(initial_state)

    def step(self, initial_state: dict[str, Any] | None = None) -> None:
        """Execute a single step.

        Args:
            initial_state: Initial graph state dictionary.
        """
        if self._compiled_graph is None and not self.is_running:
            return
        super().step(initial_state)

    def _execute_loop(self, initial_state: dict[str, Any]) -> None:
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
            current_node_id="__start__",
            breakpoints=breakpoints,
        )
        self._notify_update()

        # Brief pause to show __start__ highlighted
        time.sleep(0.2)

        # Use LangGraph's stream() for step-by-step execution
        for event in self._compiled_graph.stream(initial_state):
            if self._check_should_stop():
                break

            # Get the node name from the event for breakpoint checking
            node_name = next(iter(event.keys()), None)

            # Check for breakpoint BEFORE processing
            if node_name and not self._check_breakpoint(node_name):
                break

            # Wait while paused (manual pause)
            if not self._wait_for_pause():
                break

            # In step mode, wait for step signal
            if not self._wait_for_step():
                break

            # Process the step event
            self._process_step_event(event)

        # Record edge to __end__ and show __end__ node highlighted
        previous_node = self._state.current_node_id
        if previous_node and previous_node != "__end__":
            self._record_edge(previous_node, "__end__")
        self._set_current_node("__end__")
        self._notify_update()
        time.sleep(0.3)

        # Execution completed successfully
        self._set_status(ExecutionStatus.COMPLETED)
        self._set_current_node(None)
        self._state.paused_at_breakpoint = False
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
                self._record_edge(previous_node, node_name)

            # Update current node
            self._set_current_node(node_name)

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
            self._record_step(step_result)

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
