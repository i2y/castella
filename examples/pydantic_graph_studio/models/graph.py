"""Graph structure models for pydantic-graph Studio."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field

from castella.models.geometry import Point, Size


class GraphAPIType(str, Enum):
    """Type of pydantic-graph API being used."""

    BASE_NODE = "base_node"  # Traditional BaseNode class API
    GRAPH_BUILDER = "graph_builder"  # Beta GraphBuilder API
    MOCK = "mock"  # Mock for demo without pydantic-graph


class NodeInfo(BaseModel):
    """Information about a graph node."""

    id: str
    label: str
    node_class_name: str = ""
    docstring: str | None = None
    source_code: str | None = None
    is_start: bool = False
    is_end: bool = False  # Can return End[T]
    return_types: list[str] = Field(default_factory=list)
    fields: dict[str, str] = Field(default_factory=dict)  # Node dataclass fields
    position: Point = Field(default_factory=lambda: Point(x=0, y=0))
    size: Size = Field(default_factory=lambda: Size(width=140, height=50))


class EdgeInfo(BaseModel):
    """Information about a graph edge."""

    id: str
    source_id: str
    target_id: str
    label: str | None = None  # From Edge annotation
    is_conditional: bool = False  # Part of Union return type


class PydanticGraphModel(BaseModel):
    """Model representing a pydantic-graph structure."""

    name: str
    api_type: GraphAPIType = GraphAPIType.BASE_NODE
    nodes: list[NodeInfo] = Field(default_factory=list)
    edges: list[EdgeInfo] = Field(default_factory=list)
    state_type_name: str = ""  # StateT type name
    deps_type_name: str = ""  # DepsT type name
    return_type_name: str = ""  # RunEndT type name

    def get_node(self, node_id: str) -> NodeInfo | None:
        """Get a node by its ID."""
        for node in self.nodes:
            if node.id == node_id:
                return node
        return None

    def get_start_nodes(self) -> list[NodeInfo]:
        """Get all start nodes."""
        return [n for n in self.nodes if n.is_start]

    def get_end_nodes(self) -> list[NodeInfo]:
        """Get all end nodes (can return End[T])."""
        return [n for n in self.nodes if n.is_end]

    def get_edges_from(self, node_id: str) -> list[EdgeInfo]:
        """Get all edges originating from a node."""
        return [e for e in self.edges if e.source_id == node_id]

    def get_edges_to(self, node_id: str) -> list[EdgeInfo]:
        """Get all edges targeting a node."""
        return [e for e in self.edges if e.target_id == node_id]
