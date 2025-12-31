"""Type-specific interpolation utilities."""

from __future__ import annotations

from typing import TypeVar

from castella.models.geometry import Point, Size

from .easing import lerp

T = TypeVar("T")


def interpolate_float(start: float, end: float, t: float) -> float:
    """Interpolate between two float values."""
    return lerp(start, end, t)


def interpolate_int(start: int, end: int, t: float) -> int:
    """Interpolate between two int values."""
    return round(lerp(float(start), float(end), t))


def interpolate_point(start: Point, end: Point, t: float) -> Point:
    """Interpolate between two Point values."""
    return Point(
        x=lerp(start.x, end.x, t),
        y=lerp(start.y, end.y, t),
    )


def interpolate_size(start: Size, end: Size, t: float) -> Size:
    """Interpolate between two Size values."""
    return Size(
        width=lerp(start.width, end.width, t),
        height=lerp(start.height, end.height, t),
    )


def interpolate(start: T, end: T, t: float) -> T:
    """Generic interpolation that dispatches to type-specific interpolators.

    Args:
        start: Starting value
        end: Ending value
        t: Interpolation factor (0.0 = start, 1.0 = end)

    Returns:
        Interpolated value of the same type

    Raises:
        TypeError: If the type is not supported for interpolation
    """
    if isinstance(start, float) and isinstance(end, float):
        return interpolate_float(start, end, t)  # type: ignore
    elif isinstance(start, int) and isinstance(end, int):
        return interpolate_int(start, end, t)  # type: ignore
    elif isinstance(start, Point) and isinstance(end, Point):
        return interpolate_point(start, end, t)  # type: ignore
    elif isinstance(start, Size) and isinstance(end, Size):
        return interpolate_size(start, end, t)  # type: ignore
    else:
        raise TypeError(
            f"Cannot interpolate between {type(start).__name__} and {type(end).__name__}"
        )


def is_interpolatable(value: object) -> bool:
    """Check if a value type supports interpolation."""
    return isinstance(value, (int, float, Point, Size))
