"""Graph data models for visualization."""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field

from castella.models.geometry import Point, Size


class NodeType(str, Enum):
    """Visual type of a node for styling."""

    DEFAULT = "default"
    START = "start"
    END = "end"
    PROCESS = "process"
    DECISION = "decision"
    # LangGraph-specific types
    AGENT = "agent"
    TOOL = "tool"
    CONDITION = "condition"


class EdgeType(str, Enum):
    """Type of edge for styling."""

    NORMAL = "normal"
    CONDITIONAL = "conditional"
    BACK = "back"  # Back edge in a cycle


class NodeModel(BaseModel):
    """A node in the graph.

    Attributes:
        id: Unique identifier for the node.
        label: Display label for the node.
        node_type: Type of node for visual styling.
        position: Position on canvas (x, y).
        size: Node dimensions (width, height).
        metadata: Additional data attached to the node.
    """

    id: str
    label: str
    node_type: NodeType = NodeType.DEFAULT
    position: Point = Field(default_factory=lambda: Point(x=0, y=0))
    size: Size = Field(default_factory=lambda: Size(width=160, height=60))
    metadata: dict = Field(default_factory=dict)

    # Layout-related fields (internal use)
    _layer: int = 0
    _order: int = 0


class EdgeModel(BaseModel):
    """A directed edge between nodes.

    Attributes:
        id: Unique identifier for the edge.
        source_id: ID of the source node.
        target_id: ID of the target node.
        edge_type: Type of edge for styling.
        label: Optional label displayed on the edge.
        metadata: Additional data attached to the edge.
    """

    id: str
    source_id: str
    target_id: str
    edge_type: EdgeType = EdgeType.NORMAL
    label: str | None = None
    metadata: dict = Field(default_factory=dict)


class GraphModel(BaseModel):
    """Complete graph structure with nodes and edges.

    Attributes:
        name: Name of the graph.
        nodes: List of nodes in the graph.
        edges: List of edges connecting nodes.
        direction: Layout direction (LR, RL, TB, BT).
    """

    name: str = "Untitled"
    nodes: list[NodeModel] = Field(default_factory=list)
    edges: list[EdgeModel] = Field(default_factory=list)
    direction: Literal["LR", "RL", "TB", "BT"] = "LR"

    def get_node(self, node_id: str) -> NodeModel | None:
        """Get a node by its ID.

        Args:
            node_id: The node ID to look up.

        Returns:
            The node if found, None otherwise.
        """
        for node in self.nodes:
            if node.id == node_id:
                return node
        return None

    def get_edges_from(self, node_id: str) -> list[EdgeModel]:
        """Get all edges originating from a node.

        Args:
            node_id: The source node ID.

        Returns:
            List of edges from this node.
        """
        return [e for e in self.edges if e.source_id == node_id]

    def get_edges_to(self, node_id: str) -> list[EdgeModel]:
        """Get all edges targeting a node.

        Args:
            node_id: The target node ID.

        Returns:
            List of edges to this node.
        """
        return [e for e in self.edges if e.target_id == node_id]

    def get_successors(self, node_id: str) -> list[str]:
        """Get IDs of all successor nodes.

        Args:
            node_id: The source node ID.

        Returns:
            List of successor node IDs.
        """
        return [e.target_id for e in self.edges if e.source_id == node_id]

    def get_predecessors(self, node_id: str) -> list[str]:
        """Get IDs of all predecessor nodes.

        Args:
            node_id: The target node ID.

        Returns:
            List of predecessor node IDs.
        """
        return [e.source_id for e in self.edges if e.target_id == node_id]

    def find_start_nodes(self) -> list[str]:
        """Find nodes with no predecessors.

        Returns:
            List of start node IDs.
        """
        all_ids = {n.id for n in self.nodes}
        has_predecessors = {e.target_id for e in self.edges}
        return list(all_ids - has_predecessors)

    def find_end_nodes(self) -> list[str]:
        """Find nodes with no successors.

        Returns:
            List of end node IDs.
        """
        all_ids = {n.id for n in self.nodes}
        has_successors = {e.source_id for e in self.edges}
        return list(all_ids - has_successors)

    def build_adjacency_lists(
        self,
    ) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
        """Build adjacency lists for successors and predecessors.

        Returns:
            Tuple of (successors dict, predecessors dict).
        """
        successors: dict[str, list[str]] = {n.id: [] for n in self.nodes}
        predecessors: dict[str, list[str]] = {n.id: [] for n in self.nodes}

        for edge in self.edges:
            src, tgt = edge.source_id, edge.target_id
            if src in successors and tgt in successors:
                if tgt not in successors[src]:
                    successors[src].append(tgt)
                if src not in predecessors[tgt]:
                    predecessors[tgt].append(src)

        return successors, predecessors
