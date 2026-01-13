"""Hierarchical data models for drill-down charts."""

from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime
from typing import Any, Callable, Literal, Self, Sequence

from pydantic import BaseModel, ConfigDict, Field, PrivateAttr

from castella.chart.models.data_points import DataPoint
from castella.chart.models.series import SeriesStyle


class HierarchicalNode(BaseModel):
    """A node in a hierarchical data tree for drill-down charts.

    Each node represents one level in the hierarchy and can have children
    that represent drill-down data. When a user clicks on a data point,
    the chart navigates to the corresponding child node.

    Attributes:
        id: Unique identifier for this node.
        label: Display label for breadcrumb navigation.
        data: The chart data at this level (list of DataPoint). For single-series charts.
        series_data: Multi-series data for StackedBarChart. Dict of series_name -> list of DataPoint.
        children: Mapping of data point categories to child nodes.
        parent_id: ID of the parent node (None for root).
        level_name: Human-readable name for this level (e.g., "Region", "Country").
        style: Optional styling for this node's series.

    Example:
        >>> # Create a two-level hierarchy: Region -> Country
        >>> root = HierarchicalNode(
        ...     id="world",
        ...     label="World",
        ...     level_name="Region",
        ...     data=[
        ...         DataPoint(category="North America", value=1500),
        ...         DataPoint(category="Europe", value=1200),
        ...     ],
        ... )
        >>> root.add_child("North America", HierarchicalNode(
        ...     id="na",
        ...     label="North America",
        ...     level_name="Country",
        ...     data=[
        ...         DataPoint(category="USA", value=900),
        ...         DataPoint(category="Canada", value=600),
        ...     ],
        ... ))
    """

    model_config = ConfigDict(frozen=False)

    id: str
    label: str
    data: list[DataPoint] = Field(default_factory=list)
    series_data: dict[str, list[DataPoint]] = Field(default_factory=dict)
    children: dict[str, "HierarchicalNode"] = Field(default_factory=dict)
    parent_id: str | None = None
    level_name: str = ""
    style: SeriesStyle | None = None

    @property
    def is_multi_series(self) -> bool:
        """Check if this node has multi-series data."""
        return len(self.series_data) > 0

    @property
    def all_categories(self) -> list[str]:
        """Get all unique categories from data or series_data."""
        if self.is_multi_series:
            categories: set[str] = set()
            for points in self.series_data.values():
                for p in points:
                    categories.add(p.category)
            return sorted(categories)
        return [p.category for p in self.data]

    def add_child(self, key: str, child: "HierarchicalNode") -> Self:
        """Add a child node for drill-down.

        The key should match a category in this node's data points.
        When a user clicks on a data point with this category,
        the chart will navigate to the child node.

        Args:
            key: The identifier matching a data point's category.
            child: The child node containing drill-down data.

        Returns:
            Self for method chaining.
        """
        child.parent_id = self.id
        self.children[key] = child
        return self

    def has_children(self, key: str) -> bool:
        """Check if a data point has drill-down children.

        Args:
            key: The category to check.

        Returns:
            True if there is a child node for this category.
        """
        return key in self.children

    def get_child(self, key: str) -> "HierarchicalNode | None":
        """Get the child node for a data point.

        Args:
            key: The category to look up.

        Returns:
            The child node, or None if not found.
        """
        return self.children.get(key)

    @property
    def is_leaf(self) -> bool:
        """Check if this node has no children (leaf node)."""
        return len(self.children) == 0

    @property
    def drillable_categories(self) -> set[str]:
        """Get the set of categories that can be drilled into."""
        return set(self.children.keys())

    def get_data_with_drillable_metadata(self) -> list[DataPoint]:
        """Get data points with 'drillable' flag set in metadata.

        Returns:
            List of DataPoint with metadata['drillable'] = True/False.
        """
        result = []
        for point in self.data:
            drillable = self.has_children(point.category)
            new_metadata = {**point.metadata, "drillable": drillable}
            result.append(point.model_copy(update={"metadata": new_metadata}))
        return result

    def get_series_data_with_drillable_metadata(
        self,
    ) -> dict[str, list[DataPoint]]:
        """Get multi-series data with 'drillable' flag set in metadata.

        Returns:
            Dict of series_name -> list of DataPoint with drillable metadata.
        """
        result: dict[str, list[DataPoint]] = {}
        for series_name, points in self.series_data.items():
            series_points = []
            for point in points:
                drillable = self.has_children(point.category)
                new_metadata = {**point.metadata, "drillable": drillable}
                series_points.append(
                    point.model_copy(update={"metadata": new_metadata})
                )
            result[series_name] = series_points
        return result


class HierarchicalChartData(BaseModel):
    """Container for hierarchical chart data supporting drill-down.

    This model stores a tree of data nodes that can be navigated
    through drill-down/drill-up operations. It implements the Observer
    pattern for reactive UI updates.

    Attributes:
        root: The root node of the hierarchy.
        title: Chart title displayed at the top.

    Example:
        >>> data = HierarchicalChartData(
        ...     title="Global Sales",
        ...     root=HierarchicalNode(
        ...         id="world",
        ...         label="World",
        ...         level_name="Region",
        ...         data=[
        ...             DataPoint(category="North America", value=1500),
        ...             DataPoint(category="Europe", value=1200),
        ...             DataPoint(category="Asia", value=1800),
        ...         ],
        ...     ),
        ... )
        >>> # Add drill-down data for North America
        >>> data.root.add_child("North America", HierarchicalNode(
        ...     id="na",
        ...     label="North America",
        ...     level_name="Country",
        ...     data=[
        ...         DataPoint(category="USA", value=900),
        ...         DataPoint(category="Canada", value=400),
        ...         DataPoint(category="Mexico", value=200),
        ...     ],
        ... ))
    """

    model_config = ConfigDict(validate_assignment=True)

    root: HierarchicalNode
    title: str = ""

    # Observable pattern
    _observers: list[Any] = PrivateAttr(default_factory=list)

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

    def find_node(self, node_id: str) -> HierarchicalNode | None:
        """Find a node by its ID using breadth-first search.

        Args:
            node_id: The ID of the node to find.

        Returns:
            The node with the given ID, or None if not found.
        """
        queue = [self.root]
        while queue:
            node = queue.pop(0)
            if node.id == node_id:
                return node
            queue.extend(node.children.values())
        return None

    def get_path_to_node(self, node_id: str) -> list[HierarchicalNode]:
        """Get the path from root to a node.

        Args:
            node_id: The ID of the target node.

        Returns:
            List of nodes from root to target (inclusive).
            Empty list if node not found.
        """
        path: list[HierarchicalNode] = []

        def dfs(node: HierarchicalNode, target_id: str) -> bool:
            path.append(node)
            if node.id == target_id:
                return True
            for child in node.children.values():
                if dfs(child, target_id):
                    return True
            path.pop()
            return False

        dfs(self.root, node_id)
        return path

    def get_max_depth(self) -> int:
        """Calculate the maximum depth of the hierarchy.

        Returns:
            Maximum depth (0 for root-only, 1 for root + one level, etc.)
        """

        def calc_depth(node: HierarchicalNode) -> int:
            if node.is_leaf:
                return 0
            return 1 + max(calc_depth(child) for child in node.children.values())

        return calc_depth(self.root)


# Factory functions


def hierarchical_from_dict(
    data: dict[str, Any],
    id_prefix: str = "",
    level_names: Sequence[str] | None = None,
    depth: int = 0,
) -> HierarchicalNode:
    """Create a HierarchicalNode tree from a nested dictionary.

    The dictionary format supports two styles:
    1. Simple: {"label": "Name", "value": 100, "children": {...}}
    2. Categories: {"North America": {"value": 100, "children": {...}}, ...}

    Args:
        data: Nested dictionary with chart data.
        id_prefix: Prefix for generated IDs.
        level_names: Optional list of level names by depth.
        depth: Current depth (used internally).

    Returns:
        A HierarchicalNode representing the data.

    Example:
        >>> data = {
        ...     "North America": {
        ...         "value": 1500,
        ...         "children": {
        ...             "USA": {"value": 900},
        ...             "Canada": {"value": 600},
        ...         }
        ...     },
        ...     "Europe": {"value": 1200},
        ... }
        >>> node = hierarchical_from_dict(
        ...     {"label": "World", "children": data},
        ...     level_names=["Region", "Country"],
        ... )
    """
    label = data.get("label", "Root")
    node_id = id_prefix or label.lower().replace(" ", "_")
    level_name = level_names[depth] if level_names and depth < len(level_names) else ""

    # Build data points from children or explicit data
    data_points: list[DataPoint] = []
    children_data = data.get("children", {})

    for key, child_data in children_data.items():
        if isinstance(child_data, dict):
            value = child_data.get("value", 0)
            data_points.append(
                DataPoint(
                    category=key,
                    value=float(value),
                    label=key,
                )
            )

    node = HierarchicalNode(
        id=node_id,
        label=label,
        level_name=level_name,
        data=data_points,
    )

    # Recursively build children
    for key, child_data in children_data.items():
        if isinstance(child_data, dict) and "children" in child_data:
            child_node = hierarchical_from_dict(
                {"label": key, **child_data},
                id_prefix=f"{node_id}_{key.lower().replace(' ', '_')}",
                level_names=level_names,
                depth=depth + 1,
            )
            node.add_child(key, child_node)

    return node


# Time-series helper types
AggregationMethod = Literal["sum", "avg", "count", "min", "max"]

# Month names for labels
_MONTH_NAMES = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
]

_MONTH_NAMES_SHORT = [
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
]


def _aggregate_values(values: list[float], method: AggregationMethod) -> float:
    """Aggregate a list of values using the specified method."""
    if not values:
        return 0.0
    if method == "sum":
        return sum(values)
    elif method == "avg":
        return sum(values) / len(values)
    elif method == "count":
        return float(len(values))
    elif method == "min":
        return min(values)
    elif method == "max":
        return max(values)
    else:
        return sum(values)


def hierarchical_from_timeseries(
    data: Sequence[tuple[date | datetime, float]],
    title: str = "Time Series Data",
    aggregation: AggregationMethod = "sum",
    depth: Literal["year", "month", "day"] = "day",
    short_month_names: bool = True,
    value_format: Callable[[float], str] | None = None,
) -> HierarchicalChartData:
    """Create hierarchical drill-down data from time-series data.

    Automatically groups data by Year → Month → Day with the specified
    aggregation method. Users can drill down from yearly totals to monthly
    breakdowns to daily values.

    Args:
        data: Sequence of (date/datetime, value) tuples.
        title: Chart title.
        aggregation: How to aggregate values ("sum", "avg", "count", "min", "max").
        depth: Maximum drill-down depth ("year", "month", or "day").
        short_month_names: Use "Jan" instead of "January".
        value_format: Optional function to format values for labels.

    Returns:
        HierarchicalChartData ready for use with DrillDownChart.

    Example:
        >>> from datetime import date
        >>> data = [
        ...     (date(2024, 1, 15), 100),
        ...     (date(2024, 1, 20), 150),
        ...     (date(2024, 2, 10), 200),
        ...     (date(2024, 3, 5), 120),
        ...     (date(2023, 12, 1), 80),
        ... ]
        >>> chart_data = hierarchical_from_timeseries(
        ...     data,
        ...     title="Sales by Date",
        ...     aggregation="sum",
        ...     depth="day",
        ... )
        >>> # Root shows years: 2023, 2024
        >>> # Drill into 2024 shows months: Jan, Feb, Mar
        >>> # Drill into Jan shows days: 15, 20
    """
    month_names = _MONTH_NAMES_SHORT if short_month_names else _MONTH_NAMES

    # Group data by year, month, day
    by_year: dict[int, list[tuple[date, float]]] = defaultdict(list)
    for dt, value in data:
        if isinstance(dt, datetime):
            dt = dt.date()
        by_year[dt.year].append((dt, value))

    # Create root node with yearly data
    year_data_points: list[DataPoint] = []
    for year in sorted(by_year.keys()):
        values = [v for _, v in by_year[year]]
        agg_value = _aggregate_values(values, aggregation)
        label_value = value_format(agg_value) if value_format else str(int(agg_value))
        year_data_points.append(
            DataPoint(
                category=str(year),
                value=agg_value,
                label=f"{year}: {label_value}",
            )
        )

    root = HierarchicalNode(
        id="root",
        label="All Years",
        level_name="Year",
        data=year_data_points,
    )

    # If depth is "year", we're done
    if depth == "year":
        return HierarchicalChartData(title=title, root=root)

    # Create month-level nodes for each year
    for year in sorted(by_year.keys()):
        by_month: dict[int, list[tuple[date, float]]] = defaultdict(list)
        for dt, value in by_year[year]:
            by_month[dt.month].append((dt, value))

        month_data_points: list[DataPoint] = []
        for month in sorted(by_month.keys()):
            values = [v for _, v in by_month[month]]
            agg_value = _aggregate_values(values, aggregation)
            month_name = month_names[month - 1]
            label_value = (
                value_format(agg_value) if value_format else str(int(agg_value))
            )
            month_data_points.append(
                DataPoint(
                    category=month_name,
                    value=agg_value,
                    label=f"{month_name}: {label_value}",
                )
            )

        year_node = HierarchicalNode(
            id=f"year_{year}",
            label=str(year),
            level_name="Month",
            data=month_data_points,
        )
        root.add_child(str(year), year_node)

        # If depth is "month", we're done for this year
        if depth == "month":
            continue

        # Create day-level nodes for each month
        for month in sorted(by_month.keys()):
            day_data_points: list[DataPoint] = []
            for dt, value in sorted(by_month[month], key=lambda x: x[0]):
                day = dt.day
                label_value = value_format(value) if value_format else str(int(value))
                day_data_points.append(
                    DataPoint(
                        category=str(day),
                        value=value,
                        label=f"Day {day}: {label_value}",
                    )
                )

            month_name = month_names[month - 1]
            month_node = HierarchicalNode(
                id=f"year_{year}_month_{month}",
                label=f"{month_name} {year}",
                level_name="Day",
                data=day_data_points,
            )
            year_node.add_child(month_name, month_node)

    return HierarchicalChartData(title=title, root=root)


def hierarchical_from_timeseries_with_categories(
    data: Sequence[tuple[date | datetime, str, float]],
    title: str = "Time Series by Category",
    aggregation: AggregationMethod = "sum",
    depth: Literal["year", "month", "day"] = "day",
    short_month_names: bool = True,
) -> HierarchicalChartData:
    """Create hierarchical data from categorized time-series.

    Similar to hierarchical_from_timeseries but groups by category first,
    then drills down into time periods within each category.

    The hierarchy is: Category → Year → Month → Day

    Args:
        data: Sequence of (date/datetime, category, value) tuples.
        title: Chart title.
        aggregation: How to aggregate values.
        depth: Maximum time drill-down depth.
        short_month_names: Use "Jan" instead of "January".

    Returns:
        HierarchicalChartData with Category → Time hierarchy.

    Example:
        >>> data = [
        ...     (date(2024, 1, 15), "Product A", 100),
        ...     (date(2024, 1, 20), "Product A", 150),
        ...     (date(2024, 1, 15), "Product B", 80),
        ... ]
        >>> chart_data = hierarchical_from_timeseries_with_categories(
        ...     data,
        ...     title="Sales by Product",
        ... )
        >>> # Root shows categories: Product A, Product B
        >>> # Drill into Product A shows years
        >>> # Drill into year shows months, etc.
    """
    # Group by category first
    by_category: dict[str, list[tuple[date, float]]] = defaultdict(list)
    for dt, category, value in data:
        if isinstance(dt, datetime):
            dt = dt.date()
        by_category[category].append((dt, value))

    # Create root with category totals
    category_data_points: list[DataPoint] = []
    for category in sorted(by_category.keys()):
        values = [v for _, v in by_category[category]]
        agg_value = _aggregate_values(values, aggregation)
        category_data_points.append(
            DataPoint(
                category=category,
                value=agg_value,
                label=category,
            )
        )

    root = HierarchicalNode(
        id="root",
        label="All Categories",
        level_name="Category",
        data=category_data_points,
    )

    # For each category, create time-based hierarchy
    for category in sorted(by_category.keys()):
        category_data = by_category[category]
        category_id = category.lower().replace(" ", "_")

        # Create a sub-hierarchy for this category's time data
        time_data = [(dt, val) for dt, val in category_data]
        sub_chart = hierarchical_from_timeseries(
            time_data,
            title=category,
            aggregation=aggregation,
            depth=depth,
            short_month_names=short_month_names,
        )

        # Rename the sub-chart's root to represent the category
        sub_root = sub_chart.root
        sub_root.id = f"category_{category_id}"
        sub_root.label = category
        root.add_child(category, sub_root)

    return HierarchicalChartData(title=title, root=root)
