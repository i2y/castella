"""Theme definitions for graph visualization."""

from __future__ import annotations

from dataclasses import dataclass, field

from .models import NodeType, EdgeType


@dataclass
class GraphTheme:
    """Visual theme for graph rendering.

    Contains all color and styling information for nodes, edges,
    and canvas elements.

    Attributes:
        node_colors: Mapping of node types to their colors.
        edge_colors: Mapping of edge types to their colors.
        background_color: Canvas background color.
        grid_color: Grid line color.
        border_color: Canvas border color.
        active_node_color: Color for active/executing nodes.
        selected_border_color: Border color for selected nodes.
        node_border_width: Border width for nodes.
        node_border_radius: Corner radius for nodes.
        edge_width: Line width for edges.
        font_size: Base font size for labels.
        font_color_on_active: Text color when node is active.
    """

    # Node colors by type
    node_colors: dict[NodeType, str] = field(
        default_factory=lambda: {
            NodeType.DEFAULT: "#6b7280",  # Gray
            NodeType.START: "#22c55e",  # Green
            NodeType.END: "#ef4444",  # Red
            NodeType.PROCESS: "#3b82f6",  # Blue
            NodeType.DECISION: "#8b5cf6",  # Purple
            NodeType.AGENT: "#3b82f6",  # Blue
            NodeType.TOOL: "#f59e0b",  # Amber
            NodeType.CONDITION: "#8b5cf6",  # Purple
        }
    )

    # Edge colors by type
    edge_colors: dict[EdgeType, str] = field(
        default_factory=lambda: {
            EdgeType.NORMAL: "#9ca3af",  # Gray
            EdgeType.CONDITIONAL: "#8b5cf6",  # Purple
            EdgeType.BACK: "#f59e0b",  # Amber for back edges
        }
    )

    # Canvas colors
    background_color: str = "#1a1b26"  # Dark background
    grid_color: str = "#2a2b36"  # Grid lines
    border_color: str = "#3b4261"  # Canvas border

    # Special node states
    active_node_color: str = "#fbbf24"  # Yellow for active nodes
    selected_border_color: str = "#ffffff"  # White for selected
    hover_lighten_amount: float = 0.3  # How much to lighten on hover

    # Node styling
    node_border_width: float = 1.5
    node_border_radius: float = 8.0
    node_shadow_offset: float = 3.0
    node_shadow_color: str = "#00000022"

    # Edge styling
    edge_width: float = 1.0
    arrow_length: float = 12.0
    arrow_width: float = 6.0

    # Text styling
    font_size: float = 14.0
    font_color_on_active: str = "#1a1b26"  # Dark text on yellow

    def get_node_color(self, node_type: NodeType) -> str:
        """Get color for a node type.

        Args:
            node_type: The type of node.

        Returns:
            Hex color string.
        """
        return self.node_colors.get(node_type, self.node_colors[NodeType.DEFAULT])

    def get_edge_color(self, edge_type: EdgeType) -> str:
        """Get color for an edge type.

        Args:
            edge_type: The type of edge.

        Returns:
            Hex color string.
        """
        return self.edge_colors.get(edge_type, self.edge_colors[EdgeType.NORMAL])

    @staticmethod
    def lighten_color(hex_color: str, amount: float) -> str:
        """Lighten a hex color by a percentage.

        Args:
            hex_color: Hex color string (e.g., "#3b82f6").
            amount: Amount to lighten (0-1).

        Returns:
            Lightened hex color.
        """
        hex_color = hex_color.lstrip("#")
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)

        # Lighten towards white
        r = min(255, int(r + (255 - r) * amount))
        g = min(255, int(g + (255 - g) * amount))
        b = min(255, int(b + (255 - b) * amount))

        return f"#{r:02x}{g:02x}{b:02x}"


# Pre-defined themes
DARK_THEME = GraphTheme()

LIGHT_THEME = GraphTheme(
    background_color="#ffffff",
    grid_color="#e5e7eb",
    border_color="#d1d5db",
    node_colors={
        NodeType.DEFAULT: "#4b5563",
        NodeType.START: "#16a34a",
        NodeType.END: "#dc2626",
        NodeType.PROCESS: "#2563eb",
        NodeType.DECISION: "#7c3aed",
        NodeType.AGENT: "#2563eb",
        NodeType.TOOL: "#d97706",
        NodeType.CONDITION: "#7c3aed",
    },
    edge_colors={
        EdgeType.NORMAL: "#6b7280",
        EdgeType.CONDITIONAL: "#7c3aed",
        EdgeType.BACK: "#d97706",
    },
    active_node_color="#facc15",
    selected_border_color="#000000",
    font_color_on_active="#1f2937",
    node_shadow_color="#00000011",
)
