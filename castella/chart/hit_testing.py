"""Hit testing utilities for interactive charts."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from castella.models.geometry import Point, Rect


@runtime_checkable
class HitTestable(Protocol):
    """Protocol for elements that can be hit-tested."""

    series_index: int
    data_index: int
    value: float
    label: str

    def contains(self, point: Point) -> bool:
        """Check if the point is within this element."""
        ...


@dataclass(slots=True)
class RectElement:
    """A rectangular hit test region (for bars).

    Attributes:
        rect: The bounding rectangle.
        series_index: Index of the series this element belongs to.
        data_index: Index of the data point within the series.
        value: The value at this data point.
        label: Display label for this element.
    """

    rect: Rect
    series_index: int
    data_index: int
    value: float
    label: str

    def contains(self, point: Point) -> bool:
        """Check if the point is within this rectangle."""
        return self.rect.contain(point)

    @property
    def center(self) -> Point:
        """Get the center point of this element."""
        return self.rect.center


@dataclass(slots=True)
class CircleElement:
    """A circular hit test region (for line chart points, scatter plots).

    Attributes:
        center: Center point of the circle.
        radius: Radius of the circle.
        series_index: Index of the series this element belongs to.
        data_index: Index of the data point within the series.
        value: The value at this data point.
        label: Display label for this element.
    """

    center: Point
    radius: float
    series_index: int
    data_index: int
    value: float
    label: str

    def contains(self, point: Point) -> bool:
        """Check if the point is within this circle."""
        return self.center.distance_to(point) <= self.radius

    @property
    def top(self) -> Point:
        """Get the top point (for tooltip positioning)."""
        return Point(x=self.center.x, y=self.center.y - self.radius)


@dataclass(slots=True)
class ArcElement:
    """An arc/sector hit test region (for pie chart slices).

    Attributes:
        center: Center point of the arc.
        inner_radius: Inner radius (0 for pie, >0 for donut).
        outer_radius: Outer radius.
        start_angle: Starting angle in radians.
        end_angle: Ending angle in radians.
        series_index: Index of the series this element belongs to.
        data_index: Index of the data point within the series.
        value: The value at this data point.
        label: Display label for this element.
    """

    center: Point
    inner_radius: float
    outer_radius: float
    start_angle: float
    end_angle: float
    series_index: int
    data_index: int
    value: float
    label: str

    def contains(self, point: Point) -> bool:
        """Check if the point is within this arc/sector."""
        # Check radius
        dist = self.center.distance_to(point)
        if dist < self.inner_radius or dist > self.outer_radius:
            return False

        # Check angle
        angle = math.atan2(point.y - self.center.y, point.x - self.center.x)

        # Normalize all angles to 0 to 2*pi range
        def normalize(a: float) -> float:
            while a < 0:
                a += 2 * math.pi
            while a >= 2 * math.pi:
                a -= 2 * math.pi
            return a

        angle = normalize(angle)
        start = normalize(self.start_angle)
        end = normalize(self.end_angle)

        # For pie charts, the arc always goes counter-clockwise from start to end
        # Calculate the angular span from start to end (counter-clockwise)
        ccw_span = (end - start) % (2 * math.pi)

        # Handle full circle case
        if ccw_span < 0.001:
            ccw_span = 2 * math.pi

        # Angular distance from start to the point (counter-clockwise)
        ccw_to_angle = (angle - start) % (2 * math.pi)

        return ccw_to_angle <= ccw_span

    @property
    def centroid(self) -> Point:
        """Get the centroid point (for tooltip positioning)."""
        mid_angle = (self.start_angle + self.end_angle) / 2
        mid_radius = (self.inner_radius + self.outer_radius) / 2
        return Point(
            x=self.center.x + mid_radius * math.cos(mid_angle),
            y=self.center.y + mid_radius * math.sin(mid_angle),
        )


@dataclass(slots=True)
class LineSegmentElement:
    """A line segment with thickness for hit testing.

    Attributes:
        start: Start point of the line.
        end: End point of the line.
        thickness: Hit testing thickness (pixels).
        series_index: Index of the series this element belongs to.
        segment_index: Index of this segment within the series.
        value: Representative value (e.g., average of endpoints).
        label: Display label for this element.
    """

    start: Point
    end: Point
    thickness: float
    series_index: int
    segment_index: int
    value: float
    label: str

    # For protocol compliance
    @property
    def data_index(self) -> int:
        """Alias for segment_index for protocol compliance."""
        return self.segment_index

    def contains(self, point: Point) -> bool:
        """Check if the point is within thickness distance of this line segment."""
        dx = self.end.x - self.start.x
        dy = self.end.y - self.start.y
        length_sq = dx * dx + dy * dy

        if length_sq == 0:
            # Degenerate case: start == end
            return self.start.distance_to(point) <= self.thickness

        # Project point onto line and clamp to segment
        t = max(
            0,
            min(
                1,
                ((point.x - self.start.x) * dx + (point.y - self.start.y) * dy)
                / length_sq,
            ),
        )

        # Closest point on segment
        closest = Point(
            x=self.start.x + t * dx,
            y=self.start.y + t * dy,
        )

        return closest.distance_to(point) <= self.thickness

    @property
    def center(self) -> Point:
        """Get the center point of this segment."""
        return Point(
            x=(self.start.x + self.end.x) / 2,
            y=(self.start.y + self.end.y) / 2,
        )


@dataclass(slots=True)
class LegendItemElement:
    """A legend item for hit testing.

    Attributes:
        rect: The bounding rectangle of the legend item.
        series_index: Index of the series this legend item represents.
        data_index: Index of the data point (for PieChart, -1 for others).
        series_name: Name of the series or data point.
    """

    rect: Rect
    series_index: int
    data_index: int
    series_name: str

    def contains(self, point: Point) -> bool:
        """Check if the point is within this legend item."""
        return self.rect.contain(point)

    @property
    def value(self) -> float:
        """Dummy value for protocol compliance."""
        return 0.0

    @property
    def label(self) -> str:
        """Return series name as label."""
        return self.series_name


def hit_test(
    elements: list[HitTestable],
    point: Point,
) -> HitTestable | None:
    """Find the first element containing the point.

    Elements are tested in reverse order so that elements drawn last
    (on top) are hit first.

    Args:
        elements: List of hit-testable elements.
        point: The point to test.

    Returns:
        The first element containing the point, or None if no hit.
    """
    for element in reversed(elements):
        if element.contains(point):
            return element
    return None


def hit_test_all(
    elements: list[HitTestable],
    point: Point,
) -> list[HitTestable]:
    """Find all elements containing the point.

    Args:
        elements: List of hit-testable elements.
        point: The point to test.

    Returns:
        List of all elements containing the point, in reverse order.
    """
    return [e for e in reversed(elements) if e.contains(point)]
