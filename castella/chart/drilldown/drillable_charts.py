"""Drillable chart variants with visual indicators."""

from __future__ import annotations

import math

from castella.core import (
    Painter,
    Style,
    FillStyle,
)
from castella.models.geometry import Circle, Point

from castella.chart.bar_chart import BarChart
from castella.chart.pie_chart import PieChart
from castella.chart.stacked_bar_chart import StackedBarChart
from castella.chart.heatmap_chart import HeatmapChart
from castella.chart.base import ChartLayout
from castella.chart.hit_testing import RectElement, ArcElement
from castella.chart.models import CategoricalChartData
from castella.chart.models.heatmap_data import HeatmapChartData


class DrillableBarChart(BarChart):
    """BarChart with visual indicators for drillable data points.

    Extends BarChart to show a small indicator (dot) on bars that
    have children and can be drilled into.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._indicator_color = "#ffffff"
        self._indicator_size = 6.0

    def _render_chart(self, p: Painter, layout: ChartLayout) -> None:
        """Render the bar chart with drill indicators."""
        # First render the standard bar chart
        super()._render_chart(p, layout)

        # Then overlay drill indicators on drillable bars
        state = self._get_state()
        if not isinstance(state, CategoricalChartData):
            return

        for element in self._elements:
            if not isinstance(element, RectElement):
                continue

            # Check if this element is drillable via metadata
            series_idx = element.series_index
            data_idx = element.data_index

            if series_idx < len(state.series):
                series = state.series[series_idx]
                if data_idx < len(series.data):
                    point = series.data[data_idx]
                    if point.metadata.get("drillable", False):
                        self._draw_drill_indicator(p, element)

    def _draw_drill_indicator(self, p: Painter, element: RectElement) -> None:
        """Draw a small indicator showing the bar is drillable.

        Args:
            p: The painter to draw with.
            element: The bar element to draw on.
        """
        rect = element.rect
        padding = 4.0
        radius = self._indicator_size / 2

        # Only draw if bar is big enough
        min_size = self._indicator_size + padding * 2
        if rect.size.width < min_size or rect.size.height < min_size:
            return

        # Position at bottom-right of the bar
        x = rect.origin.x + rect.size.width - radius - padding
        y = rect.origin.y + rect.size.height - radius - padding

        # Draw filled circle
        p.save()
        p.style(Style(fill=FillStyle(color=self._indicator_color)))
        if hasattr(p, "fill_circle"):
            p.fill_circle(Circle(center=Point(x=x, y=y), radius=radius))
        else:
            # Fallback: draw small square
            from castella.models.geometry import Rect, Size

            p.fill_rect(
                Rect(
                    origin=Point(x=x - radius, y=y - radius),
                    size=Size(width=radius * 2, height=radius * 2),
                )
            )
        p.restore()


class DrillablePieChart(PieChart):
    """PieChart with visual indicators for drillable slices.

    Extends PieChart to show a small indicator on slices that
    have children and can be drilled into.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._indicator_color = "#ffffff"
        self._indicator_size = 8.0

    def _render_chart(self, p: Painter, layout: ChartLayout) -> None:
        """Render the pie chart with drill indicators."""
        # First render the standard pie chart
        super()._render_chart(p, layout)

        # Then overlay drill indicators on drillable slices
        state = self._get_state()
        if not isinstance(state, CategoricalChartData):
            return

        for element in self._elements:
            if not isinstance(element, ArcElement):
                continue

            # Check if this element is drillable via metadata
            series_idx = element.series_index
            data_idx = element.data_index

            if series_idx < len(state.series):
                series = state.series[series_idx]
                if data_idx < len(series.data):
                    point = series.data[data_idx]
                    if point.metadata.get("drillable", False):
                        self._draw_drill_indicator(p, element)

    def _draw_drill_indicator(self, p: Painter, element: ArcElement) -> None:
        """Draw a small indicator showing the slice is drillable.

        Args:
            p: The painter to draw with.
            element: The arc element to draw on.
        """
        radius = self._indicator_size / 2

        # Calculate position at ~60% of the radius from center
        mid_angle = (element.start_angle + element.end_angle) / 2
        radius_offset = element.outer_radius * 0.6

        x = element.center.x + math.cos(mid_angle) * radius_offset
        y = element.center.y + math.sin(mid_angle) * radius_offset

        # Draw filled circle
        p.save()
        p.style(Style(fill=FillStyle(color=self._indicator_color)))
        if hasattr(p, "fill_circle"):
            p.fill_circle(Circle(center=Point(x=x, y=y), radius=radius))
        else:
            # Fallback: draw small square
            from castella.models.geometry import Rect, Size

            p.fill_rect(
                Rect(
                    origin=Point(x=x - radius, y=y - radius),
                    size=Size(width=radius * 2, height=radius * 2),
                )
            )
        p.restore()


class DrillableStackedBarChart(StackedBarChart):
    """StackedBarChart with visual indicators for drillable data points.

    Extends StackedBarChart to show a small indicator (dot) on stacked bars
    that have children and can be drilled into.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._indicator_color = "#ffffff"
        self._indicator_size = 6.0

    def _render_chart(self, p: Painter, layout: ChartLayout) -> None:
        """Render the stacked bar chart with drill indicators."""
        # First render the standard stacked bar chart
        super()._render_chart(p, layout)

        # Then overlay drill indicators on drillable bars
        state = self._get_state()
        if not isinstance(state, CategoricalChartData):
            return

        for element in self._elements:
            if not isinstance(element, RectElement):
                continue

            # Check if this element is drillable via metadata
            series_idx = element.series_index
            data_idx = element.data_index

            if series_idx < len(state.series):
                series = state.series[series_idx]
                if data_idx < len(series.data):
                    point = series.data[data_idx]
                    if point.metadata.get("drillable", False):
                        self._draw_drill_indicator(p, element)

    def _draw_drill_indicator(self, p: Painter, element: RectElement) -> None:
        """Draw a small indicator showing the bar segment is drillable.

        Args:
            p: The painter to draw with.
            element: The bar element to draw on.
        """
        rect = element.rect
        padding = 4.0
        radius = self._indicator_size / 2

        # Only draw if bar segment is big enough
        min_size = self._indicator_size + padding * 2
        if rect.size.width < min_size or rect.size.height < min_size:
            return

        # Position at bottom-right of the bar segment
        x = rect.origin.x + rect.size.width - radius - padding
        y = rect.origin.y + rect.size.height - radius - padding

        # Draw filled circle
        p.save()
        p.style(Style(fill=FillStyle(color=self._indicator_color)))
        if hasattr(p, "fill_circle"):
            p.fill_circle(Circle(center=Point(x=x, y=y), radius=radius))
        else:
            # Fallback: draw small square
            from castella.models.geometry import Rect, Size

            p.fill_rect(
                Rect(
                    origin=Point(x=x - radius, y=y - radius),
                    size=Size(width=radius * 2, height=radius * 2),
                )
            )
        p.restore()


class DrillableHeatmapChart(HeatmapChart):
    """HeatmapChart with visual indicators for drillable rows.

    Extends HeatmapChart to show small indicators on rows that
    have children and can be drilled into. Drill-down is row-based:
    clicking any cell in a row drills into that row's children.
    """

    def __init__(self, *args, drillable_rows: set[int] | None = None, **kwargs):
        """Initialize the drillable heatmap chart.

        Args:
            *args: Arguments passed to HeatmapChart.
            drillable_rows: Set of row indices that can be drilled into.
            **kwargs: Keyword arguments passed to HeatmapChart.
        """
        super().__init__(*args, **kwargs)
        self._drillable_rows = drillable_rows or set()
        self._indicator_color = "#ffffff"
        self._indicator_size = 6.0

    def set_drillable_rows(self, rows: set[int]) -> None:
        """Set which rows are drillable.

        Args:
            rows: Set of row indices that can be drilled into.
        """
        self._drillable_rows = rows

    def _render_chart(self, p: Painter, layout: ChartLayout) -> None:
        """Render the heatmap chart with drill indicators on rows."""
        # First render the standard heatmap chart
        super()._render_chart(p, layout)

        # Then overlay drill indicators on drillable rows
        state = self._get_state()
        if not isinstance(state, HeatmapChartData):
            return

        if not self._drillable_rows:
            return

        # Find the first cell of each drillable row and draw indicator
        for element in self._elements:
            if not isinstance(element, RectElement):
                continue

            row_idx = element.series_index
            col_idx = element.data_index

            # Only draw on the first column of drillable rows
            if col_idx == 0 and row_idx in self._drillable_rows:
                self._draw_drill_indicator(p, element)

    def _draw_drill_indicator(self, p: Painter, element: RectElement) -> None:
        """Draw a small indicator showing the row is drillable.

        Args:
            p: The painter to draw with.
            element: The first cell element of the row.
        """
        rect = element.rect
        radius = self._indicator_size / 2

        # Only draw if cell is big enough
        min_size = self._indicator_size + 4
        if rect.size.width < min_size or rect.size.height < min_size:
            return

        # Position at the left edge of the cell (indicating row is drillable)
        x = rect.origin.x + radius + 2
        y = rect.origin.y + rect.size.height / 2

        # Draw filled circle
        p.save()
        p.style(Style(fill=FillStyle(color=self._indicator_color)))
        if hasattr(p, "fill_circle"):
            p.fill_circle(Circle(center=Point(x=x, y=y), radius=radius))
        else:
            # Fallback: draw small square
            from castella.models.geometry import Rect, Size

            p.fill_rect(
                Rect(
                    origin=Point(x=x - radius, y=y - radius),
                    size=Size(width=radius * 2, height=radius * 2),
                )
            )
        p.restore()
