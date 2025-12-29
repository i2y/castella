"""Base chart widget for interactive charts."""

from __future__ import annotations

from abc import abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable, Self

from castella.core import (
    Widget,
    Painter,
    Point,
    Size,
    Rect,
    SizePolicy,
    Style,
    FillStyle,
    StrokeStyle,
    MouseEvent,
    WheelEvent,
)
from castella.models.font import Font

from castella.chart.hit_testing import HitTestable, hit_test
from castella.chart.transform import ChartTransform, ViewBounds
from castella.chart.theme import ChartTheme, get_chart_theme
from castella.chart.events import ChartHoverEvent, ChartClickEvent
from castella.chart.models.chart_data import ChartDataBase


# Callback type aliases
HoverCallback = Callable[[ChartHoverEvent], None]
ClickCallback = Callable[[ChartClickEvent], None]


@dataclass
class ChartMargins:
    """Margins around the chart plotting area.

    Attributes:
        top: Top margin in pixels.
        right: Right margin in pixels.
        bottom: Bottom margin in pixels.
        left: Left margin in pixels.
    """

    top: float = 40.0
    right: float = 20.0
    bottom: float = 40.0
    left: float = 50.0


@dataclass
class ChartLayout:
    """Computed layout dimensions for chart rendering.

    Attributes:
        bounds: Total widget bounds.
        plot_area: Area for plotting data.
        title_area: Area for the title.
        legend_area: Area for the legend.
    """

    bounds: Rect
    plot_area: Rect
    title_area: Rect
    legend_area: Rect


class BaseChart(Widget):
    """Base class for all interactive native charts.

    Provides common functionality:
    - Hit testing infrastructure
    - Tooltip display (placeholder for now)
    - Zoom/pan support
    - Theme integration
    - Event callbacks

    Subclasses must implement:
    - _build_elements(): Build hit-testable elements from data
    - _render_chart(): Render the chart content
    - _get_element_anchor(): Get anchor point for tooltips
    """

    def __init__(
        self,
        state: ChartDataBase,
        title: str = "",
        margins: ChartMargins | None = None,
        show_legend: bool = True,
        enable_tooltip: bool = True,
        enable_zoom: bool = False,
        enable_pan: bool = False,
    ):
        """Initialize the chart.

        Args:
            state: Observable chart data.
            title: Chart title.
            margins: Custom margins (or use defaults).
            show_legend: Whether to show the legend.
            enable_tooltip: Whether to show tooltips on hover.
            enable_zoom: Whether to enable wheel zoom.
            enable_pan: Whether to enable click-drag panning.
        """
        # Widget initialization
        super().__init__(
            state=state,
            size=Size(width=0, height=0),
            pos=Point(x=0, y=0),
            pos_policy=None,
            width_policy=SizePolicy.EXPANDING,
            height_policy=SizePolicy.EXPANDING,
        )

        # Chart configuration
        self._title = title
        self._margins = margins or ChartMargins()
        self._show_legend = show_legend
        self._enable_tooltip = enable_tooltip
        self._enable_zoom = enable_zoom
        self._enable_pan = enable_pan

        # Theme
        self._theme = get_chart_theme()

        # Layout (computed during redraw)
        self._layout: ChartLayout | None = None

        # Hit testing
        self._elements: list[HitTestable] = []
        self._hovered_element: HitTestable | None = None
        self._hovered_series_idx: int = -1
        self._hovered_data_idx: int = -1

        # Transform (for zoom/pan)
        self._transform: ChartTransform | None = None

        # Panning state
        self._is_panning = False
        self._last_pan_pos: Point | None = None

        # Callbacks
        self._on_hover: HoverCallback | None = None
        self._on_click: ClickCallback | None = None

    # ========== Fluent Configuration ==========

    def on_hover(self, callback: HoverCallback) -> Self:
        """Register a callback for hover events.

        Args:
            callback: Function to call when hovering over elements.

        Returns:
            Self for chaining.
        """
        self._on_hover = callback
        return self

    def on_click(self, callback: ClickCallback) -> Self:
        """Register a callback for click events.

        Args:
            callback: Function to call when clicking on elements.

        Returns:
            Self for chaining.
        """
        self._on_click = callback
        return self

    def with_title(self, title: str) -> Self:
        """Set the chart title.

        Args:
            title: The title text.

        Returns:
            Self for chaining.
        """
        self._title = title
        return self

    def with_margins(self, margins: ChartMargins) -> Self:
        """Set custom margins.

        Args:
            margins: The margins to use.

        Returns:
            Self for chaining.
        """
        self._margins = margins
        return self

    # ========== Layout Computation ==========

    def _compute_layout(self, size: Size) -> ChartLayout:
        """Compute chart regions based on size and margins.

        Args:
            size: Total widget size.

        Returns:
            ChartLayout with computed regions.
        """
        m = self._margins

        # Title height
        title_height = 30.0 if self._title else 0.0

        # Legend height (simplified - actual implementation would measure)
        legend_height = 30.0 if self._show_legend else 0.0

        bounds = Rect(origin=Point(x=0, y=0), size=size)

        plot_area = Rect(
            origin=Point(x=m.left, y=m.top + title_height),
            size=Size(
                width=max(0, size.width - m.left - m.right),
                height=max(0, size.height - m.top - m.bottom - title_height - legend_height),
            ),
        )

        title_area = Rect(
            origin=Point(x=0, y=0),
            size=Size(width=size.width, height=title_height + m.top),
        )

        legend_area = Rect(
            origin=Point(x=m.left, y=size.height - legend_height - m.bottom / 2),
            size=Size(width=max(0, size.width - m.left - m.right), height=legend_height),
        )

        return ChartLayout(
            bounds=bounds,
            plot_area=plot_area,
            title_area=title_area,
            legend_area=legend_area,
        )

    # ========== Abstract Methods ==========

    @abstractmethod
    def _build_elements(self) -> list[HitTestable]:
        """Build list of hit-testable elements from current data.

        Called during redraw when data or view changes.

        Returns:
            List of hit-testable elements.
        """
        ...

    @abstractmethod
    def _render_chart(self, p: Painter, layout: ChartLayout) -> None:
        """Render the chart content.

        Args:
            p: The painter to use.
            layout: The computed layout.
        """
        ...

    @abstractmethod
    def _get_element_anchor(self, element: HitTestable) -> Point:
        """Get anchor point for tooltip positioning.

        Args:
            element: The element to get anchor for.

        Returns:
            Point for tooltip placement.
        """
        ...

    # ========== Mouse Event Handlers ==========

    def mouse_down(self, ev: MouseEvent) -> None:
        """Handle mouse down event."""
        if self._enable_pan:
            self._is_panning = True
            self._last_pan_pos = ev.pos

    def mouse_up(self, ev: MouseEvent) -> None:
        """Handle mouse up event."""
        was_panning = self._is_panning
        self._is_panning = False

        # Only trigger click if we weren't panning (or moved very little)
        if not was_panning or (
            self._last_pan_pos is not None
            and ev.pos.distance_to(self._last_pan_pos) < 5
        ):
            self._handle_click(ev)

        self._last_pan_pos = None

    def mouse_drag(self, ev: MouseEvent) -> None:
        """Handle mouse drag event."""
        if self._is_panning and self._enable_pan and self._transform:
            if self._last_pan_pos is not None:
                delta = ev.pos - self._last_pan_pos
                self._transform.pan(delta)
                self.dirty(True)
                self.update()
            self._last_pan_pos = ev.pos

    def cursor_pos(self, ev: MouseEvent) -> None:
        """Handle cursor position event (for hover detection)."""
        if self._is_panning:
            return

        element = hit_test(self._elements, ev.pos)

        # Check if hover state changed by comparing indices
        new_series_idx = element.series_index if element else -1
        new_data_idx = element.data_index if element else -1

        if new_series_idx != self._hovered_series_idx or new_data_idx != self._hovered_data_idx:
            self._hovered_element = element
            self._hovered_series_idx = new_series_idx
            self._hovered_data_idx = new_data_idx

            if element and self._enable_tooltip:
                # Fire hover callback
                if self._on_hover:
                    self._on_hover(
                        ChartHoverEvent(
                            series_index=element.series_index,
                            data_index=element.data_index,
                            value=element.value,
                            label=element.label,
                            position=ev.pos,
                        )
                    )

            self.dirty(True)
            self.update()

    def mouse_out(self) -> None:
        """Handle mouse leaving the widget."""
        self._hovered_element = None
        self._hovered_series_idx = -1
        self._hovered_data_idx = -1
        self.dirty(True)
        self.update()

    def mouse_wheel(self, ev: WheelEvent) -> None:
        """Handle mouse wheel event (for zoom)."""
        if not self._enable_zoom or not self._transform:
            return

        # Zoom factor based on wheel delta
        factor = 1.1 if ev.y_offset > 0 else 0.9
        self._transform.zoom(factor, ev.pos)
        self.dirty(True)
        self.update()

    # ========== Click Handling ==========

    def _handle_click(self, ev: MouseEvent) -> None:
        """Handle click on chart element."""
        element = hit_test(self._elements, ev.pos)

        if element and self._on_click:
            self._on_click(
                ChartClickEvent(
                    series_index=element.series_index,
                    data_index=element.data_index,
                    value=element.value,
                    label=element.label,
                    position=ev.pos,
                )
            )

    # ========== Rendering ==========

    def redraw(self, p: Painter, completely: bool) -> None:
        """Render the chart.

        Args:
            p: The painter to use.
            completely: Whether to redraw completely.
        """
        size = self.get_size()
        if size.width <= 0 or size.height <= 0:
            return

        self._layout = self._compute_layout(size)

        # Update transform screen size
        if self._transform:
            self._transform.set_screen_size(size)

        # Build hit-testable elements
        self._elements = self._build_elements()

        # Draw background
        self._draw_background(p)

        # Draw title
        if self._title:
            self._render_title(p)

        # Draw chart content (delegated to subclass)
        p.save()
        self._render_chart(p, self._layout)
        p.restore()

    def _draw_background(self, p: Painter) -> None:
        """Draw chart background."""
        if self._layout is None:
            return

        bg_style = Style(
            fill=FillStyle(color=self._theme.background),
            border_radius=4,
        )
        p.style(bg_style)
        p.fill_rect(self._layout.bounds)

    def _render_title(self, p: Painter) -> None:
        """Render the chart title."""
        if self._layout is None:
            return

        title_style = Style(
            fill=FillStyle(color=self._theme.title_color),
            font=Font(size=16),
        )
        p.style(title_style)

        # Center title
        title_width = p.measure_text(self._title)
        x = (self._layout.bounds.size.width - title_width) / 2
        y = self._layout.title_area.origin.y + 24

        p.fill_text(self._title, Point(x=x, y=y), None)

    # ========== Measurement ==========

    def measure(self, p: Painter) -> Size:
        """Measure the chart's preferred size.

        Charts prefer to fill available space.

        Args:
            p: The painter for measurement.

        Returns:
            Preferred size.
        """
        return Size(width=400, height=300)

    # ========== Helper Methods ==========

    def _get_state(self) -> ChartDataBase:
        """Get the chart data state.

        Returns:
            The chart data.
        """
        from typing import cast
        return cast(ChartDataBase, self._state)

    def get_series_color(self, index: int) -> str:
        """Get the color for a series by index.

        Args:
            index: Series index.

        Returns:
            Hex color string.
        """
        return self._theme.get_series_color(index)

    def is_element_hovered(self, series_index: int, data_index: int) -> bool:
        """Check if the element at the given indices is currently hovered.

        Args:
            series_index: Series index.
            data_index: Data index within the series.

        Returns:
            True if this element is hovered.
        """
        return (
            self._hovered_series_idx == series_index
            and self._hovered_data_idx == data_index
        )

    def lighten_color(self, hex_color: str, amount: float = 0.2) -> str:
        """Lighten a hex color.

        Args:
            hex_color: Hex color string (e.g., "#3b82f6").
            amount: Amount to lighten (0-1).

        Returns:
            Lightened hex color.
        """
        # Parse hex color
        hex_color = hex_color.lstrip("#")
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)

        # Lighten
        r = min(255, int(r + (255 - r) * amount))
        g = min(255, int(g + (255 - g) * amount))
        b = min(255, int(b + (255 - b) * amount))

        return f"#{r:02x}{g:02x}{b:02x}"
