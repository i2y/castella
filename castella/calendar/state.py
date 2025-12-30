"""Calendar state management classes."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
from typing import TYPE_CHECKING, Callable

from castella.core import ObservableBase

from .locale import DEFAULT_LOCALE, CalendarLocale
from .utils import days_in_month, navigate_month, navigate_year

if TYPE_CHECKING:
    pass


class ViewMode(Enum):
    """Calendar view modes."""

    DAYS = "days"  # Calendar grid showing days
    MONTHS = "months"  # Month selection view
    YEARS = "years"  # Year selection view


@dataclass
class DayInfo:
    """Information about a single day cell."""

    date: date
    is_current_month: bool
    is_today: bool
    is_selected: bool
    is_disabled: bool


class CalendarState(ObservableBase):
    """Observable state for calendar components.

    Manages the currently selected date, the date being viewed (for navigation),
    view mode (days/months/years), and constraints like min/max dates.
    """

    def __init__(
        self,
        value: datetime | date | None = None,
        min_date: date | None = None,
        max_date: date | None = None,
        disabled_dates: list[date] | None = None,
        first_day_of_week: int = 1,  # 0=Sunday, 1=Monday
        locale: CalendarLocale | None = None,
    ):
        """Initialize the calendar state.

        Args:
            value: Currently selected date/datetime
            min_date: Minimum selectable date
            max_date: Maximum selectable date
            disabled_dates: List of dates that cannot be selected
            first_day_of_week: 0=Sunday, 1=Monday (default)
            locale: Locale for calendar display (default: EN)
        """
        super().__init__()
        self._value: date | None = self._to_date(value)
        self._view_date: date = self._value or date.today()
        self._view_mode: ViewMode = ViewMode.DAYS
        self._min_date: date | None = min_date
        self._max_date: date | None = max_date
        self._disabled_dates: set[date] = set(disabled_dates or [])
        self._first_day_of_week: int = first_day_of_week
        self._locale: CalendarLocale = locale or DEFAULT_LOCALE
        self._on_change_callback: Callable[[date | None], None] | None = None

    @staticmethod
    def _to_date(value: datetime | date | None) -> date | None:
        """Convert datetime to date if needed."""
        if value is None:
            return None
        if isinstance(value, datetime):
            return value.date()
        return value

    # ================== Properties ==================

    @property
    def value(self) -> date | None:
        """Get the currently selected date."""
        return self._value

    @property
    def view_date(self) -> date:
        """Get the date currently being viewed (determines which month is shown)."""
        return self._view_date

    @property
    def view_year(self) -> int:
        """Get the year currently being viewed."""
        return self._view_date.year

    @property
    def view_month(self) -> int:
        """Get the month currently being viewed (1-12)."""
        return self._view_date.month

    @property
    def view_mode(self) -> ViewMode:
        """Get the current view mode."""
        return self._view_mode

    @property
    def min_date(self) -> date | None:
        """Get the minimum selectable date."""
        return self._min_date

    @property
    def max_date(self) -> date | None:
        """Get the maximum selectable date."""
        return self._max_date

    @property
    def first_day_of_week(self) -> int:
        """Get the first day of week setting (0=Sunday, 1=Monday)."""
        return self._first_day_of_week

    @property
    def locale(self) -> CalendarLocale:
        """Get the locale for calendar display."""
        return self._locale

    # ================== Selection ==================

    def set(self, value: datetime | date | None) -> None:
        """Set the selected date.

        Args:
            value: The date to select, or None to clear
        """
        new_date = self._to_date(value)
        if new_date != self._value:
            self._value = new_date
            if new_date:
                self._view_date = new_date
            self.notify()
            if self._on_change_callback:
                self._on_change_callback(new_date)

    def select_date(self, d: date) -> None:
        """Select a specific date.

        Args:
            d: The date to select
        """
        if not self.is_date_disabled(d):
            self.set(d)

    def clear(self) -> None:
        """Clear the selected date."""
        self.set(None)

    # ================== Navigation ==================

    def navigate_month(self, delta: int) -> None:
        """Navigate months by delta.

        Args:
            delta: Number of months to navigate (positive or negative)
        """
        new_year, new_month = navigate_month(
            self._view_date.year, self._view_date.month, delta
        )
        # Clamp day to valid range for the new month
        new_day = min(self._view_date.day, days_in_month(new_year, new_month))
        self._view_date = date(new_year, new_month, new_day)
        self.notify()

    def navigate_year(self, delta: int) -> None:
        """Navigate years by delta.

        Args:
            delta: Number of years to navigate (positive or negative)
        """
        new_year = navigate_year(self._view_date.year, delta)
        # Clamp day to valid range (handles Feb 29 in leap years)
        new_day = min(
            self._view_date.day, days_in_month(new_year, self._view_date.month)
        )
        self._view_date = date(new_year, self._view_date.month, new_day)
        self.notify()

    def go_to_today(self) -> None:
        """Navigate to today's date and select it."""
        today = date.today()
        self._view_date = today
        if not self.is_date_disabled(today):
            self._value = today
        self.notify()

    def go_to_date(self, d: date) -> None:
        """Navigate to a specific date without selecting it.

        Args:
            d: The date to navigate to
        """
        self._view_date = d
        self.notify()

    # ================== View Mode ==================

    def set_view_mode(self, mode: ViewMode) -> None:
        """Set the current view mode.

        Args:
            mode: The view mode to set
        """
        if mode != self._view_mode:
            self._view_mode = mode
            self.notify()

    def select_month(self, month: int) -> None:
        """Select a month and switch back to days view.

        Args:
            month: The month to select (1-12)
        """
        new_day = min(self._view_date.day, days_in_month(self._view_date.year, month))
        self._view_date = date(self._view_date.year, month, new_day)
        self._view_mode = ViewMode.DAYS
        self.notify()

    def select_year(self, year: int) -> None:
        """Select a year and switch to months view.

        Args:
            year: The year to select
        """
        new_day = min(self._view_date.day, days_in_month(year, self._view_date.month))
        self._view_date = date(year, self._view_date.month, new_day)
        self._view_mode = ViewMode.MONTHS
        self.notify()

    # ================== Validation ==================

    def is_date_disabled(self, d: date) -> bool:
        """Check if a date is disabled.

        Args:
            d: The date to check

        Returns:
            True if the date is disabled
        """
        if d in self._disabled_dates:
            return True
        if self._min_date and d < self._min_date:
            return True
        if self._max_date and d > self._max_date:
            return True
        return False

    def is_date_in_range(self, d: date) -> bool:
        """Check if a date is within the min/max range.

        Args:
            d: The date to check

        Returns:
            True if the date is in range
        """
        if self._min_date and d < self._min_date:
            return False
        if self._max_date and d > self._max_date:
            return False
        return True

    # ================== Callbacks ==================

    def on_change(self, callback: Callable[[date | None], None]) -> None:
        """Set the callback for when the selected date changes.

        Args:
            callback: Function to call with the new date
        """
        self._on_change_callback = callback


class TimePickerState(ObservableBase):
    """Observable state for time picker components."""

    def __init__(
        self,
        hour: int = 0,
        minute: int = 0,
        minute_step: int = 5,
        use_24_hour: bool = True,
        locale: CalendarLocale | None = None,
    ):
        """Initialize the time picker state.

        Args:
            hour: Initial hour (0-23)
            minute: Initial minute (0-59)
            minute_step: Step for minute selection (e.g., 5, 10, 15)
            use_24_hour: Whether to use 24-hour format
            locale: Locale for time picker display (default: EN)
        """
        super().__init__()
        self._hour: int = max(0, min(23, hour))
        self._minute: int = max(0, min(59, minute))
        self._minute_step: int = minute_step
        self._use_24_hour: bool = use_24_hour
        self._locale: CalendarLocale = locale or DEFAULT_LOCALE
        self._on_change_callback: Callable[[int, int], None] | None = None

    @property
    def locale(self) -> CalendarLocale:
        """Get the locale for time picker display."""
        return self._locale

    @property
    def hour(self) -> int:
        """Get the current hour (0-23)."""
        return self._hour

    @property
    def minute(self) -> int:
        """Get the current minute (0-59)."""
        return self._minute

    @property
    def minute_step(self) -> int:
        """Get the minute step value."""
        return self._minute_step

    @property
    def use_24_hour(self) -> bool:
        """Whether 24-hour format is used."""
        return self._use_24_hour

    def set_hour(self, hour: int) -> None:
        """Set the hour.

        Args:
            hour: The hour to set (0-23)
        """
        hour = max(0, min(23, hour))
        if hour != self._hour:
            self._hour = hour
            self.notify()
            self._fire_change()

    def set_minute(self, minute: int) -> None:
        """Set the minute.

        Args:
            minute: The minute to set (0-59)
        """
        minute = max(0, min(59, minute))
        if minute != self._minute:
            self._minute = minute
            self.notify()
            self._fire_change()

    def set_time(self, hour: int, minute: int) -> None:
        """Set both hour and minute.

        Args:
            hour: The hour to set (0-23)
            minute: The minute to set (0-59)
        """
        hour = max(0, min(23, hour))
        minute = max(0, min(59, minute))
        if hour != self._hour or minute != self._minute:
            self._hour = hour
            self._minute = minute
            self.notify()
            self._fire_change()

    def set_now(self) -> None:
        """Set to the current time."""
        now = datetime.now()
        self.set_time(now.hour, now.minute)

    def get_minute_options(self) -> list[int]:
        """Get available minute options based on step.

        Returns:
            List of minute values (e.g., [0, 5, 10, 15, ...])
        """
        return list(range(0, 60, self._minute_step))

    def get_hour_options(self) -> list[int]:
        """Get available hour options.

        Returns:
            List of hour values (0-23 or 1-12)
        """
        if self._use_24_hour:
            return list(range(24))
        return list(range(1, 13))

    def format_time(self) -> str:
        """Format the current time as a string.

        Returns:
            Formatted time string (e.g., "14:30" or "2:30 PM")
        """
        if self._use_24_hour:
            return f"{self._hour:02d}:{self._minute:02d}"
        else:
            am_pm = "AM" if self._hour < 12 else "PM"
            hour_12 = self._hour % 12
            if hour_12 == 0:
                hour_12 = 12
            return f"{hour_12}:{self._minute:02d} {am_pm}"

    def on_change(self, callback: Callable[[int, int], None]) -> None:
        """Set the callback for when the time changes.

        Args:
            callback: Function to call with (hour, minute)
        """
        self._on_change_callback = callback

    def _fire_change(self) -> None:
        """Fire the change callback if set."""
        if self._on_change_callback:
            self._on_change_callback(self._hour, self._minute)
