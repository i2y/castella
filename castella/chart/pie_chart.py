"""Pie chart widget."""

from __future__ import annotations

import math
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
from castella.chart.hit_testing import HitTestable, ArcElement, LegendItemElement
from castella.chart.scales import PolarScale
from castella.chart.models import CategoricalChartData


class PieChart(BaseChart):
    """Interactive pie/donut chart widget.

    Renders categorical data as slices of a circle with
    hover highlighting and click events.

    Example:
        ```python
        from castella.chart import PieChart, CategoricalChartData, CategoricalSeries

        data = CategoricalChartData(title="Market Share")
        data.add_series(CategoricalSeries.from_values(
            name="2024",
            categories=["Chrome", "Safari", "Firefox", "Edge"],
            values=[65, 20, 10, 5],
        ))

        chart = PieChart(data)
        ```
    """

    def __init__(
        self,
        state: CategoricalChartData,
        donut: bool = False,
        inner_radius_ratio: float = 0.5,
        show_labels: bool = True,
        show_percentages: bool = True,
        **kwargs,
    ):
        """Initialize the pie chart.

        Args:
            state: Categorical chart data (first series is used).
            donut: Whether to render as a donut chart.
            inner_radius_ratio: Ratio of inner to outer radius for donut (0-1).
            show_labels: Whether to show labels outside slices.
            show_percentages: Whether to show percentage in labels.
            **kwargs: Additional arguments passed to BaseChart.
        """
        super().__init__(state=state, **kwargs)
        self._donut = donut
        self._inner_radius_ratio = inner_radius_ratio
        self._show_labels = show_labels
        self._show_percentages = show_percentages

    def donut(self, is_donut: bool = True, inner_ratio: float = 0.5) -> Self:
        """Set donut mode.

        Args:
            is_donut: Whether to render as donut.
            inner_ratio: Inner radius ratio.

        Returns:
            Self for chaining.
        """
        self._donut = is_donut
        self._inner_radius_ratio = inner_ratio
        return self

    def _build_elements(self) -> list[HitTestable]:
        """Build hit-testable arc elements."""
        state = self._get_state()
        if not isinstance(state, CategoricalChartData):
            return []

        if not state.series or self._layout is None:
            return []

        # Use first series only for pie chart
        series = state.series[0]
        if not series.data:
            return []

        elements: list[HitTestable] = []
        plot = self._layout.plot_area

        # Calculate center and radius
        center = Point(
            x=plot.x + plot.width / 2,
            y=plot.y + plot.height / 2,
        )
        radius = min(plot.width, plot.height) / 2 - 20  # Leave room for labels
        inner_radius = radius * self._inner_radius_ratio if self._donut else 0

        # Create polar scale
        polar = PolarScale(
            center=center,
            inner_radius=inner_radius,
            outer_radius=radius,
        )

        # Calculate total of visible slices only
        total = sum(
            p.value for i, p in enumerate(series.data) if state.is_data_visible(0, i)
        )
        if total <= 0:
            return []

        # Build arc elements for visible slices
        current_angle = polar.start_angle
        for data_idx, point in enumerate(series.data):
            # Skip hidden slices
            if not state.is_data_visible(0, data_idx):
                continue

            slice_angle = (point.value / total) * polar.angle_span
            end_angle = current_angle + slice_angle

            elements.append(
                ArcElement(
                    center=center,
                    inner_radius=inner_radius,
                    outer_radius=radius,
                    start_angle=current_angle,
                    end_angle=end_angle,
                    series_index=0,
                    data_index=data_idx,
                    value=point.value,
                    label=point.label or point.category,
                )
            )

            current_angle = end_angle

        return elements

    def _render_chart(self, p: Painter, layout: ChartLayout) -> None:
        """Render the pie chart."""
        state = self._get_state()
        if not isinstance(state, CategoricalChartData):
            return

        if not state.series:
            return

        series = state.series[0]
        if not series.data:
            return

        plot = layout.plot_area
        if plot.width <= 0 or plot.height <= 0:
            return

        # Calculate total
        total = sum(p.value for p in series.data)
        if total <= 0:
            return

        # Draw slices
        for element in self._elements:
            if not isinstance(element, ArcElement):
                continue

            data_idx = element.data_index
            color = self.get_series_color(data_idx)

            # Highlight on hover
            is_hovered = self.is_element_hovered(
                element.series_index, element.data_index
            )
            if is_hovered:
                color = self.lighten_color(color, 0.2)

            # Draw slice
            self._draw_slice(p, element, color, is_hovered)

        # Draw labels
        if self._show_labels:
            self._render_labels(p, layout, series, total)

        # Draw legend
        if self._show_legend:
            self._render_legend(p, layout, state, series)

    def _draw_slice(
        self,
        p: Painter,
        element: ArcElement,
        color: str,
        is_hovered: bool,
    ) -> None:
        """Draw a pie slice using small circles along the arc.

        Note: This is an approximation since we don't have path drawing.
        For proper pie slices, we'd need to add arc/path support to Painter.
        """
        center = element.center
        inner_r = element.inner_radius
        outer_r = element.outer_radius

        # If hovered, slightly expand the slice
        if is_hovered:
            # Move center outward slightly
            mid_angle = (element.start_angle + element.end_angle) / 2
            offset = 5
            center = Point(
                x=center.x + offset * math.cos(mid_angle),
                y=center.y + offset * math.sin(mid_angle),
            )

        p.style(Style(fill=FillStyle(color=color)))

        # Fill the slice with circles (approximation)
        angle_span = element.end_angle - element.start_angle
        num_angle_steps = max(10, int(abs(angle_span) * 20))

        for ri in range(int(inner_r), int(outer_r) + 1, 3):
            for ai in range(num_angle_steps + 1):
                t = ai / num_angle_steps
                angle = element.start_angle + t * angle_span
                x = center.x + ri * math.cos(angle)
                y = center.y + ri * math.sin(angle)
                p.fill_circle(Circle(center=Point(x=x, y=y), radius=2))

        # Draw slice border for better definition
        p.style(Style(fill=FillStyle(color=self._theme.background)))

        # Draw lines from center to edges
        for angle in [element.start_angle, element.end_angle]:
            for r in range(int(inner_r), int(outer_r) + 1, 2):
                x = center.x + r * math.cos(angle)
                y = center.y + r * math.sin(angle)
                p.fill_circle(Circle(center=Point(x=x, y=y), radius=1))

    def _render_labels(
        self,
        p: Painter,
        layout: ChartLayout,
        series,
        total: float,
    ) -> None:
        """Render labels outside the slices."""
        if not self._elements:
            return

        label_style = Style(
            fill=FillStyle(color=self._theme.text_color),
            font=Font(size=11),
        )
        p.style(label_style)

        for element in self._elements:
            if not isinstance(element, ArcElement):
                continue

            # Calculate label position
            mid_angle = (element.start_angle + element.end_angle) / 2
            label_radius = element.outer_radius + 20
            label_x = element.center.x + label_radius * math.cos(mid_angle)
            label_y = element.center.y + label_radius * math.sin(mid_angle)

            # Build label text
            percentage = element.value / total * 100
            if self._show_percentages:
                label_text = f"{element.label} ({percentage:.1f}%)"
            else:
                label_text = element.label

            text_width = p.measure_text(label_text)

            # Adjust position based on which side of the pie
            if mid_angle > math.pi / 2 or mid_angle < -math.pi / 2:
                # Left side - align right
                label_x -= text_width
            else:
                # Right side - align left
                pass

            p.fill_text(label_text, Point(x=label_x, y=label_y + 4), None)

    def _render_legend(
        self,
        p: Painter,
        layout: ChartLayout,
        state: CategoricalChartData,
        series,
    ) -> None:
        """Render the chart legend."""
        if not series.data:
            self._legend_elements = []
            return

        self._legend_elements = []
        legend_area = layout.legend_area
        x = legend_area.x
        y = legend_area.y + 12
        box_size = 12
        spacing = 80
        item_height = 20

        for i, point in enumerate(series.data):
            is_visible = state.is_data_visible(0, i)
            color = (
                self.get_series_color(i) if is_visible else self._theme.text_secondary
            )

            # Color box
            p.style(Style(fill=FillStyle(color=color)))
            p.fill_rect(
                Rect(
                    origin=Point(x=x, y=y),
                    size=Size(width=box_size, height=box_size),
                )
            )

            # Category name
            text_color = (
                self._theme.text_color if is_visible else self._theme.text_secondary
            )
            p.style(Style(fill=FillStyle(color=text_color), font=Font(size=11)))
            label = point.label or point.category
            p.fill_text(label, Point(x=x + box_size + 6, y=y + box_size - 2), None)

            # Build hit-testable legend element (with data_index for PieChart)
            self._legend_elements.append(
                LegendItemElement(
                    rect=Rect(
                        origin=Point(x=x, y=y - 4),
                        size=Size(width=spacing - 4, height=item_height),
                    ),
                    series_index=0,
                    data_index=i,  # PieChart uses data_index for slices
                    series_name=label,
                )
            )

            x += spacing

    def _get_element_anchor(self, element: HitTestable) -> Point:
        """Get anchor point for tooltip positioning."""
        if isinstance(element, ArcElement):
            return element.centroid
        return Point(x=0, y=0)
