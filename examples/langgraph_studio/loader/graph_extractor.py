"""Extract graph structure from LangGraph compiled graphs."""

from __future__ import annotations

import inspect
from types import ModuleType
from typing import Any, Callable

from castella.models.geometry import Point

from ..models.graph import GraphModel, NodeModel, EdgeModel


class GraphExtractionError(Exception):
    """Raised when graph extraction fails."""

    pass


def find_compiled_graph(module: ModuleType) -> Any:
    """Find a CompiledGraph instance in a module.

    Searches for common variable names first, then scans all module
    attributes for anything that looks like a compiled LangGraph.

    Args:
        module: The loaded Python module.

    Returns:
        The compiled graph object.

    Raises:
        GraphExtractionError: If no compiled graph is found.
    """
    # Check common names first
    common_names = [
        "graph",
        "compiled_graph",
        "app",
        "workflow",
        "agent",
        "chain",
    ]

    for name in common_names:
        if hasattr(module, name):
            obj = getattr(module, name)
            if _is_compiled_graph(obj):
                return obj

    # Scan all module attributes
    for name in dir(module):
        if name.startswith("_"):
            continue
        try:
            obj = getattr(module, name)
            if _is_compiled_graph(obj):
                return obj
        except Exception:
            # Skip attributes that raise on access
            continue

    raise GraphExtractionError(
        "No CompiledGraph found in module. "
        "Ensure the module exports a compiled LangGraph (e.g., graph.compile())."
    )


def _is_compiled_graph(obj: Any) -> bool:
    """Check if an object is a LangGraph CompiledGraph.

    Uses duck typing to check for the get_graph() method.

    Args:
        obj: Object to check.

    Returns:
        True if the object appears to be a compiled graph.
    """
    return hasattr(obj, "get_graph") and callable(getattr(obj, "get_graph"))


def extract_graph_model(compiled_graph: Any) -> GraphModel:
    """Extract a GraphModel from a CompiledGraph.

    Parses the graph structure returned by get_graph() and converts
    it into our internal GraphModel representation with computed
    layout positions.

    Args:
        compiled_graph: A LangGraph CompiledGraph instance.

    Returns:
        GraphModel with nodes and edges.

    Raises:
        GraphExtractionError: If graph extraction fails.
    """
    try:
        # Get the underlying graph structure
        graph = compiled_graph.get_graph()
    except Exception as e:
        raise GraphExtractionError(f"Failed to get graph: {e}") from e

    nodes: list[NodeModel] = []
    edges: list[EdgeModel] = []

    try:
        # Extract nodes
        node_names = _get_node_names(graph)
        node_data_map = _get_node_data(graph)
        node_positions = _compute_layout(node_names, graph)

        for node_name in node_names:
            node_data = node_data_map.get(node_name)
            node_type = _determine_node_type(node_name, node_data)

            nodes.append(
                NodeModel(
                    id=node_name,
                    label=_format_node_label(node_name),
                    node_type=node_type,
                    position=node_positions.get(node_name, Point(x=0, y=0)),
                    metadata={"original": str(node_data)[:200] if node_data else ""},
                )
            )

        # Extract edges
        edge_list = _get_edges(graph)
        for i, edge_info in enumerate(edge_list):
            source, target = edge_info[0], edge_info[1]

            # Determine if conditional
            edge_type = "normal"
            condition_label = None

            # Check for conditional edge attributes
            # Format can be: (source, target), (source, target, label),
            # or (source, target, data, conditional)
            if len(edge_info) >= 4:
                # LangGraph Edge format: (source, target, data, conditional)
                data = edge_info[2]
                is_conditional = edge_info[3]
                if is_conditional:
                    edge_type = "conditional"
                    if data:
                        condition_label = str(data)[:30]
            elif len(edge_info) == 3:
                # Simple format: (source, target, label)
                edge_type = "conditional"
                condition_label = str(edge_info[2])[:30]

            edges.append(
                EdgeModel(
                    id=f"edge_{i}_{source}_{target}",
                    source_node_id=source,
                    target_node_id=target,
                    edge_type=edge_type,
                    condition_label=condition_label,
                )
            )

        # Get graph name if available
        name = getattr(compiled_graph, "name", None)
        if not name:
            name = getattr(graph, "name", "LangGraph")

        return GraphModel(name=str(name), nodes=nodes, edges=edges)

    except Exception as e:
        raise GraphExtractionError(f"Failed to extract graph model: {e}") from e


def _get_node_names(graph: Any) -> list[str]:
    """Get list of node names from graph."""
    # Try different access patterns
    if hasattr(graph, "nodes"):
        nodes = graph.nodes
        if isinstance(nodes, dict):
            return list(nodes.keys())
        elif hasattr(nodes, "__iter__"):
            return list(nodes)

    # Fallback: try _nodes attribute
    if hasattr(graph, "_nodes"):
        return list(graph._nodes.keys())

    return []


def _get_node_data(graph: Any) -> dict[str, Any]:
    """Get node data mapping from graph."""
    if hasattr(graph, "nodes"):
        nodes = graph.nodes
        if isinstance(nodes, dict):
            return nodes

    if hasattr(graph, "_nodes"):
        return graph._nodes

    return {}


def _get_edges(graph: Any) -> list[tuple]:
    """Get list of edges from graph.

    Returns tuples of (source, target) or (source, target, data, conditional)
    for edges with additional metadata.
    """
    edges = []

    if hasattr(graph, "edges"):
        graph_edges = graph.edges
        if isinstance(graph_edges, (list, set)):
            for edge in graph_edges:
                if hasattr(edge, "source") and hasattr(edge, "target"):
                    # LangGraph Edge object - extract all relevant attributes
                    source = edge.source
                    target = edge.target
                    conditional = getattr(edge, "conditional", False)
                    data = getattr(edge, "data", None)

                    if conditional or data:
                        edges.append((source, target, data, conditional))
                    else:
                        edges.append((source, target))
                elif isinstance(edge, (tuple, list)) and len(edge) >= 2:
                    edges.append(tuple(edge))
        elif isinstance(graph_edges, dict):
            for source, targets in graph_edges.items():
                if isinstance(targets, (list, set)):
                    for target in targets:
                        edges.append((source, target))
                else:
                    edges.append((source, targets))

    # Also check _edges attribute
    if hasattr(graph, "_edges"):
        for edge in graph._edges:
            if isinstance(edge, (tuple, list)) and len(edge) >= 2:
                edges.append(tuple(edge))

    return edges


def _determine_node_type(
    node_name: str, node_data: Any
) -> str:
    """Determine the type of a node for visual styling."""
    name_lower = node_name.lower()

    # Check for start/end nodes
    if name_lower in ("__start__", "start", "__begin__"):
        return "start"
    if name_lower in ("__end__", "end", "__finish__"):
        return "end"

    # Check node data for type hints
    if node_data:
        data_str = str(node_data).lower()

        if "agent" in data_str or "llm" in data_str:
            return "agent"
        if "tool" in data_str:
            return "tool"
        if "condition" in data_str or "branch" in data_str or "router" in data_str:
            return "condition"

    # Check node name for hints
    if "agent" in name_lower:
        return "agent"
    if "tool" in name_lower:
        return "tool"
    if any(x in name_lower for x in ("condition", "branch", "router", "decide")):
        return "condition"

    return "default"


def _format_node_label(node_name: str) -> str:
    """Format node name for display."""
    # Handle special names
    if node_name.startswith("__") and node_name.endswith("__"):
        return node_name.strip("_").title()

    # Convert snake_case to Title Case
    return node_name.replace("_", " ").title()


def _compute_layout(node_names: list[str], graph: Any) -> dict[str, Point]:
    """Compute node positions using a layered layout algorithm.

    Uses topological sorting to assign layers, then positions nodes
    within each layer for clear visualization. Handles branching by
    spreading successors vertically.

    Args:
        node_names: List of node names.
        graph: The graph object for edge information.

    Returns:
        Dict mapping node IDs to Point positions.
    """
    if not node_names:
        return {}

    positions: dict[str, Point] = {}

    # Build adjacency lists
    edges = _get_edges(graph)
    successors: dict[str, list[str]] = {n: [] for n in node_names}
    predecessors: dict[str, list[str]] = {n: [] for n in node_names}

    for edge in edges:
        src, tgt = edge[0], edge[1]
        if src in successors and tgt in successors:
            if tgt not in successors[src]:
                successors[src].append(tgt)
            if src not in predecessors[tgt]:
                predecessors[tgt].append(src)

    # Assign layers using BFS from start nodes (minimum distance approach)
    # This handles cyclic graphs by assigning each node its minimum layer
    layers: dict[str, int] = {}
    start_nodes = [n for n in node_names if not predecessors[n]]

    # If no clear start, use nodes with names suggesting start
    if not start_nodes:
        for n in node_names:
            if "start" in n.lower() or n.startswith("__"):
                start_nodes.append(n)
                break
        if not start_nodes:
            start_nodes = [node_names[0]]

    # BFS to assign minimum layers (first visit wins)
    # This ensures nodes in cycles stay at their earliest possible position
    queue = [(n, 0) for n in start_nodes]
    visited: set[str] = set(start_nodes)
    for n in start_nodes:
        layers[n] = 0

    while queue:
        node, layer = queue.pop(0)

        for succ in successors.get(node, []):
            if succ not in visited:
                # First time visiting this node - assign layer
                visited.add(succ)
                layers[succ] = layer + 1
                queue.append((succ, layer + 1))
            # If already visited, don't update layer (keeps minimum distance)

    # Handle nodes not reached by BFS
    for node in node_names:
        if node not in layers:
            layers[node] = max(layers.values()) + 1 if layers else 0

    # Group nodes by layer
    layer_nodes: dict[int, list[str]] = {}
    for node, layer in layers.items():
        if layer not in layer_nodes:
            layer_nodes[layer] = []
        layer_nodes[layer].append(node)

    # Position nodes with improved Y positioning for branching
    x_spacing = 250
    y_spacing = 120
    start_x = 100
    center_y = 250

    # First pass: assign positions based on predecessor average Y
    # Process layers in order
    for layer_idx in sorted(layer_nodes.keys()):
        nodes_in_layer = layer_nodes[layer_idx]

        if layer_idx == 0:
            # Start nodes centered
            total_height = (len(nodes_in_layer) - 1) * y_spacing
            y_start = center_y - total_height / 2
            for i, node in enumerate(nodes_in_layer):
                positions[node] = Point(
                    x=start_x + layer_idx * x_spacing,
                    y=y_start + i * y_spacing,
                )
        else:
            # Position based on predecessors
            node_y_hints: dict[str, list[float]] = {}

            for node in nodes_in_layer:
                preds = predecessors.get(node, [])
                y_hints = []
                for pred in preds:
                    if pred in positions:
                        # Get index among siblings (other successors of this predecessor)
                        siblings = successors.get(pred, [])
                        sibling_idx = siblings.index(node) if node in siblings else 0
                        sibling_count = len(siblings)

                        # Spread siblings vertically around predecessor's Y
                        pred_y = positions[pred].y
                        if sibling_count > 1:
                            offset = (sibling_idx - (sibling_count - 1) / 2) * y_spacing
                            y_hints.append(pred_y + offset)
                        else:
                            y_hints.append(pred_y)

                node_y_hints[node] = y_hints

            # Sort nodes by their average Y hint to minimize crossings
            def avg_y(node: str) -> float:
                hints = node_y_hints.get(node, [])
                return sum(hints) / len(hints) if hints else center_y

            nodes_in_layer.sort(key=avg_y)

            # Assign final Y positions, ensuring minimum spacing
            if len(nodes_in_layer) == 1:
                positions[nodes_in_layer[0]] = Point(
                    x=start_x + layer_idx * x_spacing,
                    y=avg_y(nodes_in_layer[0]),
                )
            else:
                # Space nodes evenly but respect order
                total_height = (len(nodes_in_layer) - 1) * y_spacing
                min_y = min(avg_y(n) for n in nodes_in_layer)
                max_y = max(avg_y(n) for n in nodes_in_layer)
                actual_spread = max(total_height, max_y - min_y)
                y_start = (min_y + max_y) / 2 - actual_spread / 2

                for i, node in enumerate(nodes_in_layer):
                    positions[node] = Point(
                        x=start_x + layer_idx * x_spacing,
                        y=y_start + i * y_spacing,
                    )

    return positions


def extract_node_functions(compiled_graph: Any) -> dict[str, Callable]:
    """Extract the callable functions for each node in the graph.

    Args:
        compiled_graph: A LangGraph CompiledGraph instance.

    Returns:
        Dict mapping node IDs to their callable functions.
    """
    try:
        graph = compiled_graph.get_graph()
        node_data = _get_node_data(graph)

        functions: dict[str, Callable] = {}
        for node_name, data in node_data.items():
            if callable(data):
                functions[node_name] = data
            elif hasattr(data, "func") and callable(data.func):
                # Handle wrapped functions (e.g., functools.partial)
                functions[node_name] = data.func
            elif hasattr(data, "__call__"):
                functions[node_name] = data

        return functions
    except Exception:
        return {}


def get_node_source(func: Callable | None) -> str | None:
    """Get the source code for a node function.

    Args:
        func: The function/callable to inspect.

    Returns:
        Source code string or None if unavailable.
    """
    if func is None:
        return None

    try:
        # Try to get source directly
        return inspect.getsource(func)
    except (OSError, TypeError):
        # Built-in, dynamically generated, or C function
        pass

    # Try unwrapping decorated functions
    try:
        unwrapped = inspect.unwrap(func)
        if unwrapped is not func:
            return inspect.getsource(unwrapped)
    except (OSError, TypeError, ValueError):
        pass

    return None
