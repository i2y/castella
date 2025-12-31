"""Easing functions for animations.

This module provides mathematical easing functions that control
the rate of change of animated values over time.
"""

from __future__ import annotations

from castella.chart.models.animation import EasingFunction


def apply_easing(t: float, easing: EasingFunction) -> float:
    """Apply easing function to progress value.

    Args:
        t: Progress value from 0.0 to 1.0
        easing: Easing function to apply

    Returns:
        Eased value from 0.0 to 1.0
    """
    t = max(0.0, min(1.0, t))

    match easing:
        case EasingFunction.LINEAR:
            return t
        case EasingFunction.EASE_IN:
            return _ease_in_quad(t)
        case EasingFunction.EASE_OUT:
            return _ease_out_quad(t)
        case EasingFunction.EASE_IN_OUT:
            return _ease_in_out_quad(t)
        case EasingFunction.EASE_IN_CUBIC:
            return _ease_in_cubic(t)
        case EasingFunction.EASE_OUT_CUBIC:
            return _ease_out_cubic(t)
        case EasingFunction.EASE_IN_OUT_CUBIC:
            return _ease_in_out_cubic(t)
        case EasingFunction.BOUNCE:
            return _bounce(t)
        case _:
            return t


def _ease_in_quad(t: float) -> float:
    """Quadratic ease-in: accelerating from zero velocity."""
    return t * t


def _ease_out_quad(t: float) -> float:
    """Quadratic ease-out: decelerating to zero velocity."""
    return t * (2 - t)


def _ease_in_out_quad(t: float) -> float:
    """Quadratic ease-in-out: acceleration until halfway, then deceleration."""
    if t < 0.5:
        return 2 * t * t
    return -1 + (4 - 2 * t) * t


def _ease_in_cubic(t: float) -> float:
    """Cubic ease-in: accelerating from zero velocity."""
    return t * t * t


def _ease_out_cubic(t: float) -> float:
    """Cubic ease-out: decelerating to zero velocity."""
    t1 = t - 1
    return t1 * t1 * t1 + 1


def _ease_in_out_cubic(t: float) -> float:
    """Cubic ease-in-out: acceleration until halfway, then deceleration."""
    if t < 0.5:
        return 4 * t * t * t
    t1 = 2 * t - 2
    return 0.5 * t1 * t1 * t1 + 1


def _bounce(t: float) -> float:
    """Bounce easing: bouncing effect at the end."""
    if t < 1 / 2.75:
        return 7.5625 * t * t
    elif t < 2 / 2.75:
        t -= 1.5 / 2.75
        return 7.5625 * t * t + 0.75
    elif t < 2.5 / 2.75:
        t -= 2.25 / 2.75
        return 7.5625 * t * t + 0.9375
    else:
        t -= 2.625 / 2.75
        return 7.5625 * t * t + 0.984375


def lerp(start: float, end: float, t: float) -> float:
    """Linear interpolation between two values.

    Args:
        start: Starting value
        end: Ending value
        t: Interpolation factor (0.0 = start, 1.0 = end)

    Returns:
        Interpolated value
    """
    return start + (end - start) * t
