import os
import sys


def _is_terminal_mode() -> bool:
    return os.environ.get("CASTELLA_IS_TERMINAL_MODE", "false") == "true"


if "pyodide" in sys.modules:
    from . import web_frame

    Frame = web_frame.Frame
elif _is_terminal_mode():
    from . import pt_frame

    Frame = pt_frame.PTFrame
else:
    try:
        from . import glfw_frame

        Frame = glfw_frame.Frame
    except:
        try:
            from . import sdl_frame

            Frame = sdl_frame.Frame
        except:
            try:
                from . import pt_frame

                Frame = pt_frame.PTFrame
            except:
                raise ImportError("Could not import any frame implementation")
