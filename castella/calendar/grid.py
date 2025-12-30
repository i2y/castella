"""CalendarGrid widget for displaying a month calendar."""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING, Callable

from castella.column import Column
from castella.core import SizePolicy, StatefulComponent, Widget
from castella.row import Row
from castella.text import Text
from castella.theme import ThemeManager

from .day_cell import DayCell
from .state import CalendarState
from .utils import get_month_calendar, get_weekday_names

if TYPE_CHECKING:
    pass


class CalendarGrid(StatefulComponent):
    """7-column x 6-row calendar grid widget.

    Displays a month calendar with:
    - Weekday header row (Mon-Sun or Sun-Sat)
    - 6 weeks of day cells
    - Proper styling for selected, today, disabled dates

    Example:
        state = CalendarState(value=date.today())
        grid = CalendarGrid(state)
        grid.on_select(lambda d: print(f"Selected: {d}"))
    """

    def __init__(
        self,
        state: CalendarState,
        cell_size: int = 32,
        on_select: Callable[[date], None] | None = None,
    ):
        """Initialize CalendarGrid.

        Args:
            state: CalendarState instance to manage selection and navigation
            cell_size: Size of each day cell in pixels
            on_select: Callback when a date is selected
        """
        self._cal_state = state
        self._cell_size = cell_size
        self._on_select_callback = on_select or (lambda _: None)
        super().__init__(state)

    def view(self) -> Widget:
        """Build the calendar grid view."""
        theme = ThemeManager().current
        styles = theme.calendar
        header_style = styles.get("weekday_header", styles["day_normal"])

        rows: list[Widget] = []

        # Weekday header row
        weekdays = get_weekday_names(
            self._cal_state.first_day_of_week,
            locale=self._cal_state.locale,
        )
        header_cells = []
        for weekday in weekdays:
            cell = (
                Text(weekday)
                .text_color(header_style.text_color)
                .fixed_size(self._cell_size, 24)
                .bg_color(header_style.bg_color)
            )
            header_cells.append(cell)

        header_row = Row(*header_cells).height(24).height_policy(SizePolicy.FIXED)
        rows.append(header_row)

        # Get calendar data
        calendar_data = get_month_calendar(
            self._cal_state.view_year,
            self._cal_state.view_month,
            self._cal_state.first_day_of_week,
        )

        today = date.today()
        selected_date = self._cal_state.value

        # Day rows (6 weeks)
        for week in calendar_data:
            day_cells = []
            for day_date in week:
                if day_date is None:
                    # Empty cell (shouldn't happen with our implementation)
                    cell = DayCell(
                        day=0,
                        cell_date=date(1, 1, 1),
                        is_disabled=True,
                        cell_size=self._cell_size,
                    )
                else:
                    is_current_month = day_date.month == self._cal_state.view_month
                    is_today = day_date == today
                    is_selected = day_date == selected_date
                    is_disabled = self._cal_state.is_date_disabled(day_date)

                    cell = DayCell(
                        day=day_date.day,
                        cell_date=day_date,
                        is_current_month=is_current_month,
                        is_today=is_today,
                        is_selected=is_selected,
                        is_disabled=is_disabled,
                        cell_size=self._cell_size,
                        on_click=self._handle_date_select,
                    )
                day_cells.append(cell)

            week_row = (
                Row(*day_cells).height(self._cell_size).height_policy(SizePolicy.FIXED)
            )
            rows.append(week_row)

        # Calculate total height: header + 6 weeks
        total_height = 24 + (6 * self._cell_size)
        total_width = 7 * self._cell_size

        return (
            Column(*rows)
            .width(total_width)
            .width_policy(SizePolicy.FIXED)
            .height(total_height)
            .height_policy(SizePolicy.FIXED)
        )

    def _handle_date_select(self, selected_date: date) -> None:
        """Handle date selection from a day cell."""
        self._cal_state.select_date(selected_date)
        self._on_select_callback(selected_date)

    def on_select(self, callback: Callable[[date], None]) -> "CalendarGrid":
        """Set callback for date selection.

        Args:
            callback: Function called with selected date

        Returns:
            Self for method chaining
        """
        self._on_select_callback = callback
        return self
