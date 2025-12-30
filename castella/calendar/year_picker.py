"""YearPicker widget for quick year selection."""

from __future__ import annotations

from typing import TYPE_CHECKING

from castella.button import Button
from castella.column import Column
from castella.core import Kind, SizePolicy, StatefulComponent, Widget
from castella.row import Row
from castella.spacer import Spacer
from castella.text import Text
from castella.theme import ThemeManager

from .state import CalendarState

if TYPE_CHECKING:
    pass


class YearPicker(StatefulComponent):
    """Year range selector showing 12 years at a time.

    Displays years in a 4x3 grid with navigation buttons to move
    between year ranges (12 years at a time).
    """

    YEARS_PER_PAGE = 12

    def __init__(
        self,
        state: CalendarState,
        width: int = 224,
    ):
        """Initialize YearPicker.

        Args:
            state: CalendarState instance
            width: Total width of the picker
        """
        self._cal_state = state
        self._width = width
        super().__init__(state)

    def view(self) -> Widget:
        """Build the year picker view."""
        theme = ThemeManager().current
        current_year = self._cal_state.view_year

        # Calculate the start year for the current range
        start_year = (current_year // self.YEARS_PER_PAGE) * self.YEARS_PER_PAGE

        button_width = self._width // 3 - 4
        button_height = 40

        rows: list[Widget] = []

        # Header row with navigation
        header = (
            Row(
                Button("<")
                .on_click(lambda _: self._navigate(-self.YEARS_PER_PAGE))
                .fixed_size(32, 32),
                Spacer(),
                Text(f"{start_year} - {start_year + self.YEARS_PER_PAGE - 1}")
                .text_color(theme.colors.text_primary)
                .height(32)
                .height_policy(SizePolicy.FIXED),
                Spacer(),
                Button(">")
                .on_click(lambda _: self._navigate(self.YEARS_PER_PAGE))
                .fixed_size(32, 32),
            )
            .width(self._width)
            .width_policy(SizePolicy.FIXED)
            .height(40)
            .height_policy(SizePolicy.FIXED)
        )
        rows.append(header)

        # 4 rows x 3 columns of years
        for row_idx in range(4):
            buttons: list[Widget] = []
            for col_idx in range(3):
                year = start_year + row_idx * 3 + col_idx
                is_current = year == current_year

                btn = (
                    Button(str(year))
                    .on_click(self._create_year_handler(year))
                    .fixed_size(button_width, button_height)
                )

                if is_current:
                    btn = btn.kind(Kind.INFO)

                buttons.append(btn)

            row = (
                Row(*buttons).height(button_height + 4).height_policy(SizePolicy.FIXED)
            )
            rows.append(row)

        # Total height: header + 4 rows
        total_height = 40 + 4 * (button_height + 4)

        return (
            Column(*rows)
            .width(self._width)
            .width_policy(SizePolicy.FIXED)
            .height(total_height)
            .height_policy(SizePolicy.FIXED)
            .bg_color(theme.colors.bg_primary)
        )

    def _navigate(self, delta: int) -> None:
        """Navigate to a different year range."""
        new_year = self._cal_state.view_year + delta
        # Keep within reasonable bounds
        new_year = max(1900, min(2100, new_year))
        self._cal_state.select_year(new_year)
        # Stay in years mode after navigation
        from .state import ViewMode

        self._cal_state.set_view_mode(ViewMode.YEARS)

    def _create_year_handler(self, year: int):
        """Create a click handler for a specific year."""

        def handler(_):
            self._cal_state.select_year(year)

        return handler
