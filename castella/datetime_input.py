"""DateTimeInput widget for date and time selection.

Provides a combined date/time input with optional picker popup.
"""

from __future__ import annotations

from datetime import datetime, date, time
from typing import Callable, Self

from castella.box import Box
from castella.button import Button
from castella.column import Column
from castella.core import (
    Kind,
    ObservableBase,
    SizePolicy,
    StatefulComponent,
    Widget,
)
from castella.input import Input
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
    """Date and time input widget with picker popup.

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

    def __init__(
        self,
        state: DateTimeInputState | None = None,
        label: str | None = None,
        enable_date: bool = True,
        enable_time: bool = False,
        value: datetime | date | time | str | None = None,
    ):
        """Initialize DateTimeInput.

        Args:
            state: Optional DateTimeInputState (creates new if not provided)
            label: Optional label displayed above the input
            enable_date: Whether to show date input (ignored if state provided)
            enable_time: Whether to show time input (ignored if state provided)
            value: Initial value (ignored if state provided)
        """
        self._label = label
        self._on_change_callback: Callable[[str | None], None] = lambda _: None

        if state is not None:
            self._dt_state = state
        else:
            self._dt_state = DateTimeInputState(
                value=value,
                enable_date=enable_date,
                enable_time=enable_time,
            )

        # Temporary input values for picker (don't trigger re-renders)
        self._temp_year = ""
        self._temp_month = ""
        self._temp_day = ""
        self._temp_hour = ""
        self._temp_minute = ""

        super().__init__(self._dt_state)

    def view(self) -> Widget:
        """Build the date/time input UI."""
        theme = ThemeManager().current

        # Main input display
        display_text = self._dt_state.to_display_string() or "Select..."

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

        if not self._dt_state.is_picker_open():
            return main_content

        # Build picker popup
        picker_content = self._build_picker(theme)

        # Picker popup
        picker = (
            Column(picker_content)
            .bg_color(theme.colors.bg_primary)
            .fixed_size(280, 180)
            .z_index(100)
        )

        # Backdrop
        backdrop = (
            _ClickableBackdrop(lambda _: self._close_picker())
            .bg_color("rgba(0, 0, 0, 0.3)")
            .z_index(99)
        )

        return Box(main_content.z_index(1), backdrop, picker)

    def _init_temp_values(self) -> None:
        """Initialize temporary values from current state."""
        value = self._dt_state.value() or datetime.now()
        self._temp_year = str(value.year)
        self._temp_month = str(value.month)
        self._temp_day = str(value.day)
        self._temp_hour = f"{value.hour:02d}"
        self._temp_minute = f"{value.minute:02d}"

    def _build_picker(self, theme) -> Widget:
        """Build the date/time picker UI."""
        rows = []

        if self._dt_state.enable_date:
            # Date picker: Year / Month / Day
            date_row = (
                Row(
                    Column(
                        Text("Year").height(20).height_policy(SizePolicy.FIXED),
                        Input(self._temp_year)
                        .on_change(lambda v: setattr(self, "_temp_year", v))
                        .height(32)
                        .height_policy(SizePolicy.FIXED),
                    ),
                    Column(
                        Text("Month").height(20).height_policy(SizePolicy.FIXED),
                        Input(self._temp_month)
                        .on_change(lambda v: setattr(self, "_temp_month", v))
                        .height(32)
                        .height_policy(SizePolicy.FIXED),
                    ),
                    Column(
                        Text("Day").height(20).height_policy(SizePolicy.FIXED),
                        Input(self._temp_day)
                        .on_change(lambda v: setattr(self, "_temp_day", v))
                        .height(32)
                        .height_policy(SizePolicy.FIXED),
                    ),
                )
                .height(60)
                .height_policy(SizePolicy.FIXED)
            )
            rows.append(date_row)

        if self._dt_state.enable_time:
            # Time picker: Hour : Minute
            time_row = (
                Row(
                    Column(
                        Text("Hour").height(20).height_policy(SizePolicy.FIXED),
                        Input(self._temp_hour)
                        .on_change(lambda v: setattr(self, "_temp_hour", v))
                        .height(32)
                        .height_policy(SizePolicy.FIXED),
                    ),
                    Column(
                        Text("Min").height(20).height_policy(SizePolicy.FIXED),
                        Input(self._temp_minute)
                        .on_change(lambda v: setattr(self, "_temp_minute", v))
                        .height(32)
                        .height_policy(SizePolicy.FIXED),
                    ),
                )
                .height(60)
                .height_policy(SizePolicy.FIXED)
            )
            rows.append(time_row)

        # Done button
        rows.append(
            Row(
                Spacer(),
                Button("Done")
                .on_click(lambda _: self._apply_and_close())
                .kind(Kind.INFO),
            )
            .height(50)
            .height_policy(SizePolicy.FIXED)
        )

        return Column(*rows)

    def _apply_temp_values(self) -> None:
        """Apply temporary input values to the state."""
        try:
            year = int(self._temp_year) if self._temp_year else None
            month = int(self._temp_month) if self._temp_month else None
            day = int(self._temp_day) if self._temp_day else None
            hour = int(self._temp_hour) if self._temp_hour else 0
            minute = int(self._temp_minute) if self._temp_minute else 0

            if year and month and day:
                new_dt = datetime(year, month, day, hour, minute)
                self._dt_state.set(new_dt)
        except (ValueError, TypeError):
            pass  # Ignore invalid input

    def _toggle_picker(self) -> None:
        """Toggle the picker popup."""
        if not self._dt_state.is_picker_open():
            # Initialize temp values when opening
            self._init_temp_values()
        self._dt_state.toggle_picker()

    def _close_picker(self) -> None:
        """Close the picker popup without applying changes."""
        self._dt_state.close_picker()

    def _apply_and_close(self) -> None:
        """Apply temp values, close picker and notify of change."""
        self._apply_temp_values()
        self._dt_state.close_picker()
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


class _ClickableBackdrop(Spacer):
    """Internal backdrop widget that handles click events."""

    def __init__(self, on_click: Callable | None = None):
        super().__init__()
        self._on_click_handler = on_click

    def mouse_up(self, ev) -> None:
        """Handle mouse up (click)."""
        if self._on_click_handler:
            self._on_click_handler(ev)
