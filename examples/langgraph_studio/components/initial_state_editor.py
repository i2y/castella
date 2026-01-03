"""Initial state editor component for LangGraph Studio."""

from __future__ import annotations

import json
from typing import Callable

from castella import Component, Column, Row, Text, Button, Spacer, State, SizePolicy
from castella.multiline_input import MultilineInput, MultilineInputState


# Heights
COLLAPSED_HEIGHT = 32
EXPANDED_HEIGHT = 140


# UI Constants
HEADER_HEIGHT = 32
SECTION_SPACING = 8


class InitialStateEditor(Component):
    """JSON editor for setting initial execution state.

    Provides a text editor for entering JSON that will be used as
    the initial state when running the graph.
    """

    def __init__(
        self,
        on_state_change: Callable[[dict], None] | None = None,
        collapsed: bool = True,
    ):
        """Initialize the editor.

        Args:
            on_state_change: Callback when valid JSON is entered.
            collapsed: Whether the editor starts collapsed.
        """
        super().__init__()

        self._on_state_change = on_state_change

        # Editor state
        self._input_state = MultilineInputState("{}")
        self._error: str | None = None  # Don't use State - avoid focus loss on change
        self._collapsed = State[bool](collapsed)

        self._collapsed.attach(self)

        # Set initial height based on collapsed state
        self.fixed_height(COLLAPSED_HEIGHT if collapsed else EXPANDED_HEIGHT)

    def _toggle_collapsed(self, _) -> None:
        """Toggle collapsed state and update height."""
        collapsed = not self._collapsed()
        self._collapsed.set(collapsed)
        # Update component height
        self.fixed_height(COLLAPSED_HEIGHT if collapsed else EXPANDED_HEIGHT)
        # Force parent layout recalculation
        if self._parent:
            self._parent.mark_layout_dirty()
            self._parent.update(completely=True)

    def view(self):
        """Build the editor UI."""
        collapsed = self._collapsed()

        # Header with toggle button
        header = Row(
            Spacer().fixed_width(SECTION_SPACING),
            Text("Initial State"),
            Spacer(),
            Button("Expand" if collapsed else "Collapse")
                .fixed_width(80)
                .on_click(self._toggle_collapsed),
            Spacer().fixed_width(SECTION_SPACING),
        ).fixed_height(HEADER_HEIGHT)

        if collapsed:
            return Column(header)

        # Editor content
        error = self._error

        editor = MultilineInput(
            self._input_state,
            font_size=12,
        ).on_change(self._on_text_change)

        # Error display (always 24px for consistent height)
        if error:
            error_widget = Row(
                Spacer().fixed_width(SECTION_SPACING),
                Text(f"Error: {error}"),
                Spacer(),
            ).fixed_height(24)
        else:
            error_widget = Spacer().fixed_height(24)

        # Layout: header(32) + spacing(4) + editor(80) + error(24) = 140px
        return Column(
            header,
            Spacer().fixed_height(4),
            Row(
                Spacer().fixed_width(SECTION_SPACING),
                editor.height(80).height_policy(SizePolicy.FIXED),
                Spacer().fixed_width(SECTION_SPACING),
            ).fixed_height(80),
            error_widget,
        )

    def _on_text_change(self, text: str) -> None:
        """Handle text changes in the editor.

        Args:
            text: Current editor text.
        """
        try:
            parsed = json.loads(text)
            self._error = None
            if self._on_state_change:
                self._on_state_change(parsed)
        except json.JSONDecodeError as e:
            self._error = f"Invalid JSON: {e.msg}"

    def get_state(self) -> dict:
        """Get the current parsed state.

        Returns:
            Parsed JSON as dict, or empty dict if invalid.
        """
        try:
            return json.loads(self._input_state.value())
        except json.JSONDecodeError:
            return {}

    def set_state(self, state: dict) -> None:
        """Set the editor content from a dict.

        Args:
            state: State dict to display.
        """
        self._input_state.set(json.dumps(state, indent=2))
        self._error = None

    def expand(self) -> None:
        """Expand the editor."""
        self._collapsed.set(False)

    def collapse(self) -> None:
        """Collapse the editor."""
        self._collapsed.set(True)
