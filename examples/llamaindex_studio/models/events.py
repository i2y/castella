"""Event type models for LlamaIndex Workflow Studio.

These models represent event types in the workflow for visualization.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class EventCategory(str, Enum):
    """Category of event for visual styling."""

    START = "start"       # StartEvent - green
    STOP = "stop"         # StopEvent - red
    USER = "user"         # User-defined events - blue
    SYSTEM = "system"     # System events - gray


# Event category to color mapping
EVENT_COLORS = {
    EventCategory.START: "#22c55e",   # Green
    EventCategory.STOP: "#ef4444",    # Red
    EventCategory.USER: "#3b82f6",    # Blue
    EventCategory.SYSTEM: "#9ca3af",  # Gray
}


class EventTypeModel(BaseModel):
    """Represents an event type in the workflow.

    Attributes:
        name: Event class name (e.g., "ProcessedEvent").
        module: Module where the event is defined.
        category: Event category for visual styling.
        fields: Field name to type hint mapping.
        docstring: Event class docstring.
    """

    name: str
    module: str = ""
    category: EventCategory = EventCategory.USER
    fields: dict[str, str] = Field(default_factory=dict)
    docstring: str | None = None

    def get_color(self) -> str:
        """Get the color for this event category."""
        return EVENT_COLORS.get(self.category, EVENT_COLORS[EventCategory.USER])


class EventInstance(BaseModel):
    """A concrete event instance during execution.

    Attributes:
        event_type: Name of the event type.
        timestamp_ms: When the event was emitted.
        payload: Event data/payload.
        source_step_id: Which step emitted this event.
        consumed_by_step_id: Which step consumed this event.
    """

    event_type: str
    timestamp_ms: float
    payload: dict[str, Any] = Field(default_factory=dict)
    source_step_id: str | None = None
    consumed_by_step_id: str | None = None
