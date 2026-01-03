"""Workflow model for LlamaIndex Workflow Studio.

This model represents the complete workflow structure for visualization.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from .events import EventTypeModel
from .steps import StepModel


class EventEdge(BaseModel):
    """An edge representing event flow between steps.

    Attributes:
        id: Unique edge identifier.
        event_type: The event type name flowing on this edge.
        source_step_id: Source step ID (None for StartEvent).
        target_step_id: Target step ID (None for StopEvent).
        is_part_of_union: Whether this edge is part of a Union output.
        is_part_of_collect: Whether this edge is part of a Collect input.
    """

    id: str
    event_type: str
    source_step_id: str | None = None
    target_step_id: str | None = None
    is_part_of_union: bool = False
    is_part_of_collect: bool = False


class WorkflowModel(BaseModel):
    """Complete workflow representation.

    Attributes:
        name: Workflow class name.
        event_types: Registry of event types by name.
        steps: List of steps in the workflow.
        edges: List of event flow edges.
        start_event_type: The StartEvent type name.
        stop_event_type: The StopEvent type name.
    """

    name: str = "Workflow"

    # Event types registry
    event_types: dict[str, EventTypeModel] = Field(default_factory=dict)

    # Steps
    steps: list[StepModel] = Field(default_factory=list)

    # Event flow edges
    edges: list[EventEdge] = Field(default_factory=list)

    # Entry/exit
    start_event_type: str = "StartEvent"
    stop_event_type: str = "StopEvent"

    def get_step(self, step_id: str) -> StepModel | None:
        """Get a step by ID."""
        for step in self.steps:
            if step.id == step_id:
                return step
        return None

    def get_edges_from_step(self, step_id: str) -> list[EventEdge]:
        """Get all edges originating from a step."""
        return [e for e in self.edges if e.source_step_id == step_id]

    def get_edges_to_step(self, step_id: str) -> list[EventEdge]:
        """Get all edges targeting a step."""
        return [e for e in self.edges if e.target_step_id == step_id]

    def get_event_type(self, name: str) -> EventTypeModel | None:
        """Get an event type by name."""
        return self.event_types.get(name)

    def get_steps_consuming_event(self, event_type: str) -> list[StepModel]:
        """Get all steps that consume a given event type."""
        result = []
        for step in self.steps:
            if event_type in step.input_events:
                result.append(step)
        return result

    def get_steps_producing_event(self, event_type: str) -> list[StepModel]:
        """Get all steps that produce a given event type."""
        result = []
        for step in self.steps:
            if event_type in step.output_events:
                result.append(step)
        return result
