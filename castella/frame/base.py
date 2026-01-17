"""Base frame implementation with common functionality."""

from __future__ import annotations

import threading
from abc import ABC, abstractmethod
from asyncio import Future
from queue import SimpleQueue
from typing import TYPE_CHECKING, Any, Callable, cast

from castella.models.geometry import Point, Rect, Size
from castella.models.events import (
    CursorType,
    IMEPreeditEvent,
    InputCharEvent,
    InputKeyEvent,
    MouseEvent,
    UpdateEvent,
    WheelEvent,
)

if TYPE_CHECKING:
    from castella.protocols.painter import BasePainter


class BaseFrame(ABC):
    """Abstract base class for all frame implementations.

    Provides common functionality for:
    - Event handler registration
    - Update event queuing and dispatch
    - Thread-safe update posting
    - Clipboard operations (with default not-implemented)

    Subclasses must implement:
    - _create_window(): Platform-specific window creation
    - _update_surface_and_painter(): Recreate surface after resize
    - _signal_main_thread(): Wake up main thread for updates
    - get_painter(): Return the painter
    - get_size(): Return current size
    - flush(): Flush drawing operations
    - clear(): Clear the frame
    - run(): Main event loop
    """

    def __init__(
        self, title: str = "castella", width: float = 500, height: float = 500
    ):
        self._title = title
        self._size = Size(width=width, height=height)
        self._update_event_queue: SimpleQueue[UpdateEvent] = SimpleQueue()

        # Event handlers - initialized to no-op to avoid AttributeError
        self._callback_on_mouse_down: Callable[[MouseEvent], None] = lambda ev: None
        self._callback_on_mouse_up: Callable[[MouseEvent], None] = lambda ev: None
        self._callback_on_mouse_wheel: Callable[[WheelEvent], None] = lambda ev: None
        self._callback_on_cursor_pos: Callable[[MouseEvent], None] = lambda ev: None
        self._callback_on_input_char: Callable[[InputCharEvent], None] = lambda ev: None
        self._callback_on_input_key: Callable[[InputKeyEvent], None] = lambda ev: None
        self._callback_on_ime_preedit: Callable[[IMEPreeditEvent], None] = (
            lambda ev: None
        )
        self._callback_on_redraw: Callable[[Any, bool], None] = lambda p, c: None

    # ========== Event Handler Registration (Unified API) ==========

    def on_mouse_down(self, handler: Callable[[MouseEvent], None]) -> None:
        """Register handler for mouse button down events."""
        self._callback_on_mouse_down = handler

    def on_mouse_up(self, handler: Callable[[MouseEvent], None]) -> None:
        """Register handler for mouse button up events."""
        self._callback_on_mouse_up = handler

    def on_mouse_wheel(self, handler: Callable[[WheelEvent], None]) -> None:
        """Register handler for mouse wheel events."""
        self._callback_on_mouse_wheel = handler

    def on_cursor_pos(self, handler: Callable[[MouseEvent], None]) -> None:
        """Register handler for cursor position changes."""
        self._callback_on_cursor_pos = handler

    def on_input_char(self, handler: Callable[[InputCharEvent], None]) -> None:
        """Register handler for character input events."""
        self._callback_on_input_char = handler

    def on_input_key(self, handler: Callable[[InputKeyEvent], None]) -> None:
        """Register handler for key input events."""
        self._callback_on_input_key = handler

    def on_ime_preedit(self, handler: Callable[[IMEPreeditEvent], None]) -> None:
        """Register handler for IME preedit (composition) events."""
        self._callback_on_ime_preedit = handler

    def set_ime_cursor_rect(self, x: int, y: int, w: int, h: int) -> None:
        """Set the IME cursor rectangle for candidate window positioning.

        Subclasses should override this to communicate cursor position
        to the platform's IME system.

        Args:
            x: X coordinate of the cursor
            y: Y coordinate of the cursor
            w: Width of the cursor rectangle
            h: Height of the cursor rectangle
        """
        pass  # Default no-op, subclasses override

    def set_cursor(self, cursor_type: CursorType) -> None:
        """Set the mouse cursor shape.

        Subclasses should override this to change the cursor appearance.

        Args:
            cursor_type: The type of cursor to display.
        """
        pass  # Default no-op, subclasses override

    def on_redraw(self, handler: Callable[[Any, bool], None]) -> None:
        """Register handler for redraw events."""
        self._callback_on_redraw = handler

    # ========== Thread-Safe Update Posting ==========

    def post_update(self, ev: UpdateEvent) -> None:
        """Post an update event, thread-safe.

        If called from a background thread, queues the event and signals
        the main thread. If called from the main thread, processes immediately.
        """
        if self._is_background_thread():
            self._update_event_queue.put(ev)
            self._signal_main_thread()
        else:
            self._post_update(ev)

    def _is_background_thread(self) -> bool:
        """Check if current thread is not the main thread."""
        return threading.current_thread() is not threading.main_thread()

    def _process_pending_updates(self) -> None:
        """Process all pending updates from background threads.

        Uses BuildOwner's build_scope to batch component rebuilds,
        preventing cascade issues when multiple states change.
        """
        from castella.build_owner import BuildOwner

        owner = BuildOwner.get()
        with owner.build_scope():
            while not self._update_event_queue.empty():
                self._post_update(self._update_event_queue.get_nowait())

    # ========== Common Implementation: _post_update ==========

    def _post_update(self, ev: UpdateEvent) -> None:
        """Process an update event - common implementation for all frames.

        This method:
        1. Gets the target's ABSOLUTE position (walking up parent chain)
        2. Saves painter state
        3. Translates to target position
        4. Clips if not App-level update
        5. Calls target's redraw
        6. Flushes and restores painter
        """
        if ev.target is None:
            return

        # Import here to avoid circular dependency
        from castella.core import App, Widget

        if isinstance(ev.target, App):
            pos = Point(x=0, y=0)
            clipped_rect = None
        else:
            w: Widget = cast(Widget, ev.target)
            # Calculate absolute position by walking up the parent chain
            pos = self._get_absolute_position(w)
            clipped_rect = Rect(origin=Point(x=0, y=0), size=w.get_size())

        painter = self.get_painter()
        painter.save()
        try:
            painter.translate(pos)
            if clipped_rect is not None:
                painter.clip(clipped_rect)
            ev.target.redraw(painter, ev.completely)
            painter.flush()
        finally:
            painter.restore()

    def _get_absolute_position(self, widget: Any) -> Point:
        """Get the absolute screen position of a widget.

        In Castella, widget positions are stored as absolute coordinates
        (relative to window origin), so we just return the widget's position.

        Args:
            widget: The widget to get the absolute position for

        Returns:
            The absolute screen position as a Point
        """
        return widget.get_pos()

    # ========== Abstract Methods (Platform-Specific) ==========

    @abstractmethod
    def _signal_main_thread(self) -> None:
        """Signal the main thread that an update is pending.

        This should wake up the main event loop so it can process
        the queued update events.
        """
        ...

    @abstractmethod
    def _update_surface_and_painter(self) -> None:
        """Update the rendering surface and painter after resize."""
        ...

    @abstractmethod
    def get_painter(self) -> "BasePainter":
        """Get the painter for this frame."""
        ...

    @abstractmethod
    def get_size(self) -> Size:
        """Get the current frame size."""
        ...

    @abstractmethod
    def flush(self) -> None:
        """Flush pending drawing operations to screen."""
        ...

    @abstractmethod
    def clear(self) -> None:
        """Clear the frame."""
        ...

    @abstractmethod
    def run(self) -> None:
        """Start the main event loop.

        Must be called from the main thread.
        """
        ...

    # ========== Clipboard (with default not-implemented) ==========

    def get_clipboard_text(self) -> str:
        """Synchronous clipboard read. Override if supported."""
        raise NotImplementedError(
            "Synchronous clipboard not supported on this platform"
        )

    def set_clipboard_text(self, text: str) -> None:
        """Synchronous clipboard write. Override if supported."""
        raise NotImplementedError(
            "Synchronous clipboard not supported on this platform"
        )

    def async_get_clipboard_text(self, callback: Callable[[Future[str]], None]) -> None:
        """Async clipboard read. Override if supported."""
        raise NotImplementedError("Async clipboard not supported on this platform")

    def async_set_clipboard_text(
        self, text: str, callback: Callable[[Future[Any]], None]
    ) -> None:
        """Async clipboard write. Override if supported."""
        raise NotImplementedError("Async clipboard not supported on this platform")

    # ========== Software Keyboard (for mobile) ==========

    def show_keyboard(self, initial_text: str = "") -> None:
        """Show the software keyboard for text input.

        Override on platforms with software keyboards (iOS, Android).
        Default is no-op for desktop platforms.

        Args:
            initial_text: Initial text to populate the input field with.
                         Used to sync the hidden input field with the widget's text.
        """
        pass

    def hide_keyboard(self) -> None:
        """Hide the software keyboard.

        Override on platforms with software keyboards (iOS, Android).
        Default is no-op for desktop platforms.
        """
        pass

    # ========== Utility Methods ==========

    def _ensure_main_thread(self) -> None:
        """Raise RuntimeError if not called from main thread."""
        if self._is_background_thread():
            raise RuntimeError("This method must be called from main thread")
