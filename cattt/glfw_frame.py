import threading
from queue import SimpleQueue
from typing import Callable, cast

import glfw
import skia
from OpenGL import GL

from . import core
from . import skia_painter as painter


class Frame:
    def __init__(self, title: str = "cattt", width: float = 500, height: float = 500):
        if not glfw.init():
            raise RuntimeError("glfw.init() failed")

        glfw.window_hint(glfw.STENCIL_BITS, 8)
        glfw.window_hint(glfw.DOUBLEBUFFER, glfw.FALSE)
        window = glfw.create_window(width, height, title, None, None)

        if not window:
            glfw.terminate()
            raise RuntimeError("glfw.create_window() failed")

        glfw.make_context_current(window)
        self.window = window
        GL.glClear(GL.GL_COLOR_BUFFER_BIT)
        glfw.set_mouse_button_callback(window, self.mouse_button)
        glfw.set_cursor_pos_callback(window, self.cursor_pos)
        glfw.set_char_callback(window, self.input_char)
        glfw.set_key_callback(window, self.input_key)

        self._size = core.Size(width, height)
        self.context = skia.GrDirectContext.MakeGL()
        self._update_surface_and_painter()

        self._update_event_queue = SimpleQueue()

    def _update_surface_and_painter(self) -> None:
        (fb_width, fb_height) = glfw.get_framebuffer_size(self.window)
        backend_render_target = skia.GrBackendRenderTarget(
            fb_width,
            fb_height,
            0,  # sampleCnt
            0,  # stencilBits
            skia.GrGLFramebufferInfo(0, GL.GL_RGBA8),
        )

        surface = skia.Surface.MakeFromBackendRenderTarget(
            self.context,
            backend_render_target,
            skia.kBottomLeft_GrSurfaceOrigin,
            skia.kRGBA_8888_ColorType,
            skia.ColorSpace.MakeSRGB(),
        )
        self.surface = surface
        self.painter = painter.Painter(self, self.surface)

    def mouse_button(self, window, button, action, mods):
        if button != glfw.MOUSE_BUTTON_LEFT:
            return
        pos = glfw.get_cursor_pos(window)
        if action == glfw.PRESS:
            self._callback_on_mouse_down(core.MouseEvent(core.Point(*pos)))
        elif action == glfw.RELEASE:
            self._callback_on_mouse_up(core.MouseEvent(core.Point(*pos)))

    def on_mouse_down(self, handler: Callable[[core.MouseEvent], None]) -> None:
        self._callback_on_mouse_down = handler

    def on_mouse_up(self, handler: Callable[[core.MouseEvent], None]) -> None:
        self._callback_on_mouse_up = handler

    def cursor_pos(self, window, x: float, y: float) -> None:
        self._callback_on_cursor_pos(core.MouseEvent(core.Point(x, y)))

    def on_cursor_pos(self, handler: Callable[[core.MouseEvent], None]) -> None:
        self._callback_on_cursor_pos = handler

    def input_char(self, window, char: int) -> None:
        self._callback_on_input_char(core.InputCharEvent(chr(char)))

    def on_input_char(self, handler: Callable[[core.InputCharEvent], None]) -> None:
        self._callback_on_input_char = handler

    def input_key(self, window, key: int, scancode: int, action: int, mods: int) -> None:
        self._callback_on_input_key(core.InputKeyEvent(convert_to_key_code(key),
                                                      scancode,
                                                      convert_to_key_action(action),
                                                      mods))

    def on_input_key(self, handler: Callable[[core.InputKeyEvent], None]) -> None:
        self._callback_on_input_key = handler

    def on_redraw(self, handler: Callable[[core.Painter, bool], None]) -> None:
        glfw.set_window_size_callback(
            self.window, lambda window, w, h: self._on_redraw(window, w, h, handler)
        )

    def _on_redraw(self, window, w, h, handler: Callable[[core.Painter, bool], None]) -> None:
        self._size = core.Size(w, h)
        self._update_surface_and_painter()
        handler(self.painter, True)

    def get_painter(self) -> core.Painter:
        return self.painter

    def get_size(self) -> core.Size:
        return self._size

    def post_update(self, ev: core.UpdateEvent) -> None:
        if threading.current_thread() is not threading.main_thread():
            self._update_event_queue.put(ev)
            glfw.post_empty_event()
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

        self.painter.save()
        try:
            self.painter.translate(pos)
            if clippedRect is not None:
                self.painter.clip(clippedRect)
            ev.target.redraw(self.painter, ev.completely)
            self.painter.flush()
        finally:
            self.painter.restore()

    def flush(self) -> None:
        GL.glFlush()

    def clear(self) -> None:
        GL.glClear(GL.GL_COLOR_BUFFER_BIT)

    def run(self) -> None:
        if threading.current_thread() is not threading.main_thread():
            raise RuntimeError("run method must be called from main thread")

        try:
            while not glfw.window_should_close(self.window):
                glfw.wait_events()
                if not self._update_event_queue.empty():
                    self._post_update(self._update_event_queue.get_nowait())
        finally:
            glfw.terminate()
            self.context.abandonContext()


def convert_to_key_code(glfw_key_code: int) -> core.KeyCode:
    if glfw_key_code == glfw.KEY_BACKSPACE:
        return core.KeyCode.BACKSPACE
    elif glfw_key_code == glfw.KEY_LEFT:
        return core.KeyCode.LEFT
    elif glfw_key_code == glfw.KEY_RIGHT:
        return core.KeyCode.RIGHT
    elif glfw_key_code == glfw.KEY_UP:
        return core.KeyCode.UP
    elif glfw_key_code == glfw.KEY_DOWN:
        return core.KeyCode.DOWN
    elif glfw_key_code == glfw.KEY_PAGE_UP:
        return core.KeyCode.PAGE_UP
    elif glfw_key_code == glfw.KEY_PAGE_DOWN:
        return core.KeyCode.PAGE_DOWN
    else:
        return core.KeyCode.UNKNOWN


def convert_to_key_action(glfw_key_action: int) -> core.KeyAction:
    if glfw_key_action == glfw.PRESS:
        return core.KeyAction.PRESS
    elif glfw_key_action == glfw.RELEASE:
        return core.KeyAction.RELEASE
    elif glfw_key_action == glfw.REPEAT:
        return core.KeyAction.REPEAT
    else:
        return core.KeyAction.UNKNOWN
