import sys

if "pyodide" in sys.modules:
    from . import web_frame

    Frame = web_frame.Frame
else:
    try:
        from . import glfw_frame

        Frame = glfw_frame.Frame
    except:
        try:
            from . import sdl_frame

            Frame = sdl_frame.Frame
        except:
            raise RuntimeError(
                "Could you please run `pip install castella[sdl]` or `pip install castella[glfw]`?"
            )
