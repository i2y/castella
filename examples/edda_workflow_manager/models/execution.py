"""Edda-specific execution state models.

Extends the base studio execution models with Edda-specific fields.
"""

from __future__ import annotations

from typing import Any

from pydantic import Field

from castella.studio.models.execution import (
    BaseExecutionState,
    BaseStepResult,
    ExecutionStatus,
)

from .instance import InstanceStatus, ActivityHistory, ActivityStatus


class EddaStepResult(BaseStepResult):
    """Extended step result with Edda-specific fields.

    Attributes:
        activity_name: Name of the activity function.
        event_type: Edda event type (ActivityCompleted, ActivityFailed, etc.).
        has_compensation: Whether this activity has a registered compensation.
        is_compensation: Whether this is a compensation activity.
    """

    activity_name: str = ""
    event_type: str = ""
    has_compensation: bool = False
    is_compensation: bool = False

    @classmethod
    def from_activity_history(
        cls,
        history: ActivityHistory,
        compensations: dict[str, Any] | None = None,
    ) -> EddaStepResult:
        """Create from ActivityHistory model."""
        has_compensation = False
        if compensations and history.activity_id in compensations:
            has_compensation = True

        return cls(
            node_id=history.activity_name,
            state_before={},
            state_after={},
            started_at_ms=history.executed_at.timestamp() * 1000,
            duration_ms=0,  # Duration not tracked per-activity in Edda
            error=history.error_message,
            metadata={
                "input": history.input_data,
                "output": history.output_data,
                "error_type": history.error_type,
                "stack_trace": history.stack_trace,
            },
            activity_name=history.activity_name,
            event_type=history.event_type,
            has_compensation=has_compensation,
            is_compensation=history.is_compensation,
        )


class EddaExecutionState(BaseExecutionState):
    """Execution state for Edda workflows.

    Extends BaseExecutionState with Edda-specific tracking.

    Attributes:
        instance_id: Edda workflow instance ID.
        workflow_name: Name of the workflow.
        instance_status: Status from Edda storage.
        compensations: List of registered compensation activity IDs.
        current_activity_name: Name of the current activity.
        active_step_ids: Set of currently active step IDs (for highlighting).
    """

    instance_id: str | None = None
    workflow_name: str = ""
    instance_status: InstanceStatus = InstanceStatus.RUNNING
    compensations: list[str] = Field(default_factory=list)
    current_activity_name: str | None = None
    active_step_ids: set[str] = Field(default_factory=set)

    @classmethod
    def from_instance(
        cls,
        instance_id: str,
        workflow_name: str,
        status: InstanceStatus,
        history: list[ActivityHistory],
        current_activity_id: str | None = None,
        compensations: dict[str, Any] | None = None,
    ) -> EddaExecutionState:
        """Create execution state from Edda instance data.

        Args:
            instance_id: Workflow instance ID.
            workflow_name: Workflow name.
            status: Instance status.
            history: List of activity history records.
            current_activity_id: Current activity ID.
            compensations: Dict of activity_id -> compensation info.

        Returns:
            EddaExecutionState instance.
        """
        # Map instance status to execution status
        if status == InstanceStatus.COMPLETED:
            exec_status = ExecutionStatus.COMPLETED
        elif status == InstanceStatus.FAILED:
            exec_status = ExecutionStatus.ERROR
        elif status.is_waiting:
            exec_status = ExecutionStatus.PAUSED
        elif status == InstanceStatus.RUNNING:
            exec_status = ExecutionStatus.RUNNING
        elif status == InstanceStatus.COMPENSATING:
            exec_status = ExecutionStatus.RUNNING
        else:
            exec_status = ExecutionStatus.IDLE

        # Build step history
        step_history = []
        executed_edges: list[tuple[str, str]] = []
        active_step_ids: set[str] = set()
        current_activity_name = None
        prev_activity_name = None

        for h in history:
            step = EddaStepResult.from_activity_history(h, compensations)
            step_history.append(step)

            # Track edges between activities
            if prev_activity_name and prev_activity_name != h.activity_name:
                executed_edges.append((prev_activity_name, h.activity_name))
            prev_activity_name = h.activity_name

            # Identify current/active activity
            if h.status == ActivityStatus.RUNNING:
                active_step_ids.add(h.activity_name)
                current_activity_name = h.activity_name

        # If instance is running but no running activity found,
        # the current_activity_id indicates what's being executed
        if status == InstanceStatus.RUNNING and not active_step_ids:
            if current_activity_id:
                # Try to find activity name from history
                for h in history:
                    if h.activity_id == current_activity_id:
                        active_step_ids.add(h.activity_name)
                        current_activity_name = h.activity_name
                        break

        # Get compensation activity IDs
        comp_list = list(compensations.keys()) if compensations else []

        # Find error message from failed activities
        error_message = None
        for h in reversed(history):
            if h.has_error and h.error_message:
                error_message = h.error_message
                break

        return cls(
            status=exec_status,
            current_node_id=current_activity_name,
            step_history=step_history,
            total_steps=len(step_history),
            error_message=error_message,
            breakpoints=set(),
            paused_at_breakpoint=False,
            executed_edges=executed_edges,
            instance_id=instance_id,
            workflow_name=workflow_name,
            instance_status=status,
            compensations=comp_list,
            current_activity_name=current_activity_name,
            active_step_ids=active_step_ids,
        )

    @property
    def completed_step_ids(self) -> set[str]:
        """Get set of completed step IDs for highlighting."""
        return {
            step.node_id
            for step in self.step_history
            if not step.error and not getattr(step, "is_compensation", False)
        }

    @property
    def failed_step_ids(self) -> set[str]:
        """Get set of failed step IDs for highlighting."""
        return {step.node_id for step in self.step_history if step.error}

    @property
    def compensated_step_ids(self) -> set[str]:
        """Get set of compensated step IDs."""
        return {
            step.node_id
            for step in self.step_history
            if getattr(step, "is_compensation", False) and not step.error
        }
