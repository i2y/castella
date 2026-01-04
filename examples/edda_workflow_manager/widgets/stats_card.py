"""Statistics card widget for dashboard."""

from __future__ import annotations

from castella import (
    Component,
    Column,
    Text,
    Kind,
    SizePolicy,
)


class StatsCard(Component):
    """Card displaying a single statistic.

    ```
    ┌───────────────┐
    │      42       │
    │   Running     │
    └───────────────┘
    ```
    """

    def __init__(
        self,
        title: str,
        value: int | str,
        kind: Kind = Kind.NORMAL,
    ):
        """Initialize stats card.

        Args:
            title: Label below the value.
            value: The statistic value to display.
            kind: Visual style kind.
        """
        super().__init__()
        self._title = title
        self._value = value
        self._kind = kind

    def view(self):
        """Build the stats card."""
        # Map kind to colors
        if self._kind == Kind.SUCCESS:
            value_color = "#9ece6a"  # Green
        elif self._kind == Kind.DANGER:
            value_color = "#f7768e"  # Red
        elif self._kind == Kind.WARNING:
            value_color = "#e0af68"  # Yellow
        elif self._kind == Kind.INFO:
            value_color = "#7aa2f7"  # Blue
        else:
            value_color = "#c0caf5"  # Default text

        return (
            Column(
                Text(str(self._value))
                .fixed_height(48)
                .text_color(value_color),
                Text(self._title)
                .fixed_height(24)
                .text_color("#9ca3af"),
            )
            .fixed_width(140)
            .fixed_height(100)
            .bg_color("#1e1f2b")
        )
