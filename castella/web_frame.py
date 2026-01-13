from asyncio import Future
from typing import Callable, cast

from js import Object, document, window, navigator  # type: ignore
from pyscript.ffi import create_proxy, to_js  # type: ignore

from castella import core
from castella.canvaskit_painter import Painter
from castella.models.events import CursorType


class Frame:
    def __init__(self, title: str, width: float = 0, height: float = 0) -> None:
        document.title = title
        window.resizeTo(width, height)

    def _update_surface_and_painter(self):
        self._surface = window.CK.MakeWebGLCanvasSurface(
            "castella-app",
            window.CK.ColorSpace.SRGB,
            to_js(
                {
                    # "explicitSwapControl": 1,
                    "preserveDrawingBuffer": 1,
                    # "renderViaOffscreenBackBuffer": 0,
                },
                dict_converter=Object.fromEntries,
            ),
        )
        self._painter = Painter(self, self._surface)

    def on_mouse_down(self, handler: Callable[[core.MouseEvent], None]) -> None:
        self._add_mouse_down = lambda: document.body.addEventListener(
            "mousedown",
            create_proxy(
                lambda ev: handler(core.MouseEvent(pos=core.Point(x=ev.x, y=ev.y)))
            ),
        )

    def on_mouse_up(self, handler: Callable[[core.MouseEvent], None]) -> None:
        self._add_mouse_up = lambda: document.body.addEventListener(
            "mouseup",
            create_proxy(
                lambda ev: handler(core.MouseEvent(pos=core.Point(x=ev.x, y=ev.y)))
            ),
        )

    def on_mouse_wheel(self, handler: Callable[[core.WheelEvent], None]) -> None:
        self._add_mouse_wheel = lambda: document.body.addEventListener(
            "wheel",
            create_proxy(
                lambda ev: handler(
                    core.WheelEvent(
                        pos=core.Point(x=ev.x, y=ev.y),
                        x_offset=ev.deltaX,
                        y_offset=ev.deltaY,
                    )
                )
            ),
        )

    def on_cursor_pos(self, handler: Callable[[core.MouseEvent], None]) -> None:
        self._add_cursor_pos = lambda: document.body.addEventListener(
            "mousemove",
            create_proxy(
                lambda ev: handler(core.MouseEvent(pos=core.Point(x=ev.x, y=ev.y)))
            ),
        )

    def on_input_char(self, handler: Callable[[core.InputCharEvent], None]) -> None:
        self._add_input_char = lambda: document.body.addEventListener(
            "keypress",
            create_proxy(lambda ev: handler(core.InputCharEvent(char=str(ev.key)))),
        )

    def on_input_key(self, handler: Callable[[core.InputKeyEvent], None]) -> None:
        self._add_input_key = lambda: document.body.addEventListener(
            "keydown",
            create_proxy(
                lambda ev: handler(
                    core.InputKeyEvent(
                        key=convert_to_key_code(ev.keyCode),
                        scancode=0,
                        action=core.KeyAction.PRESS,
                        mods=get_key_mods(ev),
                    )
                )
            ),
        )

    def on_ime_preedit(self, handler: Callable[[core.IMEPreeditEvent], None]) -> None:
        # Web doesn't support IME preedit events (yet)
        pass

    def on_redraw(self, handler: Callable[[core.Painter, bool], None]) -> None:
        self._add_redraw = lambda: window.addEventListener(
            "resize", create_proxy(lambda ev: self._on_redraw(handler))
        )

    def _on_redraw(self, handler: Callable[[core.Painter, bool], None]) -> None:
        # Update canvas dimensions BEFORE creating new surface
        self._canvas.width = window.innerWidth
        self._canvas.height = window.innerHeight
        self._size = core.Size(width=window.innerWidth, height=window.innerHeight)
        self._update_surface_and_painter()
        handler(self._painter, True)

    def get_painter(self) -> core.Painter:
        return self._painter

    def get_size(self) -> core.Size:
        return core.Size(width=self._canvas.width, height=self._canvas.height)

    def post_update(self, ev: "core.UpdateEvent") -> None:
        if not hasattr(self, "_painter"):
            return

        if ev.target is None:
            return

        if isinstance(ev.target, core.App):
            pos = core.Point(x=0, y=0)
            clippedRect = None
        else:
            w: core.Widget = cast(core.Widget, ev.target)
            pos = w.get_pos()
            clippedRect = core.Rect(origin=core.Point(x=0, y=0), size=w.get_size())

        self._painter.save()
        try:
            self._painter.translate(pos)
            if clippedRect is not None:
                self._painter.clip(clippedRect)
            ev.target.redraw(self._painter, ev.completely)
            self._painter.flush()
        finally:
            self._painter.restore()

    def flush(self) -> None:
        pass

    def clear(self) -> None:
        pass

    def run(self) -> None:
        style = document.createElement("style")
        style.innerHTML = """
        #castella-app {
           display: block;
           padding: 0px;
           margin: 0px;
           border: none;
        }

        html,
        body {
            min-height: 100vh;
            margin: 0px;
            padding: 0px;
            overflow: hidden;
        }
        """
        document.body.appendChild(style)
        canvas = document.createElement("canvas")
        canvas.setAttribute("id", "castella-app")
        document.body.appendChild(canvas)
        self._canvas = canvas

        self._add_mouse_down()
        self._add_mouse_up()
        self._add_mouse_wheel()
        self._add_cursor_pos()
        self._add_input_char()
        self._add_input_key()
        self._add_redraw()

        # Check if CanvasKit is already initialized (from HTML)
        if hasattr(window, "CK") and hasattr(window, "typeface"):
            # Already initialized, trigger resize
            self._trigger_resize()
        else:
            # Initialize CanvasKit
            init_script = document.createElement("script")
            init_script.innerHTML = """
            const loadFont = fetch('Roboto-Regular.ttf')
                .then((response) => response.arrayBuffer());

            const ckLoaded = CanvasKitInit();
            Promise.all([ckLoaded, loadFont]).then(([CanvasKit, robotoData]) => {
                window.CK = CanvasKit;
                window.fontMgr = CanvasKit.FontMgr.FromData([robotoData]);
                window.typeface = CanvasKit.Typeface.MakeFreeTypeFaceFromData(robotoData);
                let resize_event = new Event('resize');
                window.dispatchEvent(resize_event);
            });

            window.addEventListener("resize", resize);
            function resize() {
                let canvas = document.getElementById("castella-app");
                canvas.width = window.innerWidth;
                canvas.height = window.innerHeight;
            }

            window.addEventListener("load", resize);
            """
            document.body.appendChild(init_script)

    def _trigger_resize(self) -> None:
        resize_script = document.createElement("script")
        resize_script.innerHTML = """
        function resize() {
            let canvas = document.getElementById("castella-app");
            canvas.width = window.innerWidth;
            canvas.height = window.innerHeight;
        }
        resize();
        window.addEventListener("resize", resize);
        let resize_event = new Event('resize');
        window.dispatchEvent(resize_event);
        """
        document.body.appendChild(resize_script)

    def get_clipboard_text(self) -> str:
        raise NotImplementedError("get_clipboard_text")

    def set_clipboard_text(self, text: str) -> None:
        raise NotImplementedError("set_clipboard_text")

    def async_get_clipboard_text(self, callback: Callable[[Future[str]], None]) -> None:
        navigator.clipboard.readText().add_done_callback(callback)

    def async_set_clipboard_text(
        self, text: str, callback: Callable[[Future], None]
    ) -> None:
        return navigator.clipboard.writeText(text).add_done_callback(callback)

    def set_cursor(self, cursor_type: CursorType) -> None:
        """Set the mouse cursor shape using CSS."""
        css_cursor = _cursor_type_to_css(cursor_type)
        document.body.style.cursor = css_cursor


def _cursor_type_to_css(cursor_type: CursorType) -> str:
    """Convert CursorType to CSS cursor value."""
    match cursor_type:
        case CursorType.ARROW:
            return "default"
        case CursorType.TEXT:
            return "text"
        case CursorType.POINTER:
            return "pointer"
        case CursorType.RESIZE_H:
            return "ew-resize"
        case CursorType.RESIZE_V:
            return "ns-resize"
        case CursorType.CROSSHAIR:
            return "crosshair"
        case CursorType.WAIT:
            return "wait"
        case CursorType.NOT_ALLOWED:
            return "not-allowed"
        case _:
            return "default"


def convert_to_key_code(code: int) -> core.KeyCode:
    match code:
        case 8:
            return core.KeyCode.BACKSPACE
        case 37:
            return core.KeyCode.LEFT
        case 39:
            return core.KeyCode.RIGHT
        case 38:
            return core.KeyCode.UP
        case 40:
            return core.KeyCode.DOWN
        case 33:
            return core.KeyCode.PAGE_UP
        case 34:
            return core.KeyCode.PAGE_DOWN
        case 46:
            return core.KeyCode.DELETE
        case 65:  # 'A'
            return core.KeyCode.A
        case 67:  # 'C'
            return core.KeyCode.C
        case 86:  # 'V'
            return core.KeyCode.V
        case 88:  # 'X'
            return core.KeyCode.X
        case _:
            return core.KeyCode.UNKNOWN


def get_key_mods(ev) -> int:
    """Get keyboard modifier state from JavaScript event."""
    mods = 0
    if ev.shiftKey:
        mods |= 0x0001  # SHIFT
    if ev.ctrlKey:
        mods |= 0x0002  # CTRL
    if ev.altKey:
        mods |= 0x0004  # ALT
    if ev.metaKey:  # Cmd on macOS
        mods |= 0x0008  # SUPER/CMD
    return mods
