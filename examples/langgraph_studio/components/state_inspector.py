"""State inspector component for LangGraph Studio."""

from __future__ import annotations

import json
from typing import Any

from castella import Component, Column, Row, Text, Spacer, SizePolicy


class StateInspector(Component):
    """Panel for inspecting graph execution state.

    Displays:
    - Current node being executed
    - Current graph state as formatted JSON
    """

    def __init__(
        self,
        state: dict[str, Any] | None = None,
        node_id: str | None = None,
    ):
        """Initialize the state inspector.

        Args:
            state: Current graph state dictionary.
            node_id: Currently executing node ID.
        """
        super().__init__()

        self._state = state or {}
        self._node_id = node_id

    def view(self):
        """Build the state inspector UI."""
        return Column(
            # Header
            self._build_header(),
            # State content (scrollable area)
            self._build_state_view(),
        )

    def _build_header(self):
        """Build the header section."""
        header_parts = [Text("State Inspector")]

        if self._node_id:
            header_parts.extend([
                Spacer(),
                Text(self._node_id),
            ])

        return Row(*header_parts).fixed_height(28)

    def _build_state_view(self):
        """Build the state content view."""
        if not self._state:
            return Text("No state data").fixed_height(24)

        # Format state as JSON
        try:
            state_str = json.dumps(self._state, indent=2, default=str)
        except Exception:
            state_str = str(self._state)

        # Split into lines for display - each line needs fixed height
        lines = state_str.split("\n")[:50]  # Limit lines
        text_widgets = [
            Text(line).fixed_height(20).height_policy(SizePolicy.FIXED)
            for line in lines
        ]

        return Column(*text_widgets, scrollable=True)
