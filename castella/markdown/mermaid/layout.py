"""Layout algorithms for Mermaid diagrams."""

from collections import defaultdict

from .models import (
    Diagram,
    DiagramNode,
    DiagramType,
    Direction,
    NodeShape,
)


def layout_diagram(
    diagram: Diagram, max_width: float = 800, padding: float = 20
) -> None:
    """Calculate positions for all nodes in a diagram.

    Args:
        diagram: The diagram to layout (modified in place)
        max_width: Maximum width for the diagram
        padding: Padding around the diagram
    """
    if diagram.type == DiagramType.FLOWCHART:
        _layout_flowchart(diagram, max_width, padding)
    elif diagram.type == DiagramType.SEQUENCE:
        _layout_sequence(diagram, max_width, padding)
    elif diagram.type == DiagramType.STATE:
        _layout_state(diagram, max_width, padding)
    elif diagram.type == DiagramType.CLASS:
        _layout_class(diagram, max_width, padding)


def _layout_flowchart(diagram: Diagram, max_width: float, padding: float) -> None:
    """Layout a flowchart using a simplified layered approach."""
    if not diagram.nodes:
        return

    # Build adjacency list
    children: dict[str, list[str]] = defaultdict(list)
    parents: dict[str, list[str]] = defaultdict(list)

    for edge in diagram.edges:
        children[edge.source].append(edge.target)
        parents[edge.target].append(edge.source)

    # Find root nodes (no parents)
    all_ids = {n.id for n in diagram.nodes}
    root_ids = all_ids - set(parents.keys())

    if not root_ids:
        # Cycle detected, just use first node
        root_ids = {diagram.nodes[0].id}

    # Assign layers using BFS
    layers: dict[str, int] = {}
    queue = list(root_ids)
    for rid in root_ids:
        layers[rid] = 0

    visited = set(root_ids)
    while queue:
        node_id = queue.pop(0)
        current_layer = layers[node_id]

        for child_id in children[node_id]:
            if child_id not in visited:
                visited.add(child_id)
                layers[child_id] = current_layer + 1
                queue.append(child_id)

    # Handle any unvisited nodes (disconnected)
    for node in diagram.nodes:
        if node.id not in layers:
            layers[node.id] = 0

    # Group nodes by layer
    layer_nodes: dict[int, list[DiagramNode]] = defaultdict(list)
    for node in diagram.nodes:
        layer_nodes[layers[node.id]].append(node)

    # Calculate node sizes based on label length
    node_width = 120
    node_height = 40
    h_spacing = 40
    v_spacing = 60

    for node in diagram.nodes:
        node.width = max(node_width, len(node.label) * 8 + 20)
        node.height = node_height
        if node.shape in (NodeShape.CIRCLE, NodeShape.DOUBLE_CIRCLE):
            node.width = max(node.width, node.height)
            node.height = node.width
        elif node.shape == NodeShape.DIAMOND:
            node.width = max(node.width, len(node.label) * 8 + 40)
            node.height = node.width * 0.6

    # Position nodes
    is_horizontal = diagram.direction in (Direction.LR, Direction.RL)
    max_layers = max(layer_nodes.keys()) + 1 if layer_nodes else 1

    total_height = 0
    layer_widths: list[float] = []

    for layer_idx in range(max_layers):
        nodes = layer_nodes.get(layer_idx, [])
        if not nodes:
            continue

        if is_horizontal:
            # Horizontal layout: layers are columns
            layer_height = sum(n.height for n in nodes) + (len(nodes) - 1) * h_spacing
            total_height = max(total_height, layer_height)
            layer_widths.append(max(n.width for n in nodes))
        else:
            # Vertical layout: layers are rows
            layer_width = sum(n.width for n in nodes) + (len(nodes) - 1) * h_spacing
            layer_widths.append(layer_width)

    # Calculate positions
    if is_horizontal:
        x = padding
        for layer_idx in range(max_layers):
            nodes = layer_nodes.get(layer_idx, [])
            if not nodes:
                continue

            layer_width = (
                layer_widths[layer_idx] if layer_idx < len(layer_widths) else 100
            )
            y = padding

            for node in nodes:
                if diagram.direction == Direction.RL:
                    node.x = max_width - x - node.width - padding
                else:
                    node.x = x

                node.y = y
                y += node.height + h_spacing

            x += layer_width + v_spacing
    else:
        y = padding
        for layer_idx in range(max_layers):
            nodes = layer_nodes.get(layer_idx, [])
            if not nodes:
                continue

            layer_width = (
                layer_widths[layer_idx] if layer_idx < len(layer_widths) else 100
            )
            x = padding + (max_width - 2 * padding - layer_width) / 2

            for node in nodes:
                if diagram.direction == Direction.BT:
                    # Reverse Y for bottom-to-top
                    pass  # TODO: Calculate total height first

                node.x = x
                node.y = y
                x += node.width + h_spacing

            y += node_height + v_spacing

    # Layout subgraphs
    for subgraph in diagram.subgraphs:
        if not subgraph.node_ids:
            continue

        min_x = float("inf")
        min_y = float("inf")
        max_x = float("-inf")
        max_y = float("-inf")

        for node in diagram.nodes:
            if node.id in subgraph.node_ids:
                min_x = min(min_x, node.x)
                min_y = min(min_y, node.y)
                max_x = max(max_x, node.x + node.width)
                max_y = max(max_y, node.y + node.height)

        if min_x != float("inf"):
            sg_padding = 10
            subgraph.x = min_x - sg_padding
            subgraph.y = min_y - sg_padding - 20  # Extra for title
            subgraph.width = max_x - min_x + 2 * sg_padding
            subgraph.height = max_y - min_y + 2 * sg_padding + 20


def _layout_sequence(diagram: Diagram, max_width: float, padding: float) -> None:
    """Layout a sequence diagram."""
    if not diagram.participants:
        return

    # Participant dimensions
    participant_width = 100
    participant_height = 40
    h_spacing = 80
    message_spacing = 40

    # Calculate participant width based on name length
    for p in diagram.participants:
        p.width = max(participant_width, len(p.name) * 8 + 20)
        p.height = participant_height

    # Position participants horizontally
    total_width = (
        sum(p.width for p in diagram.participants)
        + (len(diagram.participants) - 1) * h_spacing
    )
    start_x = padding + (max_width - 2 * padding - total_width) / 2

    x = start_x
    for p in diagram.participants:
        p.x = x
        p.y = padding
        x += p.width + h_spacing

    # Position messages vertically
    y = padding + participant_height + 30

    for msg in diagram.messages:
        msg.y = y
        y += message_spacing

    # Position notes
    for note in diagram.notes:
        # Find participant
        for p in diagram.participants:
            if p.id == note.participant:
                if note.position == "left":
                    pass  # Left of participant
                elif note.position == "right":
                    pass  # Right of participant
                break


def _layout_state(diagram: Diagram, max_width: float, padding: float) -> None:
    """Layout a state diagram with special handling for start/end states."""
    if not diagram.nodes:
        return

    # Separate start, end, and regular states
    start_node = None
    end_node = None
    regular_nodes = []

    for node in diagram.nodes:
        if node.shape == NodeShape.START:
            start_node = node
            node.width = 20
            node.height = 20
        elif node.shape == NodeShape.END:
            end_node = node
            node.width = 20
            node.height = 20
        else:
            regular_nodes.append(node)

    # Calculate sizes for regular nodes
    node_width = 120
    node_height = 40
    h_spacing = 60
    v_spacing = 60

    for node in regular_nodes:
        node.width = max(node_width, len(node.label) * 10 + 30)
        node.height = node_height

    # Build adjacency for regular nodes (excluding start/end)
    children: dict[str, list[str]] = defaultdict(list)
    parents: dict[str, list[str]] = defaultdict(list)

    for edge in diagram.edges:
        # Skip edges to/from start/end for layer calculation
        if edge.source in ("__start__", "__end__") or edge.target in (
            "__start__",
            "__end__",
        ):
            continue
        children[edge.source].append(edge.target)
        parents[edge.target].append(edge.source)

    # Find the first state (connected from start)
    first_state_id = None
    for edge in diagram.edges:
        if edge.source == "__start__":
            first_state_id = edge.target
            break

    # Assign layers to regular nodes using BFS from first state
    layers: dict[str, int] = {}
    if first_state_id:
        layers[first_state_id] = 0
        queue = [first_state_id]
        visited = {first_state_id}

        while queue:
            node_id = queue.pop(0)
            current_layer = layers[node_id]

            for child_id in children[node_id]:
                if child_id not in visited:
                    visited.add(child_id)
                    layers[child_id] = current_layer + 1
                    queue.append(child_id)

    # Handle unvisited regular nodes
    for node in regular_nodes:
        if node.id not in layers:
            layers[node.id] = 0

    # Group regular nodes by layer
    layer_nodes: dict[int, list[DiagramNode]] = defaultdict(list)
    for node in regular_nodes:
        layer_nodes[layers[node.id]].append(node)

    max_layers = max(layers.values()) + 1 if layers else 1

    # Calculate layer widths
    layer_widths: list[float] = []
    for layer_idx in range(max_layers):
        nodes = layer_nodes.get(layer_idx, [])
        if nodes:
            total_width = sum(n.width for n in nodes) + (len(nodes) - 1) * h_spacing
            layer_widths.append(total_width)
        else:
            layer_widths.append(0)

    # Position start node at top center
    y = padding
    if start_node:
        start_node.x = max_width / 2 - start_node.width / 2
        start_node.y = y
        y += start_node.height + v_spacing

    # Position regular nodes layer by layer
    for layer_idx in range(max_layers):
        nodes = layer_nodes.get(layer_idx, [])
        if not nodes:
            continue

        layer_width = layer_widths[layer_idx]
        x = padding + (max_width - 2 * padding - layer_width) / 2
        max_height = 0

        for node in nodes:
            node.x = x
            node.y = y
            max_height = max(max_height, node.height)
            x += node.width + h_spacing

        y += max_height + v_spacing

    # Position end node at bottom center
    if end_node:
        end_node.x = max_width / 2 - end_node.width / 2
        end_node.y = y


def _layout_class(diagram: Diagram, max_width: float, padding: float) -> None:
    """Layout a class diagram with inheritance hierarchy."""
    if not diagram.nodes:
        return

    # Calculate class box dimensions
    min_width = 150
    line_height = 18
    class_padding = 10

    for node in diagram.nodes:
        # Title height
        title_height = line_height + 4

        # Attributes section
        attr_height = len(node.attributes) * line_height if node.attributes else 0

        # Methods section
        method_height = len(node.methods) * line_height if node.methods else 0

        # Total height with separators
        node.height = (
            title_height
            + class_padding * 2
            + attr_height
            + (class_padding if node.attributes else 0)
            + method_height
        )

        # Width based on longest line
        max_text_len = len(node.label)
        for attr in node.attributes:
            max_text_len = max(max_text_len, len(attr))
        for method in node.methods:
            max_text_len = max(max_text_len, len(method))

        node.width = max(min_width, max_text_len * 8 + class_padding * 2)

    # Build hierarchy based on edges (parent -> children)
    # In class diagrams: A <|-- B means A is parent of B (B inherits from A)
    children: dict[str, list[str]] = defaultdict(list)
    parents: dict[str, list[str]] = defaultdict(list)

    for edge in diagram.edges:
        # edge.source is parent, edge.target is child
        children[edge.source].append(edge.target)
        parents[edge.target].append(edge.source)

    # Find root nodes (no parents = base classes)
    all_ids = {n.id for n in diagram.nodes}
    root_ids = all_ids - set(parents.keys())

    if not root_ids:
        # All nodes have parents (cycle), just use all as roots
        root_ids = all_ids

    # Assign layers using BFS (parents above children)
    layers: dict[str, int] = {}
    queue = list(root_ids)
    for rid in root_ids:
        layers[rid] = 0

    visited = set(root_ids)
    while queue:
        node_id = queue.pop(0)
        current_layer = layers[node_id]

        for child_id in children[node_id]:
            if child_id not in visited:
                visited.add(child_id)
                layers[child_id] = current_layer + 1
                queue.append(child_id)

    # Handle any unvisited nodes
    for node in diagram.nodes:
        if node.id not in layers:
            layers[node.id] = 0

    # Group nodes by layer
    layer_nodes: dict[int, list[DiagramNode]] = defaultdict(list)
    for node in diagram.nodes:
        layer_nodes[layers[node.id]].append(node)

    # Layout parameters
    h_spacing = 60
    v_spacing = 80
    max_layers = max(layer_nodes.keys()) + 1 if layer_nodes else 1

    # Calculate width of each layer
    layer_widths: list[float] = []
    for layer_idx in range(max_layers):
        nodes = layer_nodes.get(layer_idx, [])
        if nodes:
            total_width = sum(n.width for n in nodes) + (len(nodes) - 1) * h_spacing
            layer_widths.append(total_width)
        else:
            layer_widths.append(0)

    # Position nodes layer by layer (centered)
    y = padding
    for layer_idx in range(max_layers):
        nodes = layer_nodes.get(layer_idx, [])
        if not nodes:
            continue

        layer_width = layer_widths[layer_idx]
        x = padding + (max_width - 2 * padding - layer_width) / 2
        max_height = 0

        for node in nodes:
            node.x = x
            node.y = y
            max_height = max(max_height, node.height)
            x += node.width + h_spacing

        y += max_height + v_spacing


def calculate_diagram_height(diagram: Diagram) -> float:
    """Calculate the total height required for a diagram."""
    if not diagram.nodes and not diagram.participants:
        return 100

    max_y = 0

    for node in diagram.nodes:
        max_y = max(max_y, node.y + node.height)

    for p in diagram.participants:
        # Sequence diagram height includes messages
        lifeline_height = 40 * (len(diagram.messages) + 2)
        max_y = max(max_y, p.y + p.height + lifeline_height)

    for subgraph in diagram.subgraphs:
        max_y = max(max_y, subgraph.y + subgraph.height)

    return max_y + 20  # Bottom padding
