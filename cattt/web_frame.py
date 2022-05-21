from typing import Callable, cast

from js import Object, document, window
from pyodide import create_proxy, to_js

import core
from canvaskit_painter import Painter


class Frame:
    def __init__(self, title: str, width: float = 0, height: float = 0) -> None:
        document.title = title
        window.resizeTo(width, height)

    def _update_surface_and_painter(self):
        self._surface = window.CK.MakeWebGLCanvasSurface(
            "cattt-app", window.CK.ColorSpace.SRGB,
            to_js({
                # "explicitSwapControl": 1,
                "preserveDrawingBuffer": 1,
                # "renderViaOffscreenBackBuffer": 0,
            }, dict_converter=Object.fromEntries))
        self._painter = Painter(self, self._surface)

    def on_mouse_down(self, handler: Callable[[core.MouseEvent], None]) -> None:
        self._add_mouse_down = lambda: document.body.addEventListener(
            'mousedown',
            create_proxy(lambda ev: handler(core.MouseEvent(core.Point(ev.x, ev.y)))))

    def on_mouse_up(self, handler: Callable[[core.MouseEvent], None]) -> None:
        self._add_mouse_up = lambda: document.body.addEventListener(
            'mouseup',
            create_proxy(lambda ev: handler(core.MouseEvent(core.Point(ev.x, ev.y)))))

    def on_cursor_pos(self, handler: Callable[[core.MouseEvent], None]) -> None:
        self._add_cursor_pos = lambda: document.body.addEventListener(
            'mousemove',
            create_proxy(lambda ev: handler(core.MouseEvent(core.Point(ev.x, ev.y)))))

    def on_input_char(self, handler: Callable[[core.InputCharEvent], None]) -> None:
        self._add_input_char = lambda: document.body.addEventListener(
            'keypress',
            create_proxy(lambda ev: handler(core.InputCharEvent(str(ev.key)))))

    def on_input_key(self, handler: Callable[[core.InputKeyEvent], None]) -> None:
        self._add_input_key = lambda: document.body.addEventListener(
            'keydown',
            create_proxy(lambda ev: handler(core.InputKeyEvent(convert_to_key_code(ev.keyCode),
                                                               0,
                                                               core.KeyAction.PRESS,
                                                               0))))

    def on_redraw(self, handler: Callable[[core.Painter, bool], None]) -> None:
        self._add_redraw = lambda: window.addEventListener(
            'resize',
            create_proxy(lambda ev: self._on_redraw(handler)))

    def _on_redraw(self, handler: Callable[[core.Painter, bool], None]) -> None:
        self._size = core.Size(window.innerWidth, window.innerHeight)
        self._update_surface_and_painter()
        handler(self._painter, True)

    def get_painter(self) -> core.Painter:
        return self._painter

    def get_size(self) -> core.Size:
        return core.Size(self._canvas.width, self._canvas.height)

    def post_update(self, ev: "core.UpdateEvent") -> None:
        if not hasattr(self, "_painter"):
            return

        if ev.target is None:
            return

        if isinstance(ev.target, core.App):
            pos = core.Point(0, 0)
            clippedRect = None
        else:
            w: core.Widget = cast(core.Widget, ev.target)
            pos = w.get_pos()
            clippedRect = core.Rect(core.Point(0, 0), w.get_size())

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
        #cattt-app {
            padding: 0px;
            border: 0px;
        }

        html,
        body {
            min-height: 100vh;
            margin: 0px;
            padding: 0px;
        }
        """
        document.body.appendChild(style)

        canvas = document.createElement("canvas")
        canvas.setAttribute("id", "cattt-app")
        document.body.appendChild(canvas)
        self._canvas = document.getElementById("cattt-app")

        init_script = document.createElement('script')
        init_script.innerHTML = """
        const loadFont = fetch('https://storage.googleapis.com/skia-cdn/misc/Roboto-Regular.ttf')
            .then((response) => response.arrayBuffer());

        const ckLoaded = CanvasKitInit({
            locattteFile: (file) => 'https://unpkg.com/canvaskit-wasm@0.33.0/bin/' + file
        });
        Promise.all([ckLoaded, loadFont]).then(([CanvasKit, robotoData]) => {
            window.CK = CanvasKit;
            window.fontMgr = CanvasKit.FontMgr.FromData([robotoData]);
            window.typeface = CanvasKit.Typeface.MakeFreeTypeFaceFromData(robotoData)
            let resize_event = new Event('resize');
            window.dispatchEvent(resize_event);
        });

        window.addEventListener("resize", resize);
        function resize() {
            let canvas = document.getElementById("cattt-app");
            canvas.width = window.innerWidth;
            canvas.height = window.innerHeight;
        }

        window.addEventListener("load", resize);
        """
        document.body.appendChild(init_script)

        self._add_mouse_down()
        self._add_mouse_up()
        self._add_cursor_pos()
        self._add_input_char()
        self._add_input_key()
        self._add_redraw()

def convert_to_key_code(code: int) -> core.KeyCode:
    print(code)
    if code == 8:
        return core.KeyCode.BACKSPACE
    elif code == 37:
        return core.KeyCode.LEFT
    elif code == 39:
        return core.KeyCode.RIGHT
    elif code == 38:
        return core.KeyCode.UP
    elif code == 40:
        return core.KeyCode.DOWN
    elif code == 33:
        return core.KeyCode.PAGE_UP
    elif code == 34:
        return core.KeyCode.PAGE_DOWN
    else:
        return core.KeyCode.UNKNOWN
