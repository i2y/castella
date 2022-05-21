import io
import urllib.request
from functools import cache
from typing import Optional, cast

import numpy as np
import skia

from . import core


def _code2rgb(color_code):
    r = int(color_code[1:3], 16)
    g = int(color_code[3:5], 16)
    b = int(color_code[5:7], 16)
    return (r, g, b)


def _to_skia_color(color: str) -> int:
    return skia.ColorSetRGB(*_code2rgb(color))


def _to_skia_rect(rect: core.Rect) -> skia.Rect:
    return skia.Rect.MakeXYWH(
        rect.origin.x, rect.origin.y, rect.size.width - 1, rect.size.height - 1
    )


@cache
def _get_font_face(font_family: str, font_style: skia.FontStyle) -> skia.Typeface:
    return skia.Typeface(font_family, font_style)


@cache
def _to_skia_font(font: core.Font) -> skia.Font:
    if font.weight is core.FontWeight.NORMAL:
        font_weight = skia.FontStyle.kNormal_Weight
    else:
        font_weight = skia.FontStyle.kBold_Weight

    if font.slant is core.FontSlant.UPRIGHT:
        font_slant = skia.FontStyle.kUpright_Slant
    else:
        font_slant = skia.FontStyle.kItalic_Slant

    font_style = skia.FontStyle(font_weight,
                                skia.FontStyle.kNormal_Width,
                                font_slant)
    return skia.Font(_get_font_face(font.family, font_style), font.size)


class Painter:
    def __init__(self, frame: core.Frame, surface: skia.Surface):
        self._frame = frame
        self._surface = surface
        self._canvas = surface.getCanvas()
        self._style: Optional[core.Style] = None
        self._style_stack = []

    def clear_all(self) -> None:
        self._frame.clear()

    def fill_rect(self, rect: core.Rect) -> None:
        style = cast(core.Style, self._style)
        paint = skia.Paint(
            Color=_to_skia_color(style.fill.color),
            Style=skia.Paint.kFill_Style,
        )
        sr = _to_skia_rect(rect)
        self._canvas.drawRect(sr, paint)

    def stroke_rect(self, rect: core.Rect) -> None:
        style = cast(core.Style, self._style)
        paint = skia.Paint(
            Color=_to_skia_color(style.stroke.color),
            Style=skia.Paint.kStroke_Style,
        )
        sr = _to_skia_rect(rect)
        self._canvas.drawRect(sr, paint)

    def measure_text(self, text: str) -> float:
        style = cast(core.Style, self._style)
        font = skia.Font(None, style.font.size)
        return font.measureText(text)

    def get_font_metrics(self) -> core.FontMetrics:
        style = cast(core.Style, self._style)
        font = skia.Font(None, style.font.size)
        return core.FontMetrics(cap_height=font.getMetrics().fCapHeight)

    def translate(self, pos: core.Point) -> None:
        self._canvas.translate(pos.x, pos.y)

    def clip(self, rect: core.Rect) -> None:
        self._canvas.clipRect(_to_skia_rect(core.Rect(core.Point(0, 0),
                                                    core.Size(rect.size.width+1,
                                                             rect.size.height+1))))

    def fill_text(
        self, text: str, pos: core.Point, max_width: Optional[float]
    ) -> None:
        if text == "":
            return

        style = cast(core.Style, self._style)
        if style is None or style.fill is None:
            color = 0
        else:
            color = _to_skia_color(style.fill.color)

        if style is None or style.font is None:
            font = skia.Font(None, 0)
        else:
            font = _to_skia_font(style.font)

        blob = skia.TextBlob(text, font)
        paint = skia.Paint(
            Style=skia.Paint.kFill_Style,
            Color=color,
        )
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
        raise NotImplementedError()

    def draw_image(self, file_path: str, rect: core.Rect, use_cache: bool=True) -> None:
        if use_cache:
            image = _get_cached_image(file_path)
        else:
            image = skia.Image.open(file_path)
        self._canvas.drawImageRect(image, _to_skia_rect(rect))

    def measure_image(self, file_path: str, use_cache: bool=True) -> core.Size:
        if use_cache:
            image = _get_cached_image(file_path)
        else:
            image = skia.Image.open(file_path)
        return core.Size(image.width(), image.height())

    def draw_net_image(self, url: str, rect: core.Rect, use_cache: bool=True) -> None:
        if use_cache:
            image = _get_cached_net_image(url)
        else:
            image = _get_net_image(url)
        self._canvas.drawImageRect(image, _to_skia_rect(rect))

    def measure_net_image(self, url: str, use_cache: bool=True) -> core.Size:
        if use_cache:
            image = _get_cached_net_image(url)
        else:
            image = _get_net_image(url)
        return core.Size(image.width(), image.height())

    def measure_np_array_as_an_image(self, array: np.ndarray) -> core.Size:
        height, width, _ = array.shape
        return core.Size(width, height)

    def get_net_image_async(self, name: str, url: str, callback) -> None:
        raise NotImplementedError()

    def draw_image_object(self, img, x: float, y: float) -> None:
        self._canvas.drawImage(img, x, y)

    def draw_np_array_as_an_image(self, array: np.ndarray, x: float, y: float) -> None:
        image = skia.Image.fromarray(array)
        self.draw_image_object(image, x, y)

    def draw_np_array_as_an_image_rect(self, array: np.ndarray, rect: core.Rect) -> None:
        image = skia.Image.fromarray(array)
        self._canvas.drawImageRect(image, _to_skia_rect(rect))

    def get_numpy_image_async(self, array: np.ndarray, callback):
        raise NotImplementedError()

    def save(self) -> None:
        self._canvas.save()
        self._style_stack.append(self._style)

    def restore(self) -> None:
        self._canvas.restore()
        self._style = self._style_stack.pop()

    def style(self, style: core.Style) -> None:
        self._style = style

    def flush(self) -> None:
        self._canvas.flush()
        self._frame.flush()


@cache
def _get_cached_image(path: str) -> skia.Image:
    return skia.Image.open(path)

@cache
def _get_cached_net_image(url: str) -> skia.Image:
    return _get_net_image(url)

def _get_net_image(url: str) -> skia.Image:
    return skia.Image.open(io.BytesIO(urllib.request.urlopen(url).read()))
