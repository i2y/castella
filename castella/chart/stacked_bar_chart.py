"""Stacked bar chart widget."""

from __future__ import annotations

from typing import Self

from castella.core import (
    Painter,
    Point,
    Size,
    Rect,
    Style,
    FillStyle,
)
from castella.models.font import Font

from castella.chart.base import BaseChart, ChartLayout
from castella.chart.hit_testing import HitTestable, RectElement, LegendItemElement
from castella.chart.scales import LinearScale, BandScale
from castella.chart.models import CategoricalChartData


class StackedBarChart(BaseChart):
    """Interactive stacked bar chart widget.

    Renders multiple series as stacked bars for each category.
    Useful for showing part-to-whole relationships over categories.

    Example:
        ```python
        from castella.chart import StackedBarChart, CategoricalChartData, CategoricalSeries

        data = CategoricalChartData(title="Revenue by Region")
        data.add_series(CategoricalSeries.from_values(
            name="North",
            categories=["Q1", "Q2", "Q3", "Q4"],
            values=[100, 120, 90, 150],
        ))
        data.add_series(CategoricalSeries.from_values(
            name="South",
            categories=["Q1", "Q2", "Q3", "Q4"],
            values=[80, 100, 110, 95],
        ))

        chart = StackedBarChart(data)
        ```
    """

    def __init__(
        self,
        state: CategoricalChartData,
        horizontal: bool = False,
        show_values: bool = False,
        bar_gap: float = 0.2,
        show_totals: bool = False,
        normalized: bool = False,
        **kwargs,
    ):
        """Initialize the stacked bar chart.

        Args:
            state: Categorical chart data.
            horizontal: Whether to render horizontal bars.
            show_values: Whether to show value labels on bars.
            bar_gap: Gap between bars (0-1, as fraction of category width).
            show_totals: Whether to show total value above each stack.
            normalized: Whether to normalize to 100% (percentage stacking).
            **kwargs: Additional arguments passed to BaseChart.
        """
        super().__init__(state=state, **kwargs)
        self._horizontal = horizontal
        self._show_values = show_values
        self._bar_gap = bar_gap
        self._show_totals = show_totals
        self._normalized = normalized

    def horizontal(self, horizontal: bool = True) -> Self:
        """Set horizontal bar orientation.

        Args:
            horizontal: Whether to use horizontal bars.

        Returns:
            Self for chaining.
        """
        self._horizontal = horizontal
        return self

    def show_values(self, show: bool = True) -> Self:
        """Set whether to show value labels.

        Args:
            show: Whether to show values.

        Returns:
            Self for chaining.
        """
        self._show_values = show
        return self

    def normalized(self, normalize: bool = True) -> Self:
        """Set whether to use percentage stacking (100% stacked).

        Args:
            normalize: Whether to normalize.

        Returns:
            Self for chaining.
        """
        self._normalized = normalize
        return self

    def _calculate_stacked_values(
        self, state: CategoricalChartData
    ) -> dict[str, list[tuple[float, float, int, int]]]:
        """Calculate stacked bar positions.

        Returns:
            Dict mapping category to list of (start, end, series_idx, data_idx) tuples.
        """
        categories = state.all_categories
        stacked: dict[str, list[tuple[float, float, int, int]]] = {
            cat: [] for cat in categories
        }

        # Calculate totals for normalization
        totals: dict[str, float] = {cat: 0 for cat in categories}
        for series in state.series:
            for point in series.data:
                totals[point.category] += point.value

        # Build stacked positions
        current_positions: dict[str, float] = {cat: 0 for cat in categories}

        for series_idx, series in enumerate(state.series):
            if not state.is_series_visible(series_idx):
                continue

            for data_idx, point in enumerate(series.data):
                cat = point.category
                start = current_positions[cat]

                if self._normalized and totals[cat] > 0:
                    # Normalize to percentage
                    value = (point.value / totals[cat]) * 100
                else:
                    value = point.value

                end = start + value
                stacked[cat].append((start, end, series_idx, data_idx))
                current_positions[cat] = end

        return stacked

    def _get_max_stacked_value(self, state: CategoricalChartData) -> float:
        """Get the maximum stacked value across all categories."""
        if self._normalized:
            return 100.0

        categories = state.all_categories
        max_val = 0

        for cat in categories:
            total = 0
            for series in state.series:
                if state.is_series_visible(state.series.index(series)):
                    for point in series.data:
                        if point.category == cat:
                            total += point.value
            max_val = max(max_val, total)

        return max_val if max_val > 0 else 1.0

    def _build_elements(self) -> list[HitTestable]:
        """Build hit-testable bar rectangles."""
        state = self._get_state()
        if not isinstance(state, CategoricalChartData):
            return []

        if not state.series or self._layout is None:
            return []

        elements: list[HitTestable] = []
        plot = self._layout.plot_area

        categories = state.all_categories
        if not categories:
            return []

        # Create scales
        cat_scale = BandScale(
            categories=categories,
            range_min=plot.x if not self._horizontal else plot.y,
            range_max=(plot.x + plot.width)
            if not self._horizontal
            else (plot.y + plot.height),
            padding_inner=self._bar_gap,
            padding_outer=self._bar_gap / 2,
        )

        max_value = self._get_max_stacked_value(state)
        val_scale = LinearScale.from_data(
            [0, max_value],
            range_min=plot.y + plot.height if not self._horizontal else plot.x,
            range_max=plot.y if not self._horizontal else plot.x + plot.width,
            include_zero=True,
        )

        # Calculate stacked positions
        stacked = self._calculate_stacked_values(state)

        # Build rectangles
        for cat in categories:
            bar_start = cat_scale(cat)
            bar_width = cat_scale.bandwidth

            for start_val, end_val, series_idx, data_idx in stacked[cat]:
                series = state.series[series_idx]
                point = series.data[data_idx]

                if self._horizontal:
                    x = val_scale(0) + (val_scale(start_val) - val_scale(0))
                    y = bar_start
                    width = val_scale(end_val) - val_scale(start_val)
                    height = bar_width
                    # Fix for horizontal: swap the scale direction
                    x = plot.x + (start_val / max_value) * plot.width
                    width = ((end_val - start_val) / max_value) * plot.width
                else:
                    x = bar_start
                    y = val_scale(end_val)
                    width = bar_width
                    height = val_scale(start_val) - val_scale(end_val)

                elements.append(
                    RectElement(
                        rect=Rect(
                            origin=Point(x=x, y=y),
                            size=Size(width=max(0, width), height=max(0, height)),
                        ),
                        series_index=series_idx,
                        data_index=data_idx,
                        value=point.value,
                        label=f"{cat}: {series.name}",
                    )
                )

        return elements

    def _render_chart(self, p: Painter, layout: ChartLayout) -> None:
        """Render the stacked bar chart."""
        state = self._get_state()
        if not isinstance(state, CategoricalChartData):
            return

        plot = layout.plot_area
        if plot.width <= 0 or plot.height <= 0:
            return

        # Draw axes
        self._render_axes(p, layout, state)

        # Draw bars
        for element in self._elements:
            if not isinstance(element, RectElement):
                continue

            series_idx = element.series_index
            series = (
                state.series[series_idx] if series_idx < len(state.series) else None
            )
            color = series.style.color if series else self.get_series_color(series_idx)

            # Highlight on hover
            if self.is_element_hovered(element.series_index, element.data_index):
                color = self.lighten_color(color, 0.2)

            # Draw bar
            p.style(Style(fill=FillStyle(color=color)))
            p.fill_rect(element.rect)

            # Value label
            if self._show_values and element.rect.height > 15:
                self._render_value_label(p, element)

        # Draw totals
        if self._show_totals:
            self._render_totals(p, layout, state)

        # Draw legend
        if self._show_legend:
            self._render_legend(p, layout, state)

    def _render_axes(
        self,
        p: Painter,
        layout: ChartLayout,
        state: CategoricalChartData,
    ) -> None:
        """Draw X and Y axes with labels."""
        plot = layout.plot_area

        # Axis lines
        axis_style = Style(fill=FillStyle(color=self._theme.axis_color))
        p.style(axis_style)

        # X axis line
        p.fill_rect(
            Rect(
                origin=Point(x=plot.x, y=plot.y + plot.height),
                size=Size(width=plot.width, height=1),
            )
        )

        # Y axis line
        p.fill_rect(
            Rect(
                origin=Point(x=plot.x, y=plot.y),
                size=Size(width=1, height=plot.height),
            )
        )

        # Category labels
        categories = state.all_categories
        if not categories:
            return

        cat_scale = BandScale(
            categories=categories,
            range_min=plot.x if not self._horizontal else plot.y,
            range_max=(plot.x + plot.width)
            if not self._horizontal
            else (plot.y + plot.height),
            padding_inner=self._bar_gap,
            padding_outer=self._bar_gap / 2,
        )

        label_style = Style(
            fill=FillStyle(color=self._theme.text_color),
            font=Font(size=11),
        )
        p.style(label_style)

        for cat in categories:
            if self._horizontal:
                x = plot.x - 8
                y = cat_scale.center(cat)
                text_width = p.measure_text(cat)
                p.fill_text(cat, Point(x=x - text_width, y=y + 4), None)
            else:
                x = cat_scale.center(cat)
                y = plot.y + plot.height + 16
                text_width = p.measure_text(cat)
                p.fill_text(cat, Point(x=x - text_width / 2, y=y), None)

        # Value axis labels
        max_value = self._get_max_stacked_value(state)
        val_scale = LinearScale.from_data(
            [0, max_value],
            range_min=plot.y + plot.height if not self._horizontal else plot.x,
            range_max=plot.y if not self._horizontal else plot.x + plot.width,
            include_zero=True,
        )

        tick_values = val_scale.ticks(5)
        for tick in tick_values:
            suffix = "%" if self._normalized else ""
            if self._horizontal:
                x = val_scale(tick)
                y = plot.y + plot.height + 16
                label = f"{tick:.0f}{suffix}"
                text_width = p.measure_text(label)
                p.fill_text(label, Point(x=x - text_width / 2, y=y), None)
            else:
                x = plot.x - 8
                y = val_scale(tick)
                label = f"{tick:.0f}{suffix}"
                text_width = p.measure_text(label)
                p.fill_text(label, Point(x=x - text_width, y=y + 4), None)

    def _render_value_label(self, p: Painter, element: RectElement) -> None:
        """Render value label on a bar segment."""
        value = element.value
        if self._normalized:
            # Show original value, not percentage
            label = f"{value:.0f}"
        else:
            label = f"{value:.0f}"

        label_style = Style(
            fill=FillStyle(color="#ffffff"),
            font=Font(size=9),
        )
        p.style(label_style)

        text_width = p.measure_text(label)

        if self._horizontal:
            x = element.rect.center.x - text_width / 2
            y = element.rect.center.y + 3
        else:
            x = element.rect.center.x - text_width / 2
            y = element.rect.center.y + 3

        # Only draw if there's enough space
        if element.rect.width > text_width + 4:
            p.fill_text(label, Point(x=x, y=y), None)

    def _render_totals(
        self,
        p: Painter,
        layout: ChartLayout,
        state: CategoricalChartData,
    ) -> None:
        """Render total values above each stack."""
        if self._normalized:
            return  # Don't show totals for normalized charts

        plot = layout.plot_area
        categories = state.all_categories

        cat_scale = BandScale(
            categories=categories,
            range_min=plot.x if not self._horizontal else plot.y,
            range_max=(plot.x + plot.width)
            if not self._horizontal
            else (plot.y + plot.height),
            padding_inner=self._bar_gap,
            padding_outer=self._bar_gap / 2,
        )

        max_value = self._get_max_stacked_value(state)
        val_scale = LinearScale.from_data(
            [0, max_value],
            range_min=plot.y + plot.height if not self._horizontal else plot.x,
            range_max=plot.y if not self._horizontal else plot.x + plot.width,
            include_zero=True,
        )

        label_style = Style(
            fill=FillStyle(color=self._theme.text_color),
            font=Font(size=10),
        )
        p.style(label_style)

        # Calculate totals
        stacked = self._calculate_stacked_values(state)

        for cat in categories:
            if not stacked[cat]:
                continue

            # Get the top of the stack
            _, total, _, _ = stacked[cat][-1]
            label = f"{total:.0f}"
            text_width = p.measure_text(label)

            if self._horizontal:
                x = plot.x + (total / max_value) * plot.width + 4
                y = cat_scale.center(cat) + 4
            else:
                x = cat_scale.center(cat) - text_width / 2
                y = val_scale(total) - 4

            p.fill_text(label, Point(x=x, y=y), None)

    def _render_legend(
        self,
        p: Painter,
        layout: ChartLayout,
        state: CategoricalChartData,
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

            # Color box
            p.style(Style(fill=FillStyle(color=color)))
            p.fill_rect(
                Rect(
                    origin=Point(x=x, y=y),
                    size=Size(width=box_size, height=box_size),
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
        if isinstance(element, RectElement):
            if self._horizontal:
                return Point(
                    x=element.rect.x + element.rect.width,
                    y=element.rect.center.y,
                )
            else:
                return Point(
                    x=element.rect.center.x,
                    y=element.rect.y,
                )
        return Point(x=0, y=0)
