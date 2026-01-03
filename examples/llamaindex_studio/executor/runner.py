"""Workflow executor for LlamaIndex Workflow Studio.

Extends BaseWorkflowExecutor to execute LlamaIndex Workflows with
event tracking and step visualization.
"""

from __future__ import annotations

import asyncio
import threading
import time
from typing import Any, Callable, TYPE_CHECKING

from castella.studio.executor.base import BaseWorkflowExecutor
from castella.studio.models.execution import ExecutionStatus

from ..models.execution import WorkflowExecutionState, StepExecution, EventQueueItem
from ..models.workflow import WorkflowModel

if TYPE_CHECKING:
    pass


class WorkflowExecutor(BaseWorkflowExecutor):
    """Executor for LlamaIndex Workflow.

    Handles workflow execution with:
    - Event tracking (input and output events)
    - Step execution timing
    - Context store monitoring
    - Breakpoint support
    - Step-by-step execution mode
    """

    def __init__(
        self,
        on_state_update: Callable[[WorkflowExecutionState], None],
    ):
        """Initialize the workflow executor.

        Args:
            on_state_update: Callback for execution state updates.
        """
        super().__init__(on_state_update)

        self._workflow_class: type | None = None
        self._workflow_instance: Any = None
        self._workflow_model: WorkflowModel | None = None
        self._asyncio_loop: asyncio.AbstractEventLoop | None = None

    def _create_initial_state(self) -> WorkflowExecutionState:
        """Create initial execution state.

        Returns:
            New WorkflowExecutionState.
        """
        return WorkflowExecutionState()

    def set_workflow(self, workflow: Any) -> None:
        """Set the workflow to execute.

        Args:
            workflow: A LlamaIndex Workflow class.
        """
        self._workflow_class = workflow
        self._workflow_instance = None

    def set_workflow_model(self, model: WorkflowModel) -> None:
        """Set the workflow model for visualization.

        Args:
            model: The WorkflowModel for the workflow.
        """
        self._workflow_model = model

    def _execute_loop(self, initial_state: dict[str, Any]) -> None:
        """Execute the workflow in the background thread.

        Creates an async event loop and runs the workflow.

        Args:
            initial_state: Initial input data for the workflow.
        """
        # Create async event loop for this thread
        self._asyncio_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._asyncio_loop)

        try:
            self._asyncio_loop.run_until_complete(
                self._async_execute(initial_state)
            )
        finally:
            self._asyncio_loop.close()
            self._asyncio_loop = None

    async def _async_execute(self, initial_input: dict[str, Any]) -> None:
        """Async execution of the workflow.

        Args:
            initial_input: Initial input data.
        """
        if self._workflow_class is None:
            self._set_error("No workflow set")
            self._notify_update()
            return

        # Reset state
        state = self._state
        if isinstance(state, WorkflowExecutionState):
            state.step_history = []
            state.event_queue = []
            state.active_step_ids = set()
            state.executed_edges = []
            state.current_context = {}
            state.start_time_ms = time.time() * 1000
            state.current_time_ms = state.start_time_ms

        self._set_status(ExecutionStatus.RUNNING)
        self._notify_update()

        try:
            # Create workflow instance
            self._workflow_instance = self._workflow_class()

            # Execute with event tracing
            await self._run_with_tracing(initial_input)

        except Exception as e:
            self._set_error(f"Workflow error: {e}")
            self._notify_update()
            return

        if self._check_should_stop():
            self._set_status(ExecutionStatus.IDLE)
        else:
            self._set_status(ExecutionStatus.COMPLETED)

        self._notify_update()

    async def _run_with_tracing(self, initial_input: dict[str, Any]) -> None:
        """Run the workflow with event and step tracing.

        LlamaIndex Workflow has a complex event-driven execution model.
        We use instrumentation to track events and steps.

        Args:
            initial_input: Initial input data.
        """
        try:
            from llama_index.core.workflow import Workflow, Event, StartEvent, StopEvent
            from llama_index.core.workflow.handler import WorkflowHandler
        except ImportError:
            self._set_error("llama-index-workflows is not installed")
            self._notify_update()
            return

        workflow = self._workflow_instance
        state = self._state

        if not isinstance(workflow, Workflow):
            self._set_error("Invalid workflow instance")
            return

        # Create StartEvent
        start_event = StartEvent(**initial_input)

        # Record start event in queue
        if isinstance(state, WorkflowExecutionState):
            state.event_queue.append(EventQueueItem(
                event_type="StartEvent",
                data=initial_input,
                source_step_id=None,
                queued_at_ms=time.time() * 1000,
            ))
            self._notify_update()

        # Get handler for streaming events
        handler: WorkflowHandler = workflow.run(**initial_input)

        # Track step executions
        try:
            # Use stream_events if available for detailed tracking
            if hasattr(handler, "stream_events"):
                await self._trace_stream_events(handler, state)
            else:
                # Fallback: just await the result
                result = await handler

                # Record final result
                if isinstance(state, WorkflowExecutionState):
                    state.current_time_ms = time.time() * 1000

                    # If result is StopEvent, extract its data
                    if isinstance(result, StopEvent):
                        self._record_stop_event(result, state)

        except Exception as e:
            self._set_error(f"Execution error: {e}")

    async def _trace_stream_events(
        self, handler: Any, state: WorkflowExecutionState
    ) -> None:
        """Trace events from the workflow handler stream.

        Args:
            handler: WorkflowHandler instance.
            state: Execution state to update.
        """
        from llama_index.core.workflow import StopEvent

        current_step_start: dict[str, float] = {}
        last_step_id: str | None = None
        last_event_type: str | None = None

        async for event in handler.stream_events():
            if self._check_should_stop():
                break

            event_type = type(event).__name__
            event_time = time.time() * 1000

            # Update current time
            if isinstance(state, WorkflowExecutionState):
                state.current_time_ms = event_time

            # Determine which step produced this event
            source_step = getattr(event, "_source_step", None)
            if source_step is None:
                # Try to infer from workflow model
                source_step = self._infer_source_step(event_type)

            # Record event in queue
            event_data = {}
            if hasattr(event, "model_dump"):
                try:
                    event_data = event.model_dump()
                except Exception:
                    event_data = {"type": event_type}
            elif hasattr(event, "__dict__"):
                event_data = {k: v for k, v in event.__dict__.items() if not k.startswith("_")}

            if isinstance(state, WorkflowExecutionState):
                state.event_queue.append(EventQueueItem(
                    event_type=event_type,
                    data=event_data,
                    source_step_id=source_step,
                    queued_at_ms=event_time,
                ))

            # If previous step ended (new event from different source)
            if last_step_id and last_step_id != source_step:
                end_time = event_time
                start_time = current_step_start.get(last_step_id, end_time)

                # Create step execution record
                step_exec = StepExecution(
                    node_id=last_step_id,
                    state_before={},
                    state_after={},
                    started_at_ms=start_time,
                    duration_ms=end_time - start_time,
                    error=None,
                    metadata={},
                    input_event_type=last_event_type or "",
                    input_event_data={},
                    output_event_type=event_type,
                    output_event_data=event_data,
                )

                self._record_step(step_exec)

                # Record edge
                if last_step_id and source_step:
                    self._record_edge(last_step_id, source_step)

                # Update active steps
                if isinstance(state, WorkflowExecutionState):
                    state.active_step_ids.discard(last_step_id)

            # Track which step will handle this event
            target_step = self._find_step_for_event(event_type)
            if target_step:
                current_step_start[target_step] = event_time

                # Check breakpoint
                if not self._check_breakpoint(target_step):
                    return

                # Wait for step in step mode
                if not self._wait_for_step():
                    return

                # Wait for pause
                if not self._wait_for_pause():
                    return

                # Set as active
                if isinstance(state, WorkflowExecutionState):
                    state.active_step_ids.add(target_step)

                self._set_current_node(target_step)

            last_step_id = target_step
            last_event_type = event_type

            self._notify_update()

            # Handle StopEvent
            if isinstance(event, StopEvent):
                self._record_stop_event(event, state)
                break

    def _record_stop_event(
        self, event: Any, state: WorkflowExecutionState
    ) -> None:
        """Record stop event details.

        Args:
            event: The StopEvent instance.
            state: Execution state to update.
        """
        # Extract result from StopEvent
        result_data = {}
        if hasattr(event, "result"):
            result = event.result
            if hasattr(result, "model_dump"):
                try:
                    result_data = result.model_dump()
                except Exception:
                    result_data = {"result": str(result)}
            else:
                result_data = {"result": str(result)}

        state.event_queue.append(EventQueueItem(
            event_type="StopEvent",
            data=result_data,
            source_step_id=None,
            queued_at_ms=time.time() * 1000,
        ))

    def _infer_source_step(self, event_type: str) -> str | None:
        """Infer which step produced an event based on workflow model.

        Args:
            event_type: The event type name.

        Returns:
            Step ID or None.
        """
        if self._workflow_model is None:
            return None

        for step in self._workflow_model.steps:
            if event_type in step.output_events:
                return step.id

        return None

    def _find_step_for_event(self, event_type: str) -> str | None:
        """Find which step handles a given event type.

        Args:
            event_type: The event type name.

        Returns:
            Step ID or None.
        """
        if self._workflow_model is None:
            return None

        for step in self._workflow_model.steps:
            if event_type in step.input_events:
                return step.id

        return None

    @property
    def workflow_instance(self) -> Any:
        """Get the current workflow instance."""
        return self._workflow_instance

    # ========== Mock Execution Methods ==========

    def run_mock(self) -> None:
        """Run mock workflow execution (simulated).

        This simulates workflow execution without requiring the actual
        llama-index-workflows library. Uses the workflow model to determine
        the execution path.
        """
        if self._workflow_model is None:
            return

        if self._thread and self._thread.is_alive():
            return  # Already running

        self._stop_requested = False
        self._pause_requested = False
        self._step_mode = False

        self._thread = threading.Thread(
            target=self._mock_execute_loop,
            daemon=True,
        )
        self._thread.start()

    def step_mock(self) -> None:
        """Execute a single mock step.

        If already running, triggers one step. Otherwise starts
        execution in step mode.
        """
        if self._workflow_model is None:
            return

        if self._thread and self._thread.is_alive():
            # Already running - trigger one step
            self._step_event.set()
            return

        # Start in step mode
        self._stop_requested = False
        self._pause_requested = False
        self._step_mode = True
        self._step_event.clear()

        self._thread = threading.Thread(
            target=self._mock_execute_loop,
            daemon=True,
        )
        self._thread.start()

    def _mock_execute_loop(self) -> None:
        """Execute mock workflow in background thread.

        Simulates workflow execution by stepping through each step
        in the workflow model in order, including START and END nodes.
        """
        if self._workflow_model is None:
            return

        state = self._state
        if isinstance(state, WorkflowExecutionState):
            state.step_history = []
            state.event_queue = []
            state.active_step_ids = set()
            state.executed_edges = []
            state.current_context = {}
            state.start_time_ms = time.time() * 1000
            state.current_time_ms = state.start_time_ms

        self._set_status(ExecutionStatus.RUNNING)
        self._notify_update()

        model = self._workflow_model

        try:
            # ===== START node =====
            if self._check_should_stop():
                self._set_status(ExecutionStatus.IDLE)
                self._notify_update()
                return

            if not self._check_breakpoint("__start__"):
                return
            if not self._wait_for_step():
                return
            if not self._wait_for_pause():
                return

            # Activate START node
            start_begin = time.time() * 1000
            self._set_current_node("__start__")
            if isinstance(state, WorkflowExecutionState):
                state.active_step_ids.add("__start__")
                state.current_time_ms = start_begin
            self._notify_update()

            time.sleep(0.3)

            start_end = time.time() * 1000

            # Record START step execution
            start_exec = StepExecution(
                node_id="__start__",
                state_before={},
                state_after={},
                started_at_ms=start_begin,
                duration_ms=start_end - start_begin,
                error=None,
                metadata={},
                input_event_type="",
                input_event_data={},
                output_event_type=model.start_event_type,
                output_event_data={},
            )
            self._record_step(start_exec)

            # Simulate StartEvent
            if isinstance(state, WorkflowExecutionState):
                state.event_queue.append(EventQueueItem(
                    event_type=model.start_event_type,
                    data={},
                    source_step_id="__start__",
                    queued_at_ms=start_end,
                ))
                state.active_step_ids.discard("__start__")
                state.current_time_ms = start_end
            self._notify_update()

            # Build execution order from edges
            execution_order = self._build_execution_order(model)

            # Find first step to record edge from START
            first_step_id = execution_order[0] if execution_order else None

            # Execute each step
            last_step_id: str = "__start__"
            for step_id in execution_order:
                if self._check_should_stop():
                    break

                # Check breakpoint
                if not self._check_breakpoint(step_id):
                    break

                # Wait for step in step mode
                if not self._wait_for_step():
                    break

                # Wait for pause
                if not self._wait_for_pause():
                    break

                step = model.get_step(step_id)
                if not step:
                    continue

                step_start = time.time() * 1000

                # Record edge from previous step
                self._record_edge(last_step_id, step_id)

                # Set as active
                self._set_current_node(step_id)
                if isinstance(state, WorkflowExecutionState):
                    state.active_step_ids.add(step_id)
                    state.current_time_ms = step_start
                self._notify_update()

                # Simulate step execution delay
                time.sleep(0.5)

                step_end = time.time() * 1000

                # Create step execution record
                input_event = step.input_events[0] if step.input_events else ""
                output_event = step.output_events[0] if step.output_events else ""

                step_exec = StepExecution(
                    node_id=step_id,
                    state_before={},
                    state_after={},
                    started_at_ms=step_start,
                    duration_ms=step_end - step_start,
                    error=None,
                    metadata={},
                    input_event_type=input_event,
                    input_event_data={},
                    output_event_type=output_event,
                    output_event_data={},
                )

                self._record_step(step_exec)

                # Record output event in queue
                if isinstance(state, WorkflowExecutionState) and output_event:
                    state.event_queue.append(EventQueueItem(
                        event_type=output_event,
                        data={},
                        source_step_id=step_id,
                        queued_at_ms=step_end,
                    ))
                    state.current_time_ms = step_end

                # Clear active
                if isinstance(state, WorkflowExecutionState):
                    state.active_step_ids.discard(step_id)

                last_step_id = step_id
                self._notify_update()

            # ===== END node =====
            if not self._check_should_stop():
                if not self._check_breakpoint("__end__"):
                    return
                if not self._wait_for_step():
                    return
                if not self._wait_for_pause():
                    return

                # Record edge to END
                self._record_edge(last_step_id, "__end__")

                # Activate END node
                end_begin = time.time() * 1000
                self._set_current_node("__end__")
                if isinstance(state, WorkflowExecutionState):
                    state.active_step_ids.add("__end__")
                    state.current_time_ms = end_begin
                self._notify_update()

                time.sleep(0.3)

                end_end = time.time() * 1000

                # Record END step execution
                end_exec = StepExecution(
                    node_id="__end__",
                    state_before={},
                    state_after={},
                    started_at_ms=end_begin,
                    duration_ms=end_end - end_begin,
                    error=None,
                    metadata={},
                    input_event_type=model.stop_event_type,
                    input_event_data={},
                    output_event_type="",
                    output_event_data={},
                )
                self._record_step(end_exec)

                # Simulate StopEvent
                if isinstance(state, WorkflowExecutionState):
                    state.event_queue.append(EventQueueItem(
                        event_type=model.stop_event_type,
                        data={},
                        source_step_id="__end__",
                        queued_at_ms=end_end,
                    ))
                    state.active_step_ids.discard("__end__")
                    state.current_time_ms = end_end

            if self._check_should_stop():
                self._set_status(ExecutionStatus.IDLE)
            else:
                self._set_status(ExecutionStatus.COMPLETED)

            self._set_current_node(None)
            self._notify_update()

        except Exception as e:
            self._set_error(f"Mock execution error: {e}")
            self._notify_update()

    def _build_execution_order(self, model: WorkflowModel) -> list[str]:
        """Build execution order from workflow model.

        Uses topological sort based on edges to determine order.

        Args:
            model: The workflow model.

        Returns:
            List of step IDs in execution order.
        """
        # Build adjacency from edges
        from collections import deque

        in_degree: dict[str, int] = {step.id: 0 for step in model.steps}
        adjacency: dict[str, list[str]] = {step.id: [] for step in model.steps}

        for edge in model.edges:
            source = edge.source_step_id
            target = edge.target_step_id
            if source and target and source in adjacency and target in in_degree:
                adjacency[source].append(target)
                in_degree[target] += 1

        # Find starting steps (in_degree == 0)
        queue = deque([s for s, d in in_degree.items() if d == 0])
        result: list[str] = []

        while queue:
            step_id = queue.popleft()
            result.append(step_id)

            for next_step in adjacency.get(step_id, []):
                in_degree[next_step] -= 1
                if in_degree[next_step] == 0:
                    queue.append(next_step)

        # If no edges, just return steps in order
        if not result:
            result = [step.id for step in model.steps]

        return result
