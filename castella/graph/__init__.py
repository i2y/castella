"""Graph visualization components for Castella.

This module provides reusable components for visualizing directed graphs
with automatic layout using the Sugiyama algorithm.

Basic usage:

    from castella import App
    from castella.frame import Frame
    from castella.graph import GraphModel, NodeModel, EdgeModel, GraphCanvas

    # Create a graph
    graph = GraphModel(
        name="My Graph",
        nodes=[
            NodeModel(id="a", label="Start"),
            NodeModel(id="b", label="Process"),
            NodeModel(id="c", label="End"),
        ],
        edges=[
            EdgeModel(id="e1", source_id="a", target_id="b"),
            EdgeModel(id="e2", source_id="b", target_id="c"),
        ],
    )

    # Create canvas (auto-layouts by default)
    canvas = GraphCanvas(graph)
    canvas.on_node_click(lambda node_id: print(f"Clicked: {node_id}"))

    App(Frame("Graph", 800, 600), canvas).run()

Custom layout configuration:

    from castella.graph import SugiyamaLayout, LayoutConfig

    config = LayoutConfig(
        direction="TB",           # Top to bottom
        layer_spacing=200,
        node_spacing=80,
    )
    canvas = GraphCanvas(graph, layout_config=config)

Custom theming:

    from castella.graph import GraphTheme, LIGHT_THEME

    canvas = GraphCanvas(graph, theme=LIGHT_THEME)
"""

# Models
from .models import (
    NodeModel,
    NodeType,
    EdgeModel,
    EdgeType,
    GraphModel,
)

# Layout
from .layout import (
    SugiyamaLayout,
    LayoutConfig,
    LayoutAlgorithm,
    compute_layout,
)

# Canvas widget
from .canvas import GraphCanvas

# Transform
from .transform import CanvasTransform

# Hit testing
from .hit_testing import (
    GraphNodeElement,
    GraphEdgeElement,
    hit_test,
)

# Theme
from .theme import (
    GraphTheme,
    DARK_THEME,
    LIGHT_THEME,
)

__all__ = [
    # Models
    "NodeModel",
    "NodeType",
    "EdgeModel",
    "EdgeType",
    "GraphModel",
    # Layout
    "SugiyamaLayout",
    "LayoutConfig",
    "LayoutAlgorithm",
    "compute_layout",
    # Canvas
    "GraphCanvas",
    # Transform
    "CanvasTransform",
    # Hit testing
    "GraphNodeElement",
    "GraphEdgeElement",
    "hit_test",
    # Theme
    "GraphTheme",
    "DARK_THEME",
    "LIGHT_THEME",
]
