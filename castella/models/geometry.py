"""Geometry primitives as Pydantic models."""

from __future__ import annotations

import math

from pydantic import BaseModel, ConfigDict, Field


class Point(BaseModel):
    """Mutable 2D point."""

    model_config = ConfigDict(validate_assignment=True)

    x: float = 0.0
    y: float = 0.0

    def __add__(self, other: Point) -> Point:
        return Point(x=self.x + other.x, y=self.y + other.y)

    def __sub__(self, other: Point) -> Point:
        return Point(x=self.x - other.x, y=self.y - other.y)

    def __mul__(self, scalar: float) -> Point:
        return Point(x=self.x * scalar, y=self.y * scalar)

    def distance_to(self, other: Point) -> float:
        return math.sqrt((self.x - other.x) ** 2 + (self.y - other.y) ** 2)

    def to_tuple(self) -> tuple[float, float]:
        return (self.x, self.y)

    @classmethod
    def origin(cls) -> Point:
        return cls(x=0.0, y=0.0)


class Size(BaseModel):
    """Mutable 2D size with non-negative validation."""

    model_config = ConfigDict(validate_assignment=True)

    width: float = Field(default=0.0, ge=0.0)
    height: float = Field(default=0.0, ge=0.0)

    def __add__(self, other: Size) -> Size:
        return Size(width=self.width + other.width, height=self.height + other.height)

    def __sub__(self, other: Size) -> Size:
        return Size(
            width=max(0.0, self.width - other.width),
            height=max(0.0, self.height - other.height),
        )

    def __mul__(self, scalar: float) -> Size:
        return Size(width=self.width * scalar, height=self.height * scalar)

    @property
    def area(self) -> float:
        return self.width * self.height

    @property
    def is_empty(self) -> bool:
        return self.width == 0.0 or self.height == 0.0

    def to_tuple(self) -> tuple[float, float]:
        return (self.width, self.height)

    @classmethod
    def zero(cls) -> Size:
        return cls(width=0.0, height=0.0)


class Rect(BaseModel):
    """Immutable rectangle with geometric operations."""

    model_config = ConfigDict(frozen=True)

    origin: Point = Field(default_factory=Point.origin)
    size: Size = Field(default_factory=Size.zero)

    @property
    def x(self) -> float:
        return self.origin.x

    @property
    def y(self) -> float:
        return self.origin.y

    @property
    def width(self) -> float:
        return self.size.width

    @property
    def height(self) -> float:
        return self.size.height

    @property
    def center(self) -> Point:
        return Point(
            x=self.origin.x + self.size.width / 2,
            y=self.origin.y + self.size.height / 2,
        )

    @property
    def max_point(self) -> Point:
        return Point(
            x=self.origin.x + self.size.width,
            y=self.origin.y + self.size.height,
        )

    def contain(self, p: Point) -> bool:
        """Check if point is inside rectangle."""
        return (self.origin.x <= p.x <= self.origin.x + self.size.width) and (
            self.origin.y <= p.y <= self.origin.y + self.size.height
        )

    def intersect(self, other: Rect) -> Rect | None:
        """Compute intersection with another rectangle."""
        x1 = max(self.origin.x, other.origin.x)
        y1 = max(self.origin.y, other.origin.y)
        x2 = min(self.max_point.x, other.max_point.x)
        y2 = min(self.max_point.y, other.max_point.y)

        if x2 <= x1 or y2 <= y1:
            return None

        return Rect(
            origin=Point(x=x1, y=y1),
            size=Size(width=x2 - x1, height=y2 - y1),
        )

    def union(self, other: Rect) -> Rect:
        """Compute union bounding box with another rectangle."""
        x1 = min(self.origin.x, other.origin.x)
        y1 = min(self.origin.y, other.origin.y)
        x2 = max(self.max_point.x, other.max_point.x)
        y2 = max(self.max_point.y, other.max_point.y)

        return Rect(
            origin=Point(x=x1, y=y1),
            size=Size(width=x2 - x1, height=y2 - y1),
        )

    def offset(self, dx: float = 0.0, dy: float = 0.0) -> Rect:
        """Create new rectangle offset by dx, dy."""
        return Rect(
            origin=Point(x=self.origin.x + dx, y=self.origin.y + dy),
            size=self.size,
        )

    def inset(self, dx: float = 0.0, dy: float = 0.0) -> Rect:
        """Create new rectangle inset by dx, dy on each side."""
        return Rect(
            origin=Point(x=self.origin.x + dx, y=self.origin.y + dy),
            size=Size(
                width=max(0.0, self.size.width - 2 * dx),
                height=max(0.0, self.size.height - 2 * dy),
            ),
        )


class Circle(BaseModel):
    """Immutable circle with geometric operations."""

    model_config = ConfigDict(frozen=True)

    center: Point = Field(default_factory=Point.origin)
    radius: float = Field(default=0.0, ge=0.0)

    def contain(self, p: Point) -> bool:
        """Check if point is inside circle."""
        return self.center.distance_to(p) <= self.radius

    @property
    def bounding_rect(self) -> Rect:
        return Rect(
            origin=Point(x=self.center.x - self.radius, y=self.center.y - self.radius),
            size=Size(width=self.radius * 2, height=self.radius * 2),
        )

    @property
    def area(self) -> float:
        return math.pi * self.radius**2
