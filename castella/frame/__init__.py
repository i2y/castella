"""Castella Frame - Window management abstractions."""

import os
import sys

from castella.frame.base import BaseFrame


def _is_terminal_mode() -> bool:
    return os.environ.get("CASTELLA_IS_TERMINAL_MODE", "false") == "true"


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
    try:
        from castella import glfw_frame

        Frame = glfw_frame.Frame
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
