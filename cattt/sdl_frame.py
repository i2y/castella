import platform
import threading
from ctypes import byref
from queue import SimpleQueue
from typing import Callable, Final, cast

import sdl2 as sdl
import skia
import zengl

from . import core
from . import skia_painter as painter

if platform.system() == "Windows":
    import ctypes
    user32 = ctypes.windll.user32
    user32.SetProcessDPIAware()


def rgba_masks():
    if platform.system() == "Windows":
        return (0, 0, 0, 0)

    if sdl.SDL_BYTEORDER == sdl.SDL_BIG_ENDIAN:
        return (0xff000000, 0x00ff0000, 0x0000ff00, 0x000000ff)
    else:
        return (0x000000ff, 0x0000ff00, 0x00ff0000, 0xff000000)


class Frame:
    UPDATE_EVENT_TYPE: Final = sdl.SDL_RegisterEvents(1)

    PIXEL_DEPTH = 32
    PIXEL_PITCH_FACTOR = 4

    def __init__(self, title: str = "cattt", width: float = 500, height: float = 500):
        sdl.SDL_Init(sdl.SDL_INIT_EVENTS)
        self._rgba_masks = rgba_masks()
        window = sdl.SDL_CreateWindow(
            bytes(title, "utf8"),
            sdl.SDL_WINDOWPOS_CENTERED, sdl.SDL_WINDOWPOS_CENTERED,
            width, height,
            sdl.SDL_WINDOW_SHOWN | sdl.SDL_WINDOW_RESIZABLE | sdl.SDL_WINDOW_ALLOW_HIGHDPI
        )

        self._window = window
        self._size = core.Size(width, height)
        self._update_surface_and_painter()
        self._update_event_queue = SimpleQueue()

    def _update_surface_and_painter(self) -> None:
        zengl.context(zengl.loader(headless=True))

        info = skia.ImageInfo.MakeN32Premul(self._size.width, self._size.height)
        surface = skia.Surface.MakeRenderTarget(skia.GrDirectContext.MakeGL(), skia.Budgeted.kNo, info)

        self._surface = surface
        self._painter = painter.Painter(self, self._surface)

    def on_mouse_down(self, handler: Callable[[core.MouseEvent], None]) -> None:
        self._callback_on_mouse_down = handler

    def on_mouse_up(self, handler: Callable[[core.MouseEvent], None]) -> None:
        self._callback_on_mouse_up = handler

    def on_cursor_pos(self, handler: Callable[[core.MouseEvent], None]) -> None:
        self._callback_on_cursor_pos = handler

    def on_input_char(self, handler: Callable[[core.InputCharEvent], None]) -> None:
        self._callback_on_input_char = handler

    def on_input_key(self, handler: Callable[[core.InputKeyEvent], None]) -> None:
        self._callback_on_input_key = handler

    def on_redraw(self, handler: Callable[[core.Painter, bool], None]) -> None:
        self._callback_on_redraw = handler

    def _on_redraw(self, w, h, handler: Callable[[core.Painter, bool], None]) -> None:
        self._size = core.Size(w, h)
        self._update_surface_and_painter()
        handler(self._painter, True)

    def get_painter(self) -> core.Painter:
        return self._painter

    def get_size(self) -> core.Size:
        return self._size

    def post_update(self, ev: core.UpdateEvent) -> None:
        if threading.current_thread() is not threading.main_thread():
            self._update_event_queue.put(ev)
            sdl_event = sdl.SDL_Event()
            sdl_event.type = Frame.UPDATE_EVENT_TYPE
            sdl.SDL_PushEvent(sdl_event)
        else:
            self._post_update(ev)

    def _post_update(self, ev: core.UpdateEvent) -> None:
        if ev.target is None:
            return

        if isinstance(ev.target, core.App):
            pos = core.Point(0, 0)
            clippedRect = None
        else:
            w: core.Widget = cast(core.Widget, ev.target)
            pos = w.get_pos()
            clippedRect = core.Rect(core.Point(0, 0), w.get_size())

        self._painter.save()
        try:
            self._painter.translate(pos)
            if clippedRect is not None:
                self._painter.clip(clippedRect)
            ev.target.redraw(self._painter, ev.completely)
            self._painter.flush()
        finally:
            self._painter.restore()

    def flush(self) -> None:
        skia_image = self._surface.makeImageSnapshot()
        skia_bytes = skia_image.tobytes()

        size = self._size
        width = size.width
        height = size.height
        sdl_surface = sdl.SDL_CreateRGBSurfaceFrom(
            skia_bytes, width, height, self.PIXEL_DEPTH, self.PIXEL_PITCH_FACTOR * width,
            *self._rgba_masks)

        rect = sdl.SDL_Rect(0, 0, width, height)
        window_surface = sdl.SDL_GetWindowSurface(self._window)
        sdl.SDL_BlitSurface(sdl_surface, rect, window_surface, rect)
        sdl.SDL_UpdateWindowSurface(self._window)

    def clear(self) -> None:
        self._surface.getCanvas().clear(0)

    def run(self) -> None:
        if threading.current_thread() is not threading.main_thread():
            raise RuntimeError("run method must be called from main thread")

        event = sdl.SDL_Event()
        while True:
            ok = sdl.SDL_WaitEvent(byref(event))
            if not ok:
                sdl.SDL_Quit()
                break

            match event.type:
                case sdl.SDL_QUIT:
                    sdl.SDL_Quit()
                    break
                case Frame.UPDATE_EVENT_TYPE:
                    if not self._update_event_queue.empty():
                        self._post_update(self._update_event_queue.get_nowait())
                case sdl.SDL_WINDOWEVENT:
                    if event.window.event == sdl.SDL_WINDOWEVENT_RESIZED:
                        width = event.window.data1
                        height = event.window.data2
                        self._on_redraw(width, height, self._callback_on_redraw)
                case sdl.SDL_MOUSEBUTTONDOWN:
                    self._callback_on_mouse_down(core.MouseEvent(core.Point(event.button.x, event.button.y)))
                case sdl.SDL_MOUSEBUTTONUP:
                    self._callback_on_mouse_up(core.MouseEvent(core.Point(event.button.x, event.button.y)))
                case sdl.SDL_MOUSEMOTION:
                    self._callback_on_cursor_pos(core.MouseEvent(core.Point(event.motion.x, event.motion.y)))
                case sdl.SDL_KEYDOWN:
                    self._callback_on_input_key(core.InputKeyEvent(convert_to_key_code(event.key.keysym.sym),
                                                                  0,
                                                                  core.KeyAction.PRESS,
                                                                  0))
                case sdl.SDL_TEXTINPUT:
                    self._callback_on_input_char(core.InputCharEvent(event.text.text.decode('utf-8')))


def convert_to_key_code(keysym: int) -> core.KeyCode:
    if keysym == sdl.SDLK_BACKSPACE:
        return core.KeyCode.BACKSPACE
    elif keysym == sdl.SDLK_LEFT:
        return core.KeyCode.LEFT
    elif keysym == sdl.SDLK_RIGHT:
        return core.KeyCode.RIGHT
    elif keysym == sdl.SDLK_UP:
        return core.KeyCode.UP
    elif keysym == sdl.SDLK_DOWN:
        return core.KeyCode.DOWN
    elif keysym == sdl.SDLK_PAGEUP:
        return core.KeyCode.PAGE_UP
    elif keysym == sdl.SDLK_PAGEDOWN:
        return core.KeyCode.PAGE_DOWN
    else:
        return core.KeyCode.UNKNOWN
