"""DateTimeInput widget for date and time selection.

Provides a combined date/time input with visual calendar picker popup.
"""

from __future__ import annotations

from datetime import date, datetime, time
from typing import Callable, Self

from castella.box import Box
from castella.button import Button
from castella.calendar.grid import CalendarGrid
from castella.calendar.header import CalendarHeader
from castella.calendar.locale import DEFAULT_LOCALE, CalendarLocale
from castella.calendar.month_picker import MonthPicker
from castella.calendar.state import CalendarState, TimePickerState, ViewMode
from castella.calendar.time_picker import TimePicker
from castella.calendar.year_picker import YearPicker
from castella.column import Column
from castella.core import (
    Kind,
    ObservableBase,
    SizePolicy,
    StatefulComponent,
    Widget,
)
from castella.row import Row
from castella.spacer import Spacer
from castella.text import Text
from castella.theme import ThemeManager


class DateTimeInputState(ObservableBase):
    """Observable state for DateTimeInput widget.

    Manages the date/time value and picker visibility.
    """

    def __init__(
        self,
        value: datetime | date | time | str | None = None,
        enable_date: bool = True,
        enable_time: bool = False,
    ):
        """Initialize DateTimeInputState.

        Args:
            value: Initial date/time value (datetime, date, time, or ISO 8601 string)
            enable_date: Whether to show date input
            enable_time: Whether to show time input
        """
        super().__init__()
        self._enable_date = enable_date
        self._enable_time = enable_time
        self._value = self._parse_value(value)
        self._picker_open = False

    def _parse_value(self, value) -> datetime | None:
        """Parse value to datetime."""
        if value is None:
            return None
        if isinstance(value, datetime):
            return value
        if isinstance(value, date):
            return datetime.combine(value, time(0, 0))
        if isinstance(value, time):
            return datetime.combine(date.today(), value)
        if isinstance(value, str):
            try:
                # Try ISO 8601 formats
                if "T" in value:
                    return datetime.fromisoformat(value)
                elif len(value) == 10:  # YYYY-MM-DD
                    return datetime.fromisoformat(value + "T00:00:00")
                elif ":" in value:  # HH:MM or HH:MM:SS
                    t = time.fromisoformat(value)
                    return datetime.combine(date.today(), t)
            except ValueError:
                pass
        return None

    def value(self) -> datetime | None:
        """Get current datetime value."""
        return self._value

    def set(self, value: datetime | date | time | str | None) -> None:
        """Set datetime value.

        Args:
            value: New date/time value
        """
        new_value = self._parse_value(value)
        if new_value != self._value:
            self._value = new_value
            self.notify()

    def to_iso(self) -> str | None:
        """Get value as ISO 8601 string.

        Returns:
            ISO 8601 formatted string or None
        """
        if self._value is None:
            return None
        if self._enable_date and self._enable_time:
            return self._value.isoformat()
        elif self._enable_date:
            return self._value.date().isoformat()
        elif self._enable_time:
            return self._value.time().isoformat()
        return None

    def to_display_string(self) -> str:
        """Get value as display string.

        Returns:
            Human-readable date/time string
        """
        if self._value is None:
            return ""
        parts = []
        if self._enable_date:
            parts.append(self._value.strftime("%Y-%m-%d"))
        if self._enable_time:
            parts.append(self._value.strftime("%H:%M"))
        return " ".join(parts)

    def is_picker_open(self) -> bool:
        """Check if picker is open."""
        return self._picker_open

    def open_picker(self) -> None:
        """Open the picker popup."""
        if not self._picker_open:
            self._picker_open = True
            self.notify()

    def close_picker(self) -> None:
        """Close the picker popup."""
        if self._picker_open:
            self._picker_open = False
            self.notify()

    def toggle_picker(self) -> None:
        """Toggle picker open/closed state."""
        self._picker_open = not self._picker_open
        self.notify()

    @property
    def enable_date(self) -> bool:
        """Whether date input is enabled."""
        return self._enable_date

    @property
    def enable_time(self) -> bool:
        """Whether time input is enabled."""
        return self._enable_time

    # Date/time component setters
    def set_year(self, year: int) -> None:
        """Set year component."""
        if self._value:
            try:
                self._value = self._value.replace(year=year)
            except ValueError:
                pass
        else:
            self._value = datetime(year, 1, 1)
        self.notify()

    def set_month(self, month: int) -> None:
        """Set month component (1-12)."""
        if self._value:
            try:
                # Handle day overflow (e.g., Jan 31 -> Feb 28)
                day = min(self._value.day, 28)  # Safe default
                self._value = self._value.replace(month=month, day=day)
            except ValueError:
                pass
        else:
            self._value = datetime(datetime.now().year, month, 1)
        self.notify()

    def set_day(self, day: int) -> None:
        """Set day component (1-31)."""
        if self._value:
            try:
                self._value = self._value.replace(day=day)
            except ValueError:
                pass
        else:
            self._value = datetime(datetime.now().year, datetime.now().month, day)
        self.notify()

    def set_hour(self, hour: int) -> None:
        """Set hour component (0-23)."""
        if self._value:
            try:
                self._value = self._value.replace(hour=hour)
            except ValueError:
                pass
        else:
            self._value = datetime.combine(date.today(), time(hour, 0))
        self.notify()

    def set_minute(self, minute: int) -> None:
        """Set minute component (0-59)."""
        if self._value:
            try:
                self._value = self._value.replace(minute=minute)
            except ValueError:
                pass
        else:
            self._value = datetime.combine(date.today(), time(0, minute))
        self.notify()


class DateTimeInput(StatefulComponent):
    """Date and time input widget with visual calendar picker popup.

    Features:
    - Visual calendar grid for date selection
    - Month/year quick navigation
    - Time picker with dropdown selectors
    - "Today" and preset time buttons

    Supports:
    - Date only (enable_date=True, enable_time=False)
    - Time only (enable_date=False, enable_time=True)
    - Both date and time (enable_date=True, enable_time=True)

    Example:
        state = DateTimeInputState(
            value="2024-12-25",
            enable_date=True,
            enable_time=False,
        )
        date_input = DateTimeInput(state, label="Birthday")

        # With callback
        date_input.on_change(lambda iso: print(f"Selected: {iso}"))
    """

    # Layout constants
    CELL_SIZE = 32
    GRID_WIDTH = 7 * CELL_SIZE  # 224px
    POPUP_PADDING = 16
    POPUP_WIDTH = GRID_WIDTH + POPUP_PADDING  # 240px
    HEADER_HEIGHT = 40
    WEEKDAY_HEIGHT = 24
    GRID_HEIGHT = 6 * CELL_SIZE  # 192px
    FOOTER_HEIGHT = 44
    TIME_PICKER_HEIGHT = 80

    def __init__(
        self,
        state: DateTimeInputState | None = None,
        label: str | None = None,
        enable_date: bool = True,
        enable_time: bool = False,
        value: datetime | date | time | str | None = None,
        min_date: date | None = None,
        max_date: date | None = None,
        first_day_of_week: int = 1,  # 1=Monday (ISO 8601)
        locale: CalendarLocale | None = None,
    ):
        """Initialize DateTimeInput.

        Args:
            state: Optional DateTimeInputState (creates new if not provided)
            label: Optional label displayed above the input
            enable_date: Whether to show date input (ignored if state provided)
            enable_time: Whether to show time input (ignored if state provided)
            value: Initial value (ignored if state provided)
            min_date: Minimum selectable date
            max_date: Maximum selectable date
            first_day_of_week: 0=Sunday, 1=Monday (default)
            locale: Locale for calendar display (default: EN)
        """
        self._label = label
        self._on_change_callback: Callable[[str | None], None] = lambda _: None
        self._min_date = min_date
        self._max_date = max_date
        self._first_day_of_week = first_day_of_week
        self._locale = locale or DEFAULT_LOCALE

        if state is not None:
            self._dt_state = state
        else:
            self._dt_state = DateTimeInputState(
                value=value,
                enable_date=enable_date,
                enable_time=enable_time,
            )

        # Internal calendar state (created when picker opens)
        self._calendar_state: CalendarState | None = None
        self._time_state: TimePickerState | None = None

        super().__init__(self._dt_state)

    def _init_picker_states(self) -> None:
        """Initialize calendar and time picker states from current value."""
        current_value = self._dt_state.value()

        # Create calendar state
        self._calendar_state = CalendarState(
            value=current_value.date() if current_value else None,
            min_date=self._min_date,
            max_date=self._max_date,
            first_day_of_week=self._first_day_of_week,
            locale=self._locale,
        )

        # Create time state if needed
        if self._dt_state.enable_time:
            if current_value:
                self._time_state = TimePickerState(
                    hour=current_value.hour,
                    minute=current_value.minute,
                    locale=self._locale,
                )
            else:
                self._time_state = TimePickerState(locale=self._locale)

    def view(self) -> Widget:
        """Build the date/time input UI."""
        theme = ThemeManager().current

        # Main input display
        display_text = self._dt_state.to_display_string() or self._locale.placeholder

        main_row = (
            Row(
                Text(display_text).text_color(theme.colors.text_primary).erase_border(),
                Button("...")
                .on_click(lambda _: self._toggle_picker())
                .fixed_size(40, 32),
            )
            .height(40)
            .height_policy(SizePolicy.FIXED)
        )

        # Wrap with label if provided
        if self._label:
            main_content = Column(
                Text(self._label)
                .text_color(theme.colors.text_info)
                .height(24)
                .height_policy(SizePolicy.FIXED),
                main_row,
            ).height_policy(SizePolicy.CONTENT)
        else:
            main_content = main_row

        # Build picker popup if open
        if self._dt_state.is_picker_open():
            # Ensure picker states exist
            if self._calendar_state is None:
                self._init_picker_states()

            # Calculate popup size
            popup_height = self.HEADER_HEIGHT + self.FOOTER_HEIGHT
            if self._dt_state.enable_date:
                popup_height += self.WEEKDAY_HEIGHT + self.GRID_HEIGHT
            if self._dt_state.enable_time:
                popup_height += self.TIME_PICKER_HEIGHT

            # Build picker with fixed size (no double wrapping)
            picker_popup = (
                self._build_picker(theme)
                .bg_color(theme.colors.bg_primary)
                .fixed_size(self.POPUP_WIDTH, popup_height)
                .z_index(100)
            )

            return Box(main_content, picker_popup)
        else:
            return main_content

    def _build_picker(self, theme) -> Widget:
        """Build the date/time picker UI with calendar."""
        rows: list[Widget] = []

        if self._dt_state.enable_date and self._calendar_state:
            # Header with navigation (40px)
            header = CalendarHeader(
                self._calendar_state, width=self.GRID_WIDTH
            ).fixed_height(self.HEADER_HEIGHT)
            rows.append(header)

            # Calendar view based on mode (24px weekday + 192px grid = 216px)
            grid_height = self.WEEKDAY_HEIGHT + self.GRID_HEIGHT
            view_mode = self._calendar_state.view_mode
            if view_mode == ViewMode.DAYS:
                grid = CalendarGrid(
                    self._calendar_state,
                    cell_size=self.CELL_SIZE,
                    on_select=self._on_date_select,
                ).fixed_height(grid_height)
                rows.append(grid)
            elif view_mode == ViewMode.MONTHS:
                month_picker = MonthPicker(
                    self._calendar_state, width=self.GRID_WIDTH
                ).fixed_height(grid_height)
                rows.append(month_picker)
            else:  # ViewMode.YEARS
                year_picker = YearPicker(
                    self._calendar_state, width=self.GRID_WIDTH
                ).fixed_height(grid_height)
                rows.append(year_picker)

        # Time picker
        if self._dt_state.enable_time and self._time_state:
            time_picker = TimePicker(
                self._time_state,
                width=self.GRID_WIDTH,
                show_presets=True,
            ).fixed_height(self.TIME_PICKER_HEIGHT)
            rows.append(time_picker)

        # Footer with Today and Done buttons
        footer = (
            Row(
                Button(self._locale.today_button)
                .on_click(lambda _: self._go_to_today())
                .height(32)
                .height_policy(SizePolicy.FIXED)
                .kind(Kind.NORMAL),
                Spacer(),
                Button(self._locale.done_button)
                .on_click(lambda _: self._apply_and_close())
                .height(32)
                .height_policy(SizePolicy.FIXED)
                .kind(Kind.SUCCESS),
            )
            .width(self.GRID_WIDTH)
            .width_policy(SizePolicy.FIXED)
            .height(self.FOOTER_HEIGHT)
            .height_policy(SizePolicy.FIXED)
        )
        rows.append(footer)

        return Column(*rows)

    def _on_date_select(self, selected_date: date) -> None:
        """Handle date selection from calendar grid."""
        # Update the main state with selected date
        current = self._dt_state.value()
        if current:
            new_dt = datetime.combine(selected_date, current.time())
        else:
            new_dt = datetime.combine(selected_date, time(0, 0))
        self._dt_state.set(new_dt)

    def _go_to_today(self) -> None:
        """Go to today's date."""
        if self._calendar_state:
            self._calendar_state.go_to_today()
            # Also update the main state
            today = date.today()
            current = self._dt_state.value()
            if current:
                new_dt = datetime.combine(today, current.time())
            else:
                new_dt = datetime.combine(today, time(0, 0))
            self._dt_state.set(new_dt)

    def _toggle_picker(self) -> None:
        """Toggle the picker popup."""
        if not self._dt_state.is_picker_open():
            # Initialize picker states when opening
            self._init_picker_states()
            self._dt_state.open_picker()
        else:
            self._close_picker()

    def _close_picker(self) -> None:
        """Close the picker popup without applying changes."""
        self._calendar_state = None
        self._time_state = None
        self._dt_state.close_picker()

    def _apply_and_close(self) -> None:
        """Apply selections, close picker and notify of change."""
        # Apply calendar selection
        if self._calendar_state and self._calendar_state.value:
            selected_date = self._calendar_state.value
        else:
            selected_date = (
                self._dt_state.value().date()
                if self._dt_state.value()
                else date.today()
            )

        # Apply time selection
        if self._time_state:
            selected_time = time(self._time_state.hour, self._time_state.minute)
        else:
            current = self._dt_state.value()
            selected_time = current.time() if current else time(0, 0)

        # Combine and set
        new_dt = datetime.combine(selected_date, selected_time)

        # Clean up and close
        self._calendar_state = None
        self._time_state = None
        self._dt_state.close_picker()

        # Set value (triggers rebuild)
        self._dt_state.set(new_dt)

        # Notify callback
        self._on_change_callback(self._dt_state.to_iso())

    def on_change(self, callback: Callable[[str | None], None]) -> Self:
        """Set callback for value changes.

        Args:
            callback: Function called with ISO 8601 string when value changes

        Returns:
            Self for method chaining
        """
        self._on_change_callback = callback
        return self

    def label(self, label: str) -> Self:
        """Set label text.

        Args:
            label: Label to display above the input

        Returns:
            Self for method chaining
        """
        self._label = label
        return self
