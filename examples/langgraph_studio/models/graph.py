"""Graph data models for LangGraph Studio."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from castella.models.geometry import Point


class NodeModel(BaseModel):
    """A node in the LangGraph.

    Attributes:
        id: Unique identifier for the node.
        label: Display label for the node.
        node_type: Type of node for visual styling.
        position: Canvas position (x, y).
        size: Node dimensions (width, height).
        metadata: Additional data from the original node.
    """

    id: str
    label: str
    node_type: Literal["start", "end", "agent", "tool", "condition", "default"] = (
        "default"
    )
    position: Point = Field(default_factory=lambda: Point(x=0, y=0))
    size: tuple[float, float] = (160, 60)
    metadata: dict = Field(default_factory=dict)


class EdgeModel(BaseModel):
    """A directed edge between nodes.

    Attributes:
        id: Unique identifier for the edge.
        source_node_id: ID of the source node.
        target_node_id: ID of the target node.
        edge_type: Type of edge (normal or conditional).
        condition_label: Label for conditional edges.
    """

    id: str
    source_node_id: str
    target_node_id: str
    edge_type: Literal["normal", "conditional"] = "normal"
    condition_label: str | None = None


class GraphModel(BaseModel):
    """Complete graph structure.

    Attributes:
        name: Name of the graph.
        nodes: List of nodes in the graph.
        edges: List of edges connecting nodes.
    """

    name: str = "Untitled Graph"
    nodes: list[NodeModel] = Field(default_factory=list)
    edges: list[EdgeModel] = Field(default_factory=list)

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
        return [e for e in self.edges if e.source_node_id == node_id]

    def get_edges_to(self, node_id: str) -> list[EdgeModel]:
        """Get all edges targeting a node.

        Args:
            node_id: The target node ID.

        Returns:
            List of edges to this node.
        """
        return [e for e in self.edges if e.target_node_id == node_id]
