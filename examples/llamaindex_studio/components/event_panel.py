"""Event panel for LlamaIndex Workflow Studio.

Displays the list of event types in the workflow with category-based colors.
"""

from __future__ import annotations

from typing import Callable

from castella import Component, Column, Row, Text, Spacer, Button, SizePolicy, Kind
from castella.models.style import TextAlign

from ..models.workflow import WorkflowModel
from ..models.events import EventTypeModel, EventCategory, EVENT_COLORS


# UI Constants
HEADER_HEIGHT = 28
EVENT_ROW_HEIGHT = 24


class EventPanel(Component):
    """Panel displaying event types in the workflow.

    Shows:
    - List of all event types
    - Color-coded category indicators
    - Click to highlight related edges in canvas
    """

    def __init__(
        self,
        workflow: WorkflowModel | None = None,
        selected_event: str | None = None,
        on_event_select: Callable[[str], None] | None = None,
    ):
        """Initialize the event panel.

        Args:
            workflow: The workflow model.
            selected_event: Currently selected event type name.
            on_event_select: Callback when an event type is clicked.
        """
        super().__init__()

        self._workflow = workflow
        self._selected_event = selected_event
        self._on_event_select = on_event_select

    def view(self):
        """Build the event panel UI."""
        rows = []

        # Header
        rows.append(
            Row(
                Spacer().fixed_width(8),
                Text("Events").fixed_height(HEADER_HEIGHT),
                Spacer(),
            ).fixed_height(HEADER_HEIGHT)
        )

        # Event type rows
        if self._workflow:
            for event_name, event_type in sorted(
                self._workflow.event_types.items(),
                key=lambda x: (x[1].category.value, x[0]),
            ):
                rows.append(self._build_event_row(event_name, event_type))

        # No trailing spacer for scrollable columns
        return Column(*rows, scrollable=True)

    def _build_event_row(
        self, event_name: str, event_type: EventTypeModel
    ) -> Row:
        """Build a row for an event type.

        Args:
            event_name: Event type name.
            event_type: Event type model.

        Returns:
            Row widget for the event.
        """
        color = event_type.get_color()
        is_selected = event_name == self._selected_event

        # Category symbol
        symbol = self._get_category_symbol(event_type.category)

        # Build clickable button styled as text
        display_text = f"{symbol}  {event_name}"

        # Use INFO kind for selected, NORMAL for unselected
        kind = Kind.INFO if is_selected else Kind.NORMAL

        if self._on_event_select:
            btn = (
                Button(display_text, align=TextAlign.LEFT)
                .kind(kind)
                .on_click(lambda _, name=event_name: self._on_event_select(name))
                .fixed_height(EVENT_ROW_HEIGHT)
                .width_policy(SizePolicy.EXPANDING)
            )
        else:
            btn = (
                Button(display_text, align=TextAlign.LEFT)
                .kind(kind)
                .fixed_height(EVENT_ROW_HEIGHT)
                .width_policy(SizePolicy.EXPANDING)
            )

        return Row(
            Spacer().fixed_width(8),
            btn,
            Spacer().fixed_width(8),
        ).fixed_height(EVENT_ROW_HEIGHT)

    def _get_category_symbol(self, category: EventCategory) -> str:
        """Get symbol for event category.

        Args:
            category: Event category.

        Returns:
            Symbol character.
        """
        symbols = {
            EventCategory.START: "▶",
            EventCategory.STOP: "■",
            EventCategory.USER: "◆",
            EventCategory.SYSTEM: "○",
        }
        return symbols.get(category, "●")


class EventQueuePanel(Component):
    """Panel showing pending events in the queue.

    Displays events waiting to be processed during execution.
    """

    def __init__(
        self,
        workflow: WorkflowModel | None = None,
        queue: list | None = None,
    ):
        """Initialize the event queue panel.

        Args:
            workflow: The workflow model for event colors.
            queue: List of EventQueueItem instances.
        """
        super().__init__()

        self._workflow = workflow
        self._queue = queue or []

    def view(self):
        """Build the event queue panel UI."""
        rows = []

        # Header
        rows.append(
            Row(
                Spacer().fixed_width(8),
                Text("Event Queue").fixed_height(HEADER_HEIGHT),
                Spacer(),
                Text(f"({len(self._queue)})").fixed_width(40),
                Spacer().fixed_width(8),
            ).fixed_height(HEADER_HEIGHT)
        )

        # Queue items
        if self._queue:
            for item in self._queue:
                rows.append(self._build_queue_item(item))
        else:
            rows.append(
                Row(
                    Spacer().fixed_width(12),
                    Text("No pending events").text_color("#6b7280"),
                    Spacer(),
                ).fixed_height(EVENT_ROW_HEIGHT)
            )

        # No trailing spacer for scrollable columns
        return Column(*rows, scrollable=True)

    def _build_queue_item(self, item) -> Row:
        """Build a row for a queue item.

        Args:
            item: EventQueueItem instance.

        Returns:
            Row widget.
        """
        event_type = item.event_type
        source = item.source_step_id or "external"

        # Get color from workflow
        color = EVENT_COLORS[EventCategory.USER]
        if self._workflow and event_type in self._workflow.event_types:
            color = self._workflow.event_types[event_type].get_color()

        return Row(
            Spacer().fixed_width(8),
            Text("●").text_color(color).fixed_width(16),
            Text(event_type).fixed_width(120),
            Text(f"from: {source}").text_color("#6b7280"),
            Spacer(),
        ).fixed_height(EVENT_ROW_HEIGHT)
