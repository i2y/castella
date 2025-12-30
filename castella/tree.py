"""Tree widget for hierarchical data display.

Provides a tree view with expand/collapse functionality,
single/multi selection, and custom icons.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Self

from castella.button import Button
from castella.column import Column
from castella.core import (
    Kind,
    ObservableBase,
    SizePolicy,
    StatefulComponent,
    Widget,
)
from castella.row import Row
from castella.spacer import Spacer
from castella.text import Text


@dataclass
class TreeNode:
    """A single node in the tree hierarchy.

    Attributes:
        id: Unique identifier for this node
        label: Display text for the node
        children: List of child nodes
        icon: Optional custom icon (emoji or unicode character)
        data: Optional user data payload
    """

    id: str
    label: str
    children: list["TreeNode"] = field(default_factory=list)
    icon: str | None = None
    data: Any = None

    def is_leaf(self) -> bool:
        """Returns True if node has no children."""
        return len(self.children) == 0

    def add_child(self, child: "TreeNode") -> Self:
        """Add a child node.

        Args:
            child: The child node to add

        Returns:
            Self for method chaining
        """
        self.children.append(child)
        return self

    @classmethod
    def from_dict(cls, data: dict) -> "TreeNode":
        """Create TreeNode from dictionary representation.

        Expected format:
        {
            "id": "node1",
            "label": "Node 1",
            "icon": "folder",
            "children": [
                {"id": "child1", "label": "Child 1", ...}
            ],
            "data": {...}
        }

        Args:
            data: Dictionary containing node data

        Returns:
            A new TreeNode instance
        """
        children = [cls.from_dict(c) for c in data.get("children", [])]
        return cls(
            id=data["id"],
            label=data["label"],
            children=children,
            icon=data.get("icon"),
            data=data.get("data"),
        )


class TreeState(ObservableBase):
    """Observable state for Tree widget.

    Manages tree nodes, expanded state, and selection.

    Attributes:
        nodes: Root-level tree nodes
        expanded_ids: Set of IDs for expanded nodes
        selected_ids: Set of IDs for selected nodes (single or multi)
        multi_select: Whether multiple selection is allowed
    """

    def __init__(
        self,
        nodes: list[TreeNode] | None = None,
        expanded_ids: set[str] | None = None,
        selected_ids: set[str] | None = None,
        multi_select: bool = False,
    ):
        """Initialize TreeState.

        Args:
            nodes: List of root-level TreeNode instances
            expanded_ids: Set of initially expanded node IDs
            selected_ids: Set of initially selected node IDs
            multi_select: Whether to allow multiple selection
        """
        super().__init__()
        self._nodes = nodes or []
        self._expanded_ids = expanded_ids or set()
        self._selected_ids = selected_ids or set()
        self._multi_select = multi_select

        # Build lookup table for O(1) node access
        self._node_map: dict[str, TreeNode] = {}
        self._rebuild_node_map()

    def _rebuild_node_map(self) -> None:
        """Build flat lookup table from tree."""
        self._node_map.clear()

        def traverse(nodes: list[TreeNode]) -> None:
            for node in nodes:
                self._node_map[node.id] = node
                traverse(node.children)

        traverse(self._nodes)

    # --- Node access ---

    def nodes(self) -> list[TreeNode]:
        """Get root-level nodes."""
        return self._nodes

    def get_node(self, node_id: str) -> TreeNode | None:
        """Get node by ID.

        Args:
            node_id: The ID of the node to find

        Returns:
            The TreeNode if found, None otherwise
        """
        return self._node_map.get(node_id)

    def set_nodes(self, nodes: list[TreeNode]) -> None:
        """Replace all nodes.

        Args:
            nodes: New list of root TreeNode instances
        """
        self._nodes = nodes
        self._rebuild_node_map()
        # Clear invalid selections/expansions
        valid_ids = set(self._node_map.keys())
        self._expanded_ids &= valid_ids
        self._selected_ids &= valid_ids
        self.notify()

    # --- Expansion ---

    def is_expanded(self, node_id: str) -> bool:
        """Check if node is expanded.

        Args:
            node_id: The ID of the node to check

        Returns:
            True if the node is expanded
        """
        return node_id in self._expanded_ids

    def expand(self, node_id: str) -> None:
        """Expand a node.

        Args:
            node_id: The ID of the node to expand
        """
        if node_id in self._node_map and node_id not in self._expanded_ids:
            node = self._node_map[node_id]
            if not node.is_leaf():
                self._expanded_ids.add(node_id)
                self.notify()

    def collapse(self, node_id: str) -> None:
        """Collapse a node.

        Args:
            node_id: The ID of the node to collapse
        """
        if node_id in self._expanded_ids:
            self._expanded_ids.discard(node_id)
            self.notify()

    def toggle_expanded(self, node_id: str) -> None:
        """Toggle expand/collapse state.

        Args:
            node_id: The ID of the node to toggle
        """
        if self.is_expanded(node_id):
            self.collapse(node_id)
        else:
            self.expand(node_id)

    def expand_all(self) -> None:
        """Expand all nodes."""
        for node_id, node in self._node_map.items():
            if not node.is_leaf():
                self._expanded_ids.add(node_id)
        self.notify()

    def collapse_all(self) -> None:
        """Collapse all nodes."""
        self._expanded_ids.clear()
        self.notify()

    def expand_to(self, node_id: str) -> None:
        """Expand all ancestors to reveal a node.

        Args:
            node_id: The ID of the node to reveal
        """
        path = self._find_path_to(node_id)
        for ancestor_id in path[:-1]:  # Exclude the node itself
            self._expanded_ids.add(ancestor_id)
        if path:
            self.notify()

    def _find_path_to(self, target_id: str) -> list[str]:
        """Find path from root to target node.

        Args:
            target_id: The ID of the target node

        Returns:
            List of node IDs from root to target
        """

        def search(nodes: list[TreeNode], path: list[str]) -> list[str] | None:
            for node in nodes:
                current_path = path + [node.id]
                if node.id == target_id:
                    return current_path
                result = search(node.children, current_path)
                if result:
                    return result
            return None

        return search(self._nodes, []) or []

    # --- Selection ---

    def is_selected(self, node_id: str) -> bool:
        """Check if node is selected.

        Args:
            node_id: The ID of the node to check

        Returns:
            True if the node is selected
        """
        return node_id in self._selected_ids

    def select(self, node_id: str, add_to_selection: bool = False) -> None:
        """Select a node.

        Args:
            node_id: ID of node to select
            add_to_selection: If True and multi_select enabled, add to selection.
                             If False, replace selection.
        """
        if node_id not in self._node_map:
            return

        if self._multi_select and add_to_selection:
            if node_id in self._selected_ids:
                # Toggle off if already selected
                self._selected_ids.discard(node_id)
            else:
                self._selected_ids.add(node_id)
        else:
            # Single select or replace selection
            self._selected_ids = {node_id}

        self.notify()

    def deselect(self, node_id: str) -> None:
        """Deselect a specific node.

        Args:
            node_id: The ID of the node to deselect
        """
        if node_id in self._selected_ids:
            self._selected_ids.discard(node_id)
            self.notify()

    def clear_selection(self) -> None:
        """Clear all selections."""
        if self._selected_ids:
            self._selected_ids.clear()
            self.notify()

    def get_selected(self) -> list[TreeNode]:
        """Get list of selected nodes.

        Returns:
            List of selected TreeNode instances
        """
        return [self._node_map[id] for id in self._selected_ids if id in self._node_map]

    def get_selected_ids(self) -> set[str]:
        """Get set of selected node IDs.

        Returns:
            Copy of the selected IDs set
        """
        return self._selected_ids.copy()

    def selected_id(self) -> str | None:
        """Get single selected ID (for single-select mode).

        Returns:
            The selected node ID, or None if nothing is selected
        """
        if self._selected_ids:
            return next(iter(self._selected_ids))
        return None

    # --- Multi-select mode ---

    def is_multi_select(self) -> bool:
        """Check if multi-select mode is enabled.

        Returns:
            True if multi-select mode is enabled
        """
        return self._multi_select

    def set_multi_select(self, enabled: bool) -> None:
        """Enable or disable multi-select mode.

        Args:
            enabled: True to enable multi-select
        """
        if self._multi_select != enabled:
            self._multi_select = enabled
            if not enabled and len(self._selected_ids) > 1:
                # Keep only first selection
                first_id = next(iter(self._selected_ids))
                self._selected_ids = {first_id}
            self.notify()


# Default icons
DEFAULT_EXPAND_ICON = ">"  # Collapsed
DEFAULT_COLLAPSE_ICON = "v"  # Expanded
DEFAULT_LEAF_SPACER = " "  # No toggle for leaf nodes


class Tree(StatefulComponent):
    """Tree widget for displaying hierarchical data.

    Supports single and multi-selection, custom icons per node,
    and expand/collapse functionality.

    Example:
        # Create tree data
        nodes = [
            TreeNode(id="root", label="Root", icon="folder", children=[
                TreeNode(id="child1", label="Child 1", icon="file"),
                TreeNode(id="child2", label="Child 2", icon="folder", children=[
                    TreeNode(id="grandchild", label="Grandchild", icon="file"),
                ]),
            ]),
        ]

        # Create tree widget
        state = TreeState(nodes, multi_select=False)
        tree = Tree(state).on_select(lambda node: print(f"Selected: {node.label}"))
    """

    def __init__(
        self,
        state: TreeState | None = None,
        indent_width: int = 20,
        row_height: int = 28,
    ):
        """Initialize Tree widget.

        Args:
            state: TreeState containing nodes and configuration
            indent_width: Pixels to indent each level
            row_height: Height of each tree row in pixels
        """
        self._tree_state = state or TreeState()
        super().__init__(self._tree_state)

        self._indent_width = indent_width
        self._row_height = row_height

        # Callbacks
        self._on_select: Callable[[TreeNode], None] = lambda _: None
        self._on_expand: Callable[[TreeNode], None] = lambda _: None
        self._on_collapse: Callable[[TreeNode], None] = lambda _: None

    def view(self) -> Widget:
        """Build the tree UI."""
        nodes = self._tree_state.nodes()

        if not nodes:
            return Spacer()

        # Build flattened visible node list with depth
        visible_rows: list[tuple[TreeNode, int]] = []
        self._collect_visible_nodes(nodes, 0, visible_rows)

        # Create row widgets
        row_widgets = [
            self._create_node_row(node, depth) for node, depth in visible_rows
        ]

        return Column(
            *row_widgets,
            scrollable=True,
        ).height_policy(SizePolicy.EXPANDING)

    def _collect_visible_nodes(
        self,
        nodes: list[TreeNode],
        depth: int,
        result: list[tuple[TreeNode, int]],
    ) -> None:
        """Collect visible nodes with their depth.

        Args:
            nodes: List of nodes to process
            depth: Current depth level
            result: Accumulator for results
        """
        for node in nodes:
            result.append((node, depth))
            if not node.is_leaf() and self._tree_state.is_expanded(node.id):
                self._collect_visible_nodes(node.children, depth + 1, result)

    def _create_node_row(self, node: TreeNode, depth: int) -> Widget:
        """Create a row widget for a single tree node.

        Args:
            node: The TreeNode to render
            depth: The depth level for indentation

        Returns:
            A Row widget representing the node
        """
        is_selected = self._tree_state.is_selected(node.id)
        is_expanded = self._tree_state.is_expanded(node.id)
        is_leaf = node.is_leaf()

        # Calculate indentation
        indent = depth * self._indent_width

        row_elements: list[Widget] = []

        # Indentation spacer
        if indent > 0:
            row_elements.append(
                Spacer()
                .width(indent)
                .width_policy(SizePolicy.FIXED)
                .height(self._row_height)
                .height_policy(SizePolicy.FIXED)
                .erase_border()
            )

        # Expand/collapse toggle (or placeholder for leaf)
        if is_leaf:
            toggle = (
                Text(DEFAULT_LEAF_SPACER, font_size=12)
                .width(20)
                .width_policy(SizePolicy.FIXED)
                .height(self._row_height)
                .height_policy(SizePolicy.FIXED)
                .erase_border()
            )
        else:
            toggle_text = DEFAULT_COLLAPSE_ICON if is_expanded else DEFAULT_EXPAND_ICON
            toggle = (
                Button(toggle_text)
                .on_click(self._create_toggle_handler(node))
                .width(20)
                .width_policy(SizePolicy.FIXED)
                .height(self._row_height)
                .height_policy(SizePolicy.FIXED)
            )
        row_elements.append(toggle)

        # Custom icon (if provided)
        if node.icon:
            icon = (
                Text(node.icon, font_size=14)
                .width(24)
                .width_policy(SizePolicy.FIXED)
                .height(self._row_height)
                .height_policy(SizePolicy.FIXED)
                .erase_border()
            )
            row_elements.append(icon)

        # Label
        label = (
            Button(node.label)
            .on_click(self._create_select_handler(node))
            .height(self._row_height)
            .height_policy(SizePolicy.FIXED)
        )

        if is_selected:
            label = label.kind(Kind.INFO)

        row_elements.append(label)

        return (
            Row(*row_elements).height(self._row_height).height_policy(SizePolicy.FIXED)
        )

    def _create_toggle_handler(self, node: TreeNode) -> Callable:
        """Create click handler for expand/collapse toggle.

        Args:
            node: The node to create the handler for

        Returns:
            A click handler function
        """

        def handler(_: Any) -> None:
            was_expanded = self._tree_state.is_expanded(node.id)
            self._tree_state.toggle_expanded(node.id)

            if was_expanded:
                self._on_collapse(node)
            else:
                self._on_expand(node)

        return handler

    def _create_select_handler(self, node: TreeNode) -> Callable:
        """Create click handler for node selection.

        Args:
            node: The node to create the handler for

        Returns:
            A click handler function
        """

        def handler(_: Any) -> None:
            # In multi-select mode, toggle selection
            add_to_selection = self._tree_state.is_multi_select()
            self._tree_state.select(node.id, add_to_selection)
            self._on_select(node)

        return handler

    # --- Fluent API ---

    def on_select(self, callback: Callable[[TreeNode], None]) -> Self:
        """Set callback for node selection.

        Args:
            callback: Function called with selected node

        Returns:
            Self for method chaining
        """
        self._on_select = callback
        return self

    def on_expand(self, callback: Callable[[TreeNode], None]) -> Self:
        """Set callback for node expansion.

        Args:
            callback: Function called when a node is expanded

        Returns:
            Self for method chaining
        """
        self._on_expand = callback
        return self

    def on_collapse(self, callback: Callable[[TreeNode], None]) -> Self:
        """Set callback for node collapse.

        Args:
            callback: Function called when a node is collapsed

        Returns:
            Self for method chaining
        """
        self._on_collapse = callback
        return self

    def indent_width(self, width: int) -> Self:
        """Set indentation width per level.

        Args:
            width: Pixels to indent each level

        Returns:
            Self for method chaining
        """
        self._indent_width = width
        return self

    def row_height(self, height: int) -> Self:
        """Set row height.

        Args:
            height: Height in pixels

        Returns:
            Self for method chaining
        """
        self._row_height = height
        return self

    # --- Convenience methods ---

    def expand_all(self) -> Self:
        """Expand all nodes.

        Returns:
            Self for method chaining
        """
        self._tree_state.expand_all()
        return self

    def collapse_all(self) -> Self:
        """Collapse all nodes.

        Returns:
            Self for method chaining
        """
        self._tree_state.collapse_all()
        return self

    def select(self, node_id: str) -> Self:
        """Select a node programmatically.

        Args:
            node_id: The ID of the node to select

        Returns:
            Self for method chaining
        """
        self._tree_state.select(node_id)
        return self

    def get_selected(self) -> list[TreeNode]:
        """Get list of selected nodes.

        Returns:
            List of selected TreeNode instances
        """
        return self._tree_state.get_selected()

    def get_state(self) -> TreeState:
        """Get the underlying TreeState.

        Returns:
            The TreeState instance
        """
        return self._tree_state
