"""Drill indicator drawing utilities for charts."""

from __future__ import annotations

import math

from castella.core import Painter, Point, Style, FillStyle
from castella.models.geometry import Rect, Size

from castella.chart.hit_testing import RectElement, ArcElement


def draw_drill_indicator_on_rect(
    p: Painter,
    element: RectElement,
    indicator_size: float = 10.0,
    color: str = "#ffffff",
    padding: float = 4.0,
) -> None:
    """Draw a drill-down indicator on a rectangular element (bar chart).

    Draws a small indicator icon at the bottom-right corner
    of the element to indicate it can be drilled into.

    Args:
        p: The painter to draw with.
        element: The rectangular element (bar) to draw on.
        indicator_size: Size of the indicator in pixels.
        color: Color of the indicator.
        padding: Padding from the element edges.
    """
    # Ensure indicator fits within the bar
    if element.width < indicator_size + padding * 2:
        return
    if element.height < indicator_size + padding * 2:
        return

    # Calculate position at bottom-right of bar
    x = element.x + element.width - indicator_size - padding
    y = element.y + element.height - indicator_size - padding

    # Draw indicator using small circle as a dot
    _draw_indicator_dot(
        p, x + indicator_size / 2, y + indicator_size / 2, indicator_size / 3, color
    )


def draw_drill_indicator_on_arc(
    p: Painter,
    element: ArcElement,
    indicator_size: float = 12.0,
    color: str = "#ffffff",
) -> None:
    """Draw a drill-down indicator on an arc element (pie chart slice).

    Draws a small indicator near the center of the arc slice.

    Args:
        p: The painter to draw with.
        element: The arc element (pie slice) to draw on.
        indicator_size: Size of the indicator in pixels.
        color: Color of the indicator.
    """
    # Calculate the midpoint angle of the arc
    mid_angle = (element.start_angle + element.end_angle) / 2

    # Calculate position at ~60% of the radius from center
    radius_offset = element.outer_radius * 0.6
    x = element.center_x + math.cos(mid_angle) * radius_offset
    y = element.center_y + math.sin(mid_angle) * radius_offset

    # Draw indicator dot
    _draw_indicator_dot(p, x, y, indicator_size / 3, color)


def _draw_indicator_dot(
    p: Painter,
    x: float,
    y: float,
    radius: float,
    color: str,
) -> None:
    """Draw a small filled circle as indicator.

    Args:
        p: The painter to draw with.
        x: Center X coordinate.
        y: Center Y coordinate.
        radius: Radius of the dot.
        color: Fill color.
    """
    # Check if painter supports circles
    if hasattr(p, "fill_circle"):
        from castella.models.geometry import Circle

        p.save()
        p.style(Style(fill=FillStyle(color=color)))
        p.fill_circle(Circle(center=Point(x=x, y=y), radius=radius))
        p.restore()
    else:
        # Fallback: draw a small square
        p.save()
        p.style(Style(fill=FillStyle(color=color)))
        half = radius
        p.fill_rect(
            Rect(
                origin=Point(x=x - half, y=y - half),
                size=Size(width=half * 2, height=half * 2),
            )
        )
        p.restore()


def draw_drill_indicator_text(
    p: Painter,
    x: float,
    y: float,
    size: float = 10.0,
    color: str = "#ffffff",
    text: str = "+",
) -> None:
    """Draw a drill indicator using text character.

    Alternative method using a text character.

    Args:
        p: The painter to draw with.
        x: X coordinate.
        y: Y coordinate.
        size: Font size.
        color: Text color.
        text: The indicator character (default: +).
    """
    from castella.models.font import Font

    p.save()
    p.style(Style(fill=FillStyle(color=color), font=Font(size=int(size))))
    p.fill_text(text, Point(x=x, y=y), None)
    p.restore()
