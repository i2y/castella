"""Calendar utility functions for date calculations."""

from __future__ import annotations

import calendar
from datetime import date
from typing import TYPE_CHECKING

from .locale import DEFAULT_LOCALE, CalendarLocale

if TYPE_CHECKING:
    pass


# Legacy constants for backward compatibility (using default locale)
MONTH_NAMES = DEFAULT_LOCALE.month_names
MONTH_NAMES_SHORT = DEFAULT_LOCALE.month_names_short
WEEKDAY_NAMES = DEFAULT_LOCALE.weekday_names
WEEKDAY_NAMES_SUNDAY_START = DEFAULT_LOCALE.weekday_names_sunday_start


def days_in_month(year: int, month: int) -> int:
    """Return the number of days in a given month."""
    return calendar.monthrange(year, month)[1]


def get_weekday_names(
    first_day_of_week: int = 1,
    locale: CalendarLocale | None = None,
) -> list[str]:
    """Return weekday names starting from the specified day.

    Args:
        first_day_of_week: 0=Sunday, 1=Monday (default)
        locale: Locale for weekday names (default: DEFAULT_LOCALE)

    Returns:
        List of weekday names
    """
    loc = locale or DEFAULT_LOCALE
    if first_day_of_week == 0:
        return loc.weekday_names_sunday_start
    return loc.weekday_names


def get_month_name(
    month: int,
    short: bool = False,
    locale: CalendarLocale | None = None,
) -> str:
    """Return the name of the month.

    Args:
        month: 1-12
        short: If True, return short name
        locale: Locale for month names (default: DEFAULT_LOCALE)

    Returns:
        Month name string
    """
    loc = locale or DEFAULT_LOCALE
    if short:
        return loc.month_names_short[month - 1]
    return loc.month_names[month - 1]


def get_first_day_of_month(year: int, month: int) -> date:
    """Return the first day of the given month."""
    return date(year, month, 1)


def get_last_day_of_month(year: int, month: int) -> date:
    """Return the last day of the given month."""
    return date(year, month, days_in_month(year, month))


def get_month_calendar(
    year: int,
    month: int,
    first_day_of_week: int = 1,
) -> list[list[date | None]]:
    """Return a 6-week calendar grid for the given month.

    Args:
        year: The year
        month: The month (1-12)
        first_day_of_week: 0=Sunday, 1=Monday (default)

    Returns:
        A 6x7 grid of dates. Days outside the month are filled with
        dates from previous/next month.
    """
    # Get the first day of the month
    first_date = date(year, month, 1)

    # Calculate the weekday of the first day (0=Monday, 6=Sunday in Python)
    first_weekday = first_date.weekday()  # 0=Monday

    # Adjust for the first day of week setting
    if first_day_of_week == 0:
        # Sunday start: convert Python weekday to Sunday-based
        # Python: Mon=0, Tue=1, ..., Sun=6
        # Sunday-start: Sun=0, Mon=1, ..., Sat=6
        start_offset = (first_weekday + 1) % 7
    else:
        # Monday start (default): use Python weekday directly
        start_offset = first_weekday

    # Calculate the start date (may be in previous month)
    from datetime import timedelta

    start_date = first_date - timedelta(days=start_offset)

    # Generate 6 weeks (42 days)
    weeks: list[list[date | None]] = []
    current_date = start_date

    for _ in range(6):
        week: list[date | None] = []
        for _ in range(7):
            week.append(current_date)
            current_date += timedelta(days=1)
        weeks.append(week)

    return weeks


def get_month_calendar_with_info(
    year: int,
    month: int,
    selected_date: date | None = None,
    first_day_of_week: int = 1,
    min_date: date | None = None,
    max_date: date | None = None,
    disabled_dates: list[date] | None = None,
) -> list[list[dict]]:
    """Return a 6-week calendar grid with day info for the given month.

    Args:
        year: The year
        month: The month (1-12)
        selected_date: Currently selected date
        first_day_of_week: 0=Sunday, 1=Monday (default)
        min_date: Minimum selectable date
        max_date: Maximum selectable date
        disabled_dates: List of disabled dates

    Returns:
        A 6x7 grid of day info dicts with keys:
        - date: The date object
        - is_current_month: Whether the day is in the current month
        - is_today: Whether the day is today
        - is_selected: Whether the day is selected
        - is_disabled: Whether the day is disabled
    """
    today = date.today()
    disabled_set = set(disabled_dates or [])
    calendar_grid = get_month_calendar(year, month, first_day_of_week)

    result: list[list[dict]] = []
    for week in calendar_grid:
        week_info: list[dict] = []
        for day in week:
            if day is None:
                week_info.append(
                    {
                        "date": None,
                        "is_current_month": False,
                        "is_today": False,
                        "is_selected": False,
                        "is_disabled": True,
                    }
                )
            else:
                is_disabled = day in disabled_set
                if min_date and day < min_date:
                    is_disabled = True
                if max_date and day > max_date:
                    is_disabled = True

                week_info.append(
                    {
                        "date": day,
                        "is_current_month": day.month == month,
                        "is_today": day == today,
                        "is_selected": day == selected_date,
                        "is_disabled": is_disabled,
                    }
                )
        result.append(week_info)

    return result


def navigate_month(year: int, month: int, delta: int) -> tuple[int, int]:
    """Navigate months by delta.

    Args:
        year: Current year
        month: Current month (1-12)
        delta: Number of months to navigate (positive or negative)

    Returns:
        Tuple of (new_year, new_month)
    """
    # Convert to 0-based month for easier calculation
    total_months = year * 12 + (month - 1) + delta
    new_year = total_months // 12
    new_month = (total_months % 12) + 1
    return new_year, new_month


def navigate_year(year: int, delta: int) -> int:
    """Navigate years by delta.

    Args:
        year: Current year
        delta: Number of years to navigate (positive or negative)

    Returns:
        New year
    """
    return year + delta
