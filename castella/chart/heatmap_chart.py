"""Heatmap chart widget for 2D data visualization."""

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
from castella.utils.color import contrast_text_color

from castella.chart.base import BaseChart, ChartLayout, ChartMargins
from castella.chart.hit_testing import HitTestable, RectElement
from castella.chart.colormap import Colormap, ColormapType, get_colormap
from castella.chart.models.heatmap_data import HeatmapChartData


class HeatmapChart(BaseChart):
    """Interactive heatmap chart widget.

    Displays a 2D matrix of values as colored cells with:
    - Configurable colormaps (Viridis, Plasma, Inferno, Magma)
    - X-axis labels (column headers)
    - Y-axis labels (row headers)
    - Color bar legend showing value-to-color mapping
    - Tooltips on hover showing cell value
    - Optional cell value annotations

    Example:
        >>> from castella.chart import HeatmapChart, HeatmapChartData, ColormapType
        >>>
        >>> data = HeatmapChartData.from_2d_array(
        ...     values=[[1, 2, 3], [4, 5, 6], [7, 8, 9]],
        ...     row_labels=["A", "B", "C"],
        ...     column_labels=["X", "Y", "Z"],
        ...     title="Correlation Matrix",
        ... )
        >>>
        >>> chart = (
        ...     HeatmapChart(data, colormap=ColormapType.VIRIDIS)
        ...     .show_values(True)
        ...     .show_colorbar(True)
        ... )
    """

    # Color bar configuration
    COLORBAR_WIDTH = 20.0
    COLORBAR_PADDING = 10.0
    COLORBAR_TICKS = 5

    def __init__(
        self,
        state: HeatmapChartData,
        colormap: Colormap | ColormapType | str = ColormapType.VIRIDIS,
        show_values: bool = False,
        show_colorbar: bool = True,
        cell_gap: float = 1.0,
        value_font_size: float = 10.0,
        **kwargs,
    ):
        """Initialize the heatmap chart.

        Args:
            state: Heatmap chart data.
            colormap: Colormap to use (Colormap instance, ColormapType, or string).
            show_values: Whether to show value annotations in cells.
            show_colorbar: Whether to show the color bar legend.
            cell_gap: Gap between cells in pixels.
            value_font_size: Font size for value annotations.
            **kwargs: Additional arguments passed to BaseChart.
        """
        # Adjust margins to accommodate colorbar on the right
        default_margins = kwargs.get("margins") or ChartMargins()
        if show_colorbar:
            kwargs["margins"] = ChartMargins(
                top=default_margins.top,
                right=default_margins.right
                + self.COLORBAR_WIDTH
                + self.COLORBAR_PADDING
                + 50,
                bottom=default_margins.bottom,
                left=default_margins.left + 30,  # Extra space for row labels
            )
        else:
            kwargs["margins"] = ChartMargins(
                top=default_margins.top,
                right=default_margins.right,
                bottom=default_margins.bottom,
                left=default_margins.left + 30,  # Extra space for row labels
            )

        # Heatmaps don't use the standard legend
        kwargs.setdefault("show_legend", False)

        super().__init__(state=state, **kwargs)

        # Resolve colormap
        if isinstance(colormap, (ColormapType, str)):
            self._colormap = get_colormap(colormap)
        else:
            self._colormap = colormap

        self._show_values = show_values
        self._show_colorbar = show_colorbar
        self._cell_gap = cell_gap
        self._value_font_size = value_font_size

    # ========== Fluent Configuration ==========

    def colormap(self, cmap: Colormap | ColormapType | str) -> Self:
        """Set the colormap.

        Args:
            cmap: Colormap to use.

        Returns:
            Self for chaining.
        """
        if isinstance(cmap, (ColormapType, str)):
            self._colormap = get_colormap(cmap)
        else:
            self._colormap = cmap
        self.dirty(True)
        return self

    def show_values(self, show: bool = True) -> Self:
        """Set whether to show value annotations.

        Args:
            show: Whether to show values.

        Returns:
            Self for chaining.
        """
        self._show_values = show
        self.dirty(True)
        return self

    def show_colorbar(self, show: bool = True) -> Self:
        """Set whether to show the color bar legend.

        Args:
            show: Whether to show colorbar.

        Returns:
            Self for chaining.
        """
        self._show_colorbar = show
        self.dirty(True)
        return self

    def cell_gap(self, gap: float) -> Self:
        """Set the gap between cells.

        Args:
            gap: Gap in pixels.

        Returns:
            Self for chaining.
        """
        self._cell_gap = gap
        self.dirty(True)
        return self

    # ========== BaseChart Implementation ==========

    def _build_elements(self) -> list[HitTestable]:
        """Build hit-testable cell rectangles."""
        state = self._get_state()
        if not isinstance(state, HeatmapChartData):
            return []

        if not state.values or self._layout is None:
            return []

        elements: list[HitTestable] = []
        plot = self._layout.plot_area

        num_rows = state.num_rows
        num_cols = state.num_cols

        if num_rows == 0 or num_cols == 0:
            return []

        # Calculate cell dimensions
        cell_width = (plot.size.width - (num_cols - 1) * self._cell_gap) / num_cols
        cell_height = (plot.size.height - (num_rows - 1) * self._cell_gap) / num_rows

        # Build rectangles for each cell
        for row in range(num_rows):
            for col in range(num_cols):
                value = state.get_value(row, col)

                x = plot.origin.x + col * (cell_width + self._cell_gap)
                y = plot.origin.y + row * (cell_height + self._cell_gap)

                # Label includes row and column labels
                row_label = state.get_row_label(row)
                col_label = state.get_column_label(col)
                label = f"{row_label}, {col_label}"

                elements.append(
                    RectElement(
                        rect=Rect(
                            origin=Point(x=x, y=y),
                            size=Size(width=cell_width, height=cell_height),
                        ),
                        series_index=row,  # Use row as series_index
                        data_index=col,  # Use col as data_index
                        value=value,
                        label=label,
                    )
                )

        return elements

    def _render_chart(self, p: Painter, layout: ChartLayout) -> None:
        """Render the heatmap chart."""
        state = self._get_state()
        if not isinstance(state, HeatmapChartData):
            return

        plot = layout.plot_area
        if plot.size.width <= 0 or plot.size.height <= 0:
            return

        num_rows = state.num_rows
        num_cols = state.num_cols

        if num_rows == 0 or num_cols == 0:
            return

        # Draw cells
        for element in self._elements:
            if not isinstance(element, RectElement):
                continue

            row = element.series_index
            col = element.data_index
            value = element.value

            # Get color from colormap
            normalized = state.normalize_value(value)
            color = self._colormap(normalized)

            # Highlight on hover
            if self.is_element_hovered(row, col):
                color = self.lighten_color(color, 0.2)
                # Draw hover border
                p.style(
                    Style(stroke=StrokeStyle(color=self._theme.text_color, width=2))
                )
                p.stroke_rect(element.rect)

            # Draw cell
            p.style(Style(fill=FillStyle(color=color)))
            p.fill_rect(element.rect)

            # Draw value annotation
            if self._show_values:
                self._render_cell_value(p, element.rect, value, state)

        # Draw axes
        self._render_axes(p, layout, state)

        # Draw color bar
        if self._show_colorbar:
            self._render_colorbar(p, layout, state)

    def _render_cell_value(
        self,
        p: Painter,
        rect: Rect,
        value: float,
        state: HeatmapChartData,
    ) -> None:
        """Render value annotation in a cell."""
        text = state.value_format.format(value)

        # Choose contrasting text color based on cell brightness
        normalized = state.normalize_value(value)
        cell_color = self._colormap(normalized)
        text_color = contrast_text_color(cell_color)

        p.style(
            Style(
                fill=FillStyle(color=text_color),
                font=Font(size=self._value_font_size),
            )
        )

        text_width = p.measure_text(text)
        x = rect.center.x - text_width / 2
        y = rect.center.y + self._value_font_size / 3

        p.fill_text(text, Point(x=x, y=y), None)

    def _render_axes(
        self,
        p: Painter,
        layout: ChartLayout,
        state: HeatmapChartData,
    ) -> None:
        """Render row and column labels."""
        plot = layout.plot_area

        num_rows = state.num_rows
        num_cols = state.num_cols

        if num_rows == 0 or num_cols == 0:
            return

        cell_width = (plot.size.width - (num_cols - 1) * self._cell_gap) / num_cols
        cell_height = (plot.size.height - (num_rows - 1) * self._cell_gap) / num_rows

        label_style = Style(
            fill=FillStyle(color=self._theme.text_color),
            font=Font(size=11),
        )
        p.style(label_style)

        # Column labels (top)
        for col in range(num_cols):
            label = state.get_column_label(col)
            x = plot.origin.x + col * (cell_width + self._cell_gap) + cell_width / 2
            y = plot.origin.y - 8

            text_width = p.measure_text(label)
            p.fill_text(label, Point(x=x - text_width / 2, y=y), None)

        # Row labels (left)
        for row in range(num_rows):
            label = state.get_row_label(row)
            x = plot.origin.x - 8
            y = (
                plot.origin.y
                + row * (cell_height + self._cell_gap)
                + cell_height / 2
                + 4
            )

            text_width = p.measure_text(label)
            p.fill_text(label, Point(x=x - text_width, y=y), None)

    def _render_colorbar(
        self,
        p: Painter,
        layout: ChartLayout,
        state: HeatmapChartData,
    ) -> None:
        """Render the color bar legend."""
        plot = layout.plot_area

        # Position colorbar to the right of the plot area
        bar_x = plot.origin.x + plot.size.width + self.COLORBAR_PADDING
        bar_y = plot.origin.y
        bar_height = plot.size.height

        # Draw gradient bar using small rectangles
        num_segments = 50
        segment_height = bar_height / num_segments

        for i in range(num_segments):
            # Invert: high values at top
            normalized = 1.0 - (i / num_segments)
            color = self._colormap(normalized)

            y = bar_y + i * segment_height

            p.style(Style(fill=FillStyle(color=color)))
            p.fill_rect(
                Rect(
                    origin=Point(x=bar_x, y=y),
                    size=Size(width=self.COLORBAR_WIDTH, height=segment_height + 1),
                )
            )

        # Draw border
        p.style(Style(stroke=StrokeStyle(color=self._theme.border_color)))
        p.stroke_rect(
            Rect(
                origin=Point(x=bar_x, y=bar_y),
                size=Size(width=self.COLORBAR_WIDTH, height=bar_height),
            )
        )

        # Draw tick marks and labels
        v_min = state.effective_min
        v_max = state.effective_max

        tick_style = Style(
            fill=FillStyle(color=self._theme.text_color),
            font=Font(size=10),
        )
        p.style(tick_style)

        for i in range(self.COLORBAR_TICKS + 1):
            t = i / self.COLORBAR_TICKS
            value = v_max - t * (v_max - v_min)  # Inverted: high at top
            y = bar_y + t * bar_height

            # Tick mark
            p.fill_rect(
                Rect(
                    origin=Point(x=bar_x + self.COLORBAR_WIDTH, y=y),
                    size=Size(width=4, height=1),
                )
            )

            # Label
            label = state.value_format.format(value)
            p.fill_text(
                label,
                Point(x=bar_x + self.COLORBAR_WIDTH + 8, y=y + 4),
                None,
            )

    def _get_element_anchor(self, element: HitTestable) -> Point:
        """Get anchor point for tooltip positioning."""
        if isinstance(element, RectElement):
            # Position tooltip above the cell
            return Point(
                x=element.rect.center.x,
                y=element.rect.origin.y,
            )
        return Point(x=0, y=0)
