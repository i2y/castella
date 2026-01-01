"""macOS native IME integration via PyObjC.

This module provides IME (Input Method Editor) support for GLFW windows
on macOS by hooking into the native Cocoa text input system.

The implementation uses method swizzling to intercept NSTextInputClient
protocol methods on GLFW's content view, enabling:
- Preedit text display (text being composed before confirmation)
- IME candidate window positioning
"""

from __future__ import annotations

import platform
from typing import TYPE_CHECKING, Callable, Optional

if TYPE_CHECKING:
    pass

# Check if we're on macOS and PyObjC is available
_available = False
_setup_error: Optional[str] = None

if platform.system() == "Darwin":
    try:
        import ctypes
        from ctypes import c_void_p

        import objc

        _available = True
    except ImportError as e:
        _setup_error = f"PyObjC not available: {e}"


def is_available() -> bool:
    """Check if macOS IME support is available."""
    return _available


def get_setup_error() -> Optional[str]:
    """Get error message if IME setup failed."""
    return _setup_error


if _available:
    import warnings

    # Suppress PyObjC warnings about NSRange pointers from IME methods
    try:
        from objc import ObjCPointerWarning

        warnings.filterwarnings(
            "ignore",
            message="PyObjCPointer created:.*_NSRange",
            category=ObjCPointerWarning,
        )
    except ImportError:
        pass

    import glfw

    # Get the GLFW shared library for native function access
    _glfw_lib = None

    def _get_glfw_lib():
        """Get the GLFW shared library handle."""
        global _glfw_lib
        if _glfw_lib is not None:
            return _glfw_lib

        # Try to find GLFW library path
        # pyglfw stores the library internally
        try:
            # Access the internal glfw library
            if hasattr(glfw, "_glfw"):
                _glfw_lib = glfw._glfw
            else:
                # Fallback: try to load directly
                import ctypes.util

                lib_path = ctypes.util.find_library("glfw")
                if lib_path:
                    _glfw_lib = ctypes.CDLL(lib_path)
        except Exception:
            pass

        return _glfw_lib

    def _get_cocoa_window(glfw_window) -> Optional[c_void_p]:
        """Get the NSWindow pointer from a GLFW window."""
        lib = _get_glfw_lib()
        if lib is None:
            return None

        try:
            glfwGetCocoaWindow = lib.glfwGetCocoaWindow
            glfwGetCocoaWindow.argtypes = [c_void_p]
            glfwGetCocoaWindow.restype = c_void_p

            # GLFW window handle
            window_ptr = ctypes.cast(glfw_window, c_void_p)
            ns_window_ptr = glfwGetCocoaWindow(window_ptr)
            return ns_window_ptr
        except Exception:
            return None

    # Store original method implementations for swizzling
    _original_set_marked_text = None
    _original_insert_text = None
    _original_unmark_text = None
    _original_do_command_by_selector = None

    # Global callback storage (set by MacOSIMEManager)
    _ime_preedit_callback: Optional[Callable[[str, int], None]] = None
    _ime_commit_callback: Optional[Callable[[str], None]] = None

    # Global cursor rect storage for firstRectForCharacterRange
    _ime_cursor_rect: tuple[int, int, int, int] = (0, 0, 1, 20)
    _ime_ns_window: Optional[object] = None

    def _swizzled_set_marked_text(self, aString, selectedRange, replacementRange):
        """Swizzled setMarkedText:selectedRange:replacementRange: implementation.

        This intercepts IME preedit text and notifies the callback.
        """
        # Call original implementation
        if _original_set_marked_text:
            _original_set_marked_text(self, aString, selectedRange, replacementRange)

        # Notify callback with preedit text
        if _ime_preedit_callback:
            if aString is None:
                text = ""
            elif hasattr(aString, "string"):
                # NSAttributedString
                text = str(aString.string())
            else:
                # NSString
                text = str(aString) if aString else ""

            # selectedRange: cursor position within preedit text
            # For Japanese IME, location is typically at the end of preedit
            if hasattr(selectedRange, "location"):
                cursor_pos = selectedRange.location + selectedRange.length
            else:
                cursor_pos = len(text)

            _ime_preedit_callback(text, cursor_pos)

    def _swizzled_insert_text(self, aString, replacementRange):
        """Swizzled insertText:replacementRange: implementation.

        This intercepts confirmed text from IME.
        """
        # Clear preedit first
        if _ime_preedit_callback:
            _ime_preedit_callback("", 0)

        # Call original implementation
        if _original_insert_text:
            _original_insert_text(self, aString, replacementRange)

        # Note: We don't call _ime_commit_callback here because
        # GLFW's char callback will handle the committed text

    def _swizzled_unmark_text(self):
        """Swizzled unmarkText implementation.

        This is called when IME composition is cancelled (e.g., pressing Escape
        or moving cursor outside the preedit area).
        """
        # Clear preedit
        if _ime_preedit_callback:
            _ime_preedit_callback("", 0)

        # Call original implementation
        if _original_unmark_text:
            _original_unmark_text(self)

    def _swizzled_do_command_by_selector(self, aSelector):
        """Swizzled doCommandBySelector: implementation.

        This is called when special keys (like backspace, enter) are pressed
        during IME composition.
        """
        # Call original implementation
        if _original_do_command_by_selector:
            _original_do_command_by_selector(self, aSelector)

    def _swizzled_first_rect_for_character_range(self, aRange, actualRange):
        """Swizzled firstRectForCharacterRange:actualRange: implementation.

        This provides the cursor position for IME candidate window placement.
        Returns an NSRect in screen coordinates.
        """
        # Get cursor rect in window coordinates
        x, y, w, h = _ime_cursor_rect

        screen_x, screen_y = 0.0, 0.0

        # Convert to screen coordinates
        if _ime_ns_window is not None:
            try:
                # Get window frame (screen coordinates)
                window_frame = _ime_ns_window.frame()
                content_rect = _ime_ns_window.contentRectForFrameRect_(window_frame)

                # Window content origin in screen coordinates
                content_origin_x = content_rect.origin.x
                content_origin_y = content_rect.origin.y
                content_height = content_rect.size.height

                # Convert from top-left origin (our coords) to bottom-left origin (macOS)
                # y in our system: 0 = top, increases downward
                # y in macOS screen: 0 = bottom, increases upward
                screen_x = content_origin_x + x
                screen_y = content_origin_y + (content_height - y - h)
            except Exception:
                pass

        # Return as nested tuple: ((origin_x, origin_y), (width, height))
        # PyObjC should convert this to NSRect/CGRect
        return ((screen_x, screen_y), (float(w), float(h)))

    class MacOSIMEManager:
        """Manages macOS IME integration for a GLFW window.

        This class hooks into the GLFW window's content view to intercept
        IME events and provide preedit text to the application.
        """

        def __init__(self, glfw_window):
            """Initialize IME manager for a GLFW window.

            Args:
                glfw_window: The GLFW window handle
            """
            self._glfw_window = glfw_window
            self._ns_window = None
            self._ns_view = None
            self._cursor_rect = (0, 0, 1, 20)
            self._swizzled = False

            self._setup_ime()

        def _setup_ime(self):
            """Set up IME support by swizzling NSView methods."""
            global _original_set_marked_text, _original_insert_text
            global _ime_ns_window

            try:
                # Get NSWindow from GLFW
                ns_window_ptr = _get_cocoa_window(self._glfw_window)
                if ns_window_ptr is None:
                    return

                # Convert pointer to PyObjC object
                self._ns_window = objc.objc_object(c_void_p=ns_window_ptr)
                if self._ns_window is None:
                    return

                # Store for global access (used by firstRectForCharacterRange)
                _ime_ns_window = self._ns_window

                # Get content view
                self._ns_view = self._ns_window.contentView()
                if self._ns_view is None:
                    return

                # Get the view's class for swizzling
                view_class = self._ns_view.__class__

                # Only swizzle once per class
                if not self._swizzled and _original_set_marked_text is None:
                    # Try to swizzle setMarkedText:selectedRange:replacementRange:
                    try:
                        sel = objc.selector(
                            _swizzled_set_marked_text,
                            selector=b"setMarkedText:selectedRange:replacementRange:",
                            signature=b"v@:@{_NSRange=QQ}{_NSRange=QQ}",
                        )

                        # Get original implementation
                        original_method = view_class.instanceMethodForSelector_(
                            b"setMarkedText:selectedRange:replacementRange:"
                        )
                        if original_method:
                            _original_set_marked_text = original_method

                            # Replace with swizzled version
                            objc.classAddMethod(view_class, sel.selector, sel)
                            self._swizzled = True
                    except Exception:
                        # Swizzling failed, IME preedit won't work but app continues
                        pass

                    # Try to replace firstRectForCharacterRange:actualRange:
                    # using ObjC runtime via ctypes
                    try:
                        libobjc = ctypes.CDLL("/usr/lib/libobjc.dylib")

                        # Define function signatures
                        libobjc.sel_registerName.argtypes = [ctypes.c_char_p]
                        libobjc.sel_registerName.restype = ctypes.c_void_p

                        libobjc.class_getInstanceMethod.argtypes = [
                            ctypes.c_void_p,
                            ctypes.c_void_p,
                        ]
                        libobjc.class_getInstanceMethod.restype = ctypes.c_void_p

                        libobjc.method_getTypeEncoding.argtypes = [ctypes.c_void_p]
                        libobjc.method_getTypeEncoding.restype = ctypes.c_char_p

                        selector_name = b"firstRectForCharacterRange:actualRange:"
                        sel = libobjc.sel_registerName(selector_name)

                        # Get class pointer using object_getClass
                        libobjc.object_getClass.argtypes = [ctypes.c_void_p]
                        libobjc.object_getClass.restype = ctypes.c_void_p

                        # Get the view's pointer and then its class
                        view_ptr = objc.pyobjc_id(self._ns_view)
                        class_ptr = libobjc.object_getClass(ctypes.c_void_p(view_ptr))

                        original_method = libobjc.class_getInstanceMethod(
                            ctypes.c_void_p(class_ptr), ctypes.c_void_p(sel)
                        )

                        if original_method:
                            type_encoding = libobjc.method_getTypeEncoding(
                                ctypes.c_void_p(original_method)
                            )

                            # Add a new method with a different name, then swap
                            swizzled_sel_name = (
                                b"_castella_firstRectForCharacterRange:actualRange:"
                            )

                            # Create a selector with the same signature
                            first_rect_sel = objc.selector(
                                _swizzled_first_rect_for_character_range,
                                selector=swizzled_sel_name,
                                signature=type_encoding,
                            )

                            # Add our method to the class
                            objc.classAddMethod(
                                view_class, first_rect_sel.selector, first_rect_sel
                            )

                            # Now get our new method
                            swizzled_sel = libobjc.sel_registerName(swizzled_sel_name)
                            new_method = libobjc.class_getInstanceMethod(
                                ctypes.c_void_p(class_ptr),
                                ctypes.c_void_p(swizzled_sel),
                            )

                            if new_method:
                                # Use method_exchangeImplementations
                                libobjc.method_exchangeImplementations.argtypes = [
                                    ctypes.c_void_p,
                                    ctypes.c_void_p,
                                ]
                                libobjc.method_exchangeImplementations.restype = None

                                libobjc.method_exchangeImplementations(
                                    ctypes.c_void_p(original_method),
                                    ctypes.c_void_p(new_method),
                                )
                    except Exception:
                        pass

                    # Swizzle unmarkText to handle IME cancellation
                    try:
                        global _original_unmark_text

                        unmark_sel = objc.selector(
                            _swizzled_unmark_text,
                            selector=b"unmarkText",
                            signature=b"v@:",
                        )

                        original_unmark = view_class.instanceMethodForSelector_(
                            b"unmarkText"
                        )
                        if original_unmark:
                            _original_unmark_text = original_unmark
                            objc.classAddMethod(
                                view_class, unmark_sel.selector, unmark_sel
                            )
                    except Exception:
                        pass

                    # Swizzle doCommandBySelector: to intercept special keys
                    try:
                        global _original_do_command_by_selector

                        cmd_sel = objc.selector(
                            _swizzled_do_command_by_selector,
                            selector=b"doCommandBySelector:",
                            signature=b"v@::",
                        )

                        original_cmd = view_class.instanceMethodForSelector_(
                            b"doCommandBySelector:"
                        )
                        if original_cmd:
                            _original_do_command_by_selector = original_cmd
                            objc.classAddMethod(view_class, cmd_sel.selector, cmd_sel)
                    except Exception:
                        pass

            except Exception:
                # Setup failed, continue without IME support
                pass

        def set_preedit_handler(
            self, handler: Optional[Callable[[str, int], None]]
        ) -> None:
            """Set the callback for preedit text updates.

            Args:
                handler: Callback function(text, cursor_pos) or None
            """
            global _ime_preedit_callback
            _ime_preedit_callback = handler

        def set_commit_handler(self, handler: Optional[Callable[[str], None]]) -> None:
            """Set the callback for committed text.

            Args:
                handler: Callback function(text) or None
            """
            global _ime_commit_callback
            _ime_commit_callback = handler

        def set_cursor_rect(self, x: int, y: int, w: int, h: int) -> None:
            """Set the IME cursor rectangle for candidate window positioning.

            Args:
                x: X coordinate (window coordinates, origin top-left)
                y: Y coordinate (window coordinates, origin top-left)
                w: Width
                h: Height
            """
            global _ime_cursor_rect
            self._cursor_rect = (x, y, w, h)
            _ime_cursor_rect = (x, y, w, h)

            # Notify the input context that cursor position changed
            if self._ns_view is not None:
                try:
                    input_context = self._ns_view.inputContext()
                    if input_context:
                        input_context.invalidateCharacterCoordinates()
                except Exception:
                    pass

        def get_cursor_rect(self) -> tuple[int, int, int, int]:
            """Get the current IME cursor rectangle."""
            return self._cursor_rect

else:
    # Stub class when PyObjC is not available
    class MacOSIMEManager:
        """Stub IME manager when PyObjC is not available."""

        def __init__(self, glfw_window):
            pass

        def set_preedit_handler(
            self, handler: Optional[Callable[[str, int], None]]
        ) -> None:
            pass

        def set_commit_handler(self, handler: Optional[Callable[[str], None]]) -> None:
            pass

        def set_cursor_rect(self, x: int, y: int, w: int, h: int) -> None:
            pass

        def get_cursor_rect(self) -> tuple[int, int, int, int]:
            return (0, 0, 1, 20)
