"""CalendarHeader widget for calendar navigation."""

from __future__ import annotations

from typing import TYPE_CHECKING

from castella.button import Button
from castella.core import Kind, SizePolicy, StatefulComponent, Widget
from castella.row import Row
from castella.spacer import Spacer
from castella.theme import ThemeManager

from .state import CalendarState, ViewMode
from .utils import get_month_name

if TYPE_CHECKING:
    pass


class CalendarHeader(StatefulComponent):
    """Header widget with month/year navigation.

    Provides:
    - Left/right arrows for month navigation
    - Clickable month name (opens month picker)
    - Clickable year (opens year picker)
    """

    def __init__(
        self,
        state: CalendarState,
        width: int = 224,
    ):
        """Initialize CalendarHeader.

        Args:
            state: CalendarState instance to manage navigation
            width: Total width of the header
        """
        self._cal_state = state
        self._width = width
        super().__init__(state)

    def view(self) -> Widget:
        """Build the header view."""
        theme = ThemeManager().current

        month_name = get_month_name(
            self._cal_state.view_month,
            locale=self._cal_state.locale,
        )
        year = self._cal_state.view_year

        # Navigation buttons
        prev_btn = (
            Button("<")
            .on_click(lambda _: self._cal_state.navigate_month(-1))
            .fixed_size(32, 32)
        )

        next_btn = (
            Button(">")
            .on_click(lambda _: self._cal_state.navigate_month(1))
            .fixed_size(32, 32)
        )

        # Month button (clickable to show month picker)
        month_btn = (
            Button(month_name)
            .on_click(lambda _: self._cal_state.set_view_mode(ViewMode.MONTHS))
            .height(32)
            .height_policy(SizePolicy.FIXED)
            .kind(Kind.NORMAL)
        )

        # Year button (clickable to show year picker)
        year_btn = (
            Button(str(year))
            .on_click(lambda _: self._cal_state.set_view_mode(ViewMode.YEARS))
            .height(32)
            .height_policy(SizePolicy.FIXED)
            .kind(Kind.NORMAL)
        )

        return (
            Row(
                prev_btn,
                Spacer().width(8).width_policy(SizePolicy.FIXED),
                month_btn,
                year_btn,
                Spacer().width(8).width_policy(SizePolicy.FIXED),
                next_btn,
            )
            .width(self._width)
            .width_policy(SizePolicy.FIXED)
            .height(40)
            .height_policy(SizePolicy.FIXED)
            .bg_color(theme.colors.bg_primary)
        )
