"""Hierarchical data models for drill-down charts."""

from __future__ import annotations

from typing import Any, Self, Sequence

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
        data: The chart data at this level (list of DataPoint).
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
    children: dict[str, "HierarchicalNode"] = Field(default_factory=dict)
    parent_id: str | None = None
    level_name: str = ""
    style: SeriesStyle | None = None

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
