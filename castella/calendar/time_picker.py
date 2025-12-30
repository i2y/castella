"""TimePicker widget for time selection."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from castella.button import Button
from castella.column import Column
from castella.core import Kind, SizePolicy, StatefulComponent, Widget
from castella.row import Row
from castella.spacer import Spacer
from castella.text import Text
from castella.theme import ThemeManager

from .state import TimePickerState

if TYPE_CHECKING:
    pass


class TimePicker(StatefulComponent):
    """Time selection widget with hour/minute selection.

    Provides:
    - Hour selection buttons (0-23)
    - Minute selection buttons (by step, e.g., 0, 5, 10, ...)
    - "Now" button for quick current time selection
    - Preset time buttons

    The picker uses a dropdown-style button grid for selection.
    """

    def __init__(
        self,
        state: TimePickerState,
        width: int = 224,
        show_presets: bool = True,
    ):
        """Initialize TimePicker.

        Args:
            state: TimePickerState instance
            width: Total width of the picker
            show_presets: Whether to show preset time buttons
        """
        self._time_state = state
        self._width = width
        self._show_presets = show_presets
        self._show_hour_picker = False
        self._show_minute_picker = False
        super().__init__(state)

    def view(self) -> Widget:
        """Build the time picker view."""
        theme = ThemeManager().current

        rows: list[Widget] = []

        # Current time display row
        hour_str = f"{self._time_state.hour:02d}"
        minute_str = f"{self._time_state.minute:02d}"

        locale = self._time_state.locale
        time_row = (
            Row(
                Text(locale.time_label)
                .text_color(theme.colors.text_info)
                .height(32)
                .height_policy(SizePolicy.FIXED),
                Spacer().width(8).width_policy(SizePolicy.FIXED),
                Button(hour_str)
                .on_click(lambda _: self._toggle_hour_picker())
                .fixed_size(48, 32)
                .kind(Kind.INFO if self._show_hour_picker else Kind.NORMAL),
                Text(":").text_color(theme.colors.text_primary).fixed_size(12, 32),
                Button(minute_str)
                .on_click(lambda _: self._toggle_minute_picker())
                .fixed_size(48, 32)
                .kind(Kind.INFO if self._show_minute_picker else Kind.NORMAL),
                Spacer(),
                Button(locale.now_button)
                .on_click(lambda _: self._set_now())
                .fixed_size(36, 32)
                .kind(Kind.SUCCESS),
            )
            .width(self._width)
            .width_policy(SizePolicy.FIXED)
            .height(40)
            .height_policy(SizePolicy.FIXED)
        )
        rows.append(time_row)

        # Hour picker grid (if shown)
        if self._show_hour_picker:
            rows.append(self._build_hour_picker())

        # Minute picker grid (if shown)
        if self._show_minute_picker:
            rows.append(self._build_minute_picker())

        # Preset buttons (if enabled and pickers are closed)
        if (
            self._show_presets
            and not self._show_hour_picker
            and not self._show_minute_picker
        ):
            presets_row = (
                Row(
                    Button("9:00")
                    .on_click(lambda _: self._set_time(9, 0))
                    .fixed_size(50, 28),
                    Button("12:00")
                    .on_click(lambda _: self._set_time(12, 0))
                    .fixed_size(50, 28),
                    Button("15:00")
                    .on_click(lambda _: self._set_time(15, 0))
                    .fixed_size(50, 28),
                    Button("18:00")
                    .on_click(lambda _: self._set_time(18, 0))
                    .fixed_size(50, 28),
                )
                .height(32)
                .height_policy(SizePolicy.FIXED)
            )
            rows.append(presets_row)

        return (
            Column(*rows)
            .width(self._width)
            .width_policy(SizePolicy.FIXED)
            .height_policy(SizePolicy.CONTENT)
            .bg_color(theme.colors.bg_primary)
        )

    def _build_hour_picker(self) -> Widget:
        """Build hour selection grid (4 rows x 6 columns = 24 hours)."""
        theme = ThemeManager().current
        button_size = 32
        rows: list[Widget] = []

        for row_idx in range(4):
            buttons: list[Widget] = []
            for col_idx in range(6):
                hour = row_idx * 6 + col_idx
                is_current = hour == self._time_state.hour

                btn = (
                    Button(f"{hour:02d}")
                    .on_click(self._create_hour_handler(hour))
                    .fixed_size(button_size, button_size)
                )

                if is_current:
                    btn = btn.kind(Kind.INFO)

                buttons.append(btn)

            row = Row(*buttons).height(button_size + 2).height_policy(SizePolicy.FIXED)
            rows.append(row)

        return (
            Column(*rows)
            .width(self._width)
            .width_policy(SizePolicy.FIXED)
            .height_policy(SizePolicy.CONTENT)
            .bg_color(theme.colors.bg_secondary)
        )

    def _build_minute_picker(self) -> Widget:
        """Build minute selection grid based on step."""
        theme = ThemeManager().current
        button_size = 36
        minutes = self._time_state.get_minute_options()

        # Arrange in rows of 6
        rows: list[Widget] = []
        for i in range(0, len(minutes), 6):
            buttons: list[Widget] = []
            for minute in minutes[i : i + 6]:
                is_current = minute == self._time_state.minute

                btn = (
                    Button(f"{minute:02d}")
                    .on_click(self._create_minute_handler(minute))
                    .fixed_size(button_size, button_size)
                )

                if is_current:
                    btn = btn.kind(Kind.INFO)

                buttons.append(btn)

            row = Row(*buttons).height(button_size + 2).height_policy(SizePolicy.FIXED)
            rows.append(row)

        return (
            Column(*rows)
            .width(self._width)
            .width_policy(SizePolicy.FIXED)
            .height_policy(SizePolicy.CONTENT)
            .bg_color(theme.colors.bg_secondary)
        )

    def _toggle_hour_picker(self) -> None:
        """Toggle hour picker visibility."""
        self._show_hour_picker = not self._show_hour_picker
        self._show_minute_picker = False
        self._time_state.notify()

    def _toggle_minute_picker(self) -> None:
        """Toggle minute picker visibility."""
        self._show_minute_picker = not self._show_minute_picker
        self._show_hour_picker = False
        self._time_state.notify()

    def _set_now(self) -> None:
        """Set to current time."""
        now = datetime.now()
        self._time_state.set_time(now.hour, now.minute)
        self._show_hour_picker = False
        self._show_minute_picker = False

    def _set_time(self, hour: int, minute: int) -> None:
        """Set a specific time."""
        self._time_state.set_time(hour, minute)
        self._show_hour_picker = False
        self._show_minute_picker = False

    def _create_hour_handler(self, hour: int):
        """Create a click handler for a specific hour."""

        def handler(_):
            self._time_state.set_hour(hour)
            self._show_hour_picker = False

        return handler

    def _create_minute_handler(self, minute: int):
        """Create a click handler for a specific minute."""

        def handler(_):
            self._time_state.set_minute(minute)
            self._show_minute_picker = False

        return handler
