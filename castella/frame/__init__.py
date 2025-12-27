"""Castella Frame - Window management abstractions."""

import os
import sys

from castella.frame.base import BaseFrame


def _is_terminal_mode() -> bool:
    return os.environ.get("CASTELLA_IS_TERMINAL_MODE", "false") == "true"


# Select appropriate Frame implementation based on environment
if "pyodide" in sys.modules:
    from castella import web_frame

    Frame = web_frame.Frame
elif _is_terminal_mode():
    from castella import pt_frame

    Frame = pt_frame.PTFrame
else:
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
