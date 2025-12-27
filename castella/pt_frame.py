"""Prompt-toolkit based TUI frame implementation."""

from __future__ import annotations

from asyncio import Future
from queue import Queue
from typing import TYPE_CHECKING, Callable, Any, cast

import pyperclip
from prompt_toolkit import Application
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.keys import Keys
from prompt_toolkit.layout import Layout as PTLayout
from prompt_toolkit.layout.containers import Window
from prompt_toolkit.layout.controls import UIContent, UIControl
from prompt_toolkit.mouse_events import MouseEvent as PTMouseEvent, MouseEventType

from castella.frame.base import BaseFrame
from castella.models.geometry import Point, Size, Rect
from castella.models.events import (
    InputCharEvent,
    InputKeyEvent,
    KeyAction,
    KeyCode,
    MouseEvent,
    WheelEvent,
)
from castella.pt_painter import PTPainter, Canvas, FONT_SIZE

if TYPE_CHECKING:
    from castella.models.events import UpdateEvent
    from castella.protocols.painter import BasePainter


class PTFrame(BaseFrame):
    """Prompt-toolkit based TUI frame."""

    def __init__(self, title: str, width: float = 0, height: float = 0) -> None:
        # Note: width/height are in logical units (character cells * FONT_SIZE)
        super().__init__(title, width, height)

        self._running = True
        self._painter = PTPainter(Canvas(0, 0))
        self._event_queue: Queue[UpdateEvent] = Queue()

        self.bindings = KeyBindings()
        self._register_keybindings()
        self.application = Application(
            full_screen=True,
            key_bindings=self.bindings,
            mouse_support=True,
            layout=PTLayout(Window(content=PTControl(self))),
            refresh_interval=0.1,
        )

    def _register_keybindings(self) -> None:
        @self.bindings.add("<sigint>")
        @self.bindings.add("c-c")
        def _(event):
            self._running = False
            event.app.exit()

        @self.bindings.add("left")
        @self.bindings.add("right")
        @self.bindings.add("backspace")
        @self.bindings.add("delete")
        @self.bindings.add("up")
        @self.bindings.add("down")
        @self.bindings.add("pageup")
        @self.bindings.add("pagedown")
        @self.bindings.add("home")
        @self.bindings.add("end")
        @self.bindings.add("enter")
        def _(event):
            ev = InputKeyEvent(
                key=_convert_to_key_code(event.key_sequence[0].key),
                scancode=0,
                action=KeyAction.PRESS,
                mods=0,
            )
            self._callback_on_input_key(ev)

        @self.bindings.add("<any>")
        def _(event):
            ev = InputCharEvent(char=event.key_sequence[0].key)
            self._callback_on_input_char(ev)

    # ========== Abstract Method Implementations ==========

    def _update_surface_and_painter(self) -> None:
        """Recreate canvas for current size."""
        width_chars = int(self._size.width / FONT_SIZE)
        height_chars = int(self._size.height / FONT_SIZE)
        self._painter.canvas = Canvas(width_chars, height_chars)
        self._painter.clear_all()

    def _signal_main_thread(self) -> None:
        """Not needed for prompt_toolkit - uses its own event loop."""
        pass

    def get_painter(self) -> "BasePainter":
        return self._painter

    def get_size(self) -> Size:
        return self._size

    def flush(self) -> None:
        pass

    def clear(self) -> None:
        self._painter.clear_all()

    def run(self) -> None:
        try:
            self.application.run()
        except KeyboardInterrupt:
            pass

    # ========== Post Update Override ==========

    def post_update(self, ev: "UpdateEvent") -> None:
        """Queue update event for processing in create_content."""
        self._event_queue.put(ev)

    # ========== Clipboard ==========

    def get_clipboard_text(self) -> str:
        return pyperclip.paste()

    def set_clipboard_text(self, text: str) -> None:
        pyperclip.copy(text)

    def async_get_clipboard_text(self, callback: Callable[[Future[str]], None]) -> None:
        raise NotImplementedError

    def async_set_clipboard_text(
        self, text: str, callback: Callable[[Future[Any]], None]
    ) -> None:
        raise NotImplementedError

    # ========== TUI-specific Methods ==========

    def redraw(self, width: int, height: int) -> None:
        """Redraw after resize."""
        self._size = Size(width=width * FONT_SIZE, height=height * FONT_SIZE)
        self._painter.canvas = Canvas(width, height)
        self._painter.clear_all()
        self._callback_on_redraw(self._painter, True)

    def init_canvas(self, width: int, height: int) -> None:
        """Initialize canvas on first render."""
        self._size = Size(width=width * FONT_SIZE, height=height * FONT_SIZE)
        self._painter.canvas = Canvas(width, height)
        self._painter.clear_all()

    def is_resized(self, width: int, height: int) -> bool:
        """Check if terminal has been resized."""
        return (
            self._size.width != width * FONT_SIZE
            or self._size.height != height * FONT_SIZE
        )


def _convert_to_key_code(code) -> KeyCode:
    match code:
        case Keys.ControlH:
            return KeyCode.BACKSPACE
        case Keys.Left:
            return KeyCode.LEFT
        case Keys.Right:
            return KeyCode.RIGHT
        case Keys.Up:
            return KeyCode.UP
        case Keys.Down:
            return KeyCode.DOWN
        case Keys.PageUp:
            return KeyCode.PAGE_UP
        case Keys.PageDown:
            return KeyCode.PAGE_DOWN
        case Keys.Delete:
            return KeyCode.DELETE
        case Keys.Any:
            return KeyCode.UNKNOWN
        case _:
            return KeyCode.UNKNOWN


class PTControl(UIControl):
    """Prompt-toolkit UI control for rendering Castella widgets."""

    def __init__(self, frame: PTFrame):
        self.frame = frame

    def _post_update(self, ev: "UpdateEvent") -> None:
        """Process an update event - uses BaseFrame's implementation."""
        if ev.target is None:
            return

        # Import here to avoid circular dependency
        from castella.core import App, Widget

        if isinstance(ev.target, App):
            pos = Point(x=0, y=0)
            clipped_rect = None
        else:
            w: Widget = cast(Widget, ev.target)
            pos = w.get_pos()
            clipped_rect = Rect(origin=Point(x=0, y=0), size=w.get_size())

        painter = self.frame.get_painter()
        painter.save()
        try:
            painter.translate(pos)
            if clipped_rect is not None:
                painter.clip(clipped_rect)
            ev.target.redraw(painter, ev.completely)
            painter.flush()
        finally:
            painter.restore()

    def create_content(self, width: int, height: int) -> UIContent:
        if self.frame._painter.canvas is None:
            self.frame.init_canvas(width, height)
        elif self.frame.is_resized(width, height):
            self.frame.redraw(width, height)
            renderable = self.frame._painter._get_renderable()

            return UIContent(
                get_line=renderable.__getitem__,  # type: ignore
                line_count=len(renderable),
            )

        while not self.frame._event_queue.empty():
            ev = self.frame._event_queue.get_nowait()
            self._post_update(ev)
        renderable = self.frame._painter._get_renderable()

        return UIContent(
            get_line=renderable.__getitem__,  # type: ignore
            line_count=len(renderable),
            show_cursor=False,
        )

    def mouse_handler(self, mouse_event: PTMouseEvent) -> None:
        pos = Point(
            x=mouse_event.position.x * FONT_SIZE,
            y=mouse_event.position.y * FONT_SIZE,
        )

        if mouse_event.event_type == MouseEventType.MOUSE_DOWN:
            ev = MouseEvent(pos=pos)
            self.frame._callback_on_mouse_down(ev)
        elif mouse_event.event_type == MouseEventType.MOUSE_UP:
            ev = MouseEvent(pos=pos)
            self.frame._callback_on_mouse_up(ev)
        elif mouse_event.event_type == MouseEventType.SCROLL_UP:
            ev = WheelEvent(x_offset=0, y_offset=-FONT_SIZE, pos=pos)
            self.frame._callback_on_mouse_wheel(ev)
        elif mouse_event.event_type == MouseEventType.SCROLL_DOWN:
            ev = WheelEvent(x_offset=0, y_offset=FONT_SIZE, pos=pos)
            self.frame._callback_on_mouse_wheel(ev)
        elif mouse_event.event_type == MouseEventType.MOUSE_MOVE:
            ev = MouseEvent(pos=pos)
            self.frame._callback_on_cursor_pos(ev)
