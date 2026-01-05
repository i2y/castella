"""Scatter chart widget."""

from __future__ import annotations

from enum import Enum
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


class PointShape(Enum):
    """Shape options for scatter plot points."""

    CIRCLE = "circle"
    SQUARE = "square"
    DIAMOND = "diamond"
    TRIANGLE = "triangle"


class ScatterChart(BaseChart):
    """Interactive scatter chart widget.

    Renders numeric data as individual points without connecting lines.
    Supports multiple series, custom point shapes, and size mapping.

    Example:
        ```python
        from castella.chart import ScatterChart, NumericChartData, NumericSeries

        data = NumericChartData(title="Correlation")
        data.add_series(NumericSeries.from_xy_values(
            name="Sample A",
            x_values=[1, 2, 3, 4, 5],
            y_values=[2.3, 3.1, 2.8, 4.2, 3.9],
        ))

        chart = ScatterChart(data)
        ```
    """

    def __init__(
        self,
        state: NumericChartData,
        point_radius: float = 5.0,
        point_shape: PointShape = PointShape.CIRCLE,
        show_grid: bool = True,
        **kwargs,
    ):
        """Initialize the scatter chart.

        Args:
            state: Numeric chart data.
            point_radius: Radius of points.
            point_shape: Shape of points (circle, square, diamond, triangle).
            show_grid: Whether to show grid lines.
            **kwargs: Additional arguments passed to BaseChart.
        """
        super().__init__(state=state, **kwargs)
        self._point_radius = point_radius
        self._point_shape = point_shape
        self._show_grid = show_grid

    def point_radius(self, radius: float) -> Self:
        """Set point radius.

        Args:
            radius: Point radius in pixels.

        Returns:
            Self for chaining.
        """
        self._point_radius = radius
        return self

    def point_shape(self, shape: PointShape) -> Self:
        """Set point shape.

        Args:
            shape: The shape to use.

        Returns:
            Self for chaining.
        """
        self._point_shape = shape
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
        ).with_padding(0.1)

        y_scale = LinearScale(
            domain_min=y_range[0],
            domain_max=y_range[1],
            range_min=plot.y + plot.height,
            range_max=plot.y,
        ).with_padding(0.1)

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
                        radius=self._point_radius + 3,  # Larger for hit testing
                        series_index=series_idx,
                        data_index=data_idx,
                        value=point.y,
                        label=point.label or f"({point.x:.1f}, {point.y:.1f})",
                    )
                )

        return elements

    def _render_chart(self, p: Painter, layout: ChartLayout) -> None:
        """Render the scatter chart."""
        state = self._get_state()
        if not isinstance(state, NumericChartData):
            return

        plot = layout.plot_area
        if plot.width <= 0 or plot.height <= 0:
            return

        # Get data ranges
        x_range = state.x_range
        y_range = state.y_range

        # Create scales
        x_scale = LinearScale(
            domain_min=x_range[0],
            domain_max=x_range[1],
            range_min=plot.x,
            range_max=plot.x + plot.width,
        ).with_padding(0.1)

        y_scale = LinearScale(
            domain_min=y_range[0],
            domain_max=y_range[1],
            range_min=plot.y + plot.height,
            range_max=plot.y,
        ).with_padding(0.1)

        # Draw grid
        if self._show_grid:
            self._render_grid(p, layout, x_scale, y_scale)

        # Draw axes
        self._render_axes(p, layout, x_scale, y_scale)

        # Draw points for each series
        for series_idx, series in enumerate(state.series):
            if not state.is_series_visible(series_idx):
                continue

            self._render_series_points(p, series, series_idx, x_scale, y_scale)

        # Draw legend
        if self._show_legend:
            self._render_legend(p, layout, state)

    def _render_series_points(
        self,
        p: Painter,
        series: NumericSeries,
        series_idx: int,
        x_scale: LinearScale,
        y_scale: LinearScale,
    ) -> None:
        """Render points for a single series."""
        if not series.data:
            return

        color = series.style.color

        for data_idx, point in enumerate(series.data):
            screen_x = x_scale(point.x)
            screen_y = y_scale(point.y)
            center = Point(x=screen_x, y=screen_y)

            # Highlight hovered point
            is_hovered = self.is_element_hovered(series_idx, data_idx)
            radius = self._point_radius * 1.4 if is_hovered else self._point_radius
            point_color = self.lighten_color(color, 0.2) if is_hovered else color

            # Draw point based on shape
            self._draw_point(p, center, radius, point_color, is_hovered)

    def _draw_point(
        self,
        p: Painter,
        center: Point,
        radius: float,
        color: str,
        is_hovered: bool,
    ) -> None:
        """Draw a single point with the configured shape."""
        # Draw white border for visibility
        if is_hovered:
            p.style(Style(fill=FillStyle(color="#ffffff")))
            self._draw_shape(p, center, radius + 2)

        # Draw the point
        p.style(Style(fill=FillStyle(color=color)))
        self._draw_shape(p, center, radius)

    def _draw_shape(self, p: Painter, center: Point, radius: float) -> None:
        """Draw shape at the given center."""
        if self._point_shape == PointShape.CIRCLE:
            p.fill_circle(Circle(center=center, radius=radius))

        elif self._point_shape == PointShape.SQUARE:
            p.fill_rect(
                Rect(
                    origin=Point(x=center.x - radius, y=center.y - radius),
                    size=Size(width=radius * 2, height=radius * 2),
                )
            )

        elif self._point_shape == PointShape.DIAMOND:
            # Draw diamond as rotated square using 4 triangles
            # Approximate with small circles along the diamond edges
            for i in range(int(radius * 2)):
                t = i / (radius * 2)
                # Top-right edge
                x1 = center.x + radius * t
                y1 = center.y - radius * (1 - t)
                p.fill_circle(Circle(center=Point(x=x1, y=y1), radius=1.5))
                # Right-bottom edge
                x2 = center.x + radius * (1 - t)
                y2 = center.y + radius * t
                p.fill_circle(Circle(center=Point(x=x2, y=y2), radius=1.5))
                # Bottom-left edge
                x3 = center.x - radius * t
                y3 = center.y + radius * (1 - t)
                p.fill_circle(Circle(center=Point(x=x3, y=y3), radius=1.5))
                # Left-top edge
                x4 = center.x - radius * (1 - t)
                y4 = center.y - radius * t
                p.fill_circle(Circle(center=Point(x=x4, y=y4), radius=1.5))
            # Fill center
            for r in range(1, int(radius)):
                for angle_step in range(8):
                    import math

                    angle = angle_step * math.pi / 4
                    x = center.x + r * 0.7 * math.cos(angle)
                    y = center.y + r * 0.7 * math.sin(angle)
                    p.fill_circle(Circle(center=Point(x=x, y=y), radius=1.5))

        elif self._point_shape == PointShape.TRIANGLE:
            # Draw triangle pointing up
            import math

            for r in range(int(radius)):
                for angle_step in range(3):
                    angle = -math.pi / 2 + angle_step * 2 * math.pi / 3
                    x = center.x + r * math.cos(angle)
                    y = center.y + r * math.sin(angle)
                    p.fill_circle(Circle(center=Point(x=x, y=y), radius=1.5))

    def _render_grid(
        self,
        p: Painter,
        layout: ChartLayout,
        x_scale: LinearScale,
        y_scale: LinearScale,
    ) -> None:
        """Draw grid lines."""
        plot = layout.plot_area

        grid_style = Style(fill=FillStyle(color=self._theme.grid_color))
        p.style(grid_style)

        # Horizontal grid lines
        for tick in y_scale.ticks(5):
            y = y_scale(tick)
            p.fill_rect(
                Rect(
                    origin=Point(x=plot.x, y=y),
                    size=Size(width=plot.width, height=1),
                )
            )

        # Vertical grid lines
        for tick in x_scale.ticks(5):
            x = x_scale(tick)
            p.fill_rect(
                Rect(
                    origin=Point(x=x, y=plot.y),
                    size=Size(width=1, height=plot.height),
                )
            )

    def _render_axes(
        self,
        p: Painter,
        layout: ChartLayout,
        x_scale: LinearScale,
        y_scale: LinearScale,
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

        # Axis labels
        label_style = Style(
            fill=FillStyle(color=self._theme.text_color),
            font=Font(size=11),
        )
        p.style(label_style)

        # X axis labels
        for tick in x_scale.ticks(5):
            x = x_scale(tick)
            y = plot.y + plot.height + 16
            label = f"{tick:.1f}"
            text_width = p.measure_text(label)
            p.fill_text(label, Point(x=x - text_width / 2, y=y), None)

        # Y axis labels
        for tick in y_scale.ticks(5):
            x = plot.x - 8
            y = y_scale(tick)
            label = f"{tick:.1f}"
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

            # Color indicator (point)
            p.style(Style(fill=FillStyle(color=color)))
            p.fill_circle(
                Circle(center=Point(x=x + box_size / 2, y=y + box_size / 2), radius=4)
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
