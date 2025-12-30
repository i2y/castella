"""Locale support for calendar components."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class CalendarLocale:
    """Locale settings for calendar display.

    Attributes:
        weekday_names: List of 7 weekday names starting from Monday
        weekday_names_short: Short weekday names (1-2 chars)
        weekday_names_sunday_start: Weekday names starting from Sunday
        month_names: List of 12 month names
        month_names_short: Short month names
        today_button: Label for "Today" button
        done_button: Label for "Done" button
        now_button: Label for "Now" button (time picker)
        time_label: Label for "Time:" in time picker
        placeholder: Placeholder text when no date selected
    """

    weekday_names: list[str]
    weekday_names_short: list[str]
    weekday_names_sunday_start: list[str]
    month_names: list[str]
    month_names_short: list[str]
    today_button: str
    done_button: str
    now_button: str
    time_label: str
    placeholder: str


# English locale
EN = CalendarLocale(
    weekday_names=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
    weekday_names_short=["M", "T", "W", "T", "F", "S", "S"],
    weekday_names_sunday_start=["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"],
    month_names=[
        "January",
        "February",
        "March",
        "April",
        "May",
        "June",
        "July",
        "August",
        "September",
        "October",
        "November",
        "December",
    ],
    month_names_short=[
        "Jan",
        "Feb",
        "Mar",
        "Apr",
        "May",
        "Jun",
        "Jul",
        "Aug",
        "Sep",
        "Oct",
        "Nov",
        "Dec",
    ],
    today_button="Today",
    done_button="Done",
    now_button="Now",
    time_label="Time:",
    placeholder="Select...",
)

# Japanese locale
JA = CalendarLocale(
    weekday_names=["月", "火", "水", "木", "金", "土", "日"],
    weekday_names_short=["月", "火", "水", "木", "金", "土", "日"],
    weekday_names_sunday_start=["日", "月", "火", "水", "木", "金", "土"],
    month_names=[
        "1月",
        "2月",
        "3月",
        "4月",
        "5月",
        "6月",
        "7月",
        "8月",
        "9月",
        "10月",
        "11月",
        "12月",
    ],
    month_names_short=["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12"],
    today_button="今日",
    done_button="完了",
    now_button="今",
    time_label="時間:",
    placeholder="選択...",
)

# Default locale
DEFAULT_LOCALE = EN


def get_locale(name: str) -> CalendarLocale:
    """Get locale by name.

    Args:
        name: Locale name ("en", "ja", etc.)

    Returns:
        CalendarLocale instance
    """
    locales = {
        "en": EN,
        "ja": JA,
    }
    return locales.get(name.lower(), DEFAULT_LOCALE)
