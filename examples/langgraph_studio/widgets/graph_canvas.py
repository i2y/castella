"""Graph canvas widget for rendering LangGraph nodes and edges."""

from __future__ import annotations

from typing import Callable, Self

from castella.core import (
    Widget,
    Painter,
    SizePolicy,
    Style,
    FillStyle,
    StrokeStyle,
    MouseEvent,
    WheelEvent,
)
from castella.models.geometry import Point, Size, Rect, Circle
from castella.models.font import Font

from ..models.graph import GraphModel, NodeModel, EdgeModel
from ..models.execution import ExecutionState
from ..models.canvas import CanvasTransform
from .hit_testing import GraphNodeElement, hit_test


# Node type colors
NODE_COLORS = {
    "start": "#22c55e",  # Green
    "end": "#ef4444",  # Red
    "agent": "#3b82f6",  # Blue
    "tool": "#f59e0b",  # Amber
    "condition": "#8b5cf6",  # Purple
    "default": "#6b7280",  # Gray
}

ACTIVE_NODE_COLOR = "#fbbf24"  # Yellow for currently executing node
BACKGROUND_COLOR = "#1a1b26"  # Dark background
GRID_COLOR = "#2a2b36"  # Grid lines
NODE_BORDER_COLOR = "#374151"  # Default border
SELECTED_BORDER_COLOR = "#ffffff"  # Selected border
EDGE_COLOR = "#9ca3af"  # Edge lines
CONDITIONAL_EDGE_COLOR = "#8b5cf6"  # Conditional edges
CANVAS_BORDER_COLOR = "#3b4261"  # Canvas border


class GraphCanvas(Widget):
    """Custom canvas widget for rendering LangGraph visualizations.

    Features:
    - Renders nodes and edges with custom Skia drawing
    - Supports zoom and pan navigation
    - Interactive node selection and hover
    - Highlights active node during execution
    """

    def __init__(
        self,
        graph: GraphModel | None = None,
        execution_state: ExecutionState | None = None,
    ):
        """Initialize the graph canvas.

        Args:
            graph: Graph model to display.
            execution_state: Current execution state for highlighting.
        """
        super().__init__(
            state=None,
            pos=Point(x=0, y=0),
            pos_policy=None,
            size=Size(width=0, height=0),
            width_policy=SizePolicy.EXPANDING,
            height_policy=SizePolicy.EXPANDING,
        )

        self._graph = graph
        self._execution_state = execution_state
        self._transform = CanvasTransform()

        # Hit testing elements (rebuilt on each redraw)
        self._elements: list[GraphNodeElement] = []

        # Interaction state
        self._hovered_node_id: str | None = None
        self._selected_node_id: str | None = None

        # Panning state
        self._is_panning = False
        self._last_pan_pos: Point | None = None

        # Callbacks
        self._on_node_click_cb: Callable[[str], None] | None = None
        self._on_node_hover_cb: Callable[[str | None], None] | None = None
        self._on_zoom_change_cb: Callable[[int], None] | None = None

    # ========== Fluent Configuration ==========

    def on_node_click(self, callback: Callable[[str], None]) -> Self:
        """Set callback for node click events.

        Args:
            callback: Function called with node ID when clicked.

        Returns:
            Self for method chaining.
        """
        self._on_node_click_cb = callback
        return self

    def on_node_hover(self, callback: Callable[[str | None], None]) -> Self:
        """Set callback for node hover events.

        Args:
            callback: Function called with node ID or None.

        Returns:
            Self for method chaining.
        """
        self._on_node_hover_cb = callback
        return self

    def on_zoom_change(self, callback: Callable[[int], None]) -> Self:
        """Set callback for zoom level changes.

        Args:
            callback: Function called with zoom percentage.

        Returns:
            Self for method chaining.
        """
        self._on_zoom_change_cb = callback
        return self

    # ========== Public Methods ==========

    def set_graph(self, graph: GraphModel | None) -> None:
        """Update the displayed graph.

        Args:
            graph: New graph to display.
        """
        self._graph = graph
        self._selected_node_id = None
        self._hovered_node_id = None
        self._elements = []

        # Auto-fit if graph has content
        if graph and graph.nodes:
            size = self.get_size()
            if size.width > 0 and size.height > 0:
                self._fit_graph_to_view()

        self.mark_paint_dirty()
        self.update()

    def set_execution_state(self, state: ExecutionState | None) -> None:
        """Update execution state for active node highlighting.

        Args:
            state: Current execution state.
        """
        self._execution_state = state
        self.mark_paint_dirty()
        self.update()

    def zoom_in(self) -> None:
        """Zoom in by 10%."""
        size = self.get_size()
        center = Point(x=size.width / 2, y=size.height / 2)
        self._transform.zoom(1.1, center)
        self._notify_zoom_change()
        self.mark_paint_dirty()
        self.update()

    def zoom_out(self) -> None:
        """Zoom out by 10%."""
        size = self.get_size()
        center = Point(x=size.width / 2, y=size.height / 2)
        self._transform.zoom(0.9, center)
        self._notify_zoom_change()
        self.mark_paint_dirty()
        self.update()

    def reset_view(self) -> None:
        """Reset zoom and pan to default."""
        self._transform.reset()
        self._notify_zoom_change()
        self.mark_paint_dirty()
        self.update()

    def fit_to_content(self) -> None:
        """Fit view to show all graph content."""
        self._fit_graph_to_view()
        self._notify_zoom_change()
        self.mark_paint_dirty()
        self.update()

    @property
    def zoom_percent(self) -> int:
        """Get current zoom level as percentage."""
        return self._transform.zoom_percent

    @property
    def selected_node_id(self) -> str | None:
        """Get ID of selected node."""
        return self._selected_node_id

    # ========== Rendering ==========

    def redraw(self, p: Painter, completely: bool) -> None:
        """Render the graph canvas.

        Args:
            p: Painter for drawing.
            completely: Whether to do a complete redraw.
        """
        size = self.get_size()
        if size.width <= 0 or size.height <= 0:
            return

        # Draw background
        self._draw_background(p, size)

        if self._graph is None:
            self._draw_empty_state(p, size)
            return

        # Build hit-test elements
        self._elements = self._build_elements()

        # Apply transform for graph content
        p.save()
        p.translate(self._transform.offset)

        # Draw edges first (under nodes)
        for edge in self._graph.edges:
            self._draw_edge(p, edge)

        # Draw nodes
        for node in self._graph.nodes:
            self._draw_node(p, node)

        p.restore()

    def _draw_background(self, p: Painter, size: Size) -> None:
        """Draw canvas background with grid and border."""
        # Fill background
        p.style(Style(fill=FillStyle(color=BACKGROUND_COLOR)))
        p.fill_rect(Rect(origin=Point(x=0, y=0), size=size))

        # Draw grid
        grid_size = 50 * self._transform.scale
        if grid_size >= 10:  # Only draw if grid is visible
            p.style(Style(fill=FillStyle(color=GRID_COLOR)))

            # Vertical lines
            start_x = self._transform.offset.x % grid_size
            x = start_x
            while x < size.width:
                p.fill_rect(
                    Rect(origin=Point(x=x, y=0), size=Size(width=1, height=size.height))
                )
                x += grid_size

            # Horizontal lines
            start_y = self._transform.offset.y % grid_size
            y = start_y
            while y < size.height:
                p.fill_rect(
                    Rect(origin=Point(x=0, y=y), size=Size(width=size.width, height=1))
                )
                y += grid_size

        # Draw border around the canvas
        p.style(Style(stroke=StrokeStyle(color=CANVAS_BORDER_COLOR, width=1)))
        p.stroke_rect(Rect(origin=Point(x=0, y=0), size=size))

    def _draw_empty_state(self, p: Painter, size: Size) -> None:
        """Draw placeholder when no graph is loaded."""
        # Draw icon
        icon = "📂"
        p.style(Style(fill=FillStyle(color="#6b7280"), font=Font(size=32)))
        icon_width = p.measure_text(icon)
        p.fill_text(
            icon,
            Point(x=(size.width - icon_width) / 2, y=size.height / 2 - 20),
            None,
        )

        # Draw instruction text
        p.style(Style(fill=FillStyle(color="#9ca3af"), font=Font(size=16)))
        text = "Select a LangGraph file to visualize"
        text_width = p.measure_text(text)
        p.fill_text(
            text,
            Point(x=(size.width - text_width) / 2, y=size.height / 2 + 20),
            None,
        )

    def _draw_node(self, p: Painter, node: NodeModel) -> None:
        """Draw a single node as a hollow rectangle (state box)."""
        # Determine visual state
        is_active = (
            self._execution_state
            and self._execution_state.current_node_id == node.id
        )
        is_hovered = self._hovered_node_id == node.id
        is_selected = self._selected_node_id == node.id

        # Determine colors - all nodes use the same border color
        # Only active nodes get filled with yellow
        node_color = NODE_COLORS.get(node.node_type, NODE_COLORS["default"])
        border_color = node_color

        if is_selected:
            border_color = SELECTED_BORDER_COLOR
        elif is_hovered:
            border_color = self._lighten_color(node_color, 0.3)

        # Scale position and size
        scale = self._transform.scale
        pos = Point(x=node.position.x * scale, y=node.position.y * scale)
        node_size = Size(width=node.size[0] * scale, height=node.size[1] * scale)
        node_rect = Rect(origin=pos, size=node_size)

        # Draw shadow (subtle)
        shadow_offset = 3 * scale
        p.style(Style(fill=FillStyle(color="#00000022"), border_radius=8 * scale))
        p.fill_rect(
            Rect(
                origin=Point(x=pos.x + shadow_offset, y=pos.y + shadow_offset),
                size=node_size,
            )
        )

        # Active nodes get filled with yellow, others are hollow
        if is_active:
            # Fill with yellow when active
            p.style(
                Style(
                    fill=FillStyle(color=ACTIVE_NODE_COLOR),
                    border_radius=8 * scale,
                )
            )
            p.fill_rect(node_rect)
        else:
            # Hollow rectangle - just fill with dark background
            p.style(
                Style(
                    fill=FillStyle(color=BACKGROUND_COLOR),
                    border_radius=8 * scale,
                )
            )
            p.fill_rect(node_rect)

        # Draw border (thicker for visibility)
        stroke_width = 2 * scale if is_selected else 1.5 * scale
        p.style(
            Style(
                stroke=StrokeStyle(color=border_color, width=stroke_width),
                border_radius=8 * scale,
            )
        )
        p.stroke_rect(node_rect)

        # Draw label - use node color for text when not active
        font_size = max(10, int(14 * scale))
        text_color = "#1a1b26" if is_active else node_color
        p.style(
            Style(
                fill=FillStyle(color=text_color),
                font=Font(size=font_size),
            )
        )
        text_width = p.measure_text(node.label)
        max_text_width = node_size.width - 16 * scale
        display_text = node.label
        if text_width > max_text_width:
            # Truncate with ellipsis
            while text_width > max_text_width and len(display_text) > 3:
                display_text = display_text[:-4] + "..."
                text_width = p.measure_text(display_text)

        text_x = pos.x + (node_size.width - p.measure_text(display_text)) / 2
        text_y = pos.y + node_size.height / 2 + font_size / 3
        p.fill_text(display_text, Point(x=text_x, y=text_y), None)

        # Draw breakpoint indicator (no special start/end indicators)
        self._draw_breakpoint_indicator(p, node, pos, node_size)

    def _draw_breakpoint_indicator(
        self, p: Painter, node: NodeModel, pos: Point, size: Size
    ) -> None:
        """Draw breakpoint indicator if set on this node."""
        if not self._execution_state or node.id not in self._execution_state.breakpoints:
            return

        scale = self._transform.scale
        breakpoint_radius = 6 * scale

        # Red circle at top-right
        p.style(Style(fill=FillStyle(color="#ef4444")))
        p.fill_circle(
            Circle(
                center=Point(
                    x=pos.x + size.width - breakpoint_radius - 4 * scale,
                    y=pos.y + breakpoint_radius + 4 * scale,
                ),
                radius=breakpoint_radius,
            )
        )
        # White inner dot for better visibility
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
        """Draw an edge with bezier curve."""
        if self._graph is None:
            return

        source = self._graph.get_node(edge.source_node_id)
        target = self._graph.get_node(edge.target_node_id)
        if not source or not target:
            return

        scale = self._transform.scale

        # Calculate edge endpoints (right side of source, left side of target)
        start = Point(
            x=(source.position.x + source.size[0]) * scale,
            y=(source.position.y + source.size[1] / 2) * scale,
        )
        end = Point(
            x=target.position.x * scale,
            y=(target.position.y + target.size[1] / 2) * scale,
        )

        # Determine edge color
        edge_color = (
            CONDITIONAL_EDGE_COLOR
            if edge.edge_type == "conditional"
            else EDGE_COLOR
        )

        # Draw bezier curve
        self._draw_bezier_edge(p, start, end, edge_color, scale)

        # Draw arrowhead
        self._draw_arrow_head(p, end, start, edge_color, scale)

        # Draw condition label if present
        if edge.condition_label:
            self._draw_edge_label(p, start, end, edge.condition_label, scale)

    def _draw_bezier_edge(
        self, p: Painter, start: Point, end: Point, color: str, scale: float
    ) -> None:
        """Draw bezier curve using small circles."""
        p.style(Style(fill=FillStyle(color=color)))

        # Control points for horizontal bezier
        dx = end.x - start.x
        cp1 = Point(x=start.x + dx * 0.4, y=start.y)
        cp2 = Point(x=end.x - dx * 0.4, y=end.y)

        # Draw curve as series of circles
        steps = 30
        radius = max(1, 1.5 * scale)
        for i in range(steps + 1):
            t = i / steps
            # Cubic bezier formula
            t2 = t * t
            t3 = t2 * t
            mt = 1 - t
            mt2 = mt * mt
            mt3 = mt2 * mt

            x = mt3 * start.x + 3 * mt2 * t * cp1.x + 3 * mt * t2 * cp2.x + t3 * end.x
            y = mt3 * start.y + 3 * mt2 * t * cp1.y + 3 * mt * t2 * cp2.y + t3 * end.y

            p.fill_circle(Circle(center=Point(x=x, y=y), radius=radius))

    def _draw_arrow_head(
        self, p: Painter, tip: Point, from_point: Point, color: str, scale: float
    ) -> None:
        """Draw arrowhead at edge endpoint."""
        import math

        # Calculate direction
        dx = tip.x - from_point.x
        dy = tip.y - from_point.y
        length = math.sqrt(dx * dx + dy * dy)
        if length == 0:
            return

        # Normalize
        dx /= length
        dy /= length

        # Arrow dimensions
        arrow_length = 12 * scale
        arrow_width = 6 * scale

        # Arrow base point
        base = Point(x=tip.x - dx * arrow_length, y=tip.y - dy * arrow_length)

        # Perpendicular for arrow wings
        perp_x = -dy
        perp_y = dx

        # Draw filled triangle
        p.style(Style(fill=FillStyle(color=color)))

        # Draw as three circles forming arrow shape
        for i in range(int(arrow_length)):
            t = i / arrow_length
            width = arrow_width * (1 - t)
            cx = base.x + dx * i
            cy = base.y + dy * i

            for w in range(-int(width), int(width) + 1):
                p.fill_circle(
                    Circle(
                        center=Point(x=cx + perp_x * w * 0.3, y=cy + perp_y * w * 0.3),
                        radius=max(1, scale),
                    )
                )

    def _draw_edge_label(
        self, p: Painter, start: Point, end: Point, label: str, scale: float
    ) -> None:
        """Draw label on edge."""
        font_size = max(8, int(11 * scale))
        p.style(
            Style(
                fill=FillStyle(color="#9ca3af"),
                font=Font(size=font_size),
            )
        )

        # Position at midpoint
        mid = Point(x=(start.x + end.x) / 2, y=(start.y + end.y) / 2 - 8 * scale)
        text_width = p.measure_text(label)
        p.fill_text(label, Point(x=mid.x - text_width / 2, y=mid.y), None)

    # ========== Hit Testing ==========

    def _build_elements(self) -> list[GraphNodeElement]:
        """Build hit-testable elements for all nodes."""
        elements = []
        if self._graph is None:
            return elements

        scale = self._transform.scale
        for node in self._graph.nodes:
            screen_pos = Point(
                x=node.position.x * scale + self._transform.offset.x,
                y=node.position.y * scale + self._transform.offset.y,
            )
            screen_rect = Rect(
                origin=screen_pos,
                size=Size(
                    width=node.size[0] * scale,
                    height=node.size[1] * scale,
                ),
            )
            elements.append(GraphNodeElement(rect=screen_rect, node_id=node.id))

        return elements

    # ========== Mouse Events ==========

    def mouse_down(self, ev: MouseEvent) -> None:
        """Handle mouse button press."""
        element = hit_test(self._elements, ev.pos)

        if element and isinstance(element, GraphNodeElement):
            self._selected_node_id = element.node_id
            if self._on_node_click_cb:
                self._on_node_click_cb(element.node_id)
        else:
            # Start panning
            self._is_panning = True
            self._last_pan_pos = ev.pos

        self.mark_paint_dirty()
        self.update()

    def mouse_up(self, ev: MouseEvent) -> None:
        """Handle mouse button release."""
        self._is_panning = False
        self._last_pan_pos = None

    def mouse_drag(self, ev: MouseEvent) -> None:
        """Handle mouse drag for panning."""
        if self._is_panning and self._last_pan_pos:
            delta = Point(
                x=ev.pos.x - self._last_pan_pos.x,
                y=ev.pos.y - self._last_pan_pos.y,
            )
            self._transform.pan(delta)
            self._last_pan_pos = ev.pos
            self.mark_paint_dirty()
            self.update()

    def cursor_pos(self, ev: MouseEvent) -> None:
        """Handle mouse movement for hover detection."""
        if self._is_panning:
            return

        element = hit_test(self._elements, ev.pos)
        new_hovered = element.node_id if isinstance(element, GraphNodeElement) else None

        if new_hovered != self._hovered_node_id:
            self._hovered_node_id = new_hovered
            if self._on_node_hover_cb:
                self._on_node_hover_cb(new_hovered)
            self.mark_paint_dirty()
            self.update()

    def mouse_wheel(self, ev: WheelEvent) -> None:
        """Handle mouse wheel for zoom."""
        factor = 1.1 if ev.y_offset > 0 else 0.9
        self._transform.zoom(factor, ev.pos)
        self._notify_zoom_change()
        self.mark_paint_dirty()
        self.update()

    # ========== Utilities ==========

    def _fit_graph_to_view(self) -> None:
        """Fit the graph to the current view."""
        if not self._graph or not self._graph.nodes:
            return

        size = self.get_size()
        if size.width <= 0 or size.height <= 0:
            return

        # Calculate content bounds
        min_x = min(n.position.x for n in self._graph.nodes)
        min_y = min(n.position.y for n in self._graph.nodes)
        max_x = max(n.position.x + n.size[0] for n in self._graph.nodes)
        max_y = max(n.position.y + n.size[1] for n in self._graph.nodes)

        self._transform.fit_to_bounds((min_x, min_y, max_x, max_y), size)

    def _notify_zoom_change(self) -> None:
        """Notify zoom change callback."""
        if self._on_zoom_change_cb:
            self._on_zoom_change_cb(self._transform.zoom_percent)

    @staticmethod
    def _lighten_color(hex_color: str, amount: float) -> str:
        """Lighten a hex color by a percentage.

        Args:
            hex_color: Hex color string (e.g., "#3b82f6").
            amount: Amount to lighten (0-1).

        Returns:
            Lightened hex color.
        """
        # Parse hex
        hex_color = hex_color.lstrip("#")
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)

        # Lighten
        r = min(255, int(r + (255 - r) * amount))
        g = min(255, int(g + (255 - g) * amount))
        b = min(255, int(b + (255 - b) * amount))

        return f"#{r:02x}{g:02x}{b:02x}"
