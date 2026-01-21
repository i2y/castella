"""SDL3-based frame implementation."""

from __future__ import annotations

import platform
from ctypes import byref, c_int
from typing import TYPE_CHECKING, Final

import sdl3

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


class Frame(BaseFrame):
    """SDL3 window frame with Skia rendering."""

    UPDATE_EVENT_TYPE: Final = sdl3.SDL_RegisterEvents(1)

    def __init__(
        self, title: str = "castella", width: float = 500, height: float = 500
    ):
        super().__init__(title, width, height)

        self._gl_context = None

        if not sdl3.SDL_Init(sdl3.SDL_INIT_EVENTS | sdl3.SDL_INIT_VIDEO):
            raise RuntimeError(f"SDL_Init failed: {sdl3.SDL_GetError().decode()}")

        # Load OpenGL library (required on Linux before creating GL context)
        if not sdl3.SDL_GL_LoadLibrary(None):
            raise RuntimeError(
                f"SDL_GL_LoadLibrary failed: {sdl3.SDL_GetError().decode()}"
            )

        # Set up OpenGL attributes for GPU mode
        # Request OpenGL 3.2 Core Profile (required for Skia on macOS)
        sdl3.SDL_GL_SetAttribute(sdl3.SDL_GL_CONTEXT_MAJOR_VERSION, 3)
        sdl3.SDL_GL_SetAttribute(sdl3.SDL_GL_CONTEXT_MINOR_VERSION, 2)
        sdl3.SDL_GL_SetAttribute(
            sdl3.SDL_GL_CONTEXT_PROFILE_MASK, sdl3.SDL_GL_CONTEXT_PROFILE_CORE
        )
        sdl3.SDL_GL_SetAttribute(sdl3.SDL_GL_STENCIL_SIZE, 8)
        # Use single buffer mode like GLFW (DOUBLEBUFFER = 0)
        sdl3.SDL_GL_SetAttribute(sdl3.SDL_GL_DOUBLEBUFFER, 0)

        # SDL3: Window flags changed - SDL_WINDOW_SHOWN is no longer needed
        # SDL_WINDOW_ALLOW_HIGHDPI renamed to SDL_WINDOW_HIGH_PIXEL_DENSITY
        window_flags = (
            sdl3.SDL_WINDOW_RESIZABLE
            | sdl3.SDL_WINDOW_HIGH_PIXEL_DENSITY
            | sdl3.SDL_WINDOW_OPENGL
        )

        # SDL3: SDL_CreateWindow signature changed (no position parameters)
        window = sdl3.SDL_CreateWindow(
            bytes(title, "utf8"),
            int(width),
            int(height),
            window_flags,
        )
        if not window:
            raise RuntimeError(
                f"SDL_CreateWindow failed: {sdl3.SDL_GetError().decode()}"
            )

        self._window = window

        # Create OpenGL context
        self._gl_context = sdl3.SDL_GL_CreateContext(window)
        if not self._gl_context:
            raise RuntimeError(
                f"SDL_GL_CreateContext failed: {sdl3.SDL_GetError().decode()}"
            )

        if not sdl3.SDL_GL_MakeCurrent(window, self._gl_context):
            raise RuntimeError(
                f"SDL_GL_MakeCurrent failed: {sdl3.SDL_GetError().decode()}"
            )

        # Enable IME text input
        sdl3.SDL_StartTextInput(window)

        # IME cursor rect for candidate window positioning
        self._ime_rect = sdl3.SDL_Rect(0, 0, 1, 20)

        # HiDPI scale factor (updated in _update_surface_and_painter)
        self._hidpi_scale = 1.0

        self._update_surface_and_painter()

        # Register event filter for real-time resize updates during drag
        self._event_filter = self._create_event_filter()
        sdl3.SDL_SetEventFilter(self._event_filter, None)

        # Cursor cache to avoid recreating cursors on every set_cursor call
        self._cursor_cache: dict[CursorType, object] = {}
        self._current_cursor_type: CursorType = CursorType.ARROW

    def _create_event_filter(self):
        """Create event filter callback for handling resize during drag."""

        @sdl3.SDL_EventFilter
        def event_filter(userdata, event_ptr):
            event = event_ptr.contents
            # SDL3: Use SDL_EVENT_WINDOW_RESIZED instead of SDL_WINDOWEVENT subtype
            if event.type == sdl3.SDL_EVENT_WINDOW_RESIZED:
                self._on_resize(event.window.data1, event.window.data2)
            return True  # SDL3 uses bool (True = keep event in queue)

        return event_filter

    def _update_surface_and_painter(self) -> None:
        """Create/recreate the Skia surface for the current size."""
        from castella import rust_skia_painter as painter

        # Get actual framebuffer size in pixels (HiDPI aware)
        fb_width = c_int()
        fb_height = c_int()
        sdl3.SDL_GetWindowSizeInPixels(self._window, byref(fb_width), byref(fb_height))

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
        sdl_event = sdl3.SDL_Event()
        sdl_event.type = Frame.UPDATE_EVENT_TYPE
        sdl3.SDL_PushEvent(sdl_event)

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

        # Trigger initial redraw
        on_load = True

        event = sdl3.SDL_Event()
        while True:
            ok = sdl3.SDL_WaitEvent(byref(event))
            if not ok:
                sdl3.SDL_Quit()
                break

            if on_load:
                # Initial redraw on first event
                self._on_resize(int(self._size.width), int(self._size.height))
                on_load = False

            # SDL3: Event types are now individual constants (SDL_EVENT_*)
            match event.type:
                case sdl3.SDL_EVENT_QUIT:
                    sdl3.SDL_Quit()
                    break
                case Frame.UPDATE_EVENT_TYPE:
                    self._process_pending_updates()
                case sdl3.SDL_EVENT_WINDOW_RESIZED:
                    # SDL3: Window events are now individual event types
                    width = event.window.data1
                    height = event.window.data2
                    self._on_resize(width, height)
                case sdl3.SDL_EVENT_MOUSE_BUTTON_DOWN:
                    # SDL3: Mouse coordinates are now floats
                    self._callback_on_mouse_down(
                        MouseEvent(
                            pos=Point(x=int(event.button.x), y=int(event.button.y))
                        )
                    )
                case sdl3.SDL_EVENT_MOUSE_BUTTON_UP:
                    self._callback_on_mouse_up(
                        MouseEvent(
                            pos=Point(x=int(event.button.x), y=int(event.button.y))
                        )
                    )
                case sdl3.SDL_EVENT_MOUSE_WHEEL:
                    # SDL3: Wheel values are floats, mouse_x/mouse_y available
                    self._callback_on_mouse_wheel(
                        WheelEvent(
                            pos=Point(
                                x=int(event.wheel.mouse_x), y=int(event.wheel.mouse_y)
                            ),
                            x_offset=int(event.wheel.x * 20),
                            y_offset=int(-event.wheel.y * 20),
                        )
                    )
                case sdl3.SDL_EVENT_MOUSE_MOTION:
                    self._callback_on_cursor_pos(
                        MouseEvent(
                            pos=Point(x=int(event.motion.x), y=int(event.motion.y))
                        )
                    )
                case sdl3.SDL_EVENT_KEY_DOWN:
                    # SDL3: event.key.key instead of event.key.keysym.sym
                    self._callback_on_input_key(
                        InputKeyEvent(
                            key=_convert_to_key_code(event.key.key),
                            scancode=event.key.scancode,
                            action=KeyAction.PRESS,
                            mods=_convert_sdl_mods_to_glfw(event.key.mod),
                        )
                    )
                case sdl3.SDL_EVENT_TEXT_EDITING:
                    # IME preedit (composition) text
                    preedit_text = event.edit.text.decode("utf-8")
                    cursor_pos = event.edit.start + event.edit.length
                    self._callback_on_ime_preedit(
                        IMEPreeditEvent(text=preedit_text, cursor_pos=cursor_pos)
                    )
                case sdl3.SDL_EVENT_TEXT_INPUT:
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
        sdl3.SDL_SetTextInputArea(self._window, byref(self._ime_rect), 0)

    def set_cursor(self, cursor_type: CursorType) -> None:
        """Set the mouse cursor shape."""
        if cursor_type == self._current_cursor_type:
            return

        # Get or create the cursor
        if cursor_type not in self._cursor_cache:
            sdl_cursor_type = _cursor_type_to_sdl3(cursor_type)
            cursor = sdl3.SDL_CreateSystemCursor(sdl_cursor_type)
            self._cursor_cache[cursor_type] = cursor
        else:
            cursor = self._cursor_cache[cursor_type]

        sdl3.SDL_SetCursor(cursor)
        self._current_cursor_type = cursor_type

    # ========== Clipboard ==========

    def get_clipboard_text(self) -> str:
        text = sdl3.SDL_GetClipboardText()
        if text:
            # SDL3 Python bindings return bytes, no need to call SDL_free
            # (Python manages the memory automatically)
            return text.decode("utf-8")
        return ""

    def set_clipboard_text(self, text: str) -> None:
        sdl3.SDL_SetClipboardText(text.encode("utf-8"))


# ========== Key Code Converter ==========


def _convert_to_key_code(key: int) -> KeyCode:
    """Convert SDL3 key code to Castella KeyCode.

    SDL3: Uses event.key.key directly (not event.key.keysym.sym)
    Key constants (SDLK_*) remain the same as SDL2.
    """
    match key:
        case sdl3.SDLK_BACKSPACE:
            return KeyCode.BACKSPACE
        case sdl3.SDLK_LEFT:
            return KeyCode.LEFT
        case sdl3.SDLK_RIGHT:
            return KeyCode.RIGHT
        case sdl3.SDLK_UP:
            return KeyCode.UP
        case sdl3.SDLK_DOWN:
            return KeyCode.DOWN
        case sdl3.SDLK_PAGEUP:
            return KeyCode.PAGE_UP
        case sdl3.SDLK_PAGEDOWN:
            return KeyCode.PAGE_DOWN
        case sdl3.SDLK_DELETE:
            return KeyCode.DELETE
        case sdl3.SDLK_A:
            return KeyCode.A
        case sdl3.SDLK_C:
            return KeyCode.C
        case sdl3.SDLK_V:
            return KeyCode.V
        case sdl3.SDLK_X:
            return KeyCode.X
        case _:
            return KeyCode.UNKNOWN


def _get_key_mods() -> int:
    """Get current keyboard modifier state in GLFW-compatible format."""
    key_mods = sdl3.SDL_GetModState()
    mods = 0
    if key_mods & (sdl3.SDL_KMOD_LSHIFT | sdl3.SDL_KMOD_RSHIFT):
        mods |= 0x0001  # SHIFT
    if key_mods & (sdl3.SDL_KMOD_LCTRL | sdl3.SDL_KMOD_RCTRL):
        mods |= 0x0002  # CTRL
    if key_mods & (sdl3.SDL_KMOD_LALT | sdl3.SDL_KMOD_RALT):
        mods |= 0x0004  # ALT
    if key_mods & (sdl3.SDL_KMOD_LGUI | sdl3.SDL_KMOD_RGUI):
        mods |= 0x0008  # SUPER/CMD
    return mods


def _convert_sdl_mods_to_glfw(sdl_mods: int) -> int:
    """Convert SDL3 event modifier state to GLFW-compatible format."""
    mods = 0
    if sdl_mods & (sdl3.SDL_KMOD_LSHIFT | sdl3.SDL_KMOD_RSHIFT):
        mods |= 0x0001  # SHIFT
    if sdl_mods & (sdl3.SDL_KMOD_LCTRL | sdl3.SDL_KMOD_RCTRL):
        mods |= 0x0002  # CTRL
    if sdl_mods & (sdl3.SDL_KMOD_LALT | sdl3.SDL_KMOD_RALT):
        mods |= 0x0004  # ALT
    if sdl_mods & (sdl3.SDL_KMOD_LGUI | sdl3.SDL_KMOD_RGUI):
        mods |= 0x0008  # SUPER/CMD
    return mods


def _cursor_type_to_sdl3(cursor_type: CursorType) -> int:
    """Convert CursorType to SDL3 system cursor constant."""
    match cursor_type:
        case CursorType.ARROW:
            return sdl3.SDL_SYSTEM_CURSOR_DEFAULT
        case CursorType.TEXT:
            return sdl3.SDL_SYSTEM_CURSOR_TEXT
        case CursorType.POINTER:
            return sdl3.SDL_SYSTEM_CURSOR_POINTER
        case CursorType.RESIZE_H:
            return sdl3.SDL_SYSTEM_CURSOR_EW_RESIZE
        case CursorType.RESIZE_V:
            return sdl3.SDL_SYSTEM_CURSOR_NS_RESIZE
        case CursorType.CROSSHAIR:
            return sdl3.SDL_SYSTEM_CURSOR_CROSSHAIR
        case CursorType.WAIT:
            return sdl3.SDL_SYSTEM_CURSOR_WAIT
        case CursorType.NOT_ALLOWED:
            return sdl3.SDL_SYSTEM_CURSOR_NOT_ALLOWED
        case _:
            return sdl3.SDL_SYSTEM_CURSOR_DEFAULT
