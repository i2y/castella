"""Extract graph structure from LangGraph compiled graphs."""

from __future__ import annotations

import inspect
from types import ModuleType
from typing import Any, Callable

from castella.graph import (
    GraphModel,
    NodeModel,
    NodeType,
    EdgeModel,
    EdgeType,
    SugiyamaLayout,
    LayoutConfig,
)


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
    layout positions using the Sugiyama algorithm.

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

        for node_name in node_names:
            node_data = node_data_map.get(node_name)
            node_type = _determine_node_type(node_name, node_data)

            nodes.append(
                NodeModel(
                    id=node_name,
                    label=_format_node_label(node_name),
                    node_type=node_type,
                    metadata={"original": str(node_data)[:200] if node_data else ""},
                )
            )

        # Extract edges
        edge_list = _get_edges(graph)
        for i, edge_info in enumerate(edge_list):
            source, target = edge_info[0], edge_info[1]

            # Determine if conditional
            edge_type = EdgeType.NORMAL
            condition_label = None

            # Check for conditional edge attributes
            # Format can be: (source, target), (source, target, label),
            # or (source, target, data, conditional)
            if len(edge_info) >= 4:
                # LangGraph Edge format: (source, target, data, conditional)
                data = edge_info[2]
                is_conditional = edge_info[3]
                if is_conditional:
                    edge_type = EdgeType.CONDITIONAL
                    if data:
                        condition_label = str(data)[:30]
            elif len(edge_info) == 3:
                # Simple format: (source, target, label)
                edge_type = EdgeType.CONDITIONAL
                condition_label = str(edge_info[2])[:30]

            edges.append(
                EdgeModel(
                    id=f"edge_{i}_{source}_{target}",
                    source_id=source,
                    target_id=target,
                    edge_type=edge_type,
                    label=condition_label,
                )
            )

        # Get graph name if available
        name = getattr(compiled_graph, "name", None)
        if not name:
            name = getattr(graph, "name", "LangGraph")

        # Create graph model
        graph_model = GraphModel(name=str(name), nodes=nodes, edges=edges)

        # Apply Sugiyama layout
        layout = SugiyamaLayout(LayoutConfig(
            direction="LR",
            layer_spacing=250,
            node_spacing=120,
        ))
        layout.layout(graph_model)

        return graph_model

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
) -> NodeType:
    """Determine the type of a node for visual styling."""
    name_lower = node_name.lower()

    # Check for start/end nodes
    if name_lower in ("__start__", "start", "__begin__"):
        return NodeType.START
    if name_lower in ("__end__", "end", "__finish__"):
        return NodeType.END

    # Check node data for type hints
    if node_data:
        data_str = str(node_data).lower()

        if "agent" in data_str or "llm" in data_str:
            return NodeType.AGENT
        if "tool" in data_str:
            return NodeType.TOOL
        if "condition" in data_str or "branch" in data_str or "router" in data_str:
            return NodeType.CONDITION

    # Check node name for hints
    if "agent" in name_lower:
        return NodeType.AGENT
    if "tool" in name_lower:
        return NodeType.TOOL
    if any(x in name_lower for x in ("condition", "branch", "router", "decide")):
        return NodeType.CONDITION

    return NodeType.DEFAULT


def _format_node_label(node_name: str) -> str:
    """Format node name for display."""
    # Handle special names
    if node_name.startswith("__") and node_name.endswith("__"):
        return node_name.strip("_").title()

    # Convert snake_case to Title Case
    return node_name.replace("_", " ").title()


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
