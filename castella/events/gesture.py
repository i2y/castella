"""Gesture recognition from pointer events.

Detects high-level gestures like tap, double-tap, long-press, and drag.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, Callable

from castella.models.geometry import Point
from castella.events.pointer import PointerTracker

if TYPE_CHECKING:
    from castella.core import Widget


@dataclass
class GestureEvent:
    """Event data for gesture callbacks.

    Attributes:
        target: The widget that received the gesture.
        position: Position where the gesture occurred.
        click_count: Number of clicks (for tap gestures).
    """

    target: "Widget | None"
    position: Point
    click_count: int = 1


@dataclass
class DragEvent:
    """Event data for drag callbacks.

    Attributes:
        target: The widget being dragged.
        position: Current drag position.
        start_position: Position where drag started.
        delta: Movement since last drag update.
    """

    target: "Widget | None"
    position: Point
    start_position: Point
    delta: Point


class GestureRecognizer:
    """Detects gestures from pointer events.

    Recognizes:
    - Tap: Quick press and release without movement
    - Double-tap: Two taps in quick succession
    - Long-press: Press held for a duration without movement
    - Drag: Press with movement beyond threshold

    Example:
        recognizer = GestureRecognizer(pointer_tracker)

        recognizer.on_tap = lambda ev: print(f"Tap at {ev.position}")
        recognizer.on_double_tap = lambda ev: print("Double tap!")
        recognizer.on_long_press = lambda ev: show_context_menu(ev.position)
        recognizer.on_drag_start = lambda ev: start_drag(ev)
        recognizer.on_drag_update = lambda ev: update_drag(ev)
        recognizer.on_drag_end = lambda ev: end_drag(ev)
    """

    def __init__(self, tracker: PointerTracker | None = None) -> None:
        self._tracker = tracker or PointerTracker()

        # Timing configuration
        self._long_press_duration = 0.5  # seconds
        self._press_start_time: float = 0
        self._long_press_triggered = False

        # Position tracking for gestures
        self._press_position = Point(x=0, y=0)
        self._press_target: Widget | None = None

        # Callbacks
        self.on_tap: Callable[[GestureEvent], None] | None = None
        self.on_double_tap: Callable[[GestureEvent], None] | None = None
        self.on_long_press: Callable[[GestureEvent], None] | None = None
        self.on_drag_start: Callable[[DragEvent], None] | None = None
        self.on_drag_update: Callable[[DragEvent], None] | None = None
        self.on_drag_end: Callable[[DragEvent], None] | None = None

    @property
    def tracker(self) -> PointerTracker:
        """The pointer tracker used by this recognizer."""
        return self._tracker

    def process_pointer_down(
        self, pos: Point, target: Widget | None, timestamp: float | None = None
    ) -> None:
        """Process a pointer down event.

        Args:
            pos: Position of the press.
            target: Widget that was hit.
            timestamp: Event timestamp.
        """
        if timestamp is None:
            timestamp = time.time()

        self._press_start_time = timestamp
        self._press_position = pos
        self._press_target = target
        self._long_press_triggered = False

        # Track click count via pointer tracker
        self._tracker.process_down(pos, target, timestamp)

    def process_pointer_up(self, pos: Point, timestamp: float | None = None) -> None:
        """Process a pointer up event.

        Args:
            pos: Position of the release.
            timestamp: Event timestamp.
        """
        if timestamp is None:
            timestamp = time.time()

        target = self._tracker.process_up(pos)

        # Don't trigger tap if long-press was triggered or if dragging
        if self._long_press_triggered or self._tracker.is_dragging():
            if self._tracker.is_dragging() and self.on_drag_end:
                self.on_drag_end(
                    DragEvent(
                        target=self._press_target,
                        position=pos,
                        start_position=self._press_position,
                        delta=Point(x=0, y=0),
                    )
                )
            return

        # Detect tap/double-tap
        click_count = self._tracker._click_count

        if click_count >= 2 and self.on_double_tap:
            self.on_double_tap(
                GestureEvent(target=target, position=pos, click_count=click_count)
            )
        elif click_count == 1 and self.on_tap:
            self.on_tap(GestureEvent(target=target, position=pos, click_count=1))

    def process_pointer_move(self, pos: Point) -> None:
        """Process a pointer move event.

        Args:
            pos: New pointer position.
        """
        was_dragging = self._tracker.is_dragging()
        self._tracker.process_move(pos)

        if self._tracker.is_pressed():
            if self._tracker.is_dragging():
                if not was_dragging and self.on_drag_start:
                    # Drag just started
                    self.on_drag_start(
                        DragEvent(
                            target=self._press_target,
                            position=pos,
                            start_position=self._press_position,
                            delta=self._tracker.get_delta(),
                        )
                    )
                elif self.on_drag_update:
                    self.on_drag_update(
                        DragEvent(
                            target=self._press_target,
                            position=pos,
                            start_position=self._press_position,
                            delta=self._tracker.get_delta(),
                        )
                    )

    def update(self, timestamp: float | None = None) -> None:
        """Update gesture state (call periodically for long-press detection).

        Args:
            timestamp: Current timestamp.
        """
        if timestamp is None:
            timestamp = time.time()

        # Check for long-press
        if (
            self._tracker.is_pressed()
            and not self._long_press_triggered
            and not self._tracker.is_dragging()
        ):
            elapsed = timestamp - self._press_start_time
            if elapsed >= self._long_press_duration:
                self._long_press_triggered = True
                if self.on_long_press:
                    self.on_long_press(
                        GestureEvent(
                            target=self._press_target,
                            position=self._press_position,
                            click_count=1,
                        )
                    )

    def reset(self) -> None:
        """Reset gesture state."""
        self._long_press_triggered = False
        self._press_target = None
        self._tracker.reset()
