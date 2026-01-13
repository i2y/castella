"""Castella Frame - Window management abstractions."""

import os
import sys

from castella.frame.base import BaseFrame


def _is_terminal_mode() -> bool:
    return os.environ.get("CASTELLA_IS_TERMINAL_MODE", "false") == "true"


def _get_preferred_frame() -> str:
    """Get preferred frame from environment variable.

    Returns:
        "glfw", "sdl", "sdl3", "tui", or "auto" (default)
    """
    return os.environ.get("CASTELLA_FRAME", "auto").lower()


def _is_ios() -> bool:
    """Detect if running on iOS via Rubicon-ObjC."""
    try:
        from rubicon.objc import ObjCClass

        # UIDevice is iOS-only; if it exists, we're on iOS
        ObjCClass("UIDevice")
        return True
    except Exception:
        return False


def _is_android() -> bool:
    """Detect if running on Android via pyjnius."""
    try:
        from jnius import autoclass

        # android.os.Build is Android-only
        autoclass("android.os.Build")
        return True
    except Exception:
        return False


# Select appropriate Frame implementation based on environment
if "pyodide" in sys.modules:
    # Web (Pyodide/PyScript)
    from castella import web_frame

    Frame = web_frame.Frame
elif _is_terminal_mode():
    # Terminal UI
    from castella import pt_frame

    Frame = pt_frame.PTFrame
elif _is_ios():
    # iOS (Rubicon-ObjC + Metal)
    from castella import ios_frame

    Frame = ios_frame.Frame
elif _is_android():
    # Android (pyjnius + Vulkan) - Not yet implemented
    raise ImportError(
        "Android support is not yet implemented. "
        "See castella-skia for planned Vulkan backend."
    )
else:
    # Desktop (GLFW/SDL + OpenGL)
    _preferred = _get_preferred_frame()

    if _preferred == "sdl3":
        # Explicitly requested SDL3
        from castella import sdl3_frame

        Frame = sdl3_frame.Frame
    elif _preferred == "sdl":
        # Explicitly requested SDL2
        from castella import sdl_frame

        Frame = sdl_frame.Frame
    elif _preferred == "glfw":
        # Explicitly requested GLFW
        from castella import glfw_frame

        Frame = glfw_frame.Frame
    elif _preferred == "tui":
        # Explicitly requested TUI
        from castella import pt_frame

        Frame = pt_frame.PTFrame
    else:
        # Auto-detect: try GLFW first, then SDL3, then SDL2, then TUI
        try:
            from castella import glfw_frame

            Frame = glfw_frame.Frame
        except Exception:
            try:
                from castella import sdl3_frame

                Frame = sdl3_frame.Frame
            except Exception:
                try:
                    from castella import sdl_frame

                    Frame = sdl_frame.Frame
                except Exception:
                    try:
                        from castella import pt_frame

                        Frame = pt_frame.PTFrame
                    except Exception:
                        raise ImportError("Could not import any frame implementation")


__all__ = ["BaseFrame", "Frame"]
