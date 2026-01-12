"""Bar chart widget."""

from __future__ import annotations

from typing import Self

from castella.core import (
    Painter,
    Point,
    Size,
    Rect,
    Style,
    FillStyle,
    StrokeStyle,
)
from castella.models.font import Font

from castella.chart.base import BaseChart, ChartLayout
from castella.chart.hit_testing import HitTestable, RectElement, LegendItemElement
from castella.chart.scales import LinearScale, BandScale
from castella.chart.models import CategoricalChartData


class BarChart(BaseChart):
    """Interactive bar chart widget.

    Renders categorical data as vertical or horizontal bars with
    full interactivity including hover highlighting and click events.

    Example:
        ```python
        from castella.chart import BarChart, CategoricalChartData, CategoricalSeries

        data = CategoricalChartData(title="Sales")
        data.add_series(CategoricalSeries.from_values(
            name="2024",
            categories=["Q1", "Q2", "Q3", "Q4"],
            values=[100, 120, 90, 150],
        ))

        chart = BarChart(data).on_click(lambda ev: print(ev.label))
        ```
    """

    def __init__(
        self,
        state: CategoricalChartData,
        horizontal: bool = False,
        show_values: bool = False,
        bar_gap: float = 0.2,
        group_gap: float = 0.1,
        **kwargs,
    ):
        """Initialize the bar chart.

        Args:
            state: Categorical chart data.
            horizontal: Whether to render horizontal bars.
            show_values: Whether to show value labels on bars.
            bar_gap: Gap between bar groups (0-1, as fraction of category width).
            group_gap: Gap between bars within a group (0-1).
            **kwargs: Additional arguments passed to BaseChart.
        """
        super().__init__(state=state, **kwargs)
        self._horizontal = horizontal
        self._show_values = show_values
        self._bar_gap = bar_gap
        self._group_gap = group_gap

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

    def _build_elements(self) -> list[HitTestable]:
        """Build hit-testable bar rectangles."""
        state = self._get_state()
        if not isinstance(state, CategoricalChartData):
            return []

        if not state.series or self._layout is None:
            return []

        elements: list[HitTestable] = []
        plot = self._layout.plot_area

        # Get all categories
        categories = state.all_categories
        if not categories:
            return []

        # Count visible series
        visible_series = [
            (i, s) for i, s in enumerate(state.series) if state.is_series_visible(i)
        ]
        if not visible_series:
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

        max_value = state.max_value
        if max_value <= 0:
            max_value = 1.0

        val_scale = LinearScale.from_data(
            [0, max_value],
            range_min=plot.y + plot.height if not self._horizontal else plot.x,
            range_max=plot.y if not self._horizontal else plot.x + plot.width,
            include_zero=True,
        )

        # Calculate bar width for grouped bars
        num_series = len(visible_series)
        bar_width = cat_scale.bandwidth / num_series * (1 - self._group_gap)
        bar_offset = cat_scale.bandwidth / num_series

        # Build rectangles for each bar
        for series_pos, (series_idx, series) in enumerate(visible_series):
            for data_idx, point in enumerate(series.data):
                cat = point.category
                value = point.value

                if self._horizontal:
                    # Horizontal bars
                    y = cat_scale(cat) + series_pos * bar_offset
                    x = plot.x
                    width = val_scale(value) - plot.x
                    height = bar_width
                else:
                    # Vertical bars
                    x = cat_scale(cat) + series_pos * bar_offset
                    y = val_scale(value)
                    width = bar_width
                    height = val_scale(0) - val_scale(value)

                elements.append(
                    RectElement(
                        rect=Rect(
                            origin=Point(x=x, y=y),
                            size=Size(width=max(0, width), height=max(0, height)),
                        ),
                        series_index=series_idx,
                        data_index=data_idx,
                        value=value,
                        label=point.label or cat,
                    )
                )

        return elements

    def _render_chart(self, p: Painter, layout: ChartLayout) -> None:
        """Render the bar chart."""
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
            data_idx = element.data_index
            series = (
                state.series[series_idx] if series_idx < len(state.series) else None
            )
            color = series.style.color if series else self.get_series_color(series_idx)

            # Check for per-point color in metadata
            if series and data_idx < len(series.data):
                point_color = series.data[data_idx].metadata.get("color")
                if point_color:
                    color = point_color

            # Highlight on hover
            if self.is_element_hovered(element.series_index, element.data_index):
                color = self.lighten_color(color, 0.2)

            # Selection indicator
            if state.is_selected(element.series_index, element.data_index):
                # Draw selection border
                p.style(Style(stroke=StrokeStyle(color="#ffffff")))
                p.stroke_rect(element.rect)

            # Draw bar
            p.style(Style(fill=FillStyle(color=color), border_radius=2))
            p.fill_rect(element.rect)

            # Value label
            if self._show_values:
                self._render_value_label(p, element)

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
        axis_style = Style(
            fill=FillStyle(color=self._theme.axis_color),
        )
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
                # Labels on left
                x = plot.x - 8
                y = cat_scale.center(cat)
                text_width = p.measure_text(cat)
                p.fill_text(cat, Point(x=x - text_width, y=y + 4), None)
            else:
                # Labels on bottom
                x = cat_scale.center(cat)
                y = plot.y + plot.height + 16
                text_width = p.measure_text(cat)
                p.fill_text(cat, Point(x=x - text_width / 2, y=y), None)

        # Value axis labels (Y for vertical, X for horizontal)
        max_value = state.max_value
        if max_value <= 0:
            max_value = 1.0

        val_scale = LinearScale.from_data(
            [0, max_value],
            range_min=plot.y + plot.height if not self._horizontal else plot.x,
            range_max=plot.y if not self._horizontal else plot.x + plot.width,
            include_zero=True,
        )

        tick_values = val_scale.ticks(5)
        for tick in tick_values:
            if self._horizontal:
                # Ticks on bottom
                x = val_scale(tick)
                y = plot.y + plot.height + 16
                label = f"{tick:.0f}"
                text_width = p.measure_text(label)
                p.fill_text(label, Point(x=x - text_width / 2, y=y), None)
            else:
                # Ticks on left
                x = plot.x - 8
                y = val_scale(tick)
                label = f"{tick:.0f}"
                text_width = p.measure_text(label)
                p.fill_text(label, Point(x=x - text_width, y=y + 4), None)

    def _render_value_label(self, p: Painter, element: RectElement) -> None:
        """Render value label on a bar."""
        label = f"{element.value:.1f}"
        label_style = Style(
            fill=FillStyle(color=self._theme.text_color),
            font=Font(size=10),
        )
        p.style(label_style)

        text_width = p.measure_text(label)

        if self._horizontal:
            x = element.rect.x + element.rect.width + 4
            y = element.rect.center.y + 4
        else:
            x = element.rect.center.x - text_width / 2
            y = element.rect.y - 4

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
