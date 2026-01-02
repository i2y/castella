"""Mermaid DSL parser."""

import re

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


class MermaidParseError(Exception):
    """Error parsing Mermaid diagram."""

    pass


def parse_mermaid(content: str) -> Diagram:
    """Parse Mermaid diagram content and return a Diagram.

    Args:
        content: Mermaid diagram source code

    Returns:
        Parsed Diagram object

    Raises:
        MermaidParseError: If parsing fails
    """
    lines = content.strip().split("\n")
    if not lines:
        raise MermaidParseError("Empty diagram")

    first_line = lines[0].strip().lower()

    # Detect diagram type
    if first_line.startswith("graph") or first_line.startswith("flowchart"):
        return _parse_flowchart(lines)
    elif first_line.startswith("sequencediagram"):
        return _parse_sequence(lines)
    elif first_line.startswith("statediagram"):
        return _parse_state(lines)
    elif first_line.startswith("classdiagram"):
        return _parse_class(lines)
    else:
        raise MermaidParseError(f"Unknown diagram type: {first_line}")


# ============================================================================
# Flowchart Parser
# ============================================================================

# Patterns for flowchart parsing
_DIRECTION_PATTERN = re.compile(r"(?:graph|flowchart)\s+(TB|BT|LR|RL|TD)", re.I)
_NODE_PATTERN = re.compile(
    r"([A-Za-z_][A-Za-z0-9_]*)"
    r"(?:"
    r"\[\[([^\]]+)\]\]"  # [[text]] subroutine
    r"|\[\(([^\)]+)\)\]"  # [(text)] cylinder
    r"|\[/([^/]+)/\]"  # [/text/] parallelogram
    r"|\[\\([^\\]+)\\\]"  # [\text\] parallelogram alt
    r"|\[/([^\\/]+)\\\]"  # [/text\] trapezoid
    r"|\[\\([^\\/]+)/\]"  # [\text/] trapezoid alt
    r"|\[\(([^\)]+)\)\]"  # [(text)] stadium left
    r"|\(\[([^\]]+)\]\)"  # ([text]) stadium
    r"|\(\(\(([^\)]+)\)\)\)"  # (((text))) double circle
    r"|\(\(([^\)]+)\)\)"  # ((text)) circle
    r"|\(([^\)]+)\)"  # (text) rounded
    r"|\{\{([^\}]+)\}\}"  # {{text}} hexagon
    r"|\{([^\}]+)\}"  # {text} diamond
    r"|\[([^\]]+)\]"  # [text] rect
    r")?"
)

_EDGE_PATTERN = re.compile(
    r"([A-Za-z_][A-Za-z0-9_]*)"  # Source node
    r"\s*"
    r"(<?)"  # Optional start arrow
    r"(--|\.\.|-\.|\=\=)"  # Line type
    r"(\|[^|]*\|)?"  # Optional edge label |text|
    r"(>|o|x)?"  # Optional end arrow
    r"\s*"
    r"([A-Za-z_][A-Za-z0-9_]*)"  # Target node
)

_SIMPLE_EDGE_PATTERN = re.compile(
    r"([A-Za-z_][A-Za-z0-9_]*)"  # Source node
    r"\s*"
    r"(-->|--o|--x|---|-\.->|-\.-|==>|===)"  # Arrow
    r"(?:\|([^|]*)\|)?"  # Optional label
    r"\s*"
    r"([A-Za-z_][A-Za-z0-9_]*)"  # Target node
)

_SUBGRAPH_PATTERN = re.compile(r"subgraph\s+([^\s\[]+)(?:\s*\[([^\]]+)\])?", re.I)


def _parse_flowchart(lines: list[str]) -> Diagram:
    """Parse a flowchart diagram."""
    diagram = Diagram(type=DiagramType.FLOWCHART)
    nodes: dict[str, DiagramNode] = {}
    current_subgraph: Subgraph | None = None
    subgraph_stack: list[Subgraph] = []

    # Parse direction from first line
    first_line = lines[0].strip()
    dir_match = _DIRECTION_PATTERN.match(first_line)
    if dir_match:
        dir_str = dir_match.group(1).upper()
        if dir_str == "TD":
            dir_str = "TB"
        diagram.direction = Direction(dir_str)

    for line in lines[1:]:
        line = line.strip()

        # Skip empty lines and comments
        if not line or line.startswith("%%"):
            continue

        # Check for subgraph
        if line.lower().startswith("subgraph"):
            match = _SUBGRAPH_PATTERN.match(line)
            if match:
                subgraph_id = match.group(1)
                title = match.group(2) or subgraph_id
                subgraph = Subgraph(id=subgraph_id, title=title)
                if current_subgraph:
                    subgraph_stack.append(current_subgraph)
                current_subgraph = subgraph
                diagram.subgraphs.append(subgraph)
            continue

        if line.lower() == "end":
            if subgraph_stack:
                current_subgraph = subgraph_stack.pop()
            else:
                current_subgraph = None
            continue

        # Try to parse edge with nodes
        edge_parsed = _parse_flowchart_edge(line, nodes)
        if edge_parsed:
            edge, new_nodes = edge_parsed
            for node_id, node in new_nodes.items():
                if node_id not in nodes:
                    nodes[node_id] = node
                    if current_subgraph:
                        current_subgraph.node_ids.append(node_id)
            diagram.edges.append(edge)
            continue

        # Try to parse standalone node definition
        node_parsed = _parse_flowchart_node(line)
        if node_parsed:
            node_id, node = node_parsed
            if node_id not in nodes:
                nodes[node_id] = node
                if current_subgraph:
                    current_subgraph.node_ids.append(node_id)

    diagram.nodes = list(nodes.values())
    return diagram


def _parse_flowchart_node(line: str) -> tuple[str, DiagramNode] | None:
    """Parse a flowchart node definition."""
    line = line.strip()
    if not line:
        return None

    # Try different shape patterns
    patterns = [
        (r"([A-Za-z_][A-Za-z0-9_]*)\[\[([^\]]+)\]\]", NodeShape.SUBROUTINE),
        (r"([A-Za-z_][A-Za-z0-9_]*)\[\(([^\)]+)\)\]", NodeShape.CYLINDER),
        (r"([A-Za-z_][A-Za-z0-9_]*)\(\[([^\]]+)\]\)", NodeShape.STADIUM),
        (r"([A-Za-z_][A-Za-z0-9_]*)\(\(\(([^\)]+)\)\)\)", NodeShape.DOUBLE_CIRCLE),
        (r"([A-Za-z_][A-Za-z0-9_]*)\(\(([^\)]+)\)\)", NodeShape.CIRCLE),
        (r"([A-Za-z_][A-Za-z0-9_]*)\(([^\)]+)\)", NodeShape.ROUNDED),
        (r"([A-Za-z_][A-Za-z0-9_]*)\{\{([^\}]+)\}\}", NodeShape.HEXAGON),
        (r"([A-Za-z_][A-Za-z0-9_]*)\{([^\}]+)\}", NodeShape.DIAMOND),
        (r"([A-Za-z_][A-Za-z0-9_]*)\[([^\]]+)\]", NodeShape.RECT),
    ]

    for pattern, shape in patterns:
        match = re.match(pattern, line)
        if match:
            node_id = match.group(1)
            label = match.group(2)
            return node_id, DiagramNode(id=node_id, label=label, shape=shape)

    # Just a node ID
    match = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)$", line)
    if match:
        node_id = match.group(1)
        return node_id, DiagramNode(id=node_id, label=node_id, shape=NodeShape.RECT)

    return None


def _parse_flowchart_edge(
    line: str, existing_nodes: dict[str, DiagramNode]
) -> tuple[DiagramEdge, dict[str, DiagramNode]] | None:
    """Parse a flowchart edge and any inline node definitions."""
    # Try to find arrow patterns
    arrow_patterns = [
        (r"-->", LineType.SOLID, ArrowType.ARROW),
        (r"---", LineType.SOLID, ArrowType.OPEN),
        (r"--o", LineType.SOLID, ArrowType.CIRCLE),
        (r"--x", LineType.SOLID, ArrowType.CROSS),
        (r"-\.->", LineType.DASHED, ArrowType.ARROW),
        (r"-\.-", LineType.DASHED, ArrowType.OPEN),
        (r"==>", LineType.THICK, ArrowType.ARROW),
        (r"===", LineType.THICK, ArrowType.OPEN),
    ]

    for arrow_re, line_type, arrow_type in arrow_patterns:
        # Pattern with optional label: A -->|label| B  or A --> B
        # Node pattern captures: ID + optional shape like [text], (text), {text}, etc.
        node_shape_pattern = (
            r"(?:\[\[[^\]]+\]\]"  # [[text]] subroutine
            r"|\[\([^\)]+\)\]"  # [(text)] cylinder
            r"|\(\[[^\]]+\]\)"  # ([text]) stadium
            r"|\(\(\([^\)]+\)\)\)"  # (((text))) double circle
            r"|\(\([^\)]+\)\)"  # ((text)) circle
            r"|\([^\)]+\)"  # (text) rounded
            r"|\{\{[^\}]+\}\}"  # {{text}} hexagon
            r"|\{[^\}]+\}"  # {text} diamond
            r"|\[[^\]]+\]"  # [text] rect
            r")?"
        )
        pattern = (
            r"([A-Za-z_][A-Za-z0-9_]*" + node_shape_pattern + r")"
            r"\s*"  # Optional whitespace before arrow
             + arrow_re + r"(?:\|([^|]*)\|)?"  # Optional |label|
            r"\s*"  # Optional whitespace after arrow
            r"([A-Za-z_][A-Za-z0-9_]*" + node_shape_pattern + r")"
        )

        match = re.search(pattern, line)
        if match:
            source_str = match.group(1)
            label = match.group(2) or ""
            target_str = match.group(3)

            nodes: dict[str, DiagramNode] = {}

            # Parse source node
            source_parsed = _parse_flowchart_node(source_str)
            if source_parsed:
                source_id, source_node = source_parsed
                nodes[source_id] = source_node
            else:
                source_id = source_str

            # Parse target node
            target_parsed = _parse_flowchart_node(target_str)
            if target_parsed:
                target_id, target_node = target_parsed
                nodes[target_id] = target_node
            else:
                target_id = target_str

            edge = DiagramEdge(
                source=source_id,
                target=target_id,
                label=label.strip(),
                line_type=line_type,
                arrow_type=arrow_type,
            )

            return edge, nodes

    return None


# ============================================================================
# Sequence Diagram Parser
# ============================================================================

_PARTICIPANT_PATTERN = re.compile(
    r"(?:participant|actor)\s+([A-Za-z_][A-Za-z0-9_]*)"
    r"(?:\s+as\s+(.+))?",
    re.I,
)

_MESSAGE_PATTERN = re.compile(
    r"([A-Za-z_][A-Za-z0-9_]*)"
    r"\s*"
    r"(--?>>?|--?>|<--?>>?|--x|->>|<<->>?)"
    r"\s*"
    r"([A-Za-z_][A-Za-z0-9_]*)"
    r"\s*:\s*(.+)?",
    re.I,
)

_NOTE_PATTERN = re.compile(
    r"note\s+(left|right|over)\s+(?:of\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*:\s*(.+)?", re.I
)


def _parse_sequence(lines: list[str]) -> Diagram:
    """Parse a sequence diagram."""
    diagram = Diagram(type=DiagramType.SEQUENCE)
    participants: dict[str, SequenceParticipant] = {}

    for line in lines[1:]:
        line = line.strip()

        if not line or line.startswith("%%"):
            continue

        # Parse participant
        match = _PARTICIPANT_PATTERN.match(line)
        if match:
            pid = match.group(1)
            name = match.group(2) or pid
            is_actor = line.lower().startswith("actor")
            participants[pid] = SequenceParticipant(
                id=pid, name=name, is_actor=is_actor
            )
            continue

        # Parse message
        match = _MESSAGE_PATTERN.match(line)
        if match:
            source = match.group(1)
            arrow = match.group(2)
            target = match.group(3)
            label = match.group(4) or ""

            # Ensure participants exist
            if source not in participants:
                participants[source] = SequenceParticipant(id=source, name=source)
            if target not in participants:
                participants[target] = SequenceParticipant(id=target, name=target)

            # Determine line type and arrow type
            line_type = LineType.DASHED if "--" in arrow else LineType.SOLID
            arrow_type = ArrowType.ARROW if ">" in arrow else ArrowType.OPEN

            message = SequenceMessage(
                source=source,
                target=target,
                label=label.strip(),
                line_type=line_type,
                arrow_type=arrow_type,
                is_self=(source == target),
            )
            diagram.messages.append(message)
            continue

        # Parse note
        match = _NOTE_PATTERN.match(line)
        if match:
            position = match.group(1).lower()
            participant = match.group(2)
            text = match.group(3) or ""

            if participant not in participants:
                participants[participant] = SequenceParticipant(
                    id=participant, name=participant
                )

            note = SequenceNote(
                participant=participant, text=text.strip(), position=position
            )
            diagram.notes.append(note)
            continue

    diagram.participants = list(participants.values())
    return diagram


# ============================================================================
# State Diagram Parser
# ============================================================================

_STATE_TRANSITION_PATTERN = re.compile(
    r"(\[\*\]|[A-Za-z_][A-Za-z0-9_]*)"
    r"\s*-->\s*"
    r"(\[\*\]|[A-Za-z_][A-Za-z0-9_]*)"
    r"(?:\s*:\s*(.+))?",
    re.I,
)

_STATE_DEF_PATTERN = re.compile(
    r"state\s+\"([^\"]+)\"\s+as\s+([A-Za-z_][A-Za-z0-9_]*)", re.I
)


def _parse_state(lines: list[str]) -> Diagram:
    """Parse a state diagram."""
    diagram = Diagram(type=DiagramType.STATE)
    nodes: dict[str, DiagramNode] = {}

    for line in lines[1:]:
        line = line.strip()

        if not line or line.startswith("%%"):
            continue

        # Parse state definition with alias
        match = _STATE_DEF_PATTERN.match(line)
        if match:
            label = match.group(1)
            state_id = match.group(2)
            nodes[state_id] = DiagramNode(
                id=state_id, label=label, shape=NodeShape.ROUNDED
            )
            continue

        # Parse transition
        match = _STATE_TRANSITION_PATTERN.match(line)
        if match:
            source = match.group(1)
            target = match.group(2)
            label = match.group(3) or ""

            # Handle [*] for start/end states
            if source == "[*]":
                source_id = "__start__"
                if source_id not in nodes:
                    nodes[source_id] = DiagramNode(
                        id=source_id, label="", shape=NodeShape.START
                    )
            else:
                source_id = source
                if source_id not in nodes:
                    nodes[source_id] = DiagramNode(
                        id=source_id, label=source_id, shape=NodeShape.ROUNDED
                    )

            if target == "[*]":
                target_id = "__end__"
                if target_id not in nodes:
                    nodes[target_id] = DiagramNode(
                        id=target_id, label="", shape=NodeShape.END
                    )
            else:
                target_id = target
                if target_id not in nodes:
                    nodes[target_id] = DiagramNode(
                        id=target_id, label=target_id, shape=NodeShape.ROUNDED
                    )

            edge = DiagramEdge(source=source_id, target=target_id, label=label.strip())
            diagram.edges.append(edge)
            continue

    diagram.nodes = list(nodes.values())
    return diagram


# ============================================================================
# Class Diagram Parser
# ============================================================================

_CLASS_DEF_PATTERN = re.compile(r"class\s+([A-Za-z_][A-Za-z0-9_]*)", re.I)
_CLASS_MEMBER_PATTERN = re.compile(
    r"([A-Za-z_][A-Za-z0-9_]*)\s*:\s*([+\-#~])?(.+)", re.I
)
_CLASS_RELATION_PATTERN = re.compile(
    r"([A-Za-z_][A-Za-z0-9_]*)"
    r"\s*"
    r"(<\|--|--\|>|\*--|--\*|o--|--o|<--|-->|--)"
    r"\s*"
    r"([A-Za-z_][A-Za-z0-9_]*)"
    r"(?:\s*:\s*(.+))?",
    re.I,
)


def _parse_class(lines: list[str]) -> Diagram:
    """Parse a class diagram."""
    diagram = Diagram(type=DiagramType.CLASS)
    classes: dict[str, DiagramNode] = {}
    current_class: DiagramNode | None = None
    in_class_block = False

    for line in lines[1:]:
        line = line.strip()

        if not line or line.startswith("%%"):
            continue

        # Check for class block start
        if line.endswith("{"):
            match = _CLASS_DEF_PATTERN.match(line[:-1].strip())
            if match:
                class_name = match.group(1)
                current_class = DiagramNode(
                    id=class_name, label=class_name, shape=NodeShape.RECT
                )
                classes[class_name] = current_class
                in_class_block = True
            continue

        # Check for class block end
        if line == "}":
            current_class = None
            in_class_block = False
            continue

        # Parse member inside class block
        if in_class_block and current_class:
            # Simple member: +attribute or +method()
            if line.startswith(("+", "-", "#", "~")):
                visibility = line[0]
                member = line[1:].strip()
                if "()" in member or "(" in member:
                    current_class.methods.append(f"{visibility}{member}")
                else:
                    current_class.attributes.append(f"{visibility}{member}")
            continue

        # Parse class definition without block
        match = _CLASS_DEF_PATTERN.match(line)
        if match and "{" not in line:
            class_name = match.group(1)
            if class_name not in classes:
                classes[class_name] = DiagramNode(
                    id=class_name, label=class_name, shape=NodeShape.RECT
                )
            continue

        # Parse relationship
        match = _CLASS_RELATION_PATTERN.match(line)
        if match:
            source = match.group(1)
            relation = match.group(2)
            target = match.group(3)
            label = match.group(4) or ""

            # Ensure classes exist
            if source not in classes:
                classes[source] = DiagramNode(
                    id=source, label=source, shape=NodeShape.RECT
                )
            if target not in classes:
                classes[target] = DiagramNode(
                    id=target, label=target, shape=NodeShape.RECT
                )

            # Determine arrow type based on relation
            arrow_type = ArrowType.ARROW
            arrow_start = False
            arrow_end = True

            if relation in ("<|--", "--"):
                arrow_type = ArrowType.ARROW
            elif relation in ("*--", "--*"):
                arrow_type = ArrowType.CIRCLE  # Composition
            elif relation in ("o--", "--o"):
                arrow_type = ArrowType.CIRCLE  # Aggregation

            if relation.startswith("<"):
                arrow_start = True
                arrow_end = False
            elif relation.endswith(">"):
                arrow_start = False
                arrow_end = True

            edge = DiagramEdge(
                source=source,
                target=target,
                label=label.strip(),
                arrow_type=arrow_type,
                arrow_start=arrow_start,
                arrow_end=arrow_end,
            )
            diagram.edges.append(edge)
            continue

        # Parse member definition outside class block: ClassName : +member
        match = _CLASS_MEMBER_PATTERN.match(line)
        if match:
            class_name = match.group(1)
            visibility = match.group(2) or "+"
            member = match.group(3).strip()

            if class_name not in classes:
                classes[class_name] = DiagramNode(
                    id=class_name, label=class_name, shape=NodeShape.RECT
                )

            if "()" in member or "(" in member:
                classes[class_name].methods.append(f"{visibility}{member}")
            else:
                classes[class_name].attributes.append(f"{visibility}{member}")
            continue

    diagram.nodes = list(classes.values())
    return diagram
