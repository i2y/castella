"""Main renderer for Mermaid diagrams."""

from castella.core import (
    FillStyle,
    Painter,
    Point,
    Rect,
    Size,
    StrokeStyle,
    Style,
)
from castella.models.font import Font

from .layout import calculate_diagram_height, layout_diagram
from .models import Diagram, DiagramType, NodeShape
from .parser import MermaidParseError, parse_mermaid
from .shapes import (
    draw_back_edge,
    draw_class_box,
    draw_edge,
    draw_lifeline,
    draw_node,
    draw_sequence_message,
    draw_sequence_participant,
)


class MermaidDiagramRenderer:
    """Renders Mermaid diagrams using Skia/CanvasKit."""

    def __init__(self, theme=None):
        """Initialize renderer with theme.

        Args:
            theme: MarkdownTheme for colors. If None, uses defaults.
        """
        self._theme = theme

        # Colors
        if theme:
            self._bg_color = theme.code_bg_color
            self._node_fill = "#2d333b" if theme.is_dark else "#ffffff"
            self._node_stroke = theme.text_color
            self._text_color = theme.text_color
            self._edge_color = theme.text_color
            self._font_family = theme.code_font
            self._font_size = theme.base_font_size
        else:
            self._bg_color = "#1e1e1e"
            self._node_fill = "#2d333b"
            self._node_stroke = "#c9d1d9"
            self._text_color = "#c9d1d9"
            self._edge_color = "#8b949e"
            self._font_family = "Menlo"
            self._font_size = 12

        # Diagram-specific colors
        self._subgraph_fill = "#21262d" if (theme and theme.is_dark) else "#f6f8fa"
        self._participant_fill = "#388bfd" if (theme and theme.is_dark) else "#0969da"

    def render(
        self,
        painter: Painter,
        content: str,
        width: float,
        y_offset: float,
    ) -> float:
        """Render a Mermaid diagram and return the height used.

        Args:
            painter: Painter to render with
            content: Mermaid diagram source code
            width: Available width
            y_offset: Y position to start rendering

        Returns:
            Total height of the rendered diagram
        """
        try:
            diagram = parse_mermaid(content)
        except MermaidParseError:
            # Return 0 height on parse error - fallback will be used
            return 0

        # Layout the diagram
        layout_diagram(diagram, max_width=width, padding=20)

        # Calculate diagram height
        diagram_height = calculate_diagram_height(diagram)

        # Draw background
        bg_rect = Rect(
            origin=Point(x=0, y=y_offset),
            size=Size(width=width, height=diagram_height),
        )
        painter.style(Style(fill=FillStyle(color=self._bg_color)))
        painter.fill_rect(bg_rect)

        # Dispatch to specific renderer
        if diagram.type == DiagramType.FLOWCHART:
            self._render_flowchart(painter, diagram, y_offset)
        elif diagram.type == DiagramType.SEQUENCE:
            self._render_sequence(painter, diagram, y_offset, width)
        elif diagram.type == DiagramType.STATE:
            self._render_state(painter, diagram, y_offset)
        elif diagram.type == DiagramType.CLASS:
            self._render_class(painter, diagram, y_offset)

        return diagram_height

    def _render_flowchart(self, p: Painter, diagram: Diagram, y_offset: float) -> None:
        """Render a flowchart diagram."""
        # Draw subgraphs first (as background)
        for subgraph in diagram.subgraphs:
            self._draw_subgraph(p, subgraph, y_offset)

        # Draw edges
        for edge in diagram.edges:
            source = diagram.get_node(edge.source)
            target = diagram.get_node(edge.target)

            if source and target:
                # Calculate connection points
                x1 = source.x + source.width / 2
                y1 = source.y + source.height + y_offset
                x2 = target.x + target.width / 2
                y2 = target.y + y_offset

                draw_edge(
                    p,
                    x1,
                    y1,
                    x2,
                    y2,
                    edge.line_type,
                    edge.arrow_type,
                    edge.arrow_start,
                    edge.arrow_end,
                    edge.label,
                    self._edge_color,
                    self._text_color,
                    self._font_family,
                    self._font_size,
                )

        # Draw nodes
        for node in diagram.nodes:
            draw_node(
                p,
                node.x,
                node.y + y_offset,
                node.width,
                node.height,
                node.shape,
                node.label,
                self._node_fill,
                self._node_stroke,
                self._text_color,
                self._font_family,
                self._font_size,
            )

    def _draw_subgraph(self, p: Painter, subgraph, y_offset: float) -> None:
        """Draw a subgraph container."""
        rect = Rect(
            origin=Point(x=subgraph.x, y=subgraph.y + y_offset),
            size=Size(width=subgraph.width, height=subgraph.height),
        )

        # Fill
        p.style(Style(fill=FillStyle(color=self._subgraph_fill)))
        p.fill_rect(rect)

        # Stroke
        p.style(Style(stroke=StrokeStyle(color=self._edge_color)))
        p.stroke_rect(rect)

        # Title
        text_style = Style(
            fill=FillStyle(color=self._text_color),
            font=Font(family=self._font_family, size=self._font_size - 2),
        )
        p.style(text_style)
        p.fill_text(
            subgraph.title,
            Point(x=subgraph.x + 8, y=subgraph.y + y_offset + 14),
            None,
        )

    def _render_sequence(
        self, p: Painter, diagram: Diagram, y_offset: float, width: float
    ) -> None:
        """Render a sequence diagram."""
        # Calculate lifeline end position
        lifeline_end_y = y_offset + 40 + 40 * (len(diagram.messages) + 1)

        # Draw participants and lifelines
        for participant in diagram.participants:
            # Draw participant box
            draw_sequence_participant(
                p,
                participant.x,
                participant.y + y_offset,
                participant.width,
                participant.height,
                participant.name,
                participant.is_actor,
                self._participant_fill,
                self._node_stroke,
                "#ffffff",  # White text on blue bg
                self._font_family,
                self._font_size,
            )

            # Draw lifeline
            lifeline_x = participant.x + participant.width / 2
            lifeline_start_y = participant.y + participant.height + y_offset
            draw_lifeline(
                p, lifeline_x, lifeline_start_y, lifeline_end_y, self._edge_color
            )

        # Draw messages
        for msg in diagram.messages:
            # Find source and target participants
            source_p = None
            target_p = None
            for p_obj in diagram.participants:
                if p_obj.id == msg.source:
                    source_p = p_obj
                if p_obj.id == msg.target:
                    target_p = p_obj

            if source_p and target_p:
                x1 = source_p.x + source_p.width / 2
                x2 = target_p.x + target_p.width / 2

                draw_sequence_message(
                    p,
                    x1,
                    msg.y + y_offset,
                    x2,
                    msg.label,
                    msg.line_type,
                    msg.arrow_type,
                    self._edge_color,
                    self._text_color,
                    self._font_family,
                    self._font_size,
                )

    def _render_state(self, p: Painter, diagram: Diagram, y_offset: float) -> None:
        """Render a state diagram."""
        # Track back edge count for offset calculation
        back_edge_count = 0

        # Draw edges first (behind nodes)
        for edge in diagram.edges:
            source = diagram.get_node(edge.source)
            target = diagram.get_node(edge.target)

            if source and target:
                # Determine edge direction and calculate connection points
                source_cy = source.y + source.height / 2
                target_cy = target.y + target.height / 2

                # Check if this is a back edge (going up) or side edge
                is_back_edge = target.y + target.height < source.y
                is_side_edge = abs(source.y - target.y) < 10  # Same level

                if is_back_edge:
                    # Back edge: draw path around left or right side (alternating)
                    x1 = source.x
                    y1 = source_cy + y_offset
                    x2 = target.x
                    y2 = target_cy + y_offset

                    # Alternate between left and right, increase offset every 2 edges
                    use_right = back_edge_count % 2 == 1
                    offset = 30 + (back_edge_count // 2) * 20
                    back_edge_count += 1

                    draw_back_edge(
                        p,
                        x1,
                        y1,
                        x2,
                        y2,
                        offset,
                        edge.line_type,
                        edge.arrow_type,
                        edge.label,
                        self._edge_color,
                        self._text_color,
                        self._font_family,
                        self._font_size,
                        source_width=source.width,
                        target_width=target.width,
                        use_right_side=use_right,
                    )
                elif is_side_edge:
                    # Side edge: connect horizontally
                    if target.x > source.x:
                        # Target is to the right
                        x1 = source.x + source.width
                        x2 = target.x
                    else:
                        # Target is to the left
                        x1 = source.x
                        x2 = target.x + target.width
                    y1 = source_cy + y_offset
                    y2 = target_cy + y_offset

                    draw_edge(
                        p,
                        x1,
                        y1,
                        x2,
                        y2,
                        edge.line_type,
                        edge.arrow_type,
                        edge.arrow_start,
                        edge.arrow_end,
                        edge.label,
                        self._edge_color,
                        self._text_color,
                        self._font_family,
                        self._font_size,
                    )
                else:
                    # Normal forward edge: bottom to top
                    x1 = source.x + source.width / 2
                    y1 = source.y + source.height + y_offset
                    x2 = target.x + target.width / 2
                    y2 = target.y + y_offset

                    draw_edge(
                        p,
                        x1,
                        y1,
                        x2,
                        y2,
                        edge.line_type,
                        edge.arrow_type,
                        edge.arrow_start,
                        edge.arrow_end,
                        edge.label,
                        self._edge_color,
                        self._text_color,
                        self._font_family,
                        self._font_size,
                    )

        # Draw state nodes
        for node in diagram.nodes:
            # Special rendering for start/end states
            if node.shape in (NodeShape.START, NodeShape.END):
                draw_node(
                    p,
                    node.x,
                    node.y + y_offset,
                    node.width,
                    node.height,
                    node.shape,
                    "",  # No label for start/end
                    self._node_stroke,  # Filled with stroke color
                    self._node_stroke,
                    self._text_color,
                    self._font_family,
                    self._font_size,
                )
            else:
                draw_node(
                    p,
                    node.x,
                    node.y + y_offset,
                    node.width,
                    node.height,
                    node.shape,
                    node.label,
                    self._node_fill,
                    self._node_stroke,
                    self._text_color,
                    self._font_family,
                    self._font_size,
                )

    def _render_class(self, p: Painter, diagram: Diagram, y_offset: float) -> None:
        """Render a class diagram."""
        # Draw edges first (behind nodes)
        for edge in diagram.edges:
            source = diagram.get_node(edge.source)
            target = diagram.get_node(edge.target)

            if source and target:
                # Calculate connection points
                x1 = source.x + source.width / 2
                y1 = source.y + source.height + y_offset
                x2 = target.x + target.width / 2
                y2 = target.y + y_offset

                draw_edge(
                    p,
                    x1,
                    y1,
                    x2,
                    y2,
                    edge.line_type,
                    edge.arrow_type,
                    edge.arrow_start,
                    edge.arrow_end,
                    edge.label,
                    self._edge_color,
                    self._text_color,
                    self._font_family,
                    self._font_size,
                )

        # Draw class boxes
        for node in diagram.nodes:
            draw_class_box(
                p,
                node.x,
                node.y + y_offset,
                node.width,
                node.height,
                node.label,
                node.attributes,
                node.methods,
                self._node_fill,
                self._node_stroke,
                self._text_color,
                self._font_family,
                self._font_size,
            )
