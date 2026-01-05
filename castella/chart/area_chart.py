"""Area chart widget."""

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


class AreaChart(BaseChart):
    """Interactive area chart widget.

    Renders numeric data as lines with filled areas underneath.
    Supports multiple series with transparency for overlapping areas.

    Example:
        ```python
        from castella.chart import AreaChart, NumericChartData, NumericSeries

        data = NumericChartData(title="Revenue")
        data.add_series(NumericSeries.from_y_values(
            name="2024",
            y_values=[100, 120, 90, 150, 130],
        ))

        chart = AreaChart(data)
        ```
    """

    def __init__(
        self,
        state: NumericChartData,
        show_points: bool = True,
        point_radius: float = 4.0,
        line_width: float = 2.0,
        fill_opacity: float = 0.3,
        stacked: bool = False,
        **kwargs,
    ):
        """Initialize the area chart.

        Args:
            state: Numeric chart data.
            show_points: Whether to show point markers.
            point_radius: Radius of point markers.
            line_width: Width of lines.
            fill_opacity: Opacity of the fill area (0-1).
            stacked: Whether to stack multiple series.
            **kwargs: Additional arguments passed to BaseChart.
        """
        super().__init__(state=state, **kwargs)
        self._show_points = show_points
        self._point_radius = point_radius
        self._line_width = line_width
        self._fill_opacity = fill_opacity
        self._stacked = stacked

    def show_points(self, show: bool = True) -> Self:
        """Set whether to show point markers.

        Args:
            show: Whether to show points.

        Returns:
            Self for chaining.
        """
        self._show_points = show
        return self

    def stacked(self, stacked: bool = True) -> Self:
        """Set whether to stack series.

        Args:
            stacked: Whether to stack.

        Returns:
            Self for chaining.
        """
        self._stacked = stacked
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

        # For stacked charts, adjust y range
        if self._stacked and len(state.series) > 1:
            max_stacked = self._calculate_stacked_max(state)
            y_range = (0, max_stacked)

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

        # Calculate stacked baselines
        stacked_baselines: dict[int, float] = {}

        # Build circles for each point
        for series_idx, series in enumerate(state.series):
            if not state.is_series_visible(series_idx):
                continue

            for data_idx, point in enumerate(series.data):
                screen_x = x_scale(point.x)

                # Calculate y position (handle stacking)
                if self._stacked and series_idx > 0:
                    base_y = stacked_baselines.get(data_idx, 0)
                    screen_y = y_scale(base_y + point.y)
                    stacked_baselines[data_idx] = base_y + point.y
                else:
                    screen_y = y_scale(point.y)
                    if self._stacked:
                        stacked_baselines[data_idx] = point.y

                elements.append(
                    CircleElement(
                        center=Point(x=screen_x, y=screen_y),
                        radius=self._point_radius + 2,
                        series_index=series_idx,
                        data_index=data_idx,
                        value=point.y,
                        label=point.label or f"({point.x}, {point.y})",
                    )
                )

        return elements

    def _calculate_stacked_max(self, state: NumericChartData) -> float:
        """Calculate the maximum stacked value."""
        if not state.series:
            return 0

        # Find max x index
        max_len = max(len(s.data) for s in state.series)
        max_stacked = 0

        for i in range(max_len):
            total = 0
            for series in state.series:
                if i < len(series.data):
                    total += series.data[i].y
            max_stacked = max(max_stacked, total)

        return max_stacked

    def _render_chart(self, p: Painter, layout: ChartLayout) -> None:
        """Render the area chart."""
        state = self._get_state()
        if not isinstance(state, NumericChartData):
            return

        plot = layout.plot_area
        if plot.width <= 0 or plot.height <= 0:
            return

        # Get data ranges
        x_range = state.x_range
        y_range = state.y_range

        # For stacked charts, adjust y range
        if self._stacked and len(state.series) > 1:
            max_stacked = self._calculate_stacked_max(state)
            y_range = (0, max_stacked)

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

        # Draw grid and axes
        self._render_grid(p, layout, y_scale)
        self._render_axes(p, layout, x_scale, y_scale)

        # Draw series in reverse order for stacked (so first series is on top visually)
        visible_series = [
            (i, s) for i, s in enumerate(state.series) if state.is_series_visible(i)
        ]

        if self._stacked:
            visible_series = list(reversed(visible_series))

        # Track stacked positions
        stacked_points: dict[int, list[tuple[float, float]]] = {}

        for series_idx, series in visible_series:
            self._render_series(
                p, series, series_idx, x_scale, y_scale, state, stacked_points
            )

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
        stacked_points: dict[int, list[tuple[float, float]]],
    ) -> None:
        """Render a single series with filled area."""
        if not series.data:
            return

        color = series.style.color
        plot = self._layout.plot_area if self._layout else None
        if not plot:
            return

        # Calculate screen points
        points: list[Point] = []
        baseline_y = y_scale(0)  # Y position of zero line

        for data_idx, point in enumerate(series.data):
            screen_x = x_scale(point.x)

            if self._stacked and series_idx > 0:
                # Get baseline from previous series
                prev_points = stacked_points.get(series_idx - 1, [])
                if data_idx < len(prev_points):
                    base_screen_y = prev_points[data_idx][1]
                    screen_y = base_screen_y - (y_scale(0) - y_scale(point.y))
                else:
                    screen_y = y_scale(point.y)
            else:
                screen_y = y_scale(point.y)

            points.append(Point(x=screen_x, y=screen_y))

        # Store points for stacking
        stacked_points[series_idx] = [(pt.x, pt.y) for pt in points]

        # Draw filled area
        self._draw_filled_area(p, points, baseline_y, color, series_idx, stacked_points)

        # Draw line
        self._draw_line_segments(p, points, color)

        # Draw points
        if self._show_points:
            for i, screen_pt in enumerate(points):
                is_hovered = self.is_element_hovered(series_idx, i)
                radius = self._point_radius * 1.5 if is_hovered else self._point_radius

                # Outer circle (white border)
                p.style(Style(fill=FillStyle(color="#ffffff")))
                p.fill_circle(Circle(center=screen_pt, radius=radius + 2))

                # Inner circle (series color)
                point_color = self.lighten_color(color, 0.2) if is_hovered else color
                p.style(Style(fill=FillStyle(color=point_color)))
                p.fill_circle(Circle(center=screen_pt, radius=radius))

    def _draw_filled_area(
        self,
        p: Painter,
        points: list[Point],
        baseline_y: float,
        color: str,
        series_idx: int,
        stacked_points: dict[int, list[tuple[float, float]]],
    ) -> None:
        """Draw filled area under the line."""
        if len(points) < 2:
            return

        # Create semi-transparent fill color
        fill_color = self._apply_opacity(color, self._fill_opacity)
        p.style(Style(fill=FillStyle(color=fill_color)))

        # Get baseline points (either zero line or previous series)
        if self._stacked and series_idx > 0:
            prev_points = stacked_points.get(series_idx - 1, [])
            baseline_points = [Point(x=x, y=y) for x, y in prev_points]
        else:
            baseline_points = [Point(x=pt.x, y=baseline_y) for pt in points]

        # Fill area between line and baseline using vertical strips
        for i in range(len(points) - 1):
            top_left = points[i]
            top_right = points[i + 1]
            bottom_left = (
                baseline_points[i]
                if i < len(baseline_points)
                else Point(x=top_left.x, y=baseline_y)
            )
            bottom_right = (
                baseline_points[i + 1]
                if i + 1 < len(baseline_points)
                else Point(x=top_right.x, y=baseline_y)
            )

            # Draw vertical strips to fill the area
            num_strips = max(2, int(abs(top_right.x - top_left.x) / 2))
            for j in range(num_strips + 1):
                t = j / num_strips
                x = top_left.x + t * (top_right.x - top_left.x)
                y_top = top_left.y + t * (top_right.y - top_left.y)
                y_bottom = bottom_left.y + t * (bottom_right.y - bottom_left.y)

                # Draw vertical line as thin rectangle
                height = max(0, y_bottom - y_top)
                if height > 0:
                    p.fill_rect(
                        Rect(
                            origin=Point(x=x - 1, y=y_top),
                            size=Size(width=2, height=height),
                        )
                    )

    def _draw_line_segments(
        self,
        p: Painter,
        points: list[Point],
        color: str,
    ) -> None:
        """Draw line segments between points."""
        import math

        p.style(Style(fill=FillStyle(color=color)))

        for i in range(len(points) - 1):
            start = points[i]
            end = points[i + 1]

            dx = end.x - start.x
            dy = end.y - start.y
            length = math.sqrt(dx * dx + dy * dy)

            if length < 0.1:
                continue

            # Draw line as series of circles
            steps = max(2, int(length / 2))
            for j in range(steps + 1):
                t = j / steps
                x = start.x + t * dx
                y = start.y + t * dy
                p.fill_circle(
                    Circle(center=Point(x=x, y=y), radius=self._line_width / 2)
                )

    def _apply_opacity(self, hex_color: str, opacity: float) -> str:
        """Apply opacity to a color by lightening toward background."""
        # Parse hex color
        hex_color = hex_color.lstrip("#")
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)

        # Blend with background (assume dark background)
        bg_r, bg_g, bg_b = 30, 30, 30  # Approximate dark theme background

        r = int(r * opacity + bg_r * (1 - opacity))
        g = int(g * opacity + bg_g * (1 - opacity))
        b = int(b * opacity + bg_b * (1 - opacity))

        return f"#{r:02x}{g:02x}{b:02x}"

    def _render_grid(
        self,
        p: Painter,
        layout: ChartLayout,
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
            label = f"{tick:.0f}"
            text_width = p.measure_text(label)
            p.fill_text(label, Point(x=x - text_width / 2, y=y), None)

        # Y axis labels
        for tick in y_scale.ticks(5):
            x = plot.x - 8
            y = y_scale(tick)
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

            # Color box (filled area indicator)
            fill_color = self._apply_opacity(color, self._fill_opacity)
            p.style(Style(fill=FillStyle(color=fill_color)))
            p.fill_rect(
                Rect(
                    origin=Point(x=x, y=y),
                    size=Size(width=box_size, height=box_size),
                )
            )

            # Border
            p.style(Style(fill=FillStyle(color=color)))
            p.fill_rect(
                Rect(
                    origin=Point(x=x, y=y),
                    size=Size(width=box_size, height=2),
                )
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
