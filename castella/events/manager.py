"""EventManager - Central event handling coordinator.

Integrates all event subsystems (focus, pointer, gesture, keyboard, shortcuts)
into a unified event handling interface.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Callable

from castella.models.geometry import Point
from castella.models.events import (
    MouseEvent,
    WheelEvent,
    InputKeyEvent,
    InputCharEvent,
    IMEPreeditEvent,
)
from castella.events.focus import FocusManager
from castella.events.pointer import PointerTracker
from castella.events.gesture import GestureRecognizer, GestureEvent, DragEvent
from castella.events.keyboard import KeyboardState
from castella.events.shortcuts import ShortcutHandler

if TYPE_CHECKING:
    from castella.core import Widget


class EventManager:
    """Central coordinator for all event handling.

    Integrates:
    - FocusManager: Keyboard focus and Tab navigation
    - PointerTracker: Mouse/touch position and state
    - GestureRecognizer: Tap, double-tap, long-press, drag
    - KeyboardState: Key press tracking
    - ShortcutHandler: Global keyboard shortcuts

    This class serves as the integration point between the Frame's
    raw events and the application's event handling logic.

    Example:
        manager = EventManager()

        # Register gesture callbacks
        manager.on_tap(lambda ev: print(f"Tap on {ev.target}"))
        manager.on_double_tap(lambda ev: print("Double tap!"))

        # Register shortcuts
        manager.shortcuts.register(SHORTCUT_SAVE, save_document)

        # In frame event handlers:
        frame.on_mouse_down(manager.handle_mouse_down)
        frame.on_input_key(manager.handle_key)
    """

    def __init__(self) -> None:
        self._focus = FocusManager()
        self._pointer = PointerTracker()
        self._gesture = GestureRecognizer(self._pointer)
        self._keyboard = KeyboardState()
        self._shortcuts = ShortcutHandler()

        self._root: Widget | None = None

    # ========== Subsystem Accessors ==========

    @property
    def focus(self) -> FocusManager:
        """Access the focus manager."""
        return self._focus

    @property
    def pointer(self) -> PointerTracker:
        """Access the pointer tracker."""
        return self._pointer

    @property
    def gesture(self) -> GestureRecognizer:
        """Access the gesture recognizer."""
        return self._gesture

    @property
    def keyboard(self) -> KeyboardState:
        """Access the keyboard state."""
        return self._keyboard

    @property
    def shortcuts(self) -> ShortcutHandler:
        """Access the shortcut handler."""
        return self._shortcuts

    # ========== Configuration ==========

    def set_root(self, widget: Widget) -> None:
        """Set the root widget for hit testing.

        Args:
            widget: The root widget of the application.
        """
        self._root = widget

    # ========== Gesture Callbacks (Convenience) ==========

    def on_tap(self, callback: Callable[[GestureEvent], None]) -> None:
        """Register a tap callback."""
        self._gesture.on_tap = callback

    def on_double_tap(self, callback: Callable[[GestureEvent], None]) -> None:
        """Register a double-tap callback."""
        self._gesture.on_double_tap = callback

    def on_long_press(self, callback: Callable[[GestureEvent], None]) -> None:
        """Register a long-press callback."""
        self._gesture.on_long_press = callback

    def on_drag_start(self, callback: Callable[[DragEvent], None]) -> None:
        """Register a drag start callback."""
        self._gesture.on_drag_start = callback

    def on_drag_update(self, callback: Callable[[DragEvent], None]) -> None:
        """Register a drag update callback."""
        self._gesture.on_drag_update = callback

    def on_drag_end(self, callback: Callable[[DragEvent], None]) -> None:
        """Register a drag end callback."""
        self._gesture.on_drag_end = callback

    # ========== Hit Testing ==========

    def hit_test(self, pos: Point) -> tuple[Widget | None, Point | None]:
        """Perform hit testing from the root widget.

        Args:
            pos: Position to test.

        Returns:
            Tuple of (hit_widget, local_position) or (None, None).
        """
        if self._root is None:
            return None, None
        return self._root.dispatch(pos)

    def hit_test_scrollable(
        self, pos: Point, is_direction_x: bool
    ) -> tuple[Widget | None, Point | None]:
        """Find a scrollable widget at a position.

        Args:
            pos: Position to test.
            is_direction_x: True for horizontal scroll, False for vertical.

        Returns:
            Tuple of (scrollable_widget, local_position) or (None, None).
        """
        if self._root is None:
            return None, None
        return self._root.dispatch_to_scrollable(pos, is_direction_x)

    # ========== Event Handlers ==========

    def handle_mouse_down(self, ev: MouseEvent) -> Widget | None:
        """Handle a mouse down event.

        Performs hit testing, updates pointer/gesture state,
        and returns the target widget.

        Args:
            ev: The mouse event.

        Returns:
            The widget that received the event, or None.
        """
        target, local_pos = self.hit_test(ev.pos)

        if target is not None and local_pos is not None:
            self._gesture.process_pointer_down(ev.pos, target)

            # Update hover target
            self._pointer.set_hover_target(target)

        return target

    def handle_mouse_up(self, ev: MouseEvent) -> Widget | None:
        """Handle a mouse up event.

        Args:
            ev: The mouse event.

        Returns:
            The widget that was released, or None.
        """
        self._gesture.process_pointer_up(ev.pos)
        return self._pointer.pressed_target

    def handle_cursor_pos(self, ev: MouseEvent) -> tuple[Widget | None, Widget | None]:
        """Handle a cursor position change.

        Args:
            ev: The mouse event.

        Returns:
            Tuple of (entered_widget, exited_widget) for hover state changes.
        """
        self._gesture.process_pointer_move(ev.pos)

        # Update hover target
        target, _ = self.hit_test(ev.pos)
        return self._pointer.set_hover_target(target)

    def handle_mouse_wheel(self, ev: WheelEvent) -> Widget | None:
        """Handle a mouse wheel event.

        Args:
            ev: The wheel event.

        Returns:
            The scrollable widget that should receive the event, or None.
        """
        # Determine scroll direction
        is_x = abs(ev.x_offset) > abs(ev.y_offset)
        target, _ = self.hit_test_scrollable(ev.pos, is_x)
        return target

    def handle_key(self, ev: InputKeyEvent) -> bool:
        """Handle a key event.

        Processes the event through shortcuts, focus manager,
        and keyboard state.

        Args:
            ev: The key event.

        Returns:
            True if the event was handled.
        """
        # Update keyboard state
        self._keyboard.process_key_event(ev)

        # Check shortcuts first
        if self._shortcuts.handle(ev):
            return True

        # Check Tab navigation
        if self._focus.handle_key_event(ev):
            return True

        return False

    def handle_char(self, ev: InputCharEvent) -> Widget | None:
        """Handle a character input event.

        Args:
            ev: The character event.

        Returns:
            The focused widget that should receive the event, or None.
        """
        return self._focus.focus

    def handle_ime_preedit(self, ev: IMEPreeditEvent) -> Widget | None:
        """Handle an IME preedit event.

        Args:
            ev: The IME event.

        Returns:
            The focused widget that should receive the event, or None.
        """
        return self._focus.focus

    # ========== State Management ==========

    def update(self) -> None:
        """Update time-based gesture detection (long-press).

        Call this periodically (e.g., each frame) to enable
        long-press detection.
        """
        self._gesture.update()

    def reset(self) -> None:
        """Reset all event state.

        Useful when the window loses focus or the application
        state is reset.
        """
        self._pointer.reset()
        self._gesture.reset()
        self._keyboard.reset()
        self._focus.clear_focus()
