"""Graph layout algorithms.

This module provides layout algorithms for positioning nodes in a graph.
The primary algorithm is the Sugiyama-style layered layout, which produces
clean, hierarchical visualizations for directed graphs.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Protocol

from castella.models.geometry import Point

from .models import GraphModel


class LayoutAlgorithm(Protocol):
    """Protocol for layout algorithms."""

    def layout(self, graph: GraphModel) -> None:
        """Apply layout to graph, modifying node positions in place.

        Args:
            graph: The graph to layout.
        """
        ...


@dataclass
class LayoutConfig:
    """Configuration for layout algorithms.

    Attributes:
        direction: Layout direction (LR=left-to-right, RL=right-to-left,
                   TB=top-to-bottom, BT=bottom-to-top).
        layer_spacing: Space between layers (horizontal for LR/RL, vertical for TB/BT).
        node_spacing: Space between nodes within the same layer.
        padding: Padding around the entire graph.
        crossing_reduction_passes: Number of barycenter sweeps for crossing reduction.
    """

    direction: Literal["LR", "RL", "TB", "BT"] = "LR"
    layer_spacing: float = 250.0
    node_spacing: float = 100.0
    padding: float = 50.0
    crossing_reduction_passes: int = 4


class SugiyamaLayout:
    """Sugiyama-style layered graph layout algorithm.

    This layout algorithm produces hierarchical visualizations by:
    1. Detecting and temporarily removing cycles (back edges)
    2. Assigning nodes to layers using longest-path method
    3. Reducing edge crossings using barycenter heuristic
    4. Assigning final coordinates

    The result is a clean, readable layout for directed graphs
    with good visual flow from source to sink nodes.
    """

    def __init__(self, config: LayoutConfig | None = None):
        """Initialize the layout algorithm.

        Args:
            config: Layout configuration. Uses defaults if not provided.
        """
        self._config = config or LayoutConfig()

    def layout(self, graph: GraphModel) -> None:
        """Apply the Sugiyama layout to the graph.

        Modifies node positions in place.

        Args:
            graph: The graph to layout.
        """
        if not graph.nodes:
            return

        # Build adjacency lists
        successors, predecessors = graph.build_adjacency_lists()

        # Phase 1: Detect and mark back edges (cycle handling)
        back_edges = self._detect_back_edges(graph, successors)

        # Phase 2: Assign layers using longest path (ignoring back edges)
        node_layers = self._assign_layers(graph, successors, predecessors, back_edges)

        # Group nodes by layer
        layer_nodes = self._group_by_layer(graph, node_layers)

        # Phase 3: Reduce edge crossings using barycenter method
        self._reduce_crossings(graph, layer_nodes, successors, predecessors, back_edges)

        # Phase 4: Assign final coordinates
        self._assign_coordinates(graph, layer_nodes)

    def _detect_back_edges(
        self, graph: GraphModel, successors: dict[str, list[str]]
    ) -> set[tuple[str, str]]:
        """Detect back edges in the graph using DFS.

        Back edges are edges that point from a node to one of its ancestors
        in the DFS tree, indicating a cycle.

        Args:
            graph: The graph to analyze.
            successors: Adjacency list of successors.

        Returns:
            Set of (source_id, target_id) tuples representing back edges.
        """
        back_edges: set[tuple[str, str]] = set()
        visited: set[str] = set()
        rec_stack: set[str] = set()  # Nodes in current recursion stack

        def dfs(node_id: str) -> None:
            visited.add(node_id)
            rec_stack.add(node_id)

            for succ_id in successors.get(node_id, []):
                if succ_id not in visited:
                    dfs(succ_id)
                elif succ_id in rec_stack:
                    # Found a back edge (cycle)
                    back_edges.add((node_id, succ_id))

            rec_stack.remove(node_id)

        # Run DFS from all unvisited nodes
        for node in graph.nodes:
            if node.id not in visited:
                dfs(node.id)

        return back_edges

    def _assign_layers(
        self,
        graph: GraphModel,
        successors: dict[str, list[str]],
        predecessors: dict[str, list[str]],
        back_edges: set[tuple[str, str]],
    ) -> dict[str, int]:
        """Assign layers to nodes using longest-path method.

        Unlike BFS (shortest path), this method assigns nodes to layers
        based on the longest path from source nodes. This creates better
        visual flow by pushing nodes as far down/right as possible.

        Args:
            graph: The graph to layout.
            successors: Adjacency list of successors.
            predecessors: Adjacency list of predecessors.
            back_edges: Set of back edges to ignore.

        Returns:
            Dictionary mapping node IDs to layer indices.
        """
        node_layers: dict[str, int] = {}

        # Find source nodes (no predecessors, ignoring back edges)
        sources: list[str] = []
        for node in graph.nodes:
            has_real_pred = False
            for pred in predecessors.get(node.id, []):
                if (pred, node.id) not in back_edges:
                    has_real_pred = True
                    break
            if not has_real_pred:
                sources.append(node.id)

        # If no sources found (all nodes in cycles), use heuristics
        if not sources:
            # Try to find nodes with "start" in name
            for node in graph.nodes:
                if "start" in node.id.lower() or node.id.startswith("__"):
                    sources.append(node.id)
                    break
            # Fallback to first node
            if not sources and graph.nodes:
                sources.append(graph.nodes[0].id)

        # Topological sort ignoring back edges
        topo_order = self._topological_sort(graph, successors, back_edges)

        # Assign layers using longest path
        for node_id in topo_order:
            if node_id in sources:
                node_layers[node_id] = 0
                continue

            # Layer = max predecessor layer + 1
            max_pred_layer = -1
            for pred_id in predecessors.get(node_id, []):
                if (pred_id, node_id) not in back_edges:
                    pred_layer = node_layers.get(pred_id, -1)
                    max_pred_layer = max(max_pred_layer, pred_layer)

            node_layers[node_id] = max_pred_layer + 1

        # Handle any remaining nodes (disconnected components)
        max_layer = max(node_layers.values()) if node_layers else 0
        for node in graph.nodes:
            if node.id not in node_layers:
                node_layers[node.id] = max_layer + 1

        return node_layers

    def _topological_sort(
        self,
        graph: GraphModel,
        successors: dict[str, list[str]],
        back_edges: set[tuple[str, str]],
    ) -> list[str]:
        """Perform topological sort ignoring back edges.

        Uses Kahn's algorithm for stable ordering.

        Args:
            graph: The graph to sort.
            successors: Adjacency list of successors.
            back_edges: Set of back edges to ignore.

        Returns:
            List of node IDs in topological order.
        """
        # Calculate in-degrees (ignoring back edges)
        in_degree: dict[str, int] = {n.id: 0 for n in graph.nodes}
        for node in graph.nodes:
            for succ_id in successors.get(node.id, []):
                if (node.id, succ_id) not in back_edges:
                    in_degree[succ_id] = in_degree.get(succ_id, 0) + 1

        # Start with nodes having in-degree 0
        queue = [n_id for n_id, deg in in_degree.items() if deg == 0]
        result: list[str] = []

        while queue:
            node_id = queue.pop(0)
            result.append(node_id)

            for succ_id in successors.get(node_id, []):
                if (node_id, succ_id) not in back_edges:
                    in_degree[succ_id] -= 1
                    if in_degree[succ_id] == 0:
                        queue.append(succ_id)

        # Add any remaining nodes (should be rare with back edge handling)
        for node in graph.nodes:
            if node.id not in result:
                result.append(node.id)

        return result

    def _group_by_layer(
        self, graph: GraphModel, node_layers: dict[str, int]
    ) -> dict[int, list[str]]:
        """Group node IDs by their layer.

        Args:
            graph: The graph.
            node_layers: Mapping of node ID to layer index.

        Returns:
            Dictionary mapping layer index to list of node IDs.
        """
        layer_nodes: dict[int, list[str]] = {}
        for node in graph.nodes:
            layer = node_layers.get(node.id, 0)
            if layer not in layer_nodes:
                layer_nodes[layer] = []
            layer_nodes[layer].append(node.id)
        return layer_nodes

    def _reduce_crossings(
        self,
        graph: GraphModel,
        layer_nodes: dict[int, list[str]],
        successors: dict[str, list[str]],
        predecessors: dict[str, list[str]],
        back_edges: set[tuple[str, str]],
    ) -> None:
        """Reduce edge crossings using barycenter heuristic.

        Performs multiple down and up sweeps, reordering nodes in each
        layer based on the average position of their neighbors in the
        adjacent layer.

        Args:
            graph: The graph.
            layer_nodes: Nodes grouped by layer.
            successors: Adjacency list of successors.
            predecessors: Adjacency list of predecessors.
            back_edges: Set of back edges to ignore.
        """
        if len(layer_nodes) <= 1:
            return

        sorted_layers = sorted(layer_nodes.keys())

        for _ in range(self._config.crossing_reduction_passes):
            # Down sweep: order each layer based on predecessors
            for i in range(1, len(sorted_layers)):
                layer_idx = sorted_layers[i]
                prev_layer_idx = sorted_layers[i - 1]

                self._order_layer_by_barycenter(
                    layer_nodes,
                    layer_idx,
                    prev_layer_idx,
                    predecessors,
                    back_edges,
                    use_predecessors=True,
                )

            # Up sweep: order each layer based on successors
            for i in range(len(sorted_layers) - 2, -1, -1):
                layer_idx = sorted_layers[i]
                next_layer_idx = sorted_layers[i + 1]

                self._order_layer_by_barycenter(
                    layer_nodes,
                    layer_idx,
                    next_layer_idx,
                    successors,
                    back_edges,
                    use_predecessors=False,
                )

    def _order_layer_by_barycenter(
        self,
        layer_nodes: dict[int, list[str]],
        layer_idx: int,
        adj_layer_idx: int,
        adjacency: dict[str, list[str]],
        back_edges: set[tuple[str, str]],
        use_predecessors: bool,
    ) -> None:
        """Reorder nodes in a layer based on barycenter of adjacent layer.

        The barycenter is the average position of a node's neighbors
        in the adjacent layer. Sorting by barycenter tends to minimize
        edge crossings.

        Args:
            layer_nodes: Nodes grouped by layer.
            layer_idx: Index of layer to reorder.
            adj_layer_idx: Index of adjacent layer to base ordering on.
            adjacency: Adjacency list (predecessors or successors).
            back_edges: Set of back edges to ignore.
            use_predecessors: True if adjacency contains predecessors.
        """
        nodes = layer_nodes[layer_idx]
        if len(nodes) <= 1:
            return

        adj_layer = layer_nodes.get(adj_layer_idx, [])
        if not adj_layer:
            return

        # Map adjacent layer nodes to positions
        adj_positions = {node_id: i for i, node_id in enumerate(adj_layer)}

        # Calculate barycenter for each node
        barycenters: dict[str, float] = {}
        for node_id in nodes:
            neighbors = adjacency.get(node_id, [])
            positions: list[int] = []

            for neighbor_id in neighbors:
                # Check if edge should be considered
                if use_predecessors:
                    edge = (neighbor_id, node_id)
                else:
                    edge = (node_id, neighbor_id)

                if edge not in back_edges and neighbor_id in adj_positions:
                    positions.append(adj_positions[neighbor_id])

            if positions:
                barycenters[node_id] = sum(positions) / len(positions)
            else:
                # Keep original order if no neighbors in adjacent layer
                barycenters[node_id] = nodes.index(node_id)

        # Sort by barycenter
        layer_nodes[layer_idx] = sorted(nodes, key=lambda n: barycenters[n])

    def _assign_coordinates(
        self, graph: GraphModel, layer_nodes: dict[int, list[str]]
    ) -> None:
        """Assign final X/Y coordinates to nodes.

        Handles both horizontal (LR/RL) and vertical (TB/BT) layouts.

        Args:
            graph: The graph.
            layer_nodes: Nodes grouped and ordered by layer.
        """
        config = self._config
        direction = config.direction
        is_horizontal = direction in ("LR", "RL")
        is_reversed = direction in ("RL", "BT")

        sorted_layers = sorted(layer_nodes.keys())
        if is_reversed:
            sorted_layers = list(reversed(sorted_layers))

        # Calculate max nodes per layer for centering
        max_nodes_in_layer = max(len(nodes) for nodes in layer_nodes.values())

        for layer_offset, layer_idx in enumerate(sorted_layers):
            nodes = layer_nodes[layer_idx]

            # Calculate primary axis position (layer position)
            primary_pos = config.padding + layer_offset * config.layer_spacing

            # Calculate secondary axis positions (within layer)
            total_span = (len(nodes) - 1) * config.node_spacing if nodes else 0

            # Center the nodes in this layer
            center_offset = (max_nodes_in_layer - 1) * config.node_spacing / 2

            for i, node_id in enumerate(nodes):
                node = graph.get_node(node_id)
                if node is None:
                    continue

                secondary_pos = (
                    config.padding
                    + center_offset
                    - total_span / 2
                    + i * config.node_spacing
                )

                if is_horizontal:
                    node.position = Point(x=primary_pos, y=secondary_pos)
                else:
                    node.position = Point(x=secondary_pos, y=primary_pos)


def compute_layout(
    graph: GraphModel,
    config: LayoutConfig | None = None,
) -> None:
    """Convenience function to apply layout to a graph.

    Args:
        graph: The graph to layout.
        config: Optional layout configuration.
    """
    layout = SugiyamaLayout(config)
    layout.layout(graph)
