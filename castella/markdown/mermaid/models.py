"""Data models for Mermaid diagrams."""

from dataclasses import dataclass, field
from enum import Enum


class DiagramType(str, Enum):
    """Types of Mermaid diagrams."""

    FLOWCHART = "flowchart"
    SEQUENCE = "sequence"
    STATE = "state"
    CLASS = "class"
    UNKNOWN = "unknown"


class Direction(str, Enum):
    """Diagram layout direction."""

    TB = "TB"  # Top to Bottom
    BT = "BT"  # Bottom to Top
    LR = "LR"  # Left to Right
    RL = "RL"  # Right to Left


class NodeShape(str, Enum):
    """Shape of a diagram node."""

    RECT = "rect"  # [text]
    ROUNDED = "rounded"  # (text)
    STADIUM = "stadium"  # ([text])
    SUBROUTINE = "subroutine"  # [[text]]
    CYLINDER = "cylinder"  # [(text)]
    CIRCLE = "circle"  # ((text))
    DIAMOND = "diamond"  # {text}
    HEXAGON = "hexagon"  # {{text}}
    PARALLELOGRAM = "parallelogram"  # [/text/]
    PARALLELOGRAM_ALT = "parallelogram_alt"  # [\text\]
    TRAPEZOID = "trapezoid"  # [/text\]
    TRAPEZOID_ALT = "trapezoid_alt"  # [\text/]
    DOUBLE_CIRCLE = "double_circle"  # (((text)))
    # State diagram specific
    START = "start"  # [*]
    END = "end"  # [*]


class LineType(str, Enum):
    """Type of connecting line."""

    SOLID = "solid"  # ---
    DASHED = "dashed"  # -.-
    DOTTED = "dotted"  # ...
    THICK = "thick"  # ===


class ArrowType(str, Enum):
    """Type of arrow head."""

    ARROW = "arrow"  # -->
    OPEN = "open"  # ---
    CIRCLE = "circle"  # --o
    CROSS = "cross"  # --x


@dataclass
class DiagramNode:
    """A node in a diagram."""

    id: str
    label: str
    shape: NodeShape = NodeShape.RECT
    x: float = 0.0
    y: float = 0.0
    width: float = 0.0
    height: float = 0.0
    # For class diagrams
    attributes: list[str] = field(default_factory=list)
    methods: list[str] = field(default_factory=list)
    # For state diagrams
    is_composite: bool = False
    children: list["DiagramNode"] = field(default_factory=list)


@dataclass
class DiagramEdge:
    """An edge connecting two nodes."""

    source: str
    target: str
    label: str = ""
    line_type: LineType = LineType.SOLID
    arrow_type: ArrowType = ArrowType.ARROW
    arrow_start: bool = False  # Arrow at source
    arrow_end: bool = True  # Arrow at target


@dataclass
class Subgraph:
    """A subgraph container for flowcharts."""

    id: str
    title: str
    node_ids: list[str] = field(default_factory=list)
    x: float = 0.0
    y: float = 0.0
    width: float = 0.0
    height: float = 0.0


@dataclass
class SequenceParticipant:
    """A participant in a sequence diagram."""

    id: str
    name: str
    x: float = 0.0
    y: float = 0.0
    width: float = 0.0
    height: float = 0.0
    is_actor: bool = False


@dataclass
class SequenceMessage:
    """A message in a sequence diagram."""

    source: str
    target: str
    label: str
    line_type: LineType = LineType.SOLID
    arrow_type: ArrowType = ArrowType.ARROW
    y: float = 0.0
    is_self: bool = False
    # For activation
    activate: bool = False
    deactivate: bool = False


@dataclass
class SequenceNote:
    """A note in a sequence diagram."""

    participant: str
    text: str
    position: str = "right"  # left, right, over
    y: float = 0.0


@dataclass
class Diagram:
    """A complete Mermaid diagram."""

    type: DiagramType
    direction: Direction = Direction.TB
    nodes: list[DiagramNode] = field(default_factory=list)
    edges: list[DiagramEdge] = field(default_factory=list)
    subgraphs: list[Subgraph] = field(default_factory=list)
    # Sequence diagram specific
    participants: list[SequenceParticipant] = field(default_factory=list)
    messages: list[SequenceMessage] = field(default_factory=list)
    notes: list[SequenceNote] = field(default_factory=list)
    # Parsed title if any
    title: str = ""

    def get_node(self, node_id: str) -> DiagramNode | None:
        """Get a node by ID."""
        for node in self.nodes:
            if node.id == node_id:
                return node
        return None
