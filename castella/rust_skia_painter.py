"""Adapter layer for castella-skia that maintains skia_painter.py interface.

This module wraps the Rust-based castella-skia renderer with the same API
as the original skia_painter.py, allowing seamless integration with existing
Frame implementations.
"""

import tempfile
import urllib.request
from typing import TYPE_CHECKING, Any, Optional, cast

import castella_skia

from castella import core
from castella.models.font import FontMetrics

if TYPE_CHECKING:
    import numpy as np


# Cache for network images - stores temp file paths
_net_image_cache: dict[str, str] = {}


def _fetch_and_save_net_image(url: str) -> str:
    """Fetch image from URL and save to temp file, return path."""
    image_bytes = urllib.request.urlopen(url).read()
    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as f:
        f.write(image_bytes)
        return f.name


def _get_cached_net_image_path(url: str) -> str:
    """Get cached temp file path for a network image URL."""
    if url not in _net_image_cache:
        _net_image_cache[url] = _fetch_and_save_net_image(url)
    return _net_image_cache[url]


class Painter:
    """Wraps castella-skia.SkiaPainter with Castella model objects.

    This adapter converts between Castella's model objects (Rect, Circle, Point, Style)
    and castella-skia's float-based API.
    """

    def __init__(self, frame: "core.Frame", surface: castella_skia.Surface):
        self._frame = frame
        self._surface = surface
        self._painter = castella_skia.SkiaPainter(surface)
        self._style: Optional[core.Style] = None
        self._style_stack: list[Optional[core.Style]] = []
        # Track last applied style key (fill_color, stroke_color, stroke_width, font_family, font_size, border_radius)
        self._applied_style_key: Optional[tuple] = None

    def clear_all(self, color: Optional[str] = None) -> None:
        """Clear the entire drawing surface."""
        if color is not None:
            # Set a temporary style with the clear color
            temp_style = castella_skia.Style(fill_color=color)
            self._painter.style(temp_style)
        self._painter.clear_all()

    def fill_rect(self, rect: core.Rect) -> None:
        """Fill a rectangle with the current fill style."""
        # Apply style before drawing (includes shadow if present)
        self._apply_style()

        # Convert Rect to float parameters
        # Note: skia_painter uses width-1, height-1 for inclusive bounds
        self._painter.fill_rect(
            rect.origin.x,
            rect.origin.y,
            rect.size.width - 1,
            rect.size.height - 1,
        )

    def stroke_rect(self, rect: core.Rect) -> None:
        """Stroke a rectangle outline with the current stroke style."""
        style = cast(core.Style, self._style)
        stroke_width = style.line.width if style.line else 1.0

        self._apply_style()

        # Inset rect for stroke (like _to_skia_stroke_rect)
        self._painter.stroke_rect(
            rect.origin.x + stroke_width,
            rect.origin.y + stroke_width,
            rect.size.width - 2 * stroke_width - 1,
            rect.size.height - 2 * stroke_width - 1,
        )

    def fill_circle(self, circle: core.Circle) -> None:
        """Fill a circle with the current fill style."""
        self._apply_style()
        self._painter.fill_circle(
            circle.center.x,
            circle.center.y,
            circle.radius,
        )

    def stroke_circle(self, circle: core.Circle) -> None:
        """Stroke a circle outline with the current stroke style."""
        self._apply_style()
        self._painter.stroke_circle(
            circle.center.x,
            circle.center.y,
            circle.radius,
        )

    def measure_text(self, text: str) -> float:
        """Measure the width of text with the current font."""
        self._apply_style()
        return self._painter.measure_text(text)

    def get_font_metrics(self) -> FontMetrics:
        """Get metrics for the current font."""
        self._apply_style()
        rs_metrics = self._painter.get_font_metrics()
        # FontMetrics in Castella only has cap_height
        # We approximate it from the Rust-side ascent
        return FontMetrics(cap_height=rs_metrics.ascent * 0.7)

    def translate(self, pos: core.Point) -> None:
        """Translate the canvas origin."""
        self._painter.translate(pos.x, pos.y)

    def scale(self, sx: float, sy: float) -> None:
        """Scale the canvas."""
        self._painter.scale(sx, sy)

    def clip(self, rect: core.Rect) -> None:
        """Set the clipping region."""
        # Like skia_painter, we clip to origin (0,0) with the given size
        self._painter.clip(
            0,
            0,
            rect.size.width,
            rect.size.height,
        )

    def fill_text(self, text: str, pos: core.Point, max_width: Optional[float]) -> None:
        """Draw filled text at the given position."""
        if text == "":
            return
        self._apply_style()
        self._painter.fill_text(text, pos.x, pos.y, max_width)

    def stroke_text(
        self, text: str, pos: core.Point, max_width: Optional[float]
    ) -> None:
        """Draw stroked text at the given position (not implemented)."""
        # Same as original - not implemented
        pass

    def draw_image(
        self, file_path: str, rect: core.Rect, use_cache: bool = True
    ) -> None:
        """Draw an image from a local file."""
        # Note: Don't subtract 1 from image dimensions - images should be drawn
        # at their exact size to avoid scaling artifacts
        self._painter.draw_image(
            file_path,
            rect.origin.x,
            rect.origin.y,
            rect.size.width,
            rect.size.height,
            use_cache,
        )

    def measure_image(self, file_path: str, use_cache: bool = True) -> core.Size:
        """Measure the size of an image from a local file."""
        width, height = self._painter.measure_image(file_path, use_cache)
        return core.Size(width=width, height=height)

    def draw_net_image(self, url: str, rect: core.Rect, use_cache: bool = True) -> None:
        """Draw an image from a network URL.

        Note: This uses Python-side network fetching for now.
        """
        if use_cache:
            temp_path = _get_cached_net_image_path(url)
        else:
            temp_path = _fetch_and_save_net_image(url)
        self.draw_image(temp_path, rect, use_cache=use_cache)

    def measure_net_image(self, url: str, use_cache: bool = True) -> core.Size:
        """Measure the size of an image from a network URL."""
        if use_cache:
            temp_path = _get_cached_net_image_path(url)
        else:
            temp_path = _fetch_and_save_net_image(url)
        return self.measure_image(temp_path, use_cache=use_cache)

    def measure_np_array_as_an_image(self, array: "np.ndarray") -> core.Size:
        """Measure the size of a numpy array as an image."""
        height, width = array.shape[:2]
        return core.Size(width=width, height=height)

    def get_net_image_async(self, name: str, url: str, callback: Any) -> None:
        """Fetch an image from a network URL asynchronously (not implemented)."""
        raise NotImplementedError()

    # NOTE: The following methods are intentionally NOT implemented to allow
    # hasattr() checks to return False, enabling graceful fallbacks:
    # - draw_image_object
    # - draw_np_array_as_an_image
    # - draw_np_array_as_an_image_rect
    # - get_numpy_image_async

    def save(self) -> None:
        """Save the current canvas state."""
        self._painter.save()
        self._style_stack.append((self._style, self._applied_style_key))

    def restore(self) -> None:
        """Restore the previously saved canvas state."""
        self._painter.restore()
        if self._style_stack:
            self._style, self._applied_style_key = self._style_stack.pop()

    def style(self, style: core.Style) -> None:
        """Set the current drawing style."""
        self._style = style

    def flush(self) -> None:
        """Flush pending drawing operations."""
        self._painter.flush()
        self._surface.flush_and_submit()
        # Only call frame.flush() for desktop frames (GLFW/SDL)
        # iOS frame's flush() calls painter.flush() which would cause recursion
        frame_class_name = self._frame.__class__.__name__
        if frame_class_name not in ("iOSFrame",):
            self._frame.flush()

    def _apply_style(self) -> None:
        """Convert and apply the current Castella style to castella-skia."""
        if self._style is None:
            return

        style = self._style

        # Extract style key for comparison
        fill_color = style.fill.color if style.fill else None
        stroke_color = style.stroke.color if style.stroke else None
        stroke_width = style.line.width if style.line else 1.0
        font_family = style.font.family if style.font else None
        font_size = style.font.size if style.font else 14.0
        border_radius = style.border_radius

        # Extract shadow properties for cache key
        shadow = style.shadow
        shadow_key = None
        if shadow is not None:
            shadow_key = (
                shadow.color,
                shadow.offset_x,
                shadow.offset_y,
                shadow.blur_radius,
            )

        style_key = (
            fill_color,
            stroke_color,
            stroke_width,
            font_family,
            font_size,
            border_radius,
            shadow_key,
        )

        # Skip if style hasn't changed
        if style_key == self._applied_style_key:
            return

        self._applied_style_key = style_key

        # Convert Castella Shadow to castella_skia.Shadow if present
        rs_shadow = None
        if shadow is not None:
            rs_shadow = castella_skia.Shadow(
                color=shadow.color,
                offset_x=shadow.offset_x,
                offset_y=shadow.offset_y,
                blur_radius=shadow.blur_radius,
            )

        # Build castella_skia.Style from Castella Style
        rs_style = castella_skia.Style(
            fill_color=fill_color,
            stroke_color=stroke_color,
            stroke_width=stroke_width,
            font_family=font_family,
            font_size=font_size,
            border_radius=border_radius,
            shadow=rs_shadow,
        )
        self._painter.style(rs_style)
