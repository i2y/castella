"""Execution state models for LlamaIndex Workflow Studio.

Extends the base execution models with event-driven specific features.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from castella.studio.models.execution import (
    ExecutionStatus,
    BaseStepResult,
    BaseExecutionState,
    compute_state_diff,
)


class EventQueueItem(BaseModel):
    """An event waiting to be processed in the queue.

    Attributes:
        event_type: The event type name.
        data: Event payload data.
        source_step_id: Which step emitted this event.
        queued_at_ms: When the event was added to the queue.
    """

    event_type: str
    data: dict[str, Any] = Field(default_factory=dict)
    source_step_id: str | None = None
    queued_at_ms: float = 0.0


class CollectState(BaseModel):
    """State for Collect (AND) pattern tracking.

    Tracks which events have been received for steps
    that require multiple events.

    Attributes:
        required_events: Set of event types required.
        received_events: Set of event types received so far.
    """

    required_events: set[str] = Field(default_factory=set)
    received_events: set[str] = Field(default_factory=set)

    @property
    def is_complete(self) -> bool:
        """Check if all required events have been received."""
        return self.required_events == self.received_events


class StepExecution(BaseStepResult):
    """Record of a single step execution with event-driven details.

    Extends BaseStepResult with:
        input_event_type: The event type that triggered this step.
        input_event_data: The event payload data.
        output_event_type: The event type emitted by this step.
        output_event_data: The emitted event payload.
        context_before: Context store before execution.
        context_after: Context store after execution.
    """

    input_event_type: str = ""
    input_event_data: dict[str, Any] = Field(default_factory=dict)

    output_event_type: str | None = None
    output_event_data: dict[str, Any] = Field(default_factory=dict)

    context_before: dict[str, Any] = Field(default_factory=dict)
    context_after: dict[str, Any] = Field(default_factory=dict)


class WorkflowExecutionState(BaseExecutionState):
    """LlamaIndex Workflow execution state.

    Extends BaseExecutionState with event-driven specific features:
        step_history: List of StepExecution records.
        event_queue: Pending events waiting to be processed.
        active_step_ids: Set of currently executing step IDs.
        collect_pending: Collect state for each step waiting on AND.
        current_context: Current context store data.
        context_history: History of context snapshots.
        start_time_ms: Workflow start time.
        current_time_ms: Current execution time.
    """

    # Override step_history type
    step_history: list[StepExecution] = Field(default_factory=list)

    # Event queue (pending events)
    event_queue: list[EventQueueItem] = Field(default_factory=list)

    # Currently active steps (can be multiple in parallel)
    active_step_ids: set[str] = Field(default_factory=set)

    # Collect state: step_id -> CollectState
    collect_pending: dict[str, CollectState] = Field(default_factory=dict)

    # Context store
    current_context: dict[str, Any] = Field(default_factory=dict)

    # Timeline
    start_time_ms: float = 0.0
    current_time_ms: float = 0.0


# Re-export for convenience
__all__ = [
    "ExecutionStatus",
    "EventQueueItem",
    "CollectState",
    "StepExecution",
    "WorkflowExecutionState",
    "compute_state_diff",
]
