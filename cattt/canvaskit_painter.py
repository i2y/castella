from typing import Optional, cast

from js import Image, ImageData, window, document
import numpy as np
from pyodide import create_proxy

import core


def code2rgb(color_code): # TODO alpha
    r = int(color_code[1:3], 16)
    g = int(color_code[3:5], 16)
    b = int(color_code[5:7], 16)
    return (r, g, b, 1.0)


def to_ck_color(color: str) -> int:
    return window.CK.Color(*code2rgb(color))


def to_ck_rect(rect: core.Rect):
    return window.CK.XYWHRect(rect.origin.x, rect.origin.y, rect.size.width, rect.size.height)


class Painter:
    def __init__(self, frame: core.Frame, surface):
        self._frame = frame
        self._surface = surface
        self._canvas = surface.getCanvas()
        self._style: Optional[core.Style] = None
        self._style_stack = []
        self._images = {}

    def clear_all(self) -> None:
        self._frame.clear()

    def fill_rect(self, rect: core.Rect) -> None:
        style = cast(core.Style, self._style)
        paint = window.CK.Paint.new()
        paint.setColor(to_ck_color(style.fill.color))
        paint.setStyle(window.CK.PaintStyle.Fill)
        sr = to_ck_rect(rect)
        self._canvas.drawRect(sr, paint)

    def stroke_rect(self, rect: core.Rect) -> None:
        style = cast(core.Style, self._style)
        paint = window.CK.Paint.new()
        paint.setColor(to_ck_color(style.stroke.color))
        paint.setStyle(window.CK.PaintStyle.Stroke)
        sr = to_ck_rect(rect)
        self._canvas.drawRect(sr, paint)

    def measure_text(self, text: str) -> float:
        style = cast(core.Style, self._style)
        font = window.CK.Font.new(window.typeface, style.font.size)
        return sum(font.getGlyphWidths(font.getGlyphIDs(text)))

    def get_font_metrics(self) -> core.FontMetrics:
        style = cast(core.Style, self._style)
        return core.FontMetrics(cap_height=style.font.size - style.font.size/4)

    def translate(self, pos: core.Point) -> None:
        self._canvas.translate(pos.x, pos.y)

    def clip(self, rect: core.Rect) -> None:
        self._canvas.clipRect(to_ck_rect(core.Rect(core.Point(0, 0),
                                                    core.Size(rect.size.width+1,
                                                             rect.size.height+1))),
                              window.CK.ClipOp.Intersect,
                              True)

    def fill_text(
        self, text: str, pos: core.Point, max_width: Optional[float]
    ) -> None:
        if text == "":
            return

        style = cast(core.Style, self._style)
        if style is None or style.fill is None:
            color = 0
        else:
            color = to_ck_color(style.fill.color)

        if style is None or style.font is None:
            font = window.CK.Font.new(window.typeface, 0)
        else:
            font = window.CK.Font.new(window.typeface, style.font.size)
        blob = window.CK.TextBlob.MakeFromText(text, font)
        paint = window.CK.Paint.new()
        paint.setColor(color)
        paint.setStyle(window.CK.PaintStyle.Fill)
        paint.setAntiAlias(True)
        self._canvas.drawTextBlob(
            blob,
            pos.x,
            pos.y,
            paint,
        )

    def stroke_text(
        self, text: str, pos: core.Point, max_width: Optional[float]
    ) -> None:
        ...

    def draw_paragraph(self, paragraph: core.Paragraph, pos: core.Point) -> None:
        # self._canvas.drawParagraph(paragraph.to_ck_paragraph(), pos.x, pos.y)
        ...

    def draw_image(self, file_path: str, rect: core.Rect, use_cache: bool=True) -> None:
        raise NotImplementedError()

    def measure_image(self, file_path: str, use_cache: bool=True) -> core.Size:
        raise NotImplementedError()

    def get_net_image_async(self, name, url, callback):
        if name in self._images:
            return self._images[name]
        img = Image.new()
        img.src = url
        img.onload = lambda _: self._on_get_image(name, img, callback)
        return None

    def _on_get_image(self, name, img, callback):
        from operator import setitem
        setitem(self._images, name, window.CK.MakeImageFromCanvasImageSource(img))
        callback()

    def draw_image_object(self, img, x, y):
        self._canvas.drawImage(img, x, y)

    def draw_net_image(self, url: str, rect: core.Rect, use_cache: bool=True) -> None:
        raise NotImplementedError()

    def measure_net_image(self, url: str, use_cache: bool=True) -> core.Size:
        raise NotImplementedError()

    def measure_np_array_as_an_image(self, array: np.ndarray) -> core.Size:
        height, width, _ = array.shape
        return core.Size(width, height)

    def draw_np_array_as_an_image(self, array: np.ndarray, x: float, y: float) -> None:
        raise NotImplementedError()

    def draw_np_array_as_an_image_rect(self, array: np.ndarray, rect: core.Rect) -> None:
        raise NotImplementedError()

    def get_numpy_image_async(self, array, callback):
        arr_id = id(array)
        if arr_id in self._images:
            return self._images[arr_id]
        h, w, d = array.shape
        img = np.ravel(np.uint8(np.reshape(array, (h * w * d, -1)))).tobytes()
        pixels_proxy = create_proxy(img)
        pixels_buf = pixels_proxy.getBuffer("u8clamped")
        img_data = ImageData.new(pixels_buf.data, w, h)
        canvas = document.createElement("canvas")
        ctx = canvas.getContext("2d")
        canvas.width = img_data.width
        canvas.height = img_data.height
        ctx.putImageData(img_data, 0, 0)

        image = Image.new()
        image.src = canvas.toDataURL()
        image.onload = lambda _: self._on_get_image(arr_id, image, callback)
        return None

    def save(self) -> None:
        self._canvas.save()
        self._style_stack.append(self._style)

    def restore(self) -> None:
        self._canvas.restore()
        self._style = self._style_stack.pop()

    def style(self, style: core.Style) -> None:
        self._style = style

    def flush(self) -> None:
        self._surface.flush()
        self._frame.flush()
