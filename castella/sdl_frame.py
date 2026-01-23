"""SDL2-based frame implementation."""

from __future__ import annotations

import platform
from ctypes import CFUNCTYPE, POINTER, byref, c_int, c_void_p
from typing import TYPE_CHECKING, Final

import sdl2 as sdl

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

if TYPE_CHECKING:
    from castella.protocols.painter import BasePainter

if platform.system() == "Windows":
    import ctypes

    user32 = ctypes.windll.user32
    user32.SetProcessDPIAware()

# SDL event filter callback type for handling resize during drag
SDL_EventFilter = CFUNCTYPE(c_int, c_void_p, POINTER(sdl.SDL_Event))


def _rgba_masks() -> tuple[int, int, int, int]:
    """Get RGBA masks based on platform byte order."""
    if platform.system() == "Windows":
        return (0, 0, 0, 0)

    if sdl.SDL_BYTEORDER == sdl.SDL_BIG_ENDIAN:
        return (0xFF000000, 0x00FF0000, 0x0000FF00, 0x000000FF)
    else:
        return (0x000000FF, 0x0000FF00, 0x00FF0000, 0xFF000000)


class Frame(BaseFrame):
    """SDL2 window frame with Skia rendering."""

    UPDATE_EVENT_TYPE: Final = sdl.SDL_RegisterEvents(1)

    PIXEL_DEPTH = 32
    PIXEL_PITCH_FACTOR = 4

    def __init__(
        self, title: str = "castella", width: float = 500, height: float = 500
    ):
        super().__init__(title, width, height)

        self._gl_context = None

        if sdl.SDL_Init(sdl.SDL_INIT_EVENTS | sdl.SDL_INIT_VIDEO) != 0:
            raise RuntimeError(f"SDL_Init failed: {sdl.SDL_GetError().decode()}")

        # Load OpenGL library (required on Linux before creating GL context)
        if sdl.SDL_GL_LoadLibrary(None) != 0:
            raise RuntimeError(
                f"SDL_GL_LoadLibrary failed: {sdl.SDL_GetError().decode()}"
            )

        self._rgba_masks = _rgba_masks()

        # Set up OpenGL attributes for GPU mode
        # Request OpenGL 3.2 Core Profile (required for Skia on macOS)
        sdl.SDL_GL_SetAttribute(sdl.SDL_GL_CONTEXT_MAJOR_VERSION, 3)
        sdl.SDL_GL_SetAttribute(sdl.SDL_GL_CONTEXT_MINOR_VERSION, 2)
        sdl.SDL_GL_SetAttribute(
            sdl.SDL_GL_CONTEXT_PROFILE_MASK, sdl.SDL_GL_CONTEXT_PROFILE_CORE
        )
        sdl.SDL_GL_SetAttribute(sdl.SDL_GL_STENCIL_SIZE, 8)
        # Use single buffer mode like GLFW (DOUBLEBUFFER = 0)
        sdl.SDL_GL_SetAttribute(sdl.SDL_GL_DOUBLEBUFFER, 0)

        window_flags = (
            sdl.SDL_WINDOW_SHOWN
            | sdl.SDL_WINDOW_RESIZABLE
            | sdl.SDL_WINDOW_ALLOW_HIGHDPI
            | sdl.SDL_WINDOW_OPENGL
        )

        window = sdl.SDL_CreateWindow(
            bytes(title, "utf8"),
            sdl.SDL_WINDOWPOS_CENTERED,
            sdl.SDL_WINDOWPOS_CENTERED,
            int(width),
            int(height),
            window_flags,
        )
        if not window:
            raise RuntimeError(
                f"SDL_CreateWindow failed: {sdl.SDL_GetError().decode()}"
            )

        self._window = window

        # Create OpenGL context
        self._gl_context = sdl.SDL_GL_CreateContext(window)
        if not self._gl_context:
            raise RuntimeError(
                f"SDL_GL_CreateContext failed: {sdl.SDL_GetError().decode()}"
            )

        if sdl.SDL_GL_MakeCurrent(window, self._gl_context) != 0:
            raise RuntimeError(
                f"SDL_GL_MakeCurrent failed: {sdl.SDL_GetError().decode()}"
            )

        # Load libGL with RTLD_GLOBAL on Linux so Skia can find GL functions via dlsym.
        # This is required because SDL_GL_LoadLibrary doesn't expose symbols globally,
        # unlike PyOpenGL which GLFW uses. Fixes "Failed to create OpenGL interface"
        # error on WSL2 and other Linux environments.
        if platform.system() == "Linux":
            import ctypes
            from ctypes.util import find_library

            libgl_name = find_library("GL")
            if libgl_name:
                ctypes.CDLL(libgl_name, mode=ctypes.RTLD_GLOBAL)

        # Enable IME text input
        sdl.SDL_StartTextInput()

        # IME cursor rect for candidate window positioning
        self._ime_rect = sdl.SDL_Rect(0, 0, 1, 20)

        # HiDPI scale factor (updated in _update_surface_and_painter)
        self._hidpi_scale = 1.0

        self._update_surface_and_painter()

        # Register event filter for real-time resize updates during drag
        self._event_filter = self._create_event_filter()
        sdl.SDL_SetEventFilter(self._event_filter, None)

        # Cursor cache to avoid recreating cursors on every set_cursor call
        self._cursor_cache: dict[CursorType, c_void_p] = {}
        self._current_cursor_type: CursorType = CursorType.ARROW

    def _create_event_filter(self):
        """Create event filter callback for handling resize during drag."""

        @SDL_EventFilter
        def event_filter(userdata, event_ptr):
            event = event_ptr.contents
            if event.type == sdl.SDL_WINDOWEVENT:
                if event.window.event in (
                    sdl.SDL_WINDOWEVENT_RESIZED,
                    sdl.SDL_WINDOWEVENT_SIZE_CHANGED,
                ):
                    self._on_resize(event.window.data1, event.window.data2)
            return 1  # Keep event in queue

        return event_filter

    def _update_surface_and_painter(self) -> None:
        """Create/recreate the Skia surface for the current size."""
        from castella import rust_skia_painter as painter

        # Get actual framebuffer size in pixels (HiDPI aware)
        fb_width = c_int()
        fb_height = c_int()
        sdl.SDL_GL_GetDrawableSize(self._window, byref(fb_width), byref(fb_height))

        width = fb_width.value
        height = fb_height.value

        # Calculate HiDPI scale factor
        logical_width = self._size.width if self._size.width > 0 else width
        self._hidpi_scale = width / logical_width if logical_width > 0 else 1.0

        if hasattr(self, "_surface") and self._surface is not None:
            # Resize existing surface (faster, avoids recreating context)
            self._surface.resize(
                width, height, sample_count=0, stencil_bits=8, framebuffer_id=0
            )
            self._painter = painter.Painter(self, self._surface)
        else:
            # Create new GPU surface
            self._surface = castella_skia.Surface.from_gl_context(
                width,
                height,
                sample_count=0,
                stencil_bits=8,
                framebuffer_id=0,
            )
            self._painter = painter.Painter(self, self._surface)

    def _signal_main_thread(self) -> None:
        """Signal main thread via SDL custom event."""
        sdl_event = sdl.SDL_Event()
        sdl_event.type = Frame.UPDATE_EVENT_TYPE
        sdl.SDL_PushEvent(sdl_event)

    # ========== Abstract Method Implementations ==========

    def get_painter(self) -> "BasePainter":
        return self._painter

    def get_size(self) -> Size:
        return self._size

    def flush(self) -> None:
        # GPU mode: flush Skia and OpenGL (single buffer, like GLFW)
        self._surface.flush_and_submit()
        from OpenGL import GL

        GL.glFlush()

    def clear(self) -> None:
        # Clear with OpenGL for GPU mode (same as GLFW)
        from OpenGL import GL

        GL.glClear(GL.GL_COLOR_BUFFER_BIT)

    def run(self) -> None:
        self._ensure_main_thread()

        # Trigger initial redraw (like GLFW's on_load)
        on_load = True

        event = sdl.SDL_Event()
        while True:
            ok = sdl.SDL_WaitEvent(byref(event))
            if not ok:
                sdl.SDL_Quit()
                break

            if on_load:
                # Initial redraw on first event
                self._on_resize(int(self._size.width), int(self._size.height))
                on_load = False

            match event.type:
                case sdl.SDL_QUIT:
                    sdl.SDL_Quit()
                    break
                case Frame.UPDATE_EVENT_TYPE:
                    self._process_pending_updates()
                case sdl.SDL_WINDOWEVENT:
                    if event.window.event == sdl.SDL_WINDOWEVENT_RESIZED:
                        width = event.window.data1
                        height = event.window.data2
                        self._on_resize(width, height)
                case sdl.SDL_MOUSEBUTTONDOWN:
                    self._callback_on_mouse_down(
                        MouseEvent(pos=Point(x=event.button.x, y=event.button.y))
                    )
                case sdl.SDL_MOUSEBUTTONUP:
                    self._callback_on_mouse_up(
                        MouseEvent(pos=Point(x=event.button.x, y=event.button.y))
                    )
                case sdl.SDL_MOUSEWHEEL:
                    x, y = c_int(0), c_int(0)
                    sdl.SDL_GetMouseState(byref(x), byref(y))
                    self._callback_on_mouse_wheel(
                        WheelEvent(
                            pos=Point(x=x.value, y=y.value),
                            x_offset=+event.wheel.x * 20,
                            y_offset=-event.wheel.y * 20,
                        )
                    )
                case sdl.SDL_MOUSEMOTION:
                    self._callback_on_cursor_pos(
                        MouseEvent(pos=Point(x=event.motion.x, y=event.motion.y))
                    )
                case sdl.SDL_KEYDOWN:
                    self._callback_on_input_key(
                        InputKeyEvent(
                            key=_convert_to_key_code(event.key.keysym.sym),
                            scancode=0,
                            action=KeyAction.PRESS,
                            mods=_get_key_mods(),
                        )
                    )
                case sdl.SDL_TEXTEDITING:
                    # IME preedit (composition) text
                    preedit_text = event.edit.text.decode("utf-8")
                    cursor_pos = event.edit.start + event.edit.length
                    self._callback_on_ime_preedit(
                        IMEPreeditEvent(text=preedit_text, cursor_pos=cursor_pos)
                    )
                case sdl.SDL_TEXTINPUT:
                    # Clear preedit when text is committed
                    self._callback_on_ime_preedit(
                        IMEPreeditEvent(text="", cursor_pos=0)
                    )
                    self._callback_on_input_char(
                        InputCharEvent(char=event.text.text.decode("utf-8"))
                    )

    def _on_resize(self, w: int, h: int) -> None:
        """Handle window resize."""
        self._size = Size(width=w, height=h)
        self._update_surface_and_painter()
        # Apply HiDPI scale before redraw
        self._painter.save()
        self._painter.scale(self._hidpi_scale, self._hidpi_scale)
        self._callback_on_redraw(self._painter, True)
        self._painter.restore()

    def _post_update(self, ev) -> None:
        """Override to apply HiDPI scale before drawing."""
        self._painter.save()
        self._painter.scale(self._hidpi_scale, self._hidpi_scale)
        super()._post_update(ev)
        self._painter.restore()

    # ========== IME Support ==========

    def set_ime_cursor_rect(self, x: int, y: int, w: int, h: int) -> None:
        """Set the IME cursor rectangle for candidate window positioning."""
        self._ime_rect.x = x
        self._ime_rect.y = y
        self._ime_rect.w = w
        self._ime_rect.h = h
        sdl.SDL_SetTextInputRect(byref(self._ime_rect))

    def set_cursor(self, cursor_type: CursorType) -> None:
        """Set the mouse cursor shape."""
        if cursor_type == self._current_cursor_type:
            return

        # Get or create the cursor
        if cursor_type not in self._cursor_cache:
            sdl_cursor_type = _cursor_type_to_sdl(cursor_type)
            cursor = sdl.SDL_CreateSystemCursor(sdl_cursor_type)
            self._cursor_cache[cursor_type] = cursor
        else:
            cursor = self._cursor_cache[cursor_type]

        sdl.SDL_SetCursor(cursor)
        self._current_cursor_type = cursor_type

    # ========== Clipboard ==========

    def get_clipboard_text(self) -> str:
        return sdl.SDL_GetClipboardText().decode("utf-8")

    def set_clipboard_text(self, text: str) -> None:
        sdl.SDL_SetClipboardText(text.encode("utf-8"))


# ========== Key Code Converter ==========


def _convert_to_key_code(keysym: int) -> KeyCode:
    match keysym:
        case sdl.SDLK_BACKSPACE:
            return KeyCode.BACKSPACE
        case sdl.SDLK_LEFT:
            return KeyCode.LEFT
        case sdl.SDLK_RIGHT:
            return KeyCode.RIGHT
        case sdl.SDLK_UP:
            return KeyCode.UP
        case sdl.SDLK_DOWN:
            return KeyCode.DOWN
        case sdl.SDLK_PAGEUP:
            return KeyCode.PAGE_UP
        case sdl.SDLK_PAGEDOWN:
            return KeyCode.PAGE_DOWN
        case sdl.SDLK_DELETE:
            return KeyCode.DELETE
        case sdl.SDLK_a:
            return KeyCode.A
        case sdl.SDLK_c:
            return KeyCode.C
        case sdl.SDLK_v:
            return KeyCode.V
        case sdl.SDLK_x:
            return KeyCode.X
        case _:
            return KeyCode.UNKNOWN


def _get_key_mods() -> int:
    """Get current keyboard modifier state in GLFW-compatible format."""
    key_mods = sdl.SDL_GetModState()
    mods = 0
    if key_mods & (sdl.KMOD_LSHIFT | sdl.KMOD_RSHIFT):
        mods |= 0x0001  # SHIFT
    if key_mods & (sdl.KMOD_LCTRL | sdl.KMOD_RCTRL):
        mods |= 0x0002  # CTRL
    if key_mods & (sdl.KMOD_LALT | sdl.KMOD_RALT):
        mods |= 0x0004  # ALT
    if key_mods & (sdl.KMOD_LGUI | sdl.KMOD_RGUI):
        mods |= 0x0008  # SUPER/CMD
    return mods


def _cursor_type_to_sdl(cursor_type: CursorType) -> int:
    """Convert CursorType to SDL2 system cursor constant."""
    match cursor_type:
        case CursorType.ARROW:
            return sdl.SDL_SYSTEM_CURSOR_ARROW
        case CursorType.TEXT:
            return sdl.SDL_SYSTEM_CURSOR_IBEAM
        case CursorType.POINTER:
            return sdl.SDL_SYSTEM_CURSOR_HAND
        case CursorType.RESIZE_H:
            return sdl.SDL_SYSTEM_CURSOR_SIZEWE
        case CursorType.RESIZE_V:
            return sdl.SDL_SYSTEM_CURSOR_SIZENS
        case CursorType.CROSSHAIR:
            return sdl.SDL_SYSTEM_CURSOR_CROSSHAIR
        case CursorType.WAIT:
            return sdl.SDL_SYSTEM_CURSOR_WAIT
        case CursorType.NOT_ALLOWED:
            return sdl.SDL_SYSTEM_CURSOR_NO
        case _:
            return sdl.SDL_SYSTEM_CURSOR_ARROW
