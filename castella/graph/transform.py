"""Canvas transformation for zoom and pan operations."""

from __future__ import annotations

from pydantic import BaseModel, Field

from castella.models.geometry import Point, Size


class CanvasTransform(BaseModel):
    """Zoom and pan state for graph canvas.

    Handles coordinate transformations between screen space and
    canvas (graph) space, supporting zoom and pan operations.

    Attributes:
        scale: Zoom level (1.0 = 100%, range 0.1 to 4.0).
        offset: Pan offset in screen coordinates.
    """

    scale: float = 1.0
    offset: Point = Field(default_factory=lambda: Point(x=0, y=0))

    # Zoom constraints
    MIN_SCALE: float = 0.1
    MAX_SCALE: float = 4.0

    def screen_to_canvas(self, screen_point: Point) -> Point:
        """Convert screen coordinates to canvas coordinates.

        Args:
            screen_point: Point in screen space.

        Returns:
            Point in canvas space.
        """
        return Point(
            x=(screen_point.x - self.offset.x) / self.scale,
            y=(screen_point.y - self.offset.y) / self.scale,
        )

    def canvas_to_screen(self, canvas_point: Point) -> Point:
        """Convert canvas coordinates to screen coordinates.

        Args:
            canvas_point: Point in canvas space.

        Returns:
            Point in screen space.
        """
        return Point(
            x=canvas_point.x * self.scale + self.offset.x,
            y=canvas_point.y * self.scale + self.offset.y,
        )

    def zoom(self, factor: float, center: Point) -> None:
        """Zoom around a center point.

        Maintains the position of the center point on screen
        while changing the zoom level.

        Args:
            factor: Zoom factor (>1 to zoom in, <1 to zoom out).
            center: Point to zoom around in screen coordinates.
        """
        old_scale = self.scale
        new_scale = max(self.MIN_SCALE, min(self.MAX_SCALE, self.scale * factor))

        if new_scale == old_scale:
            return

        # Adjust offset to keep center point fixed
        scale_change = new_scale / old_scale
        self.offset.x = center.x - (center.x - self.offset.x) * scale_change
        self.offset.y = center.y - (center.y - self.offset.y) * scale_change
        self.scale = new_scale

    def pan(self, delta: Point) -> None:
        """Pan by a screen-space delta.

        Args:
            delta: Movement delta in screen coordinates.
        """
        self.offset.x += delta.x
        self.offset.y += delta.y

    def reset(self) -> None:
        """Reset transform to default (no zoom, no pan)."""
        self.scale = 1.0
        self.offset.x = 0
        self.offset.y = 0

    def fit_to_bounds(
        self, content_bounds: tuple[float, float, float, float], canvas_size: Size
    ) -> None:
        """Fit the view to show all content.

        Calculates appropriate zoom and offset to fit all content
        within the canvas with padding.

        Args:
            content_bounds: (min_x, min_y, max_x, max_y) of content.
            canvas_size: Size of the canvas.
        """
        min_x, min_y, max_x, max_y = content_bounds
        content_width = max_x - min_x
        content_height = max_y - min_y

        if content_width <= 0 or content_height <= 0:
            self.reset()
            return

        # Calculate scale to fit content with padding
        padding = 50
        available_width = canvas_size.width - 2 * padding
        available_height = canvas_size.height - 2 * padding

        if available_width <= 0 or available_height <= 0:
            self.reset()
            return

        scale_x = available_width / content_width
        scale_y = available_height / content_height
        self.scale = max(self.MIN_SCALE, min(self.MAX_SCALE, min(scale_x, scale_y)))

        # Center content
        scaled_width = content_width * self.scale
        scaled_height = content_height * self.scale
        self.offset.x = (canvas_size.width - scaled_width) / 2 - min_x * self.scale
        self.offset.y = (canvas_size.height - scaled_height) / 2 - min_y * self.scale

    @property
    def zoom_percent(self) -> int:
        """Get zoom level as percentage."""
        return int(self.scale * 100)
