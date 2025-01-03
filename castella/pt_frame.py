from asyncio import Future
from queue import Queue
from typing import Callable, cast

import pyperclip
from prompt_toolkit import Application
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.keys import Keys
from prompt_toolkit.layout import Layout as PTLayout
from prompt_toolkit.layout.containers import Window
from prompt_toolkit.layout.controls import UIContent, UIControl
from prompt_toolkit.mouse_events import MouseEvent as PTMouseEvent, MouseEventType

from castella.core import (
    Point,
    Size,
    Painter,
    MouseEvent,
    WheelEvent,
    InputCharEvent,
    InputKeyEvent,
    UpdateEvent,
    KeyAction,
    KeyCode,
    Widget,
    App,
    Rect,
)
from castella.pt_painter import PTPainter, Canvas, FONT_SIZE


class PTFrame:
    def __init__(self, title: str, width: float = 0, height: float = 0) -> None:
        self.title = title
        self.width = width
        self.height = height
        self._on_input_char = None
        self._on_input_key = None
        self._on_mouse_down = None
        self._on_mouse_up = None
        self._on_mouse_wheel = None
        self._on_cursor_pos = None
        self._on_redraw = None
        self._painter = PTPainter(Canvas(0, 0))
        self._running = True
        self.bindings = KeyBindings()
        self._register_keybindings()
        self.application = Application(
            full_screen=True,
            key_bindings=self.bindings,
            mouse_support=True,
            layout=PTLayout(Window(content=PTControl(self))),
            refresh_interval=0.1,
        )
        self._event_queue = Queue()

    def _register_keybindings(self):
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
            if self._on_input_key:
                ev = InputKeyEvent(
                    key=convert_to_key_code(event.key_sequence[0].key),
                    scancode=0,
                    action=KeyAction.PRESS,
                    mods=0,
                )
                self._on_input_key(ev)

        @self.bindings.add("<any>")
        def _(event):
            if self._on_input_char:
                ev = InputCharEvent(char=event.key_sequence[0].key)
                self._on_input_char(ev)

    def on_input_char(self, handler: Callable[[InputCharEvent], None]) -> None:
        self._on_input_char = handler

    def on_input_key(self, handler: Callable[[InputKeyEvent], None]) -> None:
        self._on_input_key = handler

    def on_mouse_down(self, handler: Callable[[MouseEvent], None]) -> None:
        self._on_mouse_down = handler

    def on_mouse_up(self, handler: Callable[[MouseEvent], None]) -> None:
        self._on_mouse_up = handler

    def on_mouse_wheel(self, handler: Callable[[WheelEvent], None]) -> None:
        self._on_mouse_wheel = handler

    def on_cursor_pos(self, handler: Callable[[MouseEvent], None]) -> None:
        self._on_cursor_pos = handler

    def on_redraw(self, handler: Callable[[Painter, bool], None]) -> None:
        self._on_redraw = handler

    def get_painter(self) -> Painter:
        return self._painter

    def get_size(self) -> Size:
        return Size(width=self.width, height=self.height)

    def post_update(self, ev: UpdateEvent) -> None:
        # self.application.invalidate()
        self._event_queue.put(ev)

    def flush(self) -> None:
        pass

    def clear(self) -> None:
        self._painter.clear_all()

    def run(self) -> None:
        try:
            self.application.run()
        except KeyboardInterrupt:
            pass

    def get_clipboard_text(self) -> str:
        return pyperclip.paste()

    def set_clipboard_text(self, text: str) -> None:
        pyperclip.copy(text)

    def async_get_clipboard_text(self, callback: Callable[[Future[str]], None]) -> None:
        raise NotImplementedError

    def async_set_clipboard_text(
        self, text: str, callback: Callable[[Future], None]
    ) -> None:
        raise NotImplementedError

    def redraw(self, width: int, height: int):
        self.width = width * FONT_SIZE
        self.height = height * FONT_SIZE
        self._painter.canvas = Canvas(width, height)
        self._painter.clear_all()
        if self._on_redraw is not None:
            self._on_redraw(self._painter, True)

    def init_canvas(self, width: int, height: int):
        self.width = width * FONT_SIZE
        self.height = height * FONT_SIZE
        self._painter.canvas = Canvas(width, height)
        self._painter.clear_all()

    def is_resized(self, width: int, height: int) -> bool:
        return self.width != width * FONT_SIZE or self.height != height * FONT_SIZE


def convert_to_key_code(code) -> KeyCode:
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
    def __init__(self, frame: PTFrame):
        self.frame = frame

    def _post_update(self, ev: UpdateEvent):
        if ev.target is None:
            return

        if isinstance(ev.target, App):
            pos = Point(0, 0)
            clippedRect = None
        else:
            w: Widget = cast(Widget, ev.target)
            pos = w.get_pos()
            clippedRect = Rect(Point(0, 0), w.get_size())

        painter = self.frame.get_painter()
        painter.save()
        try:
            painter.translate(pos)
            if clippedRect is not None:
                painter.clip(clippedRect)
            ev.target.redraw(painter, ev.completely)
            painter.flush()
        finally:
            painter.restore()

    def create_content(self, width: int, height: int):
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
            ev: UpdateEvent = self.frame._event_queue.get_nowait()
            self._post_update(ev)
        renderable = self.frame._painter._get_renderable()

        return UIContent(
            get_line=renderable.__getitem__,  # type: ignore
            line_count=len(renderable),
        )

    def mouse_handler(self, mouse_event: PTMouseEvent):
        pos = Point(
            mouse_event.position.x * FONT_SIZE, mouse_event.position.y * FONT_SIZE
        )

        if mouse_event.event_type == MouseEventType.MOUSE_DOWN:
            if self.frame._on_mouse_down:
                ev = MouseEvent(pos=pos)
                self.frame._on_mouse_down(ev)
        elif mouse_event.event_type == MouseEventType.MOUSE_UP:
            if self.frame._on_mouse_up:
                ev = MouseEvent(pos=pos)
                self.frame._on_mouse_up(ev)
        elif mouse_event.event_type == MouseEventType.SCROLL_UP:
            if self.frame._on_mouse_wheel:
                ev = WheelEvent(x_offset=0, y_offset=-FONT_SIZE, pos=pos)
                self.frame._on_mouse_wheel(ev)
        elif mouse_event.event_type == MouseEventType.SCROLL_DOWN:
            if self.frame._on_mouse_wheel:
                ev = WheelEvent(x_offset=0, y_offset=FONT_SIZE, pos=pos)
                self.frame._on_mouse_wheel(ev)
        elif mouse_event.event_type == MouseEventType.MOUSE_MOVE:
            if self.frame._on_cursor_pos:
                ev = MouseEvent(pos=pos)
                self.frame._on_cursor_pos(ev)
        return None
