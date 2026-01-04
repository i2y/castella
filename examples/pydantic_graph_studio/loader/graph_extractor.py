"""Extract graph structure from pydantic-graph objects."""

from __future__ import annotations

import inspect
from dataclasses import fields as dataclass_fields
from types import ModuleType, UnionType
from typing import Any, get_args, get_origin, get_type_hints

from castella.graph import (
    EdgeModel,
    EdgeType,
    GraphModel,
    LayoutConfig,
    NodeModel,
    NodeType,
    SugiyamaLayout,
)

from ..models.graph import (
    EdgeInfo,
    GraphAPIType,
    NodeInfo,
    PydanticGraphModel,
)


class GraphExtractionError(Exception):
    """Raised when graph extraction fails."""

    pass


def find_pydantic_graph(module: ModuleType) -> tuple[Any, GraphAPIType]:
    """Find a pydantic-graph in a module.

    Searches for:
    1. Graph instances (BaseNode API)
    2. GraphBuilder instances (beta API)

    Args:
        module: The loaded Python module.

    Returns:
        Tuple of (graph_object, api_type).

    Raises:
        GraphExtractionError: If no graph is found.
    """
    # Check common variable names first
    common_names = ["graph", "app", "workflow", "agent", "g", "my_graph"]

    for name in common_names:
        if hasattr(module, name):
            obj = getattr(module, name)
            api_type = _detect_graph_type(obj)
            if api_type:
                return obj, api_type

    # Scan all module attributes
    for name in dir(module):
        if name.startswith("_"):
            continue
        try:
            obj = getattr(module, name)
            api_type = _detect_graph_type(obj)
            if api_type:
                return obj, api_type
        except Exception:
            continue

    raise GraphExtractionError(
        "No pydantic-graph found. "
        "Ensure the module exports a Graph or GraphBuilder instance."
    )


def _detect_graph_type(obj: Any) -> GraphAPIType | None:
    """Detect if object is a pydantic-graph and which API it uses."""
    # Check class name and module
    type_name = type(obj).__name__
    module_name = type(obj).__module__

    # Check for Graph class (BaseNode API)
    if type_name == "Graph" and "pydantic_graph" in module_name:
        return GraphAPIType.BASE_NODE

    # Duck typing for Graph
    if hasattr(obj, "node_defs") and hasattr(obj, "run") and hasattr(obj, "iter"):
        return GraphAPIType.BASE_NODE

    # Check for GraphBuilder (beta API)
    if type_name == "GraphBuilder" and "pydantic_graph" in module_name:
        return GraphAPIType.GRAPH_BUILDER

    # Duck typing for GraphBuilder
    if hasattr(obj, "step") and hasattr(obj, "build") and callable(obj.step):
        return GraphAPIType.GRAPH_BUILDER

    return None


def extract_graph_model(graph: Any, api_type: GraphAPIType) -> PydanticGraphModel:
    """Extract graph model from a pydantic-graph object.

    Args:
        graph: The Graph or GraphBuilder instance.
        api_type: The type of API being used.

    Returns:
        PydanticGraphModel with nodes and edges.
    """
    if api_type == GraphAPIType.BASE_NODE:
        return _extract_basenode_graph(graph)
    elif api_type == GraphAPIType.GRAPH_BUILDER:
        return _extract_builder_graph(graph)
    else:
        raise GraphExtractionError(f"Unsupported API type: {api_type}")


def _extract_basenode_graph(graph: Any) -> PydanticGraphModel:
    """Extract graph model from BaseNode API Graph.

    Uses graph.node_defs to get node classes and edge information.
    The NodeDef structure provides:
    - node: the actual node class
    - node_id: the node ID
    - next_node_edges: dict of target node names to Edge objects
    - end_edge: Edge object if node can return End, or None
    """
    model = PydanticGraphModel(
        name=getattr(graph, "name", "PydanticGraph") or "PydanticGraph",
        api_type=GraphAPIType.BASE_NODE,
    )

    # Get node definitions - try different access patterns
    node_defs = _get_node_defs(graph)
    if not node_defs:
        raise GraphExtractionError("No node definitions found in graph.")

    # Add __start__ and __end__ nodes
    model.nodes.append(
        NodeInfo(
            id="__start__",
            label="Start",
            is_start=True,
        )
    )
    model.nodes.append(
        NodeInfo(
            id="__end__",
            label="End",
            is_end=True,
        )
    )

    # Extract nodes from NodeDef objects
    for node_id, node_def in node_defs.items():
        # Get node class from NodeDef
        node_class = getattr(node_def, "node", node_def)

        # Get edge info from NodeDef
        next_node_edges = getattr(node_def, "next_node_edges", {}) or {}
        end_edge = getattr(node_def, "end_edge", None)
        can_end = end_edge is not None

        # Get return type names from edges
        return_types = list(next_node_edges.keys())

        # Extract dataclass fields if available
        fields = _extract_dataclass_fields(node_class)

        node_info = NodeInfo(
            id=node_id,
            label=_format_node_label(node_id),
            node_class_name=node_class.__name__ if hasattr(node_class, "__name__") else str(node_class),
            docstring=getattr(node_class, "__doc__", None),
            source_code=_get_source_code(node_class),
            return_types=return_types,
            is_end=can_end,
            fields=fields,
        )
        model.nodes.append(node_info)

    # Find start nodes (nodes that are not targets of any other node)
    all_targets: set[str] = set()
    for node_id, node_def in node_defs.items():
        next_node_edges = getattr(node_def, "next_node_edges", {}) or {}
        for target_id in next_node_edges.keys():
            all_targets.add(target_id)

    # Mark nodes that are entry points
    for node_id in node_defs.keys():
        if node_id not in all_targets:
            node = model.get_node(node_id)
            if node:
                node.is_start = True

    # Build edges from NodeDef edge info
    edge_id = 0

    # Add edges from __start__ to entry nodes
    for node in model.nodes:
        if node.is_start and node.id != "__start__":
            model.edges.append(
                EdgeInfo(
                    id=f"edge_{edge_id}",
                    source_id="__start__",
                    target_id=node.id,
                )
            )
            edge_id += 1

    # Add edges between nodes based on NodeDef.next_node_edges
    for node_id, node_def in node_defs.items():
        next_node_edges = getattr(node_def, "next_node_edges", {}) or {}
        end_edge = getattr(node_def, "end_edge", None)
        can_end = end_edge is not None

        is_conditional = len(next_node_edges) > 1 or (len(next_node_edges) >= 1 and can_end)

        for target_id, edge in next_node_edges.items():
            edge_label = getattr(edge, "label", None)
            model.edges.append(
                EdgeInfo(
                    id=f"edge_{edge_id}",
                    source_id=node_id,
                    target_id=target_id,
                    label=edge_label,
                    is_conditional=is_conditional,
                )
            )
            edge_id += 1

        if can_end:
            edge_label = getattr(end_edge, "label", None)
            model.edges.append(
                EdgeInfo(
                    id=f"edge_{edge_id}",
                    source_id=node_id,
                    target_id="__end__",
                    label=edge_label,
                    is_conditional=is_conditional,
                )
            )
            edge_id += 1

    return model


def _extract_builder_graph(builder: Any) -> PydanticGraphModel:
    """Extract graph model from GraphBuilder beta API.

    Analyzes the builder's internal structure for steps and edges.
    """
    model = PydanticGraphModel(
        name="GraphBuilder Graph",
        api_type=GraphAPIType.GRAPH_BUILDER,
    )

    # Add __start__ and __end__ nodes
    model.nodes.append(
        NodeInfo(
            id="__start__",
            label="Start",
            is_start=True,
        )
    )
    model.nodes.append(
        NodeInfo(
            id="__end__",
            label="End",
            is_end=True,
        )
    )

    # Try to access internal step definitions
    steps = getattr(builder, "_steps", None) or getattr(builder, "steps", {})

    if isinstance(steps, dict):
        for step_id, step_info in steps.items():
            func = step_info.get("func") if isinstance(step_info, dict) else step_info

            node_info = NodeInfo(
                id=step_id,
                label=_format_node_label(step_id),
                node_class_name=func.__name__ if callable(func) else str(func),
                docstring=func.__doc__ if callable(func) else None,
                source_code=_get_source_code(func) if callable(func) else None,
            )
            model.nodes.append(node_info)

    # Try to access edge definitions
    edges = getattr(builder, "_edges", None) or getattr(builder, "edges", [])

    edge_id = 0
    if isinstance(edges, list):
        for edge in edges:
            if isinstance(edge, dict):
                source = edge.get("source", "")
                target = edge.get("target", "")
            elif isinstance(edge, tuple) and len(edge) >= 2:
                source, target = edge[0], edge[1]
            else:
                continue

            model.edges.append(
                EdgeInfo(
                    id=f"edge_{edge_id}",
                    source_id=source,
                    target_id=target,
                    label=edge.get("label") if isinstance(edge, dict) else None,
                )
            )
            edge_id += 1

    return model


def _get_node_defs(graph: Any) -> dict[str, Any]:
    """Get node definitions from a Graph object."""
    # Try different access patterns
    if hasattr(graph, "node_defs"):
        defs = graph.node_defs
        if isinstance(defs, dict):
            return defs

    # Try _node_defs
    if hasattr(graph, "_node_defs"):
        defs = graph._node_defs
        if isinstance(defs, dict):
            return defs

    # Try to build from nodes tuple
    if hasattr(graph, "_nodes"):
        nodes = graph._nodes
        if isinstance(nodes, (list, tuple)):
            return {node.__name__: node for node in nodes if isinstance(node, type)}

    return {}


def _parse_node_return_types(node_class: type) -> tuple[list[str], bool]:
    """Parse return type annotation to extract next node types.

    Args:
        node_class: The node class to analyze.

    Returns:
        Tuple of (list of node type names, can_return_end).
    """
    types: list[str] = []
    can_end = False

    # Get run method
    run_method = getattr(node_class, "run", None)
    if not run_method:
        return types, can_end

    try:
        hints = get_type_hints(run_method)
        return_type = hints.get("return")
    except Exception:
        return types, can_end

    if return_type is None:
        return types, can_end

    # Handle Union types (Python 3.10+ | syntax or typing.Union)
    origin = get_origin(return_type)

    if origin is UnionType or (origin is not None and origin.__name__ == "Union"):
        # Union type - extract all alternatives
        for arg in get_args(return_type):
            if _is_end_type(arg):
                can_end = True
            elif isinstance(arg, type):
                types.append(arg.__name__)
            else:
                # Handle Annotated types
                inner = get_origin(arg)
                if inner and isinstance(inner, type):
                    if _is_end_type(inner):
                        can_end = True
                    else:
                        types.append(inner.__name__)
    elif _is_end_type(return_type):
        can_end = True
    elif isinstance(return_type, type):
        types.append(return_type.__name__)
    else:
        # Try to get the origin for generic types
        if origin and isinstance(origin, type):
            if _is_end_type(origin):
                can_end = True
            else:
                types.append(origin.__name__)

    return types, can_end


def _is_end_type(type_hint: Any) -> bool:
    """Check if type is End[T]."""
    if type_hint is None:
        return False

    # Check class name
    type_name = getattr(type_hint, "__name__", "")
    if type_name == "End":
        return True

    # Check origin for generic End[T]
    origin = get_origin(type_hint)
    if origin:
        origin_name = getattr(origin, "__name__", "")
        if origin_name == "End":
            return True

    # Check string representation
    type_str = str(type_hint)
    if "End[" in type_str or type_str == "End":
        return True

    return False


def _extract_dataclass_fields(node_class: type) -> dict[str, str]:
    """Extract dataclass field names and types from a node class."""
    fields: dict[str, str] = {}

    if not hasattr(node_class, "__dataclass_fields__"):
        return fields

    try:
        for field in dataclass_fields(node_class):
            type_str = str(field.type) if field.type else "Any"
            # Simplify type representation
            type_str = type_str.replace("typing.", "").replace("<class '", "").replace("'>", "")
            fields[field.name] = type_str
    except Exception:
        pass

    return fields


def _get_source_code(obj: Any) -> str | None:
    """Get the source code for an object."""
    if obj is None:
        return None

    try:
        return inspect.getsource(obj)
    except (OSError, TypeError):
        pass

    # Try unwrapping decorated functions
    try:
        unwrapped = inspect.unwrap(obj)
        if unwrapped is not obj:
            return inspect.getsource(unwrapped)
    except (OSError, TypeError, ValueError):
        pass

    return None


def _format_node_label(node_name: str) -> str:
    """Format node name for display."""
    # Handle special names
    if node_name.startswith("__") and node_name.endswith("__"):
        return node_name.strip("_").title()

    # Convert snake_case or CamelCase to Title Case
    # First handle snake_case
    if "_" in node_name:
        return node_name.replace("_", " ").title()

    # Handle CamelCase - insert spaces before capital letters
    result = []
    for i, char in enumerate(node_name):
        if i > 0 and char.isupper():
            result.append(" ")
        result.append(char)
    return "".join(result)


def to_castella_graph_model(pg_model: PydanticGraphModel) -> GraphModel:
    """Convert PydanticGraphModel to Castella's GraphModel for visualization.

    Args:
        pg_model: The pydantic-graph model.

    Returns:
        Castella GraphModel with computed layout positions.
    """
    nodes: list[NodeModel] = []
    edges: list[EdgeModel] = []

    # Convert nodes
    for node_info in pg_model.nodes:
        node_type = NodeType.DEFAULT

        if node_info.id == "__start__":
            node_type = NodeType.START
        elif node_info.id == "__end__":
            node_type = NodeType.END
        elif node_info.is_end:
            # Can return End[T] - mark as decision/condition
            node_type = NodeType.CONDITION
        elif node_info.is_start:
            node_type = NodeType.PROCESS

        nodes.append(
            NodeModel(
                id=node_info.id,
                label=node_info.label,
                node_type=node_type,
                metadata={
                    "docstring": node_info.docstring or "",
                    "source_code": node_info.source_code or "",
                    "return_types": node_info.return_types,
                    "fields": node_info.fields,
                },
            )
        )

    # Convert edges
    for edge_info in pg_model.edges:
        edge_type = EdgeType.CONDITIONAL if edge_info.is_conditional else EdgeType.NORMAL

        edges.append(
            EdgeModel(
                id=edge_info.id,
                source_id=edge_info.source_id,
                target_id=edge_info.target_id,
                edge_type=edge_type,
                label=edge_info.label,
            )
        )

    # Create graph model
    graph_model = GraphModel(
        name=pg_model.name,
        nodes=nodes,
        edges=edges,
    )

    # Apply Sugiyama layout
    layout = SugiyamaLayout(
        LayoutConfig(
            direction="LR",
            layer_spacing=200,
            node_spacing=100,
        )
    )
    layout.layout(graph_model)

    return graph_model
