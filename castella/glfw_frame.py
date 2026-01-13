"""GLFW-based frame implementation."""

from __future__ import annotations

import platform
from typing import TYPE_CHECKING, Callable, Optional

import glfw
from OpenGL import GL

import castella_skia

from castella.frame.base import BaseFrame
from castella.models.geometry import Point, Size
from castella.models.events import (
    CursorType,
    IMEPreeditEvent,
    InputCharEvent,
    InputKeyEvent,
    KeyAction,
    KeyCode,
    MouseEvent,
    WheelEvent,
)

# macOS IME support
if platform.system() == "Darwin":
    try:
        from castella.frame.macos_ime import (
            MacOSIMEManager,
            is_available as is_ime_available,
        )
    except ImportError:

        def is_ime_available() -> bool:
            return False

        MacOSIMEManager = None
else:

    def is_ime_available() -> bool:
        return False

    MacOSIMEManager = None

if TYPE_CHECKING:
    from castella.protocols.painter import BasePainter


class Frame(BaseFrame):
    """GLFW window frame with OpenGL/Skia rendering."""

    def __init__(
        self, title: str = "castella", width: float = 500, height: float = 500
    ):
        super().__init__(title, width, height)

        if not glfw.init():
            raise RuntimeError("glfw.init() failed")

        glfw.window_hint(glfw.STENCIL_BITS, 8)
        glfw.window_hint(glfw.DOUBLEBUFFER, glfw.FALSE)
        if platform.system() == "Darwin":
            glfw.window_hint(glfw.COCOA_RETINA_FRAMEBUFFER, glfw.FALSE)
            # Request OpenGL 3.2 Core Profile for macOS (required for GLSL 1.50+)
            glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
            glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 2)
            glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, glfw.TRUE)
            glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
        window = glfw.create_window(int(width), int(height), title, None, None)

        if not window:
            glfw.terminate()
            raise RuntimeError("glfw.create_window() failed")

        glfw.make_context_current(window)
        self.window = window
        GL.glClear(GL.GL_COLOR_BUFFER_BIT)

        # Set up callbacks
        glfw.set_mouse_button_callback(window, self._mouse_button)
        glfw.set_scroll_callback(window, self._mouse_wheel)
        glfw.set_cursor_pos_callback(window, self._cursor_pos)
        glfw.set_char_callback(window, self._input_char)
        glfw.set_key_callback(window, self._input_key)

        self._update_surface_and_painter()

        # Initialize macOS IME support
        self._ime_manager: Optional[MacOSIMEManager] = None
        if platform.system() == "Darwin" and is_ime_available() and MacOSIMEManager:
            self._ime_manager = MacOSIMEManager(window)
            self._ime_manager.set_preedit_handler(self._on_ime_preedit)

        # Cursor cache to avoid recreating cursors on every set_cursor call
        self._cursor_cache: dict[CursorType, int] = {}
        self._current_cursor_type: CursorType = CursorType.ARROW

    def _update_surface_and_painter(self) -> None:
        """Create/recreate the Skia surface for the current window size."""
        from castella import rust_skia_painter as painter

        (fb_width, fb_height) = glfw.get_framebuffer_size(self.window)

        if hasattr(self, "surface") and self.surface is not None:
            # Resize existing surface (faster, no flicker)
            self.surface.resize(
                fb_width,
                fb_height,
                sample_count=0,
                stencil_bits=8,
                framebuffer_id=0,
            )
            # Update painter with resized surface
            self.painter = painter.Painter(self, self.surface)
        else:
            # Create new surface
            self.surface = castella_skia.Surface.from_gl_context(
                fb_width,
                fb_height,
                sample_count=0,
                stencil_bits=8,
                framebuffer_id=0,
            )
            self.painter = painter.Painter(self, self.surface)

    def _signal_main_thread(self) -> None:
        """Signal main thread via GLFW empty event."""
        glfw.post_empty_event()

    # ========== GLFW Callbacks ==========

    def _mouse_button(self, window, button, action, mods):
        if button != glfw.MOUSE_BUTTON_LEFT:
            return
        pos = glfw.get_cursor_pos(window)
        if action == glfw.PRESS:
            self._callback_on_mouse_down(MouseEvent(pos=Point(x=pos[0], y=pos[1])))
        elif action == glfw.RELEASE:
            self._callback_on_mouse_up(MouseEvent(pos=Point(x=pos[0], y=pos[1])))

    def _mouse_wheel(self, window, x_offset: float, y_offset: float):
        pos = glfw.get_cursor_pos(self.window)
        self._callback_on_mouse_wheel(
            WheelEvent(
                pos=Point(x=pos[0], y=pos[1]),
                x_offset=-x_offset * 20,
                y_offset=-y_offset * 20,
            )
        )

    def _cursor_pos(self, window, x: float, y: float) -> None:
        self._callback_on_cursor_pos(MouseEvent(pos=Point(x=x, y=y)))

    def _input_char(self, window, char: int) -> None:
        # Clear any preedit text when a character is committed
        if self._ime_manager:
            self._callback_on_ime_preedit(IMEPreeditEvent(text="", cursor_pos=0))
        self._callback_on_input_char(InputCharEvent(char=chr(char)))

    def _on_ime_preedit(self, text: str, cursor_pos: int) -> None:
        """Handle IME preedit text from macOS."""
        self._callback_on_ime_preedit(IMEPreeditEvent(text=text, cursor_pos=cursor_pos))

    def set_ime_cursor_rect(self, x: int, y: int, w: int, h: int) -> None:
        """Set IME cursor rectangle for candidate window positioning."""
        if self._ime_manager:
            self._ime_manager.set_cursor_rect(x, y, w, h)

    def set_cursor(self, cursor_type: CursorType) -> None:
        """Set the mouse cursor shape."""
        if cursor_type == self._current_cursor_type:
            return

        # Get or create the cursor
        if cursor_type not in self._cursor_cache:
            glfw_cursor_type = _cursor_type_to_glfw(cursor_type)
            cursor = glfw.create_standard_cursor(glfw_cursor_type)
            self._cursor_cache[cursor_type] = cursor
        else:
            cursor = self._cursor_cache[cursor_type]

        glfw.set_cursor(self.window, cursor)
        self._current_cursor_type = cursor_type

    def _input_key(
        self, window, key: int, scancode: int, action: int, mods: int
    ) -> None:
        self._callback_on_input_key(
            InputKeyEvent(
                key=_convert_to_key_code(key),
                scancode=scancode,
                action=_convert_to_key_action(action),
                mods=mods,
            )
        )

    # ========== Redraw Handler Override ==========

    def on_redraw(self, handler: Callable[["BasePainter", bool], None]) -> None:
        """Register redraw handler and set up window resize callback."""
        self._callback_on_redraw = handler
        self._on_load = self._on_resize
        glfw.set_window_size_callback(self.window, self._on_resize)

    def _on_resize(self, window, w: int, h: int) -> None:
        """Handle window resize."""
        self._size = Size(width=w, height=h)
        self._update_surface_and_painter()
        self._callback_on_redraw(self.painter, True)

    # ========== Abstract Method Implementations ==========

    def get_painter(self) -> "BasePainter":
        return self.painter

    def get_size(self) -> Size:
        return self._size

    def flush(self) -> None:
        GL.glFlush()

    def clear(self) -> None:
        GL.glClear(GL.GL_COLOR_BUFFER_BIT)

    def run(self) -> None:
        self._ensure_main_thread()

        try:
            on_load = True
            while not glfw.window_should_close(self.window):
                glfw.wait_events()
                if on_load:
                    size = self._size
                    self._on_load(self.window, int(size.width), int(size.height))
                    on_load = False
                # Process any pending updates from background threads
                self._process_pending_updates()
        finally:
            glfw.terminate()

    # ========== Clipboard ==========

    def get_clipboard_text(self) -> str:
        return glfw.get_clipboard_string(self.window).decode("utf-8")

    def set_clipboard_text(self, text: str) -> None:
        glfw.set_clipboard_string(self.window, text)


# ========== Key Code Converters ==========


def _convert_to_key_code(glfw_key_code: int) -> KeyCode:
    match glfw_key_code:
        case glfw.KEY_BACKSPACE:
            return KeyCode.BACKSPACE
        case glfw.KEY_LEFT:
            return KeyCode.LEFT
        case glfw.KEY_RIGHT:
            return KeyCode.RIGHT
        case glfw.KEY_UP:
            return KeyCode.UP
        case glfw.KEY_DOWN:
            return KeyCode.DOWN
        case glfw.KEY_PAGE_UP:
            return KeyCode.PAGE_UP
        case glfw.KEY_PAGE_DOWN:
            return KeyCode.PAGE_DOWN
        case glfw.KEY_DELETE:
            return KeyCode.DELETE
        case glfw.KEY_ENTER:
            return KeyCode.ENTER
        case glfw.KEY_TAB:
            return KeyCode.TAB
        case glfw.KEY_ESCAPE:
            return KeyCode.ESCAPE
        case glfw.KEY_HOME:
            return KeyCode.HOME
        case glfw.KEY_END:
            return KeyCode.END
        case glfw.KEY_SPACE:
            return KeyCode.SPACE
        case glfw.KEY_A:
            return KeyCode.A
        case glfw.KEY_C:
            return KeyCode.C
        case glfw.KEY_V:
            return KeyCode.V
        case glfw.KEY_X:
            return KeyCode.X
        case _:
            return KeyCode.UNKNOWN


def _convert_to_key_action(glfw_key_action: int) -> KeyAction:
    match glfw_key_action:
        case glfw.PRESS:
            return KeyAction.PRESS
        case glfw.RELEASE:
            return KeyAction.RELEASE
        case glfw.REPEAT:
            return KeyAction.REPEAT
        case _:
            return KeyAction.UNKNOWN


def _cursor_type_to_glfw(cursor_type: CursorType) -> int:
    """Convert CursorType to GLFW cursor constant."""
    match cursor_type:
        case CursorType.ARROW:
            return glfw.ARROW_CURSOR
        case CursorType.TEXT:
            return glfw.IBEAM_CURSOR
        case CursorType.POINTER:
            return glfw.HAND_CURSOR
        case CursorType.RESIZE_H:
            return glfw.HRESIZE_CURSOR
        case CursorType.RESIZE_V:
            return glfw.VRESIZE_CURSOR
        case CursorType.CROSSHAIR:
            return glfw.CROSSHAIR_CURSOR
        case _:
            return glfw.ARROW_CURSOR
