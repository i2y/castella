"""Context inspector for LlamaIndex Workflow Studio.

Displays the workflow context store (ctx) with timeline scrubbing.
"""

from __future__ import annotations

import json

from castella import Component, Column, Row, Text, Spacer
from castella import Slider, SliderState

from ..models.execution import WorkflowExecutionState


# UI Constants
HEADER_HEIGHT = 28


class ContextInspector(Component):
    """Panel displaying the workflow context store.

    Shows:
    - Current context store as formatted JSON
    - Timeline slider to view context at different points
    - Diff view between snapshots (optional)
    """

    def __init__(
        self,
        execution_state: WorkflowExecutionState | None = None,
        show_timeline: bool = True,
    ):
        """Initialize the context inspector.

        Args:
            execution_state: Current execution state.
            show_timeline: Whether to show timeline slider.
        """
        super().__init__()

        self._execution_state = execution_state
        self._show_timeline = show_timeline

        # Timeline state
        self._slider_state = SliderState(
            value=100,
            min_val=0,
            max_val=100,
        )
        self._selected_index: int | None = None

    def view(self):
        """Build the context inspector UI."""
        rows = []

        # Header
        rows.append(
            Row(
                Spacer().fixed_width(8),
                Text("Context Store").text_color("#9ca3af"),
                Spacer(),
            ).fixed_height(HEADER_HEIGHT)
        )

        # Timeline slider if enabled and we have history
        if self._show_timeline and self._execution_state:
            history_len = len(self._execution_state.step_history)
            if history_len > 0:
                rows.append(self._build_timeline_slider(history_len))
                rows.append(Spacer().fixed_height(8))

        # Context display
        rows.extend(self._build_context_display())

        return Column(*rows, scrollable=True)

    def _build_timeline_slider(self, history_len: int) -> Row:
        """Build the timeline slider.

        Args:
            history_len: Number of steps in history.

        Returns:
            Row widget with slider.
        """
        # Update slider max to match history
        self._slider_state = SliderState(
            value=float(history_len),
            min_val=0.0,
            max_val=float(history_len),
        )

        label_text = f"Step {int(self._slider_state.value())}/{history_len}"

        return Row(
            Spacer().fixed_width(12),
            Text(label_text).fixed_width(80).text_color("#6b7280"),
            Slider(self._slider_state).on_change(self._on_timeline_change),
            Spacer().fixed_width(12),
        ).fixed_height(32)

    def _on_timeline_change(self, value: float) -> None:
        """Handle timeline slider change.

        Args:
            value: New slider value.
        """
        self._selected_index = int(value) if value < self._slider_state.max_val() else None

    def _build_context_display(self) -> list:
        """Build the context JSON display as list of rows."""
        context = self._get_current_context()

        if not context:
            return [
                Row(
                    Spacer().fixed_width(12),
                    Text("Empty context").text_color("#6b7280"),
                    Spacer(),
                ).fixed_height(24),
            ]

        # Format context as JSON
        try:
            formatted = json.dumps(context, indent=2, default=str)
        except Exception:
            formatted = str(context)

        # Split into lines for display
        lines = formatted.split("\n")
        rows = []

        for line in lines:
            # Syntax highlighting
            color = self._get_json_color(line)
            rows.append(
                Row(
                    Spacer().fixed_width(12),
                    Text(line).text_color(color),
                    Spacer(),
                ).fixed_height(18)
            )

        return rows

    def _get_current_context(self) -> dict:
        """Get the context to display based on timeline position."""
        if self._execution_state is None:
            return {}

        # If at end or no selection, use current context
        if self._selected_index is None:
            return self._execution_state.current_context

        # Get context from history
        if self._selected_index < len(self._execution_state.step_history):
            step = self._execution_state.step_history[self._selected_index]
            return step.context_after

        return self._execution_state.current_context

    def _get_json_color(self, line: str) -> str:
        """Get syntax highlighting color for a JSON line.

        Args:
            line: Line of JSON text.

        Returns:
            Color hex string.
        """
        stripped = line.strip()

        # Keys (quoted strings followed by :)
        if '":' in stripped:
            return "#3b82f6"  # Blue for keys

        # String values (quoted strings)
        if stripped.startswith('"') or '": "' in stripped:
            return "#22c55e"  # Green for strings

        # Numbers
        if any(c.isdigit() for c in stripped) and not any(c.isalpha() for c in stripped.replace("true", "").replace("false", "").replace("null", "")):
            return "#f59e0b"  # Orange for numbers

        # Booleans and null
        if stripped in ("true", "false", "null", "true,", "false,", "null,"):
            return "#a855f7"  # Purple for special values

        # Brackets
        if stripped in ("{", "}", "[", "]", "{,", "},", "[,", "]"):
            return "#9ca3af"  # Gray for structure

        return "#e5e7eb"  # Default text color


class EventDataInspector(Component):
    """Panel displaying event data (payload).

    Shows the data/payload of a selected event.
    """

    def __init__(
        self,
        event_type: str | None = None,
        event_data: dict | None = None,
    ):
        """Initialize the event data inspector.

        Args:
            event_type: Event type name.
            event_data: Event payload data.
        """
        super().__init__()

        self._event_type = event_type
        self._event_data = event_data or {}

    def view(self):
        """Build the event data inspector UI."""
        rows = []

        # Header
        header_text = f"Event: {self._event_type}" if self._event_type else "Event Data"
        rows.append(
            Row(
                Spacer().fixed_width(8),
                Text(header_text).text_color("#9ca3af"),
                Spacer(),
            ).fixed_height(HEADER_HEIGHT)
        )

        if not self._event_data:
            rows.append(
                Row(
                    Spacer().fixed_width(12),
                    Text("No event data").text_color("#6b7280"),
                    Spacer(),
                ).fixed_height(24)
            )
        else:
            # Format and display
            try:
                formatted = json.dumps(self._event_data, indent=2, default=str)
            except Exception:
                formatted = str(self._event_data)

            for line in formatted.split("\n"):
                rows.append(
                    Row(
                        Spacer().fixed_width(12),
                        Text(line).text_color("#e5e7eb"),
                        Spacer(),
                    ).fixed_height(18)
                )

        return Column(*rows, scrollable=True)
