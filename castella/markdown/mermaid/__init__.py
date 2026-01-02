"""Mermaid diagram rendering for Castella Markdown.

This module provides pure Python rendering of Mermaid diagrams
using Skia/CanvasKit via Castella's Painter API.

Supported diagram types:
- Flowchart (graph TD/LR/BT/RL)
- Sequence diagram (sequenceDiagram)
- State diagram (stateDiagram-v2)
- Class diagram (classDiagram)
"""

from .layout import calculate_diagram_height, layout_diagram
from .models import (
    ArrowType,
    Diagram,
    DiagramEdge,
    DiagramNode,
    DiagramType,
    Direction,
    LineType,
    NodeShape,
    SequenceMessage,
    SequenceNote,
    SequenceParticipant,
    Subgraph,
)
from .parser import MermaidParseError, parse_mermaid
from .renderer import MermaidDiagramRenderer

__all__ = [
    # Main API
    "MermaidDiagramRenderer",
    "parse_mermaid",
    "layout_diagram",
    "calculate_diagram_height",
    "MermaidParseError",
    # Models
    "Diagram",
    "DiagramNode",
    "DiagramEdge",
    "DiagramType",
    "Direction",
    "NodeShape",
    "LineType",
    "ArrowType",
    "Subgraph",
    "SequenceParticipant",
    "SequenceMessage",
    "SequenceNote",
]
