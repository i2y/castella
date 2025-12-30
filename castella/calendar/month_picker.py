"""MonthPicker widget for quick month selection."""

from __future__ import annotations

from typing import TYPE_CHECKING

from castella.button import Button
from castella.column import Column
from castella.core import Kind, SizePolicy, StatefulComponent, Widget
from castella.row import Row
from castella.theme import ThemeManager

from .state import CalendarState
from .utils import MONTH_NAMES_SHORT

if TYPE_CHECKING:
    pass


class MonthPicker(StatefulComponent):
    """4x3 grid of months for quick month selection.

    Displays all 12 months in a grid layout.
    Current month is highlighted.
    Clicking a month selects it and returns to day view.
    """

    def __init__(
        self,
        state: CalendarState,
        width: int = 224,
    ):
        """Initialize MonthPicker.

        Args:
            state: CalendarState instance
            width: Total width of the picker
        """
        self._cal_state = state
        self._width = width
        super().__init__(state)

    def view(self) -> Widget:
        """Build the month picker view."""
        theme = ThemeManager().current
        current_month = self._cal_state.view_month
        button_width = self._width // 3 - 4
        button_height = 40

        rows: list[Widget] = []

        # 4 rows x 3 columns
        for row_idx in range(4):
            buttons: list[Widget] = []
            for col_idx in range(3):
                month = row_idx * 3 + col_idx + 1
                is_current = month == current_month
                label = MONTH_NAMES_SHORT[month - 1] + "月"

                btn = (
                    Button(label)
                    .on_click(self._create_month_handler(month))
                    .fixed_size(button_width, button_height)
                )

                if is_current:
                    btn = btn.kind(Kind.INFO)

                buttons.append(btn)

            row = (
                Row(*buttons).height(button_height + 4).height_policy(SizePolicy.FIXED)
            )
            rows.append(row)

        total_height = 4 * (button_height + 4)

        return (
            Column(*rows)
            .width(self._width)
            .width_policy(SizePolicy.FIXED)
            .height(total_height)
            .height_policy(SizePolicy.FIXED)
            .bg_color(theme.colors.bg_primary)
        )

    def _create_month_handler(self, month: int):
        """Create a click handler for a specific month."""

        def handler(_):
            self._cal_state.select_month(month)

        return handler
