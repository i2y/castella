"""Base studio canvas with execution state visualization.

This module provides a base class for workflow studio canvases that extends
GraphCanvas with execution state highlighting.
"""

from __future__ import annotations

from typing import Self

from castella.core import (
    Painter,
    Style,
    FillStyle,
    StrokeStyle,
)
from castella.models.geometry import Point, Size, Rect, Circle
from castella.models.font import Font

from castella.graph import (
    GraphCanvas,
    GraphModel,
    NodeModel,
    EdgeModel,
    LayoutConfig,
)
from castella.graph.theme import GraphTheme, DARK_THEME
from castella.graph.transform import CanvasTransform

from castella.studio.models.execution import BaseExecutionState


# Execution state colors
ACTIVE_NODE_COLOR = "#fbbf24"  # Yellow for currently executing node
EXECUTED_EDGE_COLOR = "#22c55e"  # Green for executed edges
BREAKPOINT_COLOR = "#ef4444"  # Red for breakpoints


class BaseStudioCanvas(GraphCanvas):
    """Graph canvas with execution state visualization.

    Extends the base GraphCanvas with:
    - Active node highlighting (yellow fill during execution)
    - Executed edge highlighting (green for traversed edges)
    - Breakpoint indicators

    Subclasses can override _draw_node and _draw_edge to add
    framework-specific visual elements.
    """

    def __init__(
        self,
        graph: GraphModel | None = None,
        execution_state: BaseExecutionState | None = None,
        layout_config: LayoutConfig | None = None,
        theme: GraphTheme | None = None,
        auto_layout: bool = False,
        transform: CanvasTransform | None = None,
    ):
        """Initialize the studio canvas.

        Args:
            graph: Graph model to display.
            execution_state: Current execution state for highlighting.
            layout_config: Layout configuration.
            theme: Visual theme.
            auto_layout: Whether to automatically layout the graph.
            transform: Initial transform state. Creates new if None.
        """
        super().__init__(
            graph=graph,
            layout_config=layout_config or LayoutConfig(direction="LR"),
            theme=theme or DARK_THEME,
            auto_layout=auto_layout,
            transform=transform,
        )
        self._execution_state = execution_state

    def set_execution_state(self, state: BaseExecutionState | None) -> Self:
        """Update execution state for active node highlighting.

        Args:
            state: Current execution state.

        Returns:
            Self for method chaining.
        """
        self._execution_state = state
        self.mark_paint_dirty()
        self.update()
        return self

    def _is_node_active(self, node: NodeModel) -> bool:
        """Check if a node is currently executing.

        Args:
            node: The node to check.

        Returns:
            True if the node is currently executing.
        """
        return (
            self._execution_state is not None
            and self._execution_state.current_node_id == node.id
        )

    def _has_breakpoint(self, node_id: str) -> bool:
        """Check if a node has a breakpoint.

        Args:
            node_id: The node ID to check.

        Returns:
            True if the node has a breakpoint.
        """
        return (
            self._execution_state is not None
            and node_id in self._execution_state.breakpoints
        )

    def _is_edge_executed(self, source_id: str, target_id: str) -> bool:
        """Check if an edge has been executed.

        Args:
            source_id: Source node ID.
            target_id: Target node ID.

        Returns:
            True if the edge has been executed.
        """
        return (
            self._execution_state is not None
            and (source_id, target_id) in self._execution_state.executed_edges
        )

    def _draw_node(self, p: Painter, node: NodeModel) -> None:
        """Draw a node with execution state highlighting.

        Overrides base class to add:
        - Yellow fill for active (currently executing) nodes
        - Breakpoint indicators

        Args:
            p: Painter for drawing.
            node: The node to draw.
        """
        theme = self._theme
        scale = self._transform.scale

        # Determine visual state
        is_active = self._is_node_active(node)
        is_hovered = self._hovered_node_id == node.id
        is_selected = self._selected_node_id == node.id

        # Get base color for node type
        node_color = theme.get_node_color(node.node_type)
        border_color = node_color

        if is_selected:
            border_color = theme.selected_border_color
        elif is_hovered:
            border_color = theme.lighten_color(node_color, theme.hover_lighten_amount)

        # Scale position and size
        pos = Point(x=node.position.x * scale, y=node.position.y * scale)
        node_size = Size(width=node.size.width * scale, height=node.size.height * scale)
        node_rect = Rect(origin=pos, size=node_size)

        # Draw shadow
        shadow_offset = theme.node_shadow_offset * scale
        p.style(
            Style(
                fill=FillStyle(color=theme.node_shadow_color),
                border_radius=theme.node_border_radius * scale,
            )
        )
        p.fill_rect(
            Rect(
                origin=Point(x=pos.x + shadow_offset, y=pos.y + shadow_offset),
                size=node_size,
            )
        )

        # Draw node fill
        if is_active:
            # Active nodes get yellow fill
            p.style(
                Style(
                    fill=FillStyle(color=ACTIVE_NODE_COLOR),
                    border_radius=theme.node_border_radius * scale,
                )
            )
        else:
            # Normal nodes are hollow (filled with background)
            p.style(
                Style(
                    fill=FillStyle(color=theme.background_color),
                    border_radius=theme.node_border_radius * scale,
                )
            )
        p.fill_rect(node_rect)

        # Draw border
        stroke_width = (
            theme.node_border_width * 1.5 if is_selected else theme.node_border_width
        ) * scale
        p.style(
            Style(
                stroke=StrokeStyle(color=border_color, width=stroke_width),
                border_radius=theme.node_border_radius * scale,
            )
        )
        p.stroke_rect(node_rect)

        # Draw label
        font_size = max(10, int(theme.font_size * scale))
        # Use dark text on active (yellow) nodes, otherwise use node type color
        text_color = theme.font_color_on_active if is_active else node_color
        p.style(
            Style(
                fill=FillStyle(color=text_color),
                font=Font(size=font_size),
            )
        )

        # Truncate label if needed
        text_width = p.measure_text(node.label)
        max_text_width = node_size.width - 16 * scale
        display_text = node.label
        if text_width > max_text_width:
            while text_width > max_text_width and len(display_text) > 3:
                display_text = display_text[:-4] + "..."
                text_width = p.measure_text(display_text)

        text_x = pos.x + (node_size.width - p.measure_text(display_text)) / 2
        text_y = pos.y + node_size.height / 2 + font_size / 3
        p.fill_text(display_text, Point(x=text_x, y=text_y), None)

        # Draw breakpoint indicator
        self._draw_breakpoint_indicator(p, node, pos, node_size)

    def _draw_breakpoint_indicator(
        self, p: Painter, node: NodeModel, pos: Point, size: Size
    ) -> None:
        """Draw breakpoint indicator if set on this node.

        Args:
            p: Painter for drawing.
            node: The node.
            pos: Scaled position.
            size: Scaled size.
        """
        if not self._has_breakpoint(node.id):
            return

        scale = self._transform.scale
        breakpoint_radius = 6 * scale

        # Red circle at top-right
        p.style(Style(fill=FillStyle(color=BREAKPOINT_COLOR)))
        p.fill_circle(
            Circle(
                center=Point(
                    x=pos.x + size.width - breakpoint_radius - 4 * scale,
                    y=pos.y + breakpoint_radius + 4 * scale,
                ),
                radius=breakpoint_radius,
            )
        )

        # White inner dot for visibility
        p.style(Style(fill=FillStyle(color="#ffffff")))
        p.fill_circle(
            Circle(
                center=Point(
                    x=pos.x + size.width - breakpoint_radius - 4 * scale,
                    y=pos.y + breakpoint_radius + 4 * scale,
                ),
                radius=breakpoint_radius * 0.4,
            )
        )

    def _draw_edge(self, p: Painter, edge: EdgeModel) -> None:
        """Draw an edge with execution highlighting.

        Highlights executed edges in green.

        Args:
            p: Painter for drawing.
            edge: The edge to draw.
        """
        if self._graph is None:
            return

        source = self._graph.get_node(edge.source_id)
        target = self._graph.get_node(edge.target_id)
        if not source or not target:
            return

        scale = self._transform.scale

        # Check if edge was executed
        is_executed = self._is_edge_executed(edge.source_id, edge.target_id)

        # Get edge color
        if is_executed:
            edge_color = EXECUTED_EDGE_COLOR
        else:
            edge_color = self._theme.get_edge_color(edge.edge_type)

        # Determine layout direction for endpoint calculation
        direction = self._layout_config.direction if self._layout_config else "LR"
        is_horizontal = direction in ("LR", "RL")

        # Calculate edge endpoints
        if is_horizontal:
            start = Point(
                x=(source.position.x + source.size.width) * scale,
                y=(source.position.y + source.size.height / 2) * scale,
            )
            end = Point(
                x=target.position.x * scale,
                y=(target.position.y + target.size.height / 2) * scale,
            )
        else:
            start = Point(
                x=(source.position.x + source.size.width / 2) * scale,
                y=(source.position.y + source.size.height) * scale,
            )
            end = Point(
                x=(target.position.x + target.size.width / 2) * scale,
                y=target.position.y * scale,
            )

        # Draw bezier curve
        self._draw_bezier_edge(p, start, end, edge_color, scale, is_horizontal)

        # Draw arrowhead
        self._draw_arrow_head(p, end, start, edge_color, scale)

        # Draw label if present
        if edge.label:
            self._draw_edge_label(p, start, end, edge.label, scale)
