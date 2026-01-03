"""Shared toolbar component for workflow studios."""

from __future__ import annotations

from typing import Callable

from castella import (
    Component,
    Row,
    Button,
    Text,
    Spacer,
    Kind,
    SizePolicy,
)

# Button width constant for consistency
BUTTON_WIDTH = 72
SMALL_BUTTON_WIDTH = 40
BUTTON_SPACING = 4
GROUP_SPACING = 12


class Toolbar(Component):
    """Toolbar with workflow execution controls.

    Provides buttons for:
    - Run: Start continuous execution
    - Step: Execute single step
    - Pause: Pause running execution
    - Continue: Continue from pause/breakpoint
    - Stop: Stop execution
    - Reset: Reset execution state
    - Zoom controls
    """

    def __init__(
        self,
        can_run: bool = False,
        can_stop: bool = False,
        can_pause: bool = False,
        can_continue: bool = False,
        zoom_percent: int = 100,
        on_run: Callable[[], None] | None = None,
        on_step: Callable[[], None] | None = None,
        on_pause: Callable[[], None] | None = None,
        on_continue: Callable[[], None] | None = None,
        on_stop: Callable[[], None] | None = None,
        on_reset: Callable[[], None] | None = None,
        on_zoom_in: Callable[[], None] | None = None,
        on_zoom_out: Callable[[], None] | None = None,
        on_fit: Callable[[], None] | None = None,
    ):
        """Initialize the toolbar.

        Args:
            can_run: Whether run/step buttons should be enabled.
            can_stop: Whether stop button should be enabled.
            can_pause: Whether pause button should be enabled.
            can_continue: Whether continue button should be enabled.
            zoom_percent: Current zoom level.
            on_run: Callback for run button.
            on_step: Callback for step button.
            on_pause: Callback for pause button.
            on_continue: Callback for continue button.
            on_stop: Callback for stop button.
            on_reset: Callback for reset button.
            on_zoom_in: Callback for zoom in.
            on_zoom_out: Callback for zoom out.
            on_fit: Callback for fit to content.
        """
        super().__init__()

        self._can_run = can_run
        self._can_stop = can_stop
        self._can_pause = can_pause
        self._can_continue = can_continue
        self._zoom_percent = zoom_percent

        self._on_run = on_run
        self._on_step = on_step
        self._on_pause = on_pause
        self._on_continue = on_continue
        self._on_stop = on_stop
        self._on_reset = on_reset
        self._on_zoom_in = on_zoom_in
        self._on_zoom_out = on_zoom_out
        self._on_fit = on_fit

        # Set fixed height for the toolbar
        self._size.height = 44
        self._height_policy = SizePolicy.FIXED

    def view(self):
        """Build the toolbar UI."""
        return (
            Row(
                # Left spacing
                Spacer().fixed_width(8),
                # Run controls group
                self._build_run_button(),
                Spacer().fixed_width(BUTTON_SPACING),
                self._build_step_button(),
                # Divider
                self._vertical_divider(),
                # Pause/Stop controls group
                self._build_pause_button(),
                Spacer().fixed_width(BUTTON_SPACING),
                self._build_continue_button(),
                Spacer().fixed_width(BUTTON_SPACING),
                self._build_stop_button(),
                Spacer().fixed_width(BUTTON_SPACING),
                self._build_reset_button(),
                # Spacer pushes zoom controls to right
                Spacer(),
                # Zoom controls group
                self._build_zoom_out_button(),
                Spacer().fixed_width(BUTTON_SPACING),
                Text(f"{self._zoom_percent}%").fixed_width(48).fixed_height(28),
                Spacer().fixed_width(BUTTON_SPACING),
                self._build_zoom_in_button(),
                Spacer().fixed_width(BUTTON_SPACING),
                self._build_fit_button(),
                # Right spacing
                Spacer().fixed_width(8),
            )
            .fixed_height(44)
            .bg_color("#1e1f2b")
        )

    def _vertical_divider(self):
        """Build a vertical divider line."""
        return Spacer().fixed_width(GROUP_SPACING)

    def _build_run_button(self):
        """Build the Run button."""
        if self._on_run and self._can_run:
            btn = Button("Run").kind(Kind.SUCCESS)
            btn = btn.on_click(lambda _: self._on_run())
        else:
            btn = Button("Run").kind(Kind.NORMAL)
        return btn.fixed_size(BUTTON_WIDTH, 28)

    def _build_step_button(self):
        """Build the Step button."""
        if self._on_step and self._can_run:
            btn = Button("Step").kind(Kind.INFO)
            btn = btn.on_click(lambda _: self._on_step())
        else:
            btn = Button("Step").kind(Kind.NORMAL)
        return btn.fixed_size(BUTTON_WIDTH, 28)

    def _build_pause_button(self):
        """Build the Pause button."""
        if self._on_pause and self._can_pause:
            btn = Button("Pause").kind(Kind.WARNING)
            btn = btn.on_click(lambda _: self._on_pause())
        else:
            btn = Button("Pause").kind(Kind.NORMAL)
        return btn.fixed_size(BUTTON_WIDTH, 28)

    def _build_continue_button(self):
        """Build the Continue button."""
        if self._on_continue and self._can_continue:
            btn = Button("Continue").kind(Kind.SUCCESS)
            btn = btn.on_click(lambda _: self._on_continue())
        else:
            btn = Button("Continue").kind(Kind.NORMAL)
        return btn.fixed_size(BUTTON_WIDTH + 8, 28)

    def _build_stop_button(self):
        """Build the Stop button."""
        if self._on_stop and self._can_stop:
            btn = Button("Stop").kind(Kind.DANGER)
            btn = btn.on_click(lambda _: self._on_stop())
        else:
            btn = Button("Stop").kind(Kind.NORMAL)
        return btn.fixed_size(BUTTON_WIDTH, 28)

    def _build_reset_button(self):
        """Build the Reset button."""
        btn = Button("Reset")
        if self._on_reset:
            btn = btn.on_click(lambda _: self._on_reset())
        return btn.fixed_size(BUTTON_WIDTH, 28)

    def _build_zoom_out_button(self):
        """Build the zoom out button."""
        btn = Button("-").fixed_size(SMALL_BUTTON_WIDTH, 28)
        if self._on_zoom_out:
            btn = btn.on_click(lambda _: self._on_zoom_out())
        return btn

    def _build_zoom_in_button(self):
        """Build the zoom in button."""
        btn = Button("+").fixed_size(SMALL_BUTTON_WIDTH, 28)
        if self._on_zoom_in:
            btn = btn.on_click(lambda _: self._on_zoom_in())
        return btn

    def _build_fit_button(self):
        """Build the fit to content button."""
        btn = Button("Fit").fixed_size(SMALL_BUTTON_WIDTH + 8, 28)
        if self._on_fit:
            btn = btn.on_click(lambda _: self._on_fit())
        return btn
