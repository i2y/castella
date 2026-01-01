"""Pointer (mouse/touch) state tracking.

Tracks pointer position, button state, and drag operations.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from castella.models.geometry import Point

if TYPE_CHECKING:
    from castella.core import Widget


class PointerTracker:
    """Tracks pointer state across events.

    Maintains current position, pressed state, hover target,
    and supports drag detection with configurable threshold.

    Example:
        tracker = PointerTracker()

        def on_mouse_down(ev):
            tracker.process_down(ev.pos, time.time())

        def on_mouse_move(ev):
            entered, exited = tracker.process_move(ev.pos)
            if exited:
                exited.mouse_out()
            if entered:
                entered.mouse_over()
    """

    def __init__(self) -> None:
        self._position = Point(x=0, y=0)
        self._last_position = Point(x=0, y=0)
        self._pressed_target: Widget | None = None
        self._hover_target: Widget | None = None
        self._is_dragging = False
        self._drag_start = Point(x=0, y=0)
        self._drag_threshold = 4.0  # pixels before drag starts

        # Click detection
        self._last_click_time: float = 0
        self._last_click_pos = Point(x=0, y=0)
        self._click_count = 0
        self._double_click_time = 0.3  # seconds
        self._double_click_radius = 5.0  # pixels

    @property
    def position(self) -> Point:
        """Current pointer position."""
        return self._position

    @property
    def last_position(self) -> Point:
        """Previous pointer position."""
        return self._last_position

    def is_pressed(self) -> bool:
        """Check if pointer button is currently pressed."""
        return self._pressed_target is not None

    def is_dragging(self) -> bool:
        """Check if a drag operation is in progress."""
        return self._is_dragging

    @property
    def hover_target(self) -> Widget | None:
        """Widget currently under the pointer."""
        return self._hover_target

    @property
    def pressed_target(self) -> Widget | None:
        """Widget that received the press event."""
        return self._pressed_target

    def process_down(
        self, pos: Point, target: Widget | None, timestamp: float | None = None
    ) -> int:
        """Process a pointer down event.

        Args:
            pos: Position of the press.
            target: Widget that was hit.
            timestamp: Event timestamp (defaults to current time).

        Returns:
            Click count (1 for single, 2 for double, etc.).
        """
        if timestamp is None:
            timestamp = time.time()

        self._position = pos
        self._pressed_target = target
        self._drag_start = pos
        self._is_dragging = False

        # Detect multi-click
        time_delta = timestamp - self._last_click_time
        dist = (
            (pos.x - self._last_click_pos.x) ** 2
            + (pos.y - self._last_click_pos.y) ** 2
        ) ** 0.5

        if time_delta < self._double_click_time and dist < self._double_click_radius:
            self._click_count += 1
        else:
            self._click_count = 1

        self._last_click_time = timestamp
        self._last_click_pos = pos

        return self._click_count

    def process_up(self, pos: Point) -> Widget | None:
        """Process a pointer up event.

        Args:
            pos: Position of the release.

        Returns:
            The widget that was pressed (for click handling).
        """
        self._position = pos
        target = self._pressed_target
        self._pressed_target = None
        self._is_dragging = False
        return target

    def process_move(self, pos: Point) -> tuple[Widget | None, Widget | None]:
        """Process a pointer move event.

        Args:
            pos: New pointer position.

        Returns:
            Tuple of (entered_widget, exited_widget) for hover tracking.
        """
        self._last_position = self._position
        self._position = pos

        # Check for drag start
        if self._pressed_target is not None and not self._is_dragging:
            dist = (
                (pos.x - self._drag_start.x) ** 2 + (pos.y - self._drag_start.y) ** 2
            ) ** 0.5
            if dist >= self._drag_threshold:
                self._is_dragging = True

        # Hover changes are tracked externally
        return None, None

    def set_hover_target(
        self, target: Widget | None
    ) -> tuple[Widget | None, Widget | None]:
        """Update the hover target.

        Args:
            target: New hover target (or None).

        Returns:
            Tuple of (entered_widget, exited_widget).
        """
        old = self._hover_target
        if old is target:
            return None, None

        self._hover_target = target
        return target, old

    def get_delta(self) -> Point:
        """Get pointer movement since last position."""
        return Point(
            x=self._position.x - self._last_position.x,
            y=self._position.y - self._last_position.y,
        )

    def reset(self) -> None:
        """Reset all pointer state."""
        self._pressed_target = None
        self._hover_target = None
        self._is_dragging = False
        self._click_count = 0
