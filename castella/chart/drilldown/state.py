"""Drill-down navigation state management."""

from __future__ import annotations

from typing import Any, Callable, Self

from pydantic import BaseModel, ConfigDict, Field, PrivateAttr

from castella.chart.models.hierarchy import HierarchicalChartData, HierarchicalNode
from castella.chart.models.series import CategoricalSeries, SeriesStyle
from castella.chart.models.chart_data import CategoricalChartData
from castella.chart.models.heatmap_data import HeatmapChartData

from .events import DrillDownEvent, DrillUpEvent


class DrillPath(BaseModel):
    """Represents a single step in the drill-down path.

    Attributes:
        node_id: The ID of the node at this step.
        clicked_key: The key (category) that was clicked to reach this level.
        label: Display label for breadcrumb navigation.
    """

    model_config = ConfigDict(frozen=True)

    node_id: str
    clicked_key: str = ""
    label: str = ""


class DrillDownState(BaseModel):
    """Observable state for drill-down navigation.

    Manages the current position in the hierarchy and provides
    navigation methods for drill-down/drill-up operations.
    The state is observable, triggering UI updates when navigation occurs.

    Attributes:
        hierarchical_data: The hierarchical data being navigated.
        path: The current drill-down path from root.
        current_node_id: ID of the currently displayed node.

    Example:
        >>> state = DrillDownState(hierarchical_data=data)
        >>> state.attach(my_component)  # Component will rebuild on changes
        >>>
        >>> # Navigate down
        >>> if state.can_drill_down("North America"):
        ...     state.drill_down("North America")
        >>>
        >>> # Navigate up
        >>> if state.can_drill_up:
        ...     state.drill_up()
        >>>
        >>> # Jump to specific node via breadcrumb
        >>> state.navigate_to("world")
    """

    model_config = ConfigDict(validate_assignment=True, arbitrary_types_allowed=True)

    hierarchical_data: HierarchicalChartData
    path: list[DrillPath] = Field(default_factory=list)
    current_node_id: str = ""

    # Observable pattern
    _observers: list[Any] = PrivateAttr(default_factory=list)
    _on_drill_down: Callable[[DrillDownEvent], None] | None = PrivateAttr(default=None)
    _on_drill_up: Callable[[DrillUpEvent], None] | None = PrivateAttr(default=None)

    def model_post_init(self, __context: Any) -> None:
        """Initialize current node to root if not set."""
        if not self.current_node_id:
            self.current_node_id = self.hierarchical_data.root.id
            self.path = [
                DrillPath(
                    node_id=self.hierarchical_data.root.id,
                    label=self.hierarchical_data.root.label,
                )
            ]

    def attach(self, observer: Any) -> None:
        """Attach an observer for reactive updates.

        Args:
            observer: An object with on_notify() method.
        """
        if observer not in self._observers:
            self._observers.append(observer)
            if hasattr(observer, "on_attach"):
                observer.on_attach(self)

    def detach(self, observer: Any) -> None:
        """Detach an observer.

        Args:
            observer: The observer to remove.
        """
        if observer in self._observers:
            self._observers.remove(observer)
            if hasattr(observer, "on_detach"):
                observer.on_detach(self)

    def notify(self, event: Any = None) -> None:
        """Notify all observers of a change.

        Args:
            event: Optional event data to pass to observers.
        """
        for observer in self._observers:
            observer.on_notify(event)

    @property
    def current_node(self) -> HierarchicalNode | None:
        """Get the currently displayed node."""
        return self.hierarchical_data.find_node(self.current_node_id)

    @property
    def current_depth(self) -> int:
        """Get the current depth in the hierarchy (0 = root)."""
        return len(self.path) - 1

    @property
    def can_drill_up(self) -> bool:
        """Check if drill-up is possible (not at root)."""
        return len(self.path) > 1

    @property
    def breadcrumbs(self) -> list[tuple[str, str]]:
        """Get breadcrumb items as (node_id, label) tuples.

        Returns:
            List of (node_id, label) tuples representing the path.
        """
        return [(p.node_id, p.label) for p in self.path]

    def can_drill_down(self, key: str) -> bool:
        """Check if a data point can be drilled into.

        Args:
            key: The category to check.

        Returns:
            True if the category has child data.
        """
        node = self.current_node
        return node is not None and node.has_children(key)

    def drill_down(self, key: str) -> bool:
        """Navigate into a child node.

        Args:
            key: The category of the clicked data point.

        Returns:
            True if navigation succeeded, False if no children.
        """
        node = self.current_node
        if node is None or not node.has_children(key):
            return False

        child = node.get_child(key)
        if child is None:
            return False

        old_node_id = self.current_node_id

        # Update path and current node
        self.path = [
            *self.path,
            DrillPath(
                node_id=child.id,
                clicked_key=key,
                label=child.label or key,
            ),
        ]
        self.current_node_id = child.id

        # Fire callback
        if self._on_drill_down:
            self._on_drill_down(
                DrillDownEvent(
                    from_node_id=old_node_id,
                    to_node_id=child.id,
                    clicked_key=key,
                    new_depth=self.current_depth,
                )
            )

        self.notify()
        return True

    def drill_up(self) -> bool:
        """Navigate to the parent node.

        Returns:
            True if navigation succeeded, False if at root.
        """
        if not self.can_drill_up:
            return False

        old_id = self.current_node_id
        self.path = self.path[:-1]
        self.current_node_id = self.path[-1].node_id

        # Fire callback
        if self._on_drill_up:
            self._on_drill_up(
                DrillUpEvent(
                    from_node_id=old_id,
                    to_node_id=self.current_node_id,
                    new_depth=self.current_depth,
                )
            )

        self.notify()
        return True

    def navigate_to(self, node_id: str) -> bool:
        """Navigate directly to a node (e.g., from breadcrumb click).

        Only nodes in the current path can be navigated to directly.
        To navigate to arbitrary nodes, use drill_down/drill_up.

        Args:
            node_id: The target node ID.

        Returns:
            True if navigation succeeded.
        """
        # Find the node in the current path
        for i, step in enumerate(self.path):
            if step.node_id == node_id:
                old_id = self.current_node_id
                self.path = self.path[: i + 1]
                self.current_node_id = node_id

                # Fire drill-up callback if going up
                if self._on_drill_up and old_id != node_id:
                    self._on_drill_up(
                        DrillUpEvent(
                            from_node_id=old_id,
                            to_node_id=node_id,
                            new_depth=self.current_depth,
                        )
                    )

                self.notify()
                return True
        return False

    def reset(self) -> None:
        """Reset to root node."""
        old_id = self.current_node_id
        root = self.hierarchical_data.root

        self.path = [
            DrillPath(
                node_id=root.id,
                label=root.label,
            )
        ]
        self.current_node_id = root.id

        # Fire drill-up callback
        if self._on_drill_up and old_id != root.id:
            self._on_drill_up(
                DrillUpEvent(
                    from_node_id=old_id,
                    to_node_id=root.id,
                    new_depth=0,
                )
            )

        self.notify()

    def to_categorical_chart_data(self) -> CategoricalChartData:
        """Convert current node to CategoricalChartData for chart rendering.

        The returned data includes 'drillable' metadata on each data point
        to indicate whether it can be drilled into.

        For multi-series data (StackedBarChart), returns multiple series.
        For single-series data (BarChart, PieChart), returns one series.

        Returns:
            CategoricalChartData suitable for BarChart, PieChart, StackedBarChart.
        """
        node = self.current_node
        if node is None:
            return CategoricalChartData()

        # Color palette for visual distinction
        colors = [
            "#3b82f6",  # Blue
            "#22c55e",  # Green
            "#f59e0b",  # Amber
            "#ef4444",  # Red
            "#8b5cf6",  # Purple
            "#06b6d4",  # Cyan
            "#ec4899",  # Pink
            "#84cc16",  # Lime
        ]

        # Handle multi-series data (for StackedBarChart)
        if node.is_multi_series:
            series_data = node.get_series_data_with_drillable_metadata()
            series_list = []
            for i, (series_name, data_points) in enumerate(series_data.items()):
                color = colors[i % len(colors)]
                style = SeriesStyle(color=color)
                series_list.append(
                    CategoricalSeries(
                        name=series_name,
                        data=tuple(data_points),
                        style=style,
                    )
                )
            return CategoricalChartData(
                title=self.hierarchical_data.title,
                series=series_list,
            )

        # Handle single-series data (for BarChart, PieChart)
        data_points = node.get_data_with_drillable_metadata()

        # Assign colors to each data point for visual distinction
        colored_points = []
        for i, point in enumerate(data_points):
            color = colors[i % len(colors)]
            new_metadata = {**point.metadata, "color": color}
            colored_points.append(point.model_copy(update={"metadata": new_metadata}))

        series = CategoricalSeries(
            name=node.label,
            data=tuple(colored_points),
            style=node.style or SeriesStyle(),
        )

        return CategoricalChartData(
            title=self.hierarchical_data.title,
            series=[series],
        )

    def to_heatmap_chart_data(self) -> HeatmapChartData:
        """Convert current node to HeatmapChartData for heatmap rendering.

        Uses series_data where:
        - Series names become column labels
        - Categories become row labels
        - Values fill the 2D matrix

        The returned data includes 'drillable' metadata tracking for row-based
        drill-down (clicking any cell in a row drills into that row's children).

        Returns:
            HeatmapChartData suitable for HeatmapChart.
        """
        node = self.current_node
        if node is None:
            return HeatmapChartData()

        if not node.is_multi_series:
            # Fall back to empty heatmap if no multi-series data
            return HeatmapChartData(title=self.hierarchical_data.title)

        # Get column labels (series names) and row labels (categories)
        column_labels = list(node.series_data.keys())
        row_labels = node.all_categories

        # Build the 2D value matrix
        values: list[list[float]] = []
        for category in row_labels:
            row: list[float] = []
            for col_name in column_labels:
                points = node.series_data[col_name]
                # Find the value for this category in this series
                value = next(
                    (p.value for p in points if p.category == category),
                    0.0,
                )
                row.append(value)
            values.append(row)

        return HeatmapChartData(
            title=self.hierarchical_data.title,
            values=values,
            row_labels=row_labels,
            column_labels=column_labels,
        )

    def on_drill_down_callback(
        self, callback: Callable[[DrillDownEvent], None]
    ) -> Self:
        """Set callback for drill-down events.

        Args:
            callback: Function to call when drilling down.

        Returns:
            Self for method chaining.
        """
        self._on_drill_down = callback
        return self

    def on_drill_up_callback(self, callback: Callable[[DrillUpEvent], None]) -> Self:
        """Set callback for drill-up events.

        Args:
            callback: Function to call when drilling up.

        Returns:
            Self for method chaining.
        """
        self._on_drill_up = callback
        return self
