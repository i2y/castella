"""Navigation bar component for Edda Workflow Manager."""

from __future__ import annotations

from typing import Callable

from castella import (
    Component,
    Row,
    Button,
    Text,
    Spacer,
    Kind,
    SizePolicy,
)


# Navigation tabs
NAV_TABS = [
    ("dashboard", "Dashboard"),
    ("executions", "Executions"),
    ("live", "Live Viewer"),
    ("definitions", "Definitions"),
]


class NavigationBar(Component):
    """Top navigation bar with tabs.

    ```
    ┌─────────────────────────────────────────────────────────────┐
    │  Edda Workflow Manager  [Dashboard] [Executions] [Live] ...│
    └─────────────────────────────────────────────────────────────┘
    ```
    """

    def __init__(
        self,
        current_view: str,
        on_view_change: Callable[[str], None],
    ):
        """Initialize navigation bar.

        Args:
            current_view: Currently active view ID.
            on_view_change: Callback when view changes.
        """
        super().__init__()
        self._current_view = current_view
        self._on_view_change = on_view_change

    def view(self):
        """Build the navigation bar."""
        return (
            Row(
                # Logo/Title
                Text("Edda Workflow Manager")
                .fixed_width(200)
                .text_color("#bb9af7"),
                # Spacer
                Spacer().fixed_width(40),
                # Navigation tabs
                *[
                    self._build_tab_button(tab_id, label)
                    for tab_id, label in NAV_TABS
                ],
                # Right spacer
                Spacer(),
            )
            .fixed_height(48)
            .bg_color("#1a1b26")
        )

    def _build_tab_button(self, tab_id: str, label: str) -> Button:
        """Build a navigation tab button."""
        is_active = self._current_view == tab_id
        kind = Kind.INFO if is_active else Kind.NORMAL

        return (
            Button(label)
            .kind(kind)
            .fixed_height(36)
            .fixed_width(100)
            .on_click(lambda _, tid=tab_id: self._on_view_change(tid))
        )
