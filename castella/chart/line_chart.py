"""Line chart widget."""

from __future__ import annotations

from typing import Self

from castella.core import (
    Painter,
    Point,
    Size,
    Rect,
    Style,
    FillStyle,
    Circle,
)
from castella.models.font import Font

from castella.chart.base import BaseChart, ChartLayout
from castella.chart.hit_testing import HitTestable, CircleElement, LegendItemElement
from castella.chart.scales import LinearScale
from castella.chart.models import NumericChartData, NumericSeries


def _catmull_rom_point(p0: Point, p1: Point, p2: Point, p3: Point, t: float) -> Point:
    """Calculate a point on a Catmull-Rom spline.

    Args:
        p0: Control point before the segment.
        p1: Start point of the segment.
        p2: End point of the segment.
        p3: Control point after the segment.
        t: Parameter from 0 to 1.

    Returns:
        Point on the spline at parameter t.
    """
    t2 = t * t
    t3 = t2 * t

    x = 0.5 * (
        (2 * p1.x)
        + (-p0.x + p2.x) * t
        + (2 * p0.x - 5 * p1.x + 4 * p2.x - p3.x) * t2
        + (-p0.x + 3 * p1.x - 3 * p2.x + p3.x) * t3
    )
    y = 0.5 * (
        (2 * p1.y)
        + (-p0.y + p2.y) * t
        + (2 * p0.y - 5 * p1.y + 4 * p2.y - p3.y) * t2
        + (-p0.y + 3 * p1.y - 3 * p2.y + p3.y) * t3
    )
    return Point(x=x, y=y)


class LineChart(BaseChart):
    """Interactive line chart widget.

    Renders numeric data as connected lines with optional point markers.
    Supports multiple series, hover highlighting, and click events.

    Example:
        ```python
        from castella.chart import LineChart, NumericChartData, NumericSeries

        data = NumericChartData(title="Temperature")
        data.add_series(NumericSeries.from_y_values(
            name="Sensor A",
            y_values=[20.5, 22.3, 21.1, 23.4, 22.8],
        ))

        chart = LineChart(data)
        ```
    """

    def __init__(
        self,
        state: NumericChartData,
        show_points: bool = True,
        point_radius: float = 4.0,
        line_width: float = 2.0,
        smooth: bool = False,
        fill_area: bool = False,
        **kwargs,
    ):
        """Initialize the line chart.

        Args:
            state: Numeric chart data.
            show_points: Whether to show point markers.
            point_radius: Radius of point markers.
            line_width: Width of lines.
            smooth: Whether to use smooth curves (Catmull-Rom splines).
            fill_area: Whether to fill the area under the line.
            **kwargs: Additional arguments passed to BaseChart.
        """
        super().__init__(state=state, **kwargs)
        self._show_points = show_points
        self._point_radius = point_radius
        self._line_width = line_width
        self._smooth = smooth
        self._fill_area = fill_area

    def show_points(self, show: bool = True) -> Self:
        """Set whether to show point markers.

        Args:
            show: Whether to show points.

        Returns:
            Self for chaining.
        """
        self._show_points = show
        return self

    def fill_area(self, fill: bool = True) -> Self:
        """Set whether to fill area under the line.

        Args:
            fill: Whether to fill.

        Returns:
            Self for chaining.
        """
        self._fill_area = fill
        return self

    def _build_elements(self) -> list[HitTestable]:
        """Build hit-testable point circles."""
        state = self._get_state()
        if not isinstance(state, NumericChartData):
            return []

        if not state.series or self._layout is None:
            return []

        elements: list[HitTestable] = []
        plot = self._layout.plot_area

        # Get data ranges
        x_range = state.x_range
        y_range = state.y_range

        # Create scales
        x_scale = LinearScale(
            domain_min=x_range[0],
            domain_max=x_range[1],
            range_min=plot.x,
            range_max=plot.x + plot.width,
        )

        y_scale = LinearScale(
            domain_min=y_range[0],
            domain_max=y_range[1],
            range_min=plot.y + plot.height,
            range_max=plot.y,
        )

        # Add some padding to scales
        x_scale = x_scale.with_padding(0.05)
        y_scale = y_scale.with_padding(0.1)

        # Build circles for each point
        for series_idx, series in enumerate(state.series):
            if not state.is_series_visible(series_idx):
                continue

            for data_idx, point in enumerate(series.data):
                screen_x = x_scale(point.x)
                screen_y = y_scale(point.y)

                elements.append(
                    CircleElement(
                        center=Point(x=screen_x, y=screen_y),
                        radius=self._point_radius
                        + 2,  # Slightly larger for hit testing
                        series_index=series_idx,
                        data_index=data_idx,
                        value=point.y,
                        label=point.label or f"({point.x}, {point.y})",
                    )
                )

        return elements

    def _render_chart(self, p: Painter, layout: ChartLayout) -> None:
        """Render the line chart."""
        state = self._get_state()
        if not isinstance(state, NumericChartData):
            return

        plot = layout.plot_area
        if plot.width <= 0 or plot.height <= 0:
            return

        # Draw grid and axes
        self._render_grid(p, layout, state)
        self._render_axes(p, layout, state)

        # Get data ranges
        x_range = state.x_range
        y_range = state.y_range

        # Create scales
        x_scale = LinearScale(
            domain_min=x_range[0],
            domain_max=x_range[1],
            range_min=plot.x,
            range_max=plot.x + plot.width,
        ).with_padding(0.05)

        y_scale = LinearScale(
            domain_min=y_range[0],
            domain_max=y_range[1],
            range_min=plot.y + plot.height,
            range_max=plot.y,
        ).with_padding(0.1)

        # Draw each series
        for series_idx, series in enumerate(state.series):
            if not state.is_series_visible(series_idx):
                continue

            self._render_series(p, series, series_idx, x_scale, y_scale, state)

        # Draw legend
        if self._show_legend:
            self._render_legend(p, layout, state)

    def _render_series(
        self,
        p: Painter,
        series: NumericSeries,
        series_idx: int,
        x_scale: LinearScale,
        y_scale: LinearScale,
        state: NumericChartData,
    ) -> None:
        """Render a single series."""
        if not series.data:
            return

        color = series.style.color
        points: list[Point] = []

        for point in series.data:
            screen_x = x_scale(point.x)
            screen_y = y_scale(point.y)
            points.append(Point(x=screen_x, y=screen_y))

        # Draw lines between points
        if self._smooth and len(points) >= 2:
            self._draw_smooth_curve(p, points, color, self._line_width)
        else:
            line_style = Style(fill=FillStyle(color=color))
            p.style(line_style)
            for i in range(len(points) - 1):
                self._draw_line(p, points[i], points[i + 1], color, self._line_width)

        # Draw points
        if self._show_points:
            for i, screen_pt in enumerate(points):
                # Highlight hovered point
                is_hovered = self.is_element_hovered(series_idx, i)

                radius = self._point_radius * 1.5 if is_hovered else self._point_radius

                # Outer circle (white border)
                p.style(Style(fill=FillStyle(color="#ffffff")))
                p.fill_circle(Circle(center=screen_pt, radius=radius + 2))

                # Inner circle (series color)
                point_color = self.lighten_color(color, 0.2) if is_hovered else color
                p.style(Style(fill=FillStyle(color=point_color)))
                p.fill_circle(Circle(center=screen_pt, radius=radius))

    def _draw_line(
        self,
        p: Painter,
        start: Point,
        end: Point,
        color: str,
        width: float,
    ) -> None:
        """Draw a line between two points using rectangles.

        Note: This is a workaround since Painter doesn't have a draw_line method.
        For better quality, we'd need to add path drawing support.
        """
        import math

        dx = end.x - start.x
        dy = end.y - start.y
        length = math.sqrt(dx * dx + dy * dy)

        if length < 0.1:
            return

        # Draw line as a thin rectangle (rotated)
        # Since we can't rotate, draw as a series of small circles
        steps = max(2, int(length / 2))
        p.style(Style(fill=FillStyle(color=color)))

        for i in range(steps + 1):
            t = i / steps
            x = start.x + t * dx
            y = start.y + t * dy
            p.fill_circle(Circle(center=Point(x=x, y=y), radius=width / 2))

    def _draw_smooth_curve(
        self,
        p: Painter,
        points: list[Point],
        color: str,
        width: float,
    ) -> None:
        """Draw a smooth curve through points using Catmull-Rom splines.

        Args:
            p: The painter.
            points: List of points to connect.
            color: Line color.
            width: Line width.
        """
        if len(points) < 2:
            return

        p.style(Style(fill=FillStyle(color=color)))

        # Extend points for spline calculation (duplicate first and last)
        extended = [points[0]] + points + [points[-1]]

        for i in range(len(points) - 1):
            p0 = extended[i]
            p1 = extended[i + 1]
            p2 = extended[i + 2]
            p3 = extended[i + 3]

            # Draw circles along the curve segment
            steps = 20  # segments per curve section
            for j in range(steps + 1):
                t = j / steps
                pt = _catmull_rom_point(p0, p1, p2, p3, t)
                p.fill_circle(Circle(center=pt, radius=width / 2))

    def _render_grid(
        self,
        p: Painter,
        layout: ChartLayout,
        state: NumericChartData,
    ) -> None:
        """Draw grid lines."""
        plot = layout.plot_area

        grid_style = Style(fill=FillStyle(color=self._theme.grid_color))
        p.style(grid_style)

        # Get scales for tick positions
        y_range = state.y_range
        y_scale = LinearScale(
            domain_min=y_range[0],
            domain_max=y_range[1],
            range_min=plot.y + plot.height,
            range_max=plot.y,
        ).with_padding(0.1)

        # Horizontal grid lines
        for tick in y_scale.ticks(5):
            y = y_scale(tick)
            p.fill_rect(
                Rect(
                    origin=Point(x=plot.x, y=y),
                    size=Size(width=plot.width, height=1),
                )
            )

    def _render_axes(
        self,
        p: Painter,
        layout: ChartLayout,
        state: NumericChartData,
    ) -> None:
        """Draw axes with labels."""
        plot = layout.plot_area

        # Axis lines
        axis_style = Style(fill=FillStyle(color=self._theme.axis_color))
        p.style(axis_style)

        # X axis
        p.fill_rect(
            Rect(
                origin=Point(x=plot.x, y=plot.y + plot.height),
                size=Size(width=plot.width, height=1),
            )
        )

        # Y axis
        p.fill_rect(
            Rect(
                origin=Point(x=plot.x, y=plot.y),
                size=Size(width=1, height=plot.height),
            )
        )

        # Get scales
        x_range = state.x_range
        y_range = state.y_range

        x_scale = LinearScale(
            domain_min=x_range[0],
            domain_max=x_range[1],
            range_min=plot.x,
            range_max=plot.x + plot.width,
        ).with_padding(0.05)

        y_scale = LinearScale(
            domain_min=y_range[0],
            domain_max=y_range[1],
            range_min=plot.y + plot.height,
            range_max=plot.y,
        ).with_padding(0.1)

        # Axis labels
        label_style = Style(
            fill=FillStyle(color=self._theme.text_color),
            font=Font(size=11),
        )
        p.style(label_style)

        # X axis labels
        x_tick_count = state.x_axis.tick_count if state.x_axis else 5
        x_ticks = list(x_scale.ticks(x_tick_count))
        x_tick_labels = state.x_axis.tick_labels if state.x_axis else None

        for i, tick in enumerate(x_ticks):
            x = x_scale(tick)
            y = plot.y + plot.height + 16
            # Use custom tick_labels if provided, otherwise format the value
            if x_tick_labels and i < len(x_tick_labels):
                label = x_tick_labels[i]
            else:
                label = f"{tick:.0f}"
            text_width = p.measure_text(label)
            p.fill_text(label, Point(x=x - text_width / 2, y=y), None)

        # Y axis labels
        y_tick_count = state.y_axis.tick_count if state.y_axis else 5
        y_ticks = list(y_scale.ticks(y_tick_count))
        y_tick_labels = state.y_axis.tick_labels if state.y_axis else None

        for i, tick in enumerate(y_ticks):
            x = plot.x - 8
            y = y_scale(tick)
            # Use custom tick_labels if provided, otherwise format the value
            if y_tick_labels and i < len(y_tick_labels):
                label = y_tick_labels[i]
            else:
                label = f"{tick:.0f}"
            text_width = p.measure_text(label)
            p.fill_text(label, Point(x=x - text_width, y=y + 4), None)

    def _render_legend(
        self,
        p: Painter,
        layout: ChartLayout,
        state: NumericChartData,
    ) -> None:
        """Render the chart legend."""
        if not state.series:
            self._legend_elements = []
            return

        self._legend_elements = []
        legend_area = layout.legend_area
        x = legend_area.x
        y = legend_area.y + 12
        box_size = 12
        spacing = 100
        item_height = 20

        for i, series in enumerate(state.series):
            is_visible = state.is_series_visible(i)
            color = series.style.color if is_visible else self._theme.text_secondary

            # Color indicator (line segment)
            p.style(Style(fill=FillStyle(color=color)))
            p.fill_rect(
                Rect(
                    origin=Point(x=x, y=y + box_size / 2 - 1),
                    size=Size(width=box_size, height=2),
                )
            )

            # Point on the line
            p.fill_circle(
                Circle(center=Point(x=x + box_size / 2, y=y + box_size / 2), radius=3)
            )

            # Series name
            text_color = (
                self._theme.text_color if is_visible else self._theme.text_secondary
            )
            p.style(Style(fill=FillStyle(color=text_color), font=Font(size=11)))
            p.fill_text(
                series.name, Point(x=x + box_size + 6, y=y + box_size - 2), None
            )

            # Build hit-testable legend element
            self._legend_elements.append(
                LegendItemElement(
                    rect=Rect(
                        origin=Point(x=x, y=y - 4),
                        size=Size(width=spacing - 4, height=item_height),
                    ),
                    series_index=i,
                    data_index=-1,
                    series_name=series.name,
                )
            )

            x += spacing

    def _get_element_anchor(self, element: HitTestable) -> Point:
        """Get anchor point for tooltip positioning."""
        if isinstance(element, CircleElement):
            return element.top
        return Point(x=0, y=0)
