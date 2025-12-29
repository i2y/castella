"""Polar scale for pie/donut/gauge charts."""

from __future__ import annotations

import math
from dataclasses import dataclass

from castella.models.geometry import Point


@dataclass
class PolarScale:
    """Maps values to angles and radii for polar charts.

    Used for pie charts, donut charts, and gauges where data is
    represented as angles around a center point.

    Attributes:
        center: Center point of the polar coordinate system.
        inner_radius: Inner radius (for donut charts, 0 for pie).
        outer_radius: Outer radius.
        start_angle: Starting angle in radians (-pi/2 = top/12 o'clock).
        end_angle: Ending angle in radians (3*pi/2 = top after full circle).
    """

    center: Point
    inner_radius: float = 0.0
    outer_radius: float = 100.0
    start_angle: float = -math.pi / 2  # Start at top (12 o'clock)
    end_angle: float = 3 * math.pi / 2  # Full circle back to top

    @property
    def angle_span(self) -> float:
        """Get the total angle span in radians."""
        return self.end_angle - self.start_angle

    def value_to_angle(self, value: float, total: float) -> float:
        """Convert a value to an angle based on proportion of total.

        Args:
            value: The value to convert.
            total: The total of all values.

        Returns:
            The angle in radians.
        """
        if total == 0:
            return self.start_angle
        return self.start_angle + (value / total) * self.angle_span

    def percentage_to_angle(self, percentage: float) -> float:
        """Convert a percentage (0-1) to an angle.

        Args:
            percentage: Value between 0 and 1.

        Returns:
            The angle in radians.
        """
        return self.start_angle + percentage * self.angle_span

    def point_at_angle(self, angle: float, radius: float) -> Point:
        """Get a point at the given angle and radius from center.

        Args:
            angle: Angle in radians (0 = right, counter-clockwise positive).
            radius: Distance from center.

        Returns:
            The Point at this position.
        """
        return Point(
            x=self.center.x + radius * math.cos(angle),
            y=self.center.y + radius * math.sin(angle),
        )

    def arc_points(
        self,
        start_angle: float,
        end_angle: float,
        radius: float,
        num_points: int | None = None,
    ) -> list[Point]:
        """Generate points along an arc.

        Args:
            start_angle: Starting angle in radians.
            end_angle: Ending angle in radians.
            radius: Radius of the arc.
            num_points: Number of points to generate (default: based on arc length).

        Returns:
            List of Points along the arc.
        """
        angle_span = abs(end_angle - start_angle)

        # Default: approximately one point per 5 degrees
        if num_points is None:
            num_points = max(2, int(angle_span * 180 / math.pi / 5))

        points: list[Point] = []
        for i in range(num_points + 1):
            t = i / num_points
            angle = start_angle + t * (end_angle - start_angle)
            points.append(self.point_at_angle(angle, radius))

        return points

    def slice_path(
        self,
        start_angle: float,
        end_angle: float,
        include_center: bool = True,
    ) -> list[Point]:
        """Generate points for a pie slice path.

        Args:
            start_angle: Starting angle in radians.
            end_angle: Ending angle in radians.
            include_center: Whether to include center point (for pie, not donut).

        Returns:
            List of Points forming the slice path (closed).
        """
        points: list[Point] = []

        if self.inner_radius > 0:
            # Donut slice: outer arc, then inner arc (reverse)
            points.extend(self.arc_points(start_angle, end_angle, self.outer_radius))
            inner_points = self.arc_points(end_angle, start_angle, self.inner_radius)
            points.extend(inner_points)
        else:
            # Pie slice: center, outer arc, back to center
            if include_center:
                points.append(self.center)
            points.extend(self.arc_points(start_angle, end_angle, self.outer_radius))
            if include_center:
                points.append(self.center)

        return points

    def slice_centroid(self, start_angle: float, end_angle: float) -> Point:
        """Get the centroid point of a slice (useful for labels).

        Args:
            start_angle: Starting angle in radians.
            end_angle: Ending angle in radians.

        Returns:
            The centroid Point of the slice.
        """
        mid_angle = (start_angle + end_angle) / 2
        mid_radius = (self.inner_radius + self.outer_radius) / 2
        return self.point_at_angle(mid_angle, mid_radius)

    def label_point(
        self,
        start_angle: float,
        end_angle: float,
        offset: float = 1.2,
    ) -> Point:
        """Get a point for placing a label outside the slice.

        Args:
            start_angle: Starting angle in radians.
            end_angle: Ending angle in radians.
            offset: Multiplier for placing label outside arc (>1).

        Returns:
            The Point for label placement.
        """
        mid_angle = (start_angle + end_angle) / 2
        label_radius = self.outer_radius * offset
        return self.point_at_angle(mid_angle, label_radius)

    def contains_point(
        self,
        point: Point,
        start_angle: float,
        end_angle: float,
    ) -> bool:
        """Check if a point is within a slice.

        Args:
            point: The point to check.
            start_angle: Slice starting angle.
            end_angle: Slice ending angle.

        Returns:
            True if point is within the slice.
        """
        # Check radius
        dist = self.center.distance_to(point)
        if dist < self.inner_radius or dist > self.outer_radius:
            return False

        # Check angle
        angle = math.atan2(point.y - self.center.y, point.x - self.center.x)

        # Normalize angles for comparison
        def normalize_angle(a: float) -> float:
            while a < 0:
                a += 2 * math.pi
            while a >= 2 * math.pi:
                a -= 2 * math.pi
            return a

        angle = normalize_angle(angle)
        start = normalize_angle(start_angle)
        end = normalize_angle(end_angle)

        if start <= end:
            return start <= angle <= end
        else:
            # Arc crosses 0
            return angle >= start or angle <= end

    def with_radii(
        self,
        inner: float | None = None,
        outer: float | None = None,
    ) -> PolarScale:
        """Create a new scale with different radii.

        Args:
            inner: New inner radius (None to keep current).
            outer: New outer radius (None to keep current).

        Returns:
            A new PolarScale with updated radii.
        """
        return PolarScale(
            center=self.center,
            inner_radius=inner if inner is not None else self.inner_radius,
            outer_radius=outer if outer is not None else self.outer_radius,
            start_angle=self.start_angle,
            end_angle=self.end_angle,
        )

    @classmethod
    def for_gauge(
        cls,
        center: Point,
        radius: float,
        arc_width: float = 20.0,
        start_degrees: float = -135.0,
        end_degrees: float = 135.0,
    ) -> PolarScale:
        """Create a polar scale configured for a gauge.

        Args:
            center: Center point.
            radius: Outer radius.
            arc_width: Width of the gauge arc.
            start_degrees: Starting angle in degrees (-135 = bottom-left).
            end_degrees: Ending angle in degrees (135 = bottom-right).

        Returns:
            A PolarScale configured for gauge rendering.
        """
        return cls(
            center=center,
            inner_radius=radius - arc_width,
            outer_radius=radius,
            start_angle=math.radians(start_degrees),
            end_angle=math.radians(end_degrees),
        )
