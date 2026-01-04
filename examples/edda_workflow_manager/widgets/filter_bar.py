"""Filter bar widget for execution list."""

from __future__ import annotations

from typing import Callable

from castella import (
    Component,
    Row,
    Button,
    Input,
    Text,
    Spacer,
    Kind,
    SizePolicy,
)

from edda_workflow_manager.models.instance import InstanceStatus


# Status filter options
STATUS_FILTERS = [
    (None, "All"),
    ("running", "Running"),
    ("completed", "Completed"),
    ("failed", "Failed"),
    ("waiting_for_event", "Waiting"),
    ("compensating", "Compensating"),
]


class FilterBar(Component):
    """Filter bar for execution list.

    ```
    ┌────────────────────────────────────────────────────────────────┐
    │  [All] [Running] [Completed] [Failed] ...  [Search: ______]   │
    └────────────────────────────────────────────────────────────────┘
    ```
    """

    def __init__(
        self,
        status_filter: str | None = None,
        search_query: str = "",
        on_status_change: Callable[[str | None], None] | None = None,
        on_search_change: Callable[[str], None] | None = None,
        on_refresh: Callable[[], None] | None = None,
    ):
        """Initialize filter bar.

        Args:
            status_filter: Current status filter.
            search_query: Current search query.
            on_status_change: Callback when status filter changes.
            on_search_change: Callback when search query changes.
            on_refresh: Callback for refresh button.
        """
        super().__init__()
        self._status_filter = status_filter
        self._search_query = search_query
        self._on_status_change = on_status_change
        self._on_search_change = on_search_change
        self._on_refresh = on_refresh

    def view(self):
        """Build the filter bar."""
        # Build status filter buttons
        status_buttons = [
            self._build_status_button(status, label)
            for status, label in STATUS_FILTERS
        ]

        return (
            Row(
                # Status filters (left side)
                *status_buttons,
                # Flexible spacer
                Spacer().width_policy(SizePolicy.EXPANDING),
                # Search input
                Input(self._search_query)
                .fixed_width(200)
                .fixed_height(32)
                .on_change(self._on_search),
                # Refresh button
                Button("Refresh")
                .fixed_height(32)
                .fixed_width(80)
                .on_click(lambda _: self._on_refresh() if self._on_refresh else None),
            )
            .fixed_height(48)
            .bg_color("#1e1f2b")
        )

    def _build_status_button(
        self, status: str | None, label: str
    ) -> Button:
        """Build a status filter button."""
        is_active = self._status_filter == status
        kind = Kind.INFO if is_active else Kind.NORMAL

        return (
            Button(label)
            .kind(kind)
            .fixed_height(32)
            .fixed_width(90)
            .on_click(lambda _, s=status: self._on_status_click(s))
        )

    def _on_status_click(self, status: str | None) -> None:
        """Handle status filter button click."""
        if self._on_status_change:
            self._on_status_change(status)

    def _on_search(self, text: str) -> None:
        """Handle search input change."""
        if self._on_search_change:
            self._on_search_change(text)
