"""Zoom/pan transformation state for interactive charts."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Self

from castella.models.geometry import Point, Size


@dataclass
class ViewBounds:
    """Represents the visible data range.

    Attributes:
        x_min: Minimum X value.
        x_max: Maximum X value.
        y_min: Minimum Y value.
        y_max: Maximum Y value.
    """

    x_min: float
    x_max: float
    y_min: float
    y_max: float

    @property
    def width(self) -> float:
        """Get the width of the bounds."""
        return self.x_max - self.x_min

    @property
    def height(self) -> float:
        """Get the height of the bounds."""
        return self.y_max - self.y_min

    @property
    def center(self) -> tuple[float, float]:
        """Get the center point of the bounds."""
        return (
            (self.x_min + self.x_max) / 2,
            (self.y_min + self.y_max) / 2,
        )

    def contains(self, x: float, y: float) -> bool:
        """Check if a point is within bounds."""
        return self.x_min <= x <= self.x_max and self.y_min <= y <= self.y_max

    def expand(self, factor: float) -> ViewBounds:
        """Create expanded bounds by a factor.

        Args:
            factor: Expansion factor (>1 to expand, <1 to shrink).

        Returns:
            New ViewBounds instance.
        """
        cx, cy = self.center
        half_w = self.width / 2 * factor
        half_h = self.height / 2 * factor
        return ViewBounds(
            x_min=cx - half_w,
            x_max=cx + half_w,
            y_min=cy - half_h,
            y_max=cy + half_h,
        )


@dataclass
class ChartTransform:
    """Manages zoom/pan transformation for charts.

    Maintains the mapping between data coordinates and screen coordinates,
    with support for zooming and panning.

    Attributes:
        data_bounds: Full data range.
        view_bounds: Currently visible range.
        screen_size: Screen size in pixels.
        min_zoom: Minimum zoom level (1.0 = full data visible).
        max_zoom: Maximum zoom level.
    """

    data_bounds: ViewBounds
    view_bounds: ViewBounds | None = None
    screen_size: Size = field(default_factory=lambda: Size(width=100, height=100))
    min_zoom: float = 1.0
    max_zoom: float = 20.0

    # Observable pattern
    _observers: list[Any] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Initialize view_bounds to data_bounds if not set."""
        if self.view_bounds is None:
            self.view_bounds = ViewBounds(
                x_min=self.data_bounds.x_min,
                x_max=self.data_bounds.x_max,
                y_min=self.data_bounds.y_min,
                y_max=self.data_bounds.y_max,
            )

    def attach(self, observer: Any) -> None:
        """Attach an observer. Duplicates are ignored."""
        if observer not in self._observers:
            self._observers.append(observer)

    def detach(self, observer: Any) -> None:
        """Detach an observer."""
        if observer in self._observers:
            self._observers.remove(observer)

    def notify(self) -> None:
        """Notify all observers of a change."""
        for observer in self._observers:
            if hasattr(observer, "on_notify"):
                observer.on_notify()

    @property
    def zoom_level(self) -> float:
        """Get current zoom level (1.0 = showing full data)."""
        if self.view_bounds is None:
            return 1.0
        data_width = self.data_bounds.width
        view_width = self.view_bounds.width
        if view_width == 0:
            return 1.0
        return data_width / view_width

    def set_screen_size(self, size: Size) -> None:
        """Update screen size for coordinate transformation.

        Args:
            size: New screen size.
        """
        self.screen_size = size

    def data_to_screen(self, data_x: float, data_y: float) -> Point:
        """Convert data coordinates to screen coordinates.

        Args:
            data_x: X coordinate in data space.
            data_y: Y coordinate in data space.

        Returns:
            Point in screen coordinates.
        """
        if self.view_bounds is None:
            return Point(x=0, y=0)

        # Normalize to 0-1 within view bounds
        if self.view_bounds.width != 0:
            norm_x = (data_x - self.view_bounds.x_min) / self.view_bounds.width
        else:
            norm_x = 0.5

        if self.view_bounds.height != 0:
            norm_y = (data_y - self.view_bounds.y_min) / self.view_bounds.height
        else:
            norm_y = 0.5

        # Convert to screen coordinates (Y is inverted)
        screen_x = norm_x * self.screen_size.width
        screen_y = (1 - norm_y) * self.screen_size.height

        return Point(x=screen_x, y=screen_y)

    def screen_to_data(self, screen_point: Point) -> tuple[float, float]:
        """Convert screen coordinates to data coordinates.

        Args:
            screen_point: Point in screen coordinates.

        Returns:
            Tuple of (data_x, data_y).
        """
        if self.view_bounds is None:
            return (0.0, 0.0)

        # Normalize screen coordinates
        if self.screen_size.width != 0:
            norm_x = screen_point.x / self.screen_size.width
        else:
            norm_x = 0.5

        if self.screen_size.height != 0:
            norm_y = 1 - (screen_point.y / self.screen_size.height)
        else:
            norm_y = 0.5

        # Convert to data coordinates
        data_x = self.view_bounds.x_min + norm_x * self.view_bounds.width
        data_y = self.view_bounds.y_min + norm_y * self.view_bounds.height

        return (data_x, data_y)

    def zoom(self, factor: float, center: Point) -> Self:
        """Zoom by factor around a screen point.

        Args:
            factor: Zoom factor (>1 to zoom in, <1 to zoom out).
            center: Screen point to zoom around.

        Returns:
            Self for chaining.
        """
        if self.view_bounds is None:
            return self

        new_zoom = self.zoom_level * factor
        new_zoom = max(self.min_zoom, min(self.max_zoom, new_zoom))

        if new_zoom == self.zoom_level:
            return self

        # Get data point at zoom center
        data_center = self.screen_to_data(center)

        # Calculate new view bounds
        new_width = self.data_bounds.width / new_zoom
        new_height = self.data_bounds.height / new_zoom

        # Keep the data point under the cursor in the same screen position
        # Calculate what fraction of the view the cursor is at
        if self.screen_size.width != 0:
            frac_x = center.x / self.screen_size.width
        else:
            frac_x = 0.5

        if self.screen_size.height != 0:
            frac_y = 1 - (center.y / self.screen_size.height)
        else:
            frac_y = 0.5

        # New view bounds centered on the data point
        self.view_bounds = ViewBounds(
            x_min=data_center[0] - new_width * frac_x,
            x_max=data_center[0] + new_width * (1 - frac_x),
            y_min=data_center[1] - new_height * frac_y,
            y_max=data_center[1] + new_height * (1 - frac_y),
        )

        self._clamp_view_bounds()
        self.notify()
        return self

    def pan(self, screen_delta: Point) -> Self:
        """Pan by screen coordinates delta.

        Args:
            screen_delta: Movement in screen coordinates.

        Returns:
            Self for chaining.
        """
        if self.view_bounds is None:
            return self

        # Convert screen delta to data delta
        if self.screen_size.width != 0:
            data_dx = (screen_delta.x / self.screen_size.width) * self.view_bounds.width
        else:
            data_dx = 0

        if self.screen_size.height != 0:
            # Invert Y because screen Y goes down
            data_dy = (
                -(screen_delta.y / self.screen_size.height) * self.view_bounds.height
            )
        else:
            data_dy = 0

        self.view_bounds = ViewBounds(
            x_min=self.view_bounds.x_min - data_dx,
            x_max=self.view_bounds.x_max - data_dx,
            y_min=self.view_bounds.y_min - data_dy,
            y_max=self.view_bounds.y_max - data_dy,
        )

        self._clamp_view_bounds()
        self.notify()
        return self

    def reset(self) -> Self:
        """Reset to initial full view.

        Returns:
            Self for chaining.
        """
        self.view_bounds = ViewBounds(
            x_min=self.data_bounds.x_min,
            x_max=self.data_bounds.x_max,
            y_min=self.data_bounds.y_min,
            y_max=self.data_bounds.y_max,
        )
        self.notify()
        return self

    def _clamp_view_bounds(self) -> None:
        """Ensure view bounds don't exceed data bounds."""
        if self.view_bounds is None:
            return

        # Clamp width/height to data bounds
        view_w = min(self.view_bounds.width, self.data_bounds.width)
        view_h = min(self.view_bounds.height, self.data_bounds.height)

        # Clamp position
        x_min = max(
            self.data_bounds.x_min,
            min(self.data_bounds.x_max - view_w, self.view_bounds.x_min),
        )
        y_min = max(
            self.data_bounds.y_min,
            min(self.data_bounds.y_max - view_h, self.view_bounds.y_min),
        )

        self.view_bounds = ViewBounds(
            x_min=x_min,
            x_max=x_min + view_w,
            y_min=y_min,
            y_max=y_min + view_h,
        )

    def update_data_bounds(self, new_bounds: ViewBounds) -> Self:
        """Update data bounds (e.g., when data changes).

        Args:
            new_bounds: New data bounds.

        Returns:
            Self for chaining.
        """
        self.data_bounds = new_bounds
        if self.view_bounds is not None:
            self._clamp_view_bounds()
        else:
            self.view_bounds = ViewBounds(
                x_min=new_bounds.x_min,
                x_max=new_bounds.x_max,
                y_min=new_bounds.y_min,
                y_max=new_bounds.y_max,
            )
        self.notify()
        return self
