import io
import urllib.request
from functools import cache
from typing import Optional, cast

import numpy as np
import skia

from castella import core
from castella.font import FontSlant, FontWeight
from castella.font_fallback import segment_text_by_font
from castella.models.style import Shadow


def _code2rgb(color_code):
    r = int(color_code[1:3], 16)
    g = int(color_code[3:5], 16)
    b = int(color_code[5:7], 16)
    return (r, g, b)


def _code2rgba(color_code: str) -> tuple[int, int, int, int]:
    """Parse hex color code with optional alpha channel."""
    r = int(color_code[1:3], 16)
    g = int(color_code[3:5], 16)
    b = int(color_code[5:7], 16)
    if len(color_code) >= 9:
        a = int(color_code[7:9], 16)
    else:
        a = 255
    return (r, g, b, a)


def _to_skia_color(color: str) -> int:
    return skia.ColorSetRGB(*_code2rgb(color))


def _to_skia_color_with_alpha(color: str) -> int:
    """Convert hex color (with optional alpha) to Skia color."""
    r, g, b, a = _code2rgba(color)
    return skia.ColorSetARGB(a, r, g, b)


def _to_skia_rect(rect: core.Rect) -> skia.Rect:
    return skia.Rect.MakeXYWH(
        rect.origin.x, rect.origin.y, rect.size.width - 1, rect.size.height - 1
    )


def _to_skia_stroke_rect(rect: core.Rect, stroke_width: float) -> skia.Rect:
    """Create a Skia rect for stroke drawing.

    Strokes are drawn centered on the rect edge. To keep the stroke fully
    within the widget bounds (avoiding clipping at boundaries with adjacent
    widgets), we inset by the full stroke width so the outer edge of the
    stroke stays inside the clip region.
    """
    return skia.Rect.MakeXYWH(
        rect.origin.x + stroke_width,
        rect.origin.y + stroke_width,
        rect.size.width - 2 * stroke_width - 1,
        rect.size.height - 2 * stroke_width - 1,
    )


def _parse_font_stack(font_family: str) -> list[str]:
    """Parse CSS-style font stack into individual font names.

    Examples:
        "'JetBrains Mono', 'Fira Code', monospace" -> ["JetBrains Mono", "Fira Code", "monospace"]
        "Helvetica, Arial, sans-serif" -> ["Helvetica", "Arial", "sans-serif"]
    """
    if not font_family:
        return []

    fonts = []
    for part in font_family.split(","):
        name = part.strip().strip("'\"")
        if name:
            fonts.append(name)
    return fonts


@cache
def _resolve_font_family(font_family: str, font_style: skia.FontStyle) -> skia.Typeface:
    """Resolve CSS-style font stack to the first available Skia Typeface."""
    fm = skia.FontMgr()

    # Parse font stack and try each font
    for name in _parse_font_stack(font_family):
        # Skip generic family names that Skia doesn't understand
        if name in ("sans-serif", "serif", "monospace", "cursive", "fantasy"):
            continue
        typeface = fm.matchFamilyStyle(name, font_style)
        if typeface is not None:
            return typeface

    # Fallback to system default
    return fm.matchFamilyStyle("", font_style)


@cache
def _get_font_face(font_family: str, font_style: skia.FontStyle) -> skia.Typeface:
    if font_family == "":
        font_family = core.App.get_default_font_family()

    # Try to resolve CSS-style font stack
    typeface = _resolve_font_family(font_family, font_style)
    if typeface is not None:
        return typeface

    # Final fallback
    return skia.Typeface(font_family, font_style)


@cache
def _to_skia_font(font: core.Font) -> skia.Font:
    if font.weight is FontWeight.NORMAL:
        font_weight = skia.FontStyle.kNormal_Weight
    else:
        font_weight = skia.FontStyle.kBold_Weight

    if font.slant is FontSlant.UPRIGHT:
        font_slant = skia.FontStyle.kUpright_Slant
    else:
        font_slant = skia.FontStyle.kItalic_Slant

    font_style = skia.FontStyle(font_weight, skia.FontStyle.kNormal_Width, font_slant)
    return skia.Font(_get_font_face(font.family, font_style), font.size)


class Painter:
    def __init__(self, frame: core.Frame, surface: skia.Surface):
        self._frame = frame
        self._surface = surface
        self._canvas = surface.getCanvas()
        self._style: Optional[core.Style] = None
        self._style_stack = []

    def clear_all(self, color: Optional[str] = None) -> None:
        if color is not None:
            self._canvas.clear(_to_skia_color(color))
        self._frame.clear()

    def fill_rect(self, rect: core.Rect) -> None:
        style = cast(core.Style, self._style)

        # Draw shadow first (behind the shape)
        if style.shadow is not None:
            self._draw_shadow(rect, style.shadow, style.border_radius)

        paint = skia.Paint(
            Color=_to_skia_color(style.fill.color),
            Style=skia.Paint.kFill_Style,
            AntiAlias=style.border_radius > 0,
        )
        sr = _to_skia_rect(rect)

        if style.border_radius > 0:
            rrect = skia.RRect.MakeRectXY(sr, style.border_radius, style.border_radius)
            self._canvas.drawRRect(rrect, paint)
        else:
            self._canvas.drawRect(sr, paint)

    def stroke_rect(self, rect: core.Rect) -> None:
        style = cast(core.Style, self._style)
        stroke_width = style.line.width
        paint = skia.Paint(
            Color=_to_skia_color(style.stroke.color),
            Style=skia.Paint.kStroke_Style,
            AntiAlias=style.border_radius > 0,
        )
        paint.setStrokeWidth(stroke_width)
        sr = _to_skia_stroke_rect(rect, stroke_width)

        if style.border_radius > 0:
            rrect = skia.RRect.MakeRectXY(sr, style.border_radius, style.border_radius)
            self._canvas.drawRRect(rrect, paint)
        else:
            self._canvas.drawRect(sr, paint)

    def _draw_shadow(
        self, rect: core.Rect, shadow: Shadow, border_radius: float = 0.0
    ) -> None:
        """Draw a drop shadow behind a rectangle."""
        paint = skia.Paint(
            Color=_to_skia_color_with_alpha(shadow.color),
            Style=skia.Paint.kFill_Style,
            AntiAlias=True,
        )
        paint.setMaskFilter(
            skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, shadow.blur_radius / 2)
        )

        # Offset rectangle for shadow
        shadow_rect = skia.Rect.MakeXYWH(
            rect.origin.x + shadow.offset_x,
            rect.origin.y + shadow.offset_y,
            rect.size.width - 1,
            rect.size.height - 1,
        )

        if border_radius > 0:
            rrect = skia.RRect.MakeRectXY(shadow_rect, border_radius, border_radius)
            self._canvas.drawRRect(rrect, paint)
        else:
            self._canvas.drawRect(shadow_rect, paint)

    def fill_circle(self, circle: core.Circle) -> None:
        style = cast(core.Style, self._style)
        paint = skia.Paint(
            Color=_to_skia_color(style.fill.color),
            Style=skia.Paint.kFill_Style,
            AntiAlias=True,
        )
        c = circle.center
        self._canvas.drawCircle(c.x, c.y, circle.radius, paint)

    def stroke_circle(self, circle: core.Circle) -> None:
        style = cast(core.Style, self._style)
        paint = skia.Paint(
            Color=_to_skia_color(style.stroke.color),
            Style=skia.Paint.kStroke_Style,
            AntiAlias=True,
        )
        c = circle.center
        self._canvas.drawCircle(c.x, c.y, circle.radius, paint)

    def measure_text(self, text: str) -> float:
        style = cast(core.Style, self._style)
        font = _to_skia_font(style.font)

        primary_typeface = font.getTypeface()
        if primary_typeface is None:
            return font.measureText(text)

        font_style = primary_typeface.fontStyle()
        font_size = font.getSize()

        segments = segment_text_by_font(text, primary_typeface, font_style)

        total_width = 0.0
        for segment_text, typeface in segments:
            segment_font = skia.Font(typeface, font_size)
            total_width += segment_font.measureText(segment_text)

        return total_width

    def get_font_metrics(self) -> core.FontMetrics:
        style = cast(core.Style, self._style)
        font = _to_skia_font(style.font)
        return core.FontMetrics(cap_height=font.getMetrics().fCapHeight)

    def translate(self, pos: core.Point) -> None:
        self._canvas.translate(pos.x, pos.y)

    def clip(self, rect: core.Rect) -> None:
        self._canvas.clipRect(
            _to_skia_rect(
                core.Rect(
                    origin=core.Point(x=0, y=0),
                    size=core.Size(
                        width=rect.size.width + 1, height=rect.size.height + 1
                    ),
                )
            )
        )

    def fill_text(self, text: str, pos: core.Point, max_width: Optional[float]) -> None:
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

        paint = skia.Paint(
            Style=skia.Paint.kFill_Style,
            Color=color,
        )

        primary_typeface = font.getTypeface()
        if primary_typeface is None:
            # No primary typeface, render without fallback
            blob = skia.TextBlob(text, font)
            self._canvas.drawTextBlob(blob, pos.x, pos.y, paint)
            return

        font_style = primary_typeface.fontStyle()
        font_size = font.getSize()

        # Segment text by font availability
        segments = segment_text_by_font(text, primary_typeface, font_style)

        # Render each segment with its appropriate font
        x_offset = 0.0
        for segment_text, typeface in segments:
            segment_font = skia.Font(typeface, font_size)
            blob = skia.TextBlob(segment_text, segment_font)
            self._canvas.drawTextBlob(blob, pos.x + x_offset, pos.y, paint)
            x_offset += segment_font.measureText(segment_text)

    def stroke_text(
        self, text: str, pos: core.Point, max_width: Optional[float]
    ) -> None: ...

    def draw_image(
        self, file_path: str, rect: core.Rect, use_cache: bool = True
    ) -> None:
        if use_cache:
            image = _get_cached_image(file_path)
        else:
            image = skia.Image.open(file_path)
        self._canvas.drawImageRect(image, _to_skia_rect(rect))

    def measure_image(self, file_path: str, use_cache: bool = True) -> core.Size:
        if use_cache:
            image = _get_cached_image(file_path)
        else:
            image = skia.Image.open(file_path)
        return core.Size(width=image.width(), height=image.height())

    def draw_net_image(self, url: str, rect: core.Rect, use_cache: bool = True) -> None:
        if use_cache:
            image = _get_cached_net_image(url)
        else:
            image = _get_net_image(url)
        self._canvas.drawImageRect(image, _to_skia_rect(rect))

    def measure_net_image(self, url: str, use_cache: bool = True) -> core.Size:
        if use_cache:
            image = _get_cached_net_image(url)
        else:
            image = _get_net_image(url)
        return core.Size(width=image.width(), height=image.height())

    def measure_np_array_as_an_image(self, array: np.ndarray) -> core.Size:
        height, width, _ = array.shape
        return core.Size(width=width, height=height)

    def get_net_image_async(self, name: str, url: str, callback) -> None:
        raise NotImplementedError()

    def draw_image_object(self, img, x: float, y: float) -> None:
        self._canvas.drawImage(img, x, y)

    def draw_np_array_as_an_image(self, array: np.ndarray, x: float, y: float) -> None:
        image = skia.Image.fromarray(array)
        self.draw_image_object(image, x, y)

    def draw_np_array_as_an_image_rect(
        self, array: np.ndarray, rect: core.Rect
    ) -> None:
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
