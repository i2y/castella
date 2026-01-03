"""Base workflow executor with threading support.

This module provides the abstract base class for workflow executors,
handling common threading logic for run, step, pause, resume, and stop.
"""

from __future__ import annotations

import threading
from abc import ABC, abstractmethod
from typing import Any, Callable

from castella.studio.models.execution import (
    BaseExecutionState,
    BaseStepResult,
    ExecutionStatus,
)


class BaseWorkflowExecutor(ABC):
    """Base class for workflow executors with threading support.

    Provides common threading logic for:
    - Continuous execution (run)
    - Step-by-step execution (step)
    - Pause/resume
    - Stop
    - Breakpoints

    Subclasses must implement:
    - _create_initial_state(): Create framework-specific initial state
    - set_workflow(workflow): Set the workflow to execute
    - _execute_loop(initial_state): Main execution loop (framework-specific)
    """

    def __init__(
        self,
        on_state_update: Callable[[BaseExecutionState], None],
    ):
        """Initialize the executor.

        Args:
            on_state_update: Callback for execution state updates.
                Called from background thread, but Castella's State.set()
                is thread-safe.
        """
        self._on_state_update = on_state_update

        # Threading state
        self._thread: threading.Thread | None = None
        self._stop_requested = False
        self._pause_requested = False
        self._step_mode = False
        self._step_event = threading.Event()

        # Execution state
        self._state: BaseExecutionState = self._create_initial_state()

    @abstractmethod
    def _create_initial_state(self) -> BaseExecutionState:
        """Create the initial execution state.

        Subclasses should return their framework-specific state class.

        Returns:
            Initial execution state.
        """
        pass

    @abstractmethod
    def set_workflow(self, workflow: Any) -> None:
        """Set the workflow to execute.

        Args:
            workflow: A workflow instance (CompiledGraph, Workflow, etc.).
        """
        pass

    @abstractmethod
    def _execute_loop(self, initial_state: dict[str, Any]) -> None:
        """Main execution loop (runs in background thread).

        Subclasses must implement the framework-specific execution logic.
        Use the following helper methods:
        - _check_should_stop(): Returns True if stop was requested
        - _check_breakpoint(node_id): Handles breakpoint pause
        - _wait_for_pause(): Handles manual pause
        - _wait_for_step(): Handles step mode
        - _record_step(result): Records a step result
        - _notify_update(): Notifies UI of state change

        Args:
            initial_state: Initial workflow state.
        """
        pass

    def run(self, initial_state: dict[str, Any] | None = None) -> None:
        """Start continuous execution in background thread.

        Args:
            initial_state: Initial workflow state dictionary.
        """
        if self._thread and self._thread.is_alive():
            return  # Already running

        self._stop_requested = False
        self._pause_requested = False
        self._step_mode = False
        self._step_event.clear()  # Clear any previous event state

        self._thread = threading.Thread(
            target=self._run_wrapper,
            args=(initial_state or {},),
            daemon=True,
        )
        self._thread.start()

    def step(self, initial_state: dict[str, Any] | None = None) -> None:
        """Execute a single step.

        If already running, triggers one step. Otherwise starts
        execution in step mode.

        Args:
            initial_state: Initial workflow state dictionary.
        """
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
            target=self._run_wrapper,
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
        self._state = self._create_initial_state()
        self._state.breakpoints = breakpoints
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
    def current_state(self) -> BaseExecutionState:
        """Get current execution state."""
        return self._state

    def _run_wrapper(self, initial_state: dict[str, Any]) -> None:
        """Wrapper for _execute_loop with error handling.

        Args:
            initial_state: Initial workflow state.
        """
        try:
            self._execute_loop(initial_state)
        except Exception as e:
            self._state.status = ExecutionStatus.ERROR
            self._state.error_message = str(e)
            self._notify_update()

    def _check_should_stop(self) -> bool:
        """Check if stop was requested.

        Returns:
            True if stop was requested.
        """
        return self._stop_requested

    def _check_breakpoint(self, node_id: str) -> bool:
        """Check and handle breakpoint at the given node.

        If a breakpoint is set, this method will pause execution and wait
        for continue signal.

        Args:
            node_id: The node ID to check for breakpoint.

        Returns:
            True if execution should continue, False if stop was requested.
        """
        if node_id not in self._state.breakpoints:
            return True

        self._state.status = ExecutionStatus.PAUSED
        self._state.paused_at_breakpoint = True
        self._state.current_node_id = node_id
        self._notify_update()

        # Wait for continue signal
        self._step_event.wait()
        self._step_event.clear()

        if self._stop_requested:
            return False

        self._state.paused_at_breakpoint = False
        self._state.status = ExecutionStatus.RUNNING
        return True

    def _wait_for_pause(self) -> bool:
        """Wait while paused (manual pause).

        Returns:
            True if execution should continue, False if stop was requested.
        """
        import time

        while self._pause_requested and not self._stop_requested:
            self._state.status = ExecutionStatus.PAUSED
            self._notify_update()
            time.sleep(0.1)

        if self._stop_requested:
            return False

        if self._state.status == ExecutionStatus.PAUSED:
            self._state.status = ExecutionStatus.RUNNING

        return True

    def _wait_for_step(self) -> bool:
        """Wait for step signal in step mode.

        Returns:
            True if execution should continue, False if stop was requested.
        """
        if not self._step_mode:
            return True

        self._state.status = ExecutionStatus.PAUSED
        self._notify_update()
        self._step_event.wait()
        self._step_event.clear()

        if self._stop_requested:
            return False

        self._state.status = ExecutionStatus.RUNNING
        return True

    def _record_step(self, result: BaseStepResult) -> None:
        """Record a step result.

        Args:
            result: The step result to record.
        """
        self._state.step_history.append(result)
        self._state.total_steps += 1

    def _record_edge(self, source_id: str, target_id: str) -> None:
        """Record an executed edge.

        Args:
            source_id: Source node ID.
            target_id: Target node ID.
        """
        self._state.executed_edges.append((source_id, target_id))

    def _set_current_node(self, node_id: str | None) -> None:
        """Set the current node ID.

        Args:
            node_id: The current node ID.
        """
        self._state.current_node_id = node_id

    def _set_status(self, status: ExecutionStatus) -> None:
        """Set the execution status.

        Args:
            status: The new status.
        """
        self._state.status = status

    def _set_error(self, message: str) -> None:
        """Set an error message.

        Args:
            message: The error message.
        """
        self._state.status = ExecutionStatus.ERROR
        self._state.error_message = message

    def _notify_update(self) -> None:
        """Notify UI of state update.

        Creates a deep copy to ensure thread safety.
        """
        # Create a copy to avoid threading issues
        state_copy = self._state.model_copy(deep=True)
        self._on_state_update(state_copy)
