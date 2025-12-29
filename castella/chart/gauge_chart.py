"""Gauge chart widget."""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from typing import Self

from castella.core import (
    Painter,
    Point,
    Style,
    FillStyle,
    Circle,
)
from castella.models.font import Font

from castella.chart.base import BaseChart, ChartLayout
from castella.chart.hit_testing import HitTestable, ArcElement
from castella.chart.models import GaugeChartData


class GaugeStyle(Enum):
    """Style options for gauge charts."""

    HALF_CIRCLE = "half"  # 180 degrees, bottom half
    THREE_QUARTER = "three_quarter"  # 270 degrees
    FULL_CIRCLE = "full"  # 360 degrees (donut style)


@dataclass
class GaugeThreshold:
    """A threshold for color-coded gauge segments.

    This is a convenience wrapper. You can also use the tuple format
    directly in GaugeChartData.thresholds: [(percentage, color), ...]
    """

    percentage: float  # 0.0 to 1.0
    color: str
    label: str = ""


class GaugeChart(BaseChart):
    """Interactive gauge chart widget.

    Displays a single value as a gauge/meter with optional thresholds
    for color-coded segments.

    Example:
        ```python
        from castella.chart import GaugeChart, GaugeChartData

        data = GaugeChartData(
            title="CPU Usage",
            value=65,
            min_value=0,
            max_value=100,
            value_format="{:.0f}%",
            thresholds=[
                (0.0, "#22c55e"),   # Green for 0-50%
                (0.5, "#f59e0b"),   # Yellow for 50-80%
                (0.8, "#ef4444"),   # Red for 80-100%
            ],
        )

        chart = GaugeChart(data)
        ```
    """

    def __init__(
        self,
        state: GaugeChartData,
        style: GaugeStyle = GaugeStyle.HALF_CIRCLE,
        show_value: bool = True,
        show_ticks: bool = True,
        arc_width: float = 20.0,
        **kwargs,
    ):
        """Initialize the gauge chart.

        Args:
            state: Gauge chart data.
            style: Gauge style (half, three_quarter, full).
            show_value: Whether to show the current value in center.
            show_ticks: Whether to show tick marks.
            arc_width: Width of the gauge arc.
            **kwargs: Additional arguments passed to BaseChart.
        """
        # Disable legend for gauge charts
        kwargs.setdefault("show_legend", False)
        super().__init__(state=state, **kwargs)
        self._gauge_style = style
        self._show_value = show_value
        self._show_ticks = show_ticks
        self._arc_width = arc_width

    def gauge_style(self, style: GaugeStyle) -> Self:
        """Set gauge style.

        Args:
            style: The gauge style.

        Returns:
            Self for chaining.
        """
        self._gauge_style = style
        return self

    def arc_width(self, width: float) -> Self:
        """Set arc width.

        Args:
            width: Width in pixels.

        Returns:
            Self for chaining.
        """
        self._arc_width = width
        return self

    def _get_angle_range(self) -> tuple[float, float]:
        """Get start and end angles based on gauge style."""
        if self._gauge_style == GaugeStyle.HALF_CIRCLE:
            return (math.pi, 0)  # 180 to 0 degrees (bottom half, left to right)
        elif self._gauge_style == GaugeStyle.THREE_QUARTER:
            return (math.pi * 0.75, -math.pi * 0.25)  # 135 to -45 degrees
        else:  # FULL_CIRCLE
            return (-math.pi / 2, math.pi * 1.5)  # -90 to 270 degrees (start at top)

    def _build_elements(self) -> list[HitTestable]:
        """Build hit-testable arc element for the value arc."""
        state = self._get_state()
        if not isinstance(state, GaugeChartData):
            return []

        if self._layout is None:
            return []

        plot = self._layout.plot_area
        center = Point(x=plot.x + plot.width / 2, y=plot.y + plot.height / 2)

        # Adjust center for half circle
        if self._gauge_style == GaugeStyle.HALF_CIRCLE:
            center = Point(x=center.x, y=plot.y + plot.height * 0.7)

        radius = min(plot.width, plot.height) / 2 - 30
        inner_radius = radius - self._arc_width

        start_angle, end_angle = self._get_angle_range()
        value_angle = start_angle + (end_angle - start_angle) * state.percentage

        return [
            ArcElement(
                center=center,
                inner_radius=inner_radius,
                outer_radius=radius,
                start_angle=start_angle,
                end_angle=value_angle,
                series_index=0,
                data_index=0,
                value=state.value,
                label=state.value_format.format(state.value),
            )
        ]

    def _render_chart(self, p: Painter, layout: ChartLayout) -> None:
        """Render the gauge chart."""
        state = self._get_state()
        if not isinstance(state, GaugeChartData):
            return

        plot = layout.plot_area
        if plot.width <= 0 or plot.height <= 0:
            return

        center = Point(x=plot.x + plot.width / 2, y=plot.y + plot.height / 2)

        # Adjust center for half circle
        if self._gauge_style == GaugeStyle.HALF_CIRCLE:
            center = Point(x=center.x, y=plot.y + plot.height * 0.7)

        radius = min(plot.width, plot.height) / 2 - 30
        inner_radius = radius - self._arc_width

        start_angle, end_angle = self._get_angle_range()

        # Draw background arc (track)
        self._draw_arc(
            p,
            center,
            inner_radius,
            radius,
            start_angle,
            end_angle,
            self._theme.grid_color,
        )

        # Draw threshold segments or single value arc
        if state.thresholds:
            self._draw_threshold_segments(
                p, center, inner_radius, radius, start_angle, end_angle, state
            )
        else:
            # Draw single value arc
            value_angle = start_angle + (end_angle - start_angle) * state.percentage
            color = state.current_color

            # Highlight if hovered
            if self.is_element_hovered(0, 0):
                color = self.lighten_color(color, 0.2)

            self._draw_arc(
                p, center, inner_radius, radius, start_angle, value_angle, color
            )

        # Draw tick marks
        if self._show_ticks:
            self._draw_ticks(p, center, radius, start_angle, end_angle, state)

        # Draw center value
        if self._show_value:
            self._draw_center_value(p, center, state)

    def _draw_arc(
        self,
        p: Painter,
        center: Point,
        inner_radius: float,
        outer_radius: float,
        start_angle: float,
        end_angle: float,
        color: str,
    ) -> None:
        """Draw an arc segment using small circles."""
        p.style(Style(fill=FillStyle(color=color)))

        angle_span = end_angle - start_angle
        num_steps = max(20, int(abs(angle_span) * 30))

        for ri in range(int(inner_radius), int(outer_radius) + 1, 2):
            for ai in range(num_steps + 1):
                t = ai / num_steps
                angle = start_angle + t * angle_span
                x = center.x + ri * math.cos(angle)
                y = center.y + ri * math.sin(angle)
                p.fill_circle(Circle(center=Point(x=x, y=y), radius=1.5))

    def _draw_threshold_segments(
        self,
        p: Painter,
        center: Point,
        inner_radius: float,
        outer_radius: float,
        start_angle: float,
        end_angle: float,
        state: GaugeChartData,
    ) -> None:
        """Draw colored segments based on thresholds.

        Thresholds define color ranges: [(start_pct, color), ...]
        Each threshold defines the color from start_pct up to the next threshold.
        Example: [(0.0, green), (0.5, yellow), (0.8, red)]
        means: 0-50% green, 50-80% yellow, 80-100% red
        """
        if not state.thresholds:
            return

        angle_span = end_angle - start_angle
        current_pct = state.percentage

        # Sort thresholds and add implicit end at 1.0
        sorted_thresholds = sorted(state.thresholds, key=lambda t: t[0])

        # Draw each segment
        for i, (start_pct, color) in enumerate(sorted_thresholds):
            # Determine end of this segment
            if i + 1 < len(sorted_thresholds):
                end_pct = sorted_thresholds[i + 1][0]
            else:
                end_pct = 1.0  # Last segment goes to 100%

            # Only draw if this segment is within the current value
            if start_pct < current_pct:
                # Calculate how much of this segment to draw
                draw_end_pct = min(end_pct, current_pct)

                # Calculate angles for this segment
                seg_start = start_angle + start_pct * angle_span
                seg_end = start_angle + draw_end_pct * angle_span

                draw_color = color

                # Highlight if hovered
                if self.is_element_hovered(0, 0):
                    draw_color = self.lighten_color(draw_color, 0.2)

                self._draw_arc(
                    p,
                    center,
                    inner_radius,
                    outer_radius,
                    seg_start,
                    seg_end,
                    draw_color,
                )

    def _draw_ticks(
        self,
        p: Painter,
        center: Point,
        radius: float,
        start_angle: float,
        end_angle: float,
        state: GaugeChartData,
    ) -> None:
        """Draw tick marks around the gauge."""
        angle_span = end_angle - start_angle
        value_range = state.max_value - state.min_value

        if value_range <= 0:
            return

        # Determine number of major ticks
        num_ticks = 5

        tick_style = Style(fill=FillStyle(color=self._theme.text_color))
        p.style(tick_style)

        outer_radius = radius + 5
        inner_radius = radius + 2

        for i in range(num_ticks + 1):
            t = i / num_ticks
            angle = start_angle + t * angle_span
            value = state.min_value + t * value_range

            # Draw tick line
            x1 = center.x + inner_radius * math.cos(angle)
            y1 = center.y + inner_radius * math.sin(angle)
            x2 = center.x + outer_radius * math.cos(angle)
            y2 = center.y + outer_radius * math.sin(angle)

            for step in range(5):
                tx = x1 + (x2 - x1) * step / 4
                ty = y1 + (y2 - y1) * step / 4
                p.fill_circle(Circle(center=Point(x=tx, y=ty), radius=1))

            # Draw tick label
            label_radius = outer_radius + 12
            label_x = center.x + label_radius * math.cos(angle)
            label_y = center.y + label_radius * math.sin(angle)

            label = f"{value:.0f}"
            p.style(
                Style(
                    fill=FillStyle(color=self._theme.text_secondary), font=Font(size=9)
                )
            )
            text_width = p.measure_text(label)
            p.fill_text(label, Point(x=label_x - text_width / 2, y=label_y + 3), None)

    def _draw_center_value(
        self,
        p: Painter,
        center: Point,
        state: GaugeChartData,
    ) -> None:
        """Draw the current value in the center."""
        # Main value using format string
        value_text = state.value_format.format(state.value)
        p.style(Style(fill=FillStyle(color=self._theme.text_color), font=Font(size=28)))
        value_width = p.measure_text(value_text)
        p.fill_text(
            value_text, Point(x=center.x - value_width / 2, y=center.y + 10), None
        )

        # Title (if set via data)
        if state.title:
            p.style(
                Style(
                    fill=FillStyle(color=self._theme.text_secondary), font=Font(size=11)
                )
            )
            title_width = p.measure_text(state.title)
            p.fill_text(
                state.title, Point(x=center.x - title_width / 2, y=center.y - 20), None
            )

    def _get_element_anchor(self, element: HitTestable) -> Point:
        """Get anchor point for tooltip positioning."""
        if isinstance(element, ArcElement):
            return element.centroid
        return Point(x=0, y=0)


# Alias for convenience
DonutChart = GaugeChart
