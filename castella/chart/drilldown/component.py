"""DrillDownChart - Wrapper component for drill-down chart functionality."""

from __future__ import annotations

from typing import Any, Callable, Self, Type

from castella.core import Component, Widget, SizePolicy
from castella.column import Column
from castella.row import Row
from castella.button import Button
from castella.text import Text
from castella.spacer import Spacer

from castella.chart.base import BaseChart
from castella.chart.bar_chart import BarChart
from castella.chart.pie_chart import PieChart
from castella.chart.stacked_bar_chart import StackedBarChart
from castella.chart.heatmap_chart import HeatmapChart
from castella.chart.events import ChartClickEvent
from castella.chart.models.hierarchy import HierarchicalChartData

from .state import DrillDownState
from .breadcrumb import Breadcrumb
from .events import DrillDownEvent, DrillUpEvent
from .drillable_charts import (
    DrillableBarChart,
    DrillablePieChart,
    DrillableStackedBarChart,
    DrillableHeatmapChart,
)


class DrillDownChart(Component):
    """Wrapper component that adds drill-down/drill-up capability to charts.

    Wraps existing chart types (BarChart, PieChart, StackedBarChart) and
    automatically handles navigation when clicking on data points that
    have children.

    The component displays:
    - Navigation bar with back button and breadcrumbs
    - Current level name indicator
    - The chart itself with drill-down interaction

    Example:
        ```python
        from castella.chart import (
            DrillDownChart, HierarchicalChartData, HierarchicalNode,
            DataPoint, BarChart,
        )

        # Create hierarchical data
        data = HierarchicalChartData(
            title="Sales by Region",
            root=HierarchicalNode(
                id="world",
                label="World",
                level_name="Region",
                data=[
                    DataPoint(category="North America", value=1000),
                    DataPoint(category="Europe", value=800),
                ],
            ),
        )

        # Add drill-down data
        data.root.add_child("North America", HierarchicalNode(
            id="na",
            label="North America",
            level_name="Country",
            data=[DataPoint(category="USA", value=600), ...],
        ))

        # Create drill-down chart
        chart = DrillDownChart(data, chart_type=BarChart)
        chart.on_drill_down(lambda ev: print(f"Drilled into {ev.to_node_id}"))
        ```
    """

    def __init__(
        self,
        data: HierarchicalChartData,
        chart_type: Type[BaseChart] = BarChart,
        show_breadcrumb: bool = True,
        show_back_button: bool = True,
        show_level_name: bool = True,
        **chart_kwargs: Any,
    ):
        """Initialize the drill-down chart.

        Args:
            data: Hierarchical chart data.
            chart_type: The chart class to use (BarChart, PieChart, etc.).
            show_breadcrumb: Whether to show breadcrumb navigation.
            show_back_button: Whether to show a back button.
            show_level_name: Whether to show the current level name.
            **chart_kwargs: Additional arguments passed to the chart.
        """
        super().__init__()

        self._hierarchical_data = data
        self._chart_type = chart_type
        self._show_breadcrumb = show_breadcrumb
        self._show_back_button = show_back_button
        self._show_level_name = show_level_name
        self._chart_kwargs = chart_kwargs

        # Create drill-down state
        self._drill_state = DrillDownState(hierarchical_data=data)
        self._drill_state.attach(self)

        # User callbacks
        self._on_drill_down: Callable[[DrillDownEvent], None] | None = None
        self._on_drill_up: Callable[[DrillUpEvent], None] | None = None

    def view(self) -> Widget:
        """Build the drill-down chart widget."""
        # Use drillable chart variants for visual indicators
        actual_chart_type = self._get_drillable_chart_type()

        # Handle HeatmapChart specially (uses different data type)
        if (
            self._chart_type is HeatmapChart
            or self._chart_type is DrillableHeatmapChart
        ):
            chart_data = self._drill_state.to_heatmap_chart_data()
            # Determine which rows are drillable
            node = self._drill_state.current_node
            drillable_rows: set[int] = set()
            if node and node.is_multi_series:
                row_labels = node.all_categories
                for i, cat in enumerate(row_labels):
                    if node.has_children(cat):
                        drillable_rows.add(i)
            # Create the heatmap chart with drillable rows info
            chart = DrillableHeatmapChart(
                state=chart_data,
                drillable_rows=drillable_rows,
                **self._chart_kwargs,
            ).on_click(self._handle_chart_click)
        else:
            # Convert current node to chart-compatible data
            chart_data = self._drill_state.to_categorical_chart_data()
            # Create the chart with click handler
            chart = actual_chart_type(
                state=chart_data,
                **self._chart_kwargs,
            ).on_click(self._handle_chart_click)

        # Build navigation bar
        nav_items: list[Widget] = []

        # Back button (only show if not at root)
        if self._show_back_button and self._drill_state.can_drill_up:
            nav_items.append(
                Button("< Back", font_size=12)
                .on_click(self._handle_back_click)
                .height(28)
                .height_policy(SizePolicy.FIXED)
                .width_policy(SizePolicy.CONTENT)
            )
            nav_items.append(Spacer().width(8).width_policy(SizePolicy.FIXED))

        # Breadcrumb navigation
        if self._show_breadcrumb:
            nav_items.append(Breadcrumb(self._drill_state))

        nav_items.append(Spacer())

        # Current level name
        if self._show_level_name:
            node = self._drill_state.current_node
            if node and node.level_name:
                nav_items.append(
                    Text(f"Level: {node.level_name}")
                    .text_color("#888888")
                    .height(28)
                    .height_policy(SizePolicy.FIXED)
                )

        nav_bar = (
            Row(*nav_items)
            .height(36)
            .height_policy(SizePolicy.FIXED)
            .width_policy(SizePolicy.EXPANDING)
        )

        return Column(nav_bar, chart)

    def _get_drillable_chart_type(self) -> Type[BaseChart]:
        """Get the drillable variant of the configured chart type.

        Returns the drillable chart class that shows visual indicators
        on data points that can be drilled into.

        Returns:
            The chart class to use.
        """
        # Map standard chart types to their drillable variants
        if self._chart_type is BarChart or self._chart_type is DrillableBarChart:
            return DrillableBarChart
        elif self._chart_type is PieChart or self._chart_type is DrillablePieChart:
            return DrillablePieChart
        elif (
            self._chart_type is StackedBarChart
            or self._chart_type is DrillableStackedBarChart
        ):
            return DrillableStackedBarChart
        elif (
            self._chart_type is HeatmapChart
            or self._chart_type is DrillableHeatmapChart
        ):
            return DrillableHeatmapChart
        else:
            # For other chart types, use the original
            return self._chart_type

    def _handle_chart_click(self, event: ChartClickEvent) -> None:
        """Handle click on chart element - drill down if possible.

        Args:
            event: The chart click event.
        """
        # Get the clicked category from data point
        # Use data_index to get the actual category (not label which may include series name)
        key = self._get_category_from_event(event)

        if key and self._drill_state.can_drill_down(key):
            old_node_id = self._drill_state.current_node_id

            # Perform drill-down
            if self._drill_state.drill_down(key):
                # Fire user callback
                if self._on_drill_down:
                    self._on_drill_down(
                        DrillDownEvent(
                            from_node_id=old_node_id,
                            to_node_id=self._drill_state.current_node_id,
                            clicked_key=key,
                            new_depth=self._drill_state.current_depth,
                        )
                    )

    def _get_category_from_event(self, event: ChartClickEvent) -> str | None:
        """Extract the category key from a click event.

        For StackedBarChart, the label is "Category: SeriesName", so we need
        to get the actual category from the data point.

        For HeatmapChart, series_index is the row index, so we get the
        category from row labels (all_categories).

        Args:
            event: The chart click event.

        Returns:
            The category key for drill-down lookup.
        """
        node = self._drill_state.current_node
        if node is None:
            return None

        # For HeatmapChart: series_index = row, data_index = column
        # We drill based on row (category)
        if (
            self._chart_type is HeatmapChart
            or self._chart_type is DrillableHeatmapChart
        ):
            row_idx = event.series_index
            categories = node.all_categories
            if row_idx < len(categories):
                return categories[row_idx]
            return None

        # For multi-series data (StackedBarChart)
        if node.is_multi_series:
            # Get category from the series data using series_index and data_index
            series_names = list(node.series_data.keys())
            series_idx = event.series_index
            data_idx = event.data_index
            if series_idx < len(series_names):
                series_name = series_names[series_idx]
                points = node.series_data[series_name]
                if data_idx < len(points):
                    return points[data_idx].category
            # Fallback: use all_categories
            categories = node.all_categories
            if data_idx < len(categories):
                return categories[data_idx]

        # For single-series data (BarChart, PieChart)
        data_idx = event.data_index
        if data_idx < len(node.data):
            return node.data[data_idx].category

        # Fallback to label (for charts that set label to category)
        return event.label

    def _handle_back_click(self, _: Any) -> None:
        """Handle back button click."""
        old_node_id = self._drill_state.current_node_id

        if self._drill_state.drill_up():
            # Fire user callback
            if self._on_drill_up:
                self._on_drill_up(
                    DrillUpEvent(
                        from_node_id=old_node_id,
                        to_node_id=self._drill_state.current_node_id,
                        new_depth=self._drill_state.current_depth,
                    )
                )

    # Fluent API

    def on_drill_down(self, callback: Callable[[DrillDownEvent], None]) -> Self:
        """Set callback for drill-down events.

        Args:
            callback: Function to call when drilling down.

        Returns:
            Self for method chaining.
        """
        self._on_drill_down = callback
        self._drill_state.on_drill_down_callback(callback)
        return self

    def on_drill_up(self, callback: Callable[[DrillUpEvent], None]) -> Self:
        """Set callback for drill-up events.

        Args:
            callback: Function to call when drilling up.

        Returns:
            Self for method chaining.
        """
        self._on_drill_up = callback
        self._drill_state.on_drill_up_callback(callback)
        return self

    def chart_type(self, chart_type: Type[BaseChart]) -> Self:
        """Set the chart type.

        Args:
            chart_type: The chart class to use.

        Returns:
            Self for method chaining.
        """
        self._chart_type = chart_type
        return self

    def show_breadcrumb(self, show: bool = True) -> Self:
        """Set whether to show breadcrumb navigation.

        Args:
            show: Whether to show breadcrumbs.

        Returns:
            Self for method chaining.
        """
        self._show_breadcrumb = show
        return self

    def show_back_button(self, show: bool = True) -> Self:
        """Set whether to show the back button.

        Args:
            show: Whether to show the back button.

        Returns:
            Self for method chaining.
        """
        self._show_back_button = show
        return self

    # State access

    @property
    def state(self) -> DrillDownState:
        """Get the drill-down state for programmatic control.

        Returns:
            The DrillDownState instance.
        """
        return self._drill_state

    def reset(self) -> Self:
        """Reset to root level.

        Returns:
            Self for method chaining.
        """
        self._drill_state.reset()
        return self

    def navigate_to(self, node_id: str) -> Self:
        """Navigate to a specific node.

        Args:
            node_id: The ID of the node to navigate to.

        Returns:
            Self for method chaining.
        """
        self._drill_state.navigate_to(node_id)
        return self
