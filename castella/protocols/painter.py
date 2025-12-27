"""Painter protocol definitions - split into required core and optional capabilities."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

if TYPE_CHECKING:
    try:
        import numpy as np
    except ImportError:
        pass

from castella.models.geometry import Circle, Point, Rect, Size
from castella.models.font import FontMetrics
from castella.models.style import Style


@runtime_checkable
class BasePainter(Protocol):
    """Core painter protocol - all painters MUST implement these."""

    def clear_all(self) -> None:
        """Clear the entire drawing surface."""
        ...

    def fill_rect(self, rect: Rect) -> None:
        """Fill a rectangle with the current fill style."""
        ...

    def stroke_rect(self, rect: Rect) -> None:
        """Stroke a rectangle outline with the current stroke style."""
        ...

    def translate(self, pos: Point) -> None:
        """Translate the canvas origin."""
        ...

    def clip(self, rect: Rect) -> None:
        """Set the clipping region."""
        ...

    def fill_text(self, text: str, pos: Point, max_width: float | None) -> None:
        """Draw filled text at the given position."""
        ...

    def stroke_text(self, text: str, pos: Point, max_width: float | None) -> None:
        """Draw stroked text at the given position."""
        ...

    def measure_text(self, text: str) -> float:
        """Measure the width of text with the current font."""
        ...

    def get_font_metrics(self) -> FontMetrics:
        """Get metrics for the current font."""
        ...

    def save(self) -> None:
        """Save the current canvas state."""
        ...

    def restore(self) -> None:
        """Restore the previously saved canvas state."""
        ...

    def style(self, style: Style) -> None:
        """Set the current drawing style."""
        ...

    def flush(self) -> None:
        """Flush pending drawing operations."""
        ...


@runtime_checkable
class CircleCapable(Protocol):
    """Optional: Circle drawing capability."""

    def fill_circle(self, circle: Circle) -> None:
        """Fill a circle with the current fill style."""
        ...

    def stroke_circle(self, circle: Circle) -> None:
        """Stroke a circle outline with the current stroke style."""
        ...


@runtime_checkable
class LocalImageCapable(Protocol):
    """Optional: Local file image capability."""

    def draw_image(self, file_path: str, rect: Rect, use_cache: bool = True) -> None:
        """Draw an image from a local file."""
        ...

    def measure_image(self, file_path: str, use_cache: bool = True) -> Size:
        """Measure the size of an image from a local file."""
        ...


@runtime_checkable
class SyncNetworkImageCapable(Protocol):
    """Optional: Synchronous network image capability."""

    def draw_net_image(self, url: str, rect: Rect, use_cache: bool = True) -> None:
        """Draw an image from a network URL (synchronously)."""
        ...

    def measure_net_image(self, url: str, use_cache: bool = True) -> Size:
        """Measure the size of an image from a network URL (synchronously)."""
        ...


@runtime_checkable
class AsyncNetworkImageCapable(Protocol):
    """Optional: Asynchronous network image capability."""

    def get_net_image_async(self, name: str, url: str, callback: Any) -> None:
        """Fetch an image from a network URL asynchronously."""
        ...

    def draw_image_object(self, img: Any, x: float, y: float) -> None:
        """Draw a pre-loaded image object."""
        ...


@runtime_checkable
class NumpyImageCapable(Protocol):
    """Optional: Numpy array as image capability."""

    def measure_np_array_as_an_image(self, array: "np.ndarray") -> Size:
        """Measure the size of a numpy array as an image."""
        ...

    def draw_np_array_as_an_image(
        self, array: "np.ndarray", x: float, y: float
    ) -> None:
        """Draw a numpy array as an image at the given position."""
        ...

    def draw_np_array_as_an_image_rect(self, array: "np.ndarray", rect: Rect) -> None:
        """Draw a numpy array as an image within a rectangle."""
        ...


@runtime_checkable
class AsyncNumpyImageCapable(Protocol):
    """Optional: Async numpy image capability (for web)."""

    def get_numpy_image_async(self, array: "np.ndarray", callback: Any) -> None:
        """Convert numpy array to image asynchronously."""
        ...

    def draw_image_object(self, img: Any, x: float, y: float) -> None:
        """Draw a pre-loaded image object."""
        ...


@runtime_checkable
class CaretDrawable(Protocol):
    """Optional: Caret drawing for text input (terminal)."""

    def draw_caret(self, pos: Point, height: int) -> None:
        """Draw a text input caret."""
        ...


# Full Painter type alias for backward compatibility
# Combines all capabilities (not all painters implement all)
Painter = BasePainter
