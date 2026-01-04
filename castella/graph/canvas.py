"""Graph canvas widget for rendering and interacting with graphs."""

from __future__ import annotations

import math
import time
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

from .models import GraphModel, NodeModel, EdgeModel
from .layout import SugiyamaLayout, LayoutConfig
from .transform import CanvasTransform
from .hit_testing import GraphNodeElement, GraphEdgeElement, hit_test
from .theme import GraphTheme, DARK_THEME


class GraphCanvas(Widget):
    """Interactive graph visualization widget.

    Renders nodes and edges with GPU-accelerated custom painting.
    Supports zoom, pan, selection, and hover interactions.

    Features:
        - Automatic layout using Sugiyama algorithm
        - Smooth zoom and pan navigation
        - Node selection and hover highlighting
        - Customizable theme
        - Hit testing for mouse interactions
    """

    def __init__(
        self,
        graph: GraphModel | None = None,
        layout_config: LayoutConfig | None = None,
        theme: GraphTheme | None = None,
        auto_layout: bool = True,
        transform: CanvasTransform | None = None,
    ):
        """Initialize the graph canvas.

        Args:
            graph: Initial graph to display.
            layout_config: Layout configuration. Uses defaults if None.
            theme: Visual theme. Uses dark theme if None.
            auto_layout: Whether to automatically layout the graph.
            transform: Initial transform state. Creates new if None.
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
        self._layout_config = layout_config or LayoutConfig()
        self._theme = theme or DARK_THEME
        self._auto_layout = auto_layout
        self._transform = transform or CanvasTransform()

        # Apply initial layout if graph provided
        if graph and auto_layout:
            self._apply_layout()

        # Hit testing elements
        self._elements: list[GraphNodeElement | GraphEdgeElement] = []

        # Interaction state
        self._hovered_node_id: str | None = None
        self._selected_node_id: str | None = None

        # Panning state
        self._is_panning = False
        self._last_pan_pos: Point | None = None

        # Callbacks
        self._on_node_click_cb: Callable[[str], None] | None = None
        self._on_node_double_click_cb: Callable[[str], None] | None = None
        self._on_node_hover_cb: Callable[[str | None], None] | None = None
        self._on_edge_click_cb: Callable[[str], None] | None = None
        self._on_zoom_change_cb: Callable[[int], None] | None = None

        # Double-click detection
        self._last_click_time: float = 0.0
        self._last_click_node_id: str | None = None
        self._double_click_threshold_ms: float = 400.0  # Max time between clicks

        # Pending center node (applied when size becomes valid)
        self._pending_center_node_id: str | None = None

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

    def on_node_double_click(self, callback: Callable[[str], None]) -> Self:
        """Set callback for node double-click events.

        Args:
            callback: Function called with node ID when double-clicked.

        Returns:
            Self for method chaining.
        """
        self._on_node_double_click_cb = callback
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

    def on_edge_click(self, callback: Callable[[str], None]) -> Self:
        """Set callback for edge click events.

        Args:
            callback: Function called with edge ID when clicked.

        Returns:
            Self for method chaining.
        """
        self._on_edge_click_cb = callback
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

        if graph and self._auto_layout:
            self._apply_layout()

        # Auto-fit if graph has content
        if graph and graph.nodes:
            size = self.get_size()
            if size.width > 0 and size.height > 0:
                self._fit_graph_to_view()

        self.mark_paint_dirty()
        self.update()

    def get_graph(self) -> GraphModel | None:
        """Get the current graph.

        Returns:
            The current graph or None.
        """
        return self._graph

    def relayout(self) -> None:
        """Reapply the layout algorithm to the graph."""
        if self._graph:
            self._apply_layout()
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

    def center_on_node(self, node_id: str) -> None:
        """Center the view on a specific node.

        Args:
            node_id: ID of the node to center on.
        """
        if self._graph is None:
            return

        node = self._graph.get_node(node_id)
        if node is None:
            return

        size = self.get_size()

        # If size is not yet valid, defer centering to redraw
        if size.width <= 0 or size.height <= 0:
            self._pending_center_node_id = node_id
            return

        self._apply_center_on_node(node_id)

    def _apply_center_on_node(self, node_id: str, trigger_update: bool = True) -> None:
        """Actually apply centering on the node.

        Called either directly from center_on_node or deferred from redraw.

        Args:
            node_id: ID of the node to center on.
            trigger_update: Whether to trigger a repaint. Set to False when
                called from within redraw to avoid recursion.
        """
        if self._graph is None:
            return

        node = self._graph.get_node(node_id)
        if node is None:
            return

        size = self.get_size()
        center_x = size.width / 2
        center_y = size.height / 2

        # Calculate offset to center the node
        node_center_x = (node.position.x + node.size.width / 2) * self._transform.scale
        node_center_y = (node.position.y + node.size.height / 2) * self._transform.scale

        self._transform.offset.x = center_x - node_center_x
        self._transform.offset.y = center_y - node_center_y

        if trigger_update:
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

    @selected_node_id.setter
    def selected_node_id(self, node_id: str | None) -> None:
        """Set the selected node ID."""
        if self._selected_node_id != node_id:
            self._selected_node_id = node_id
            self.mark_paint_dirty()
            self.update()

    @property
    def hovered_node_id(self) -> str | None:
        """Get ID of hovered node."""
        return self._hovered_node_id

    @property
    def theme(self) -> GraphTheme:
        """Get the current theme."""
        return self._theme

    def set_theme(self, theme: GraphTheme) -> None:
        """Set a new theme.

        Args:
            theme: New theme to use.
        """
        self._theme = theme
        self.mark_paint_dirty()
        self.update()

    # ========== Layout ==========

    def _apply_layout(self) -> None:
        """Apply the layout algorithm to the current graph."""
        if self._graph is None:
            return

        layout = SugiyamaLayout(self._layout_config)
        layout.layout(self._graph)

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

        # Apply pending center if size is now valid
        if self._pending_center_node_id is not None:
            pending_id = self._pending_center_node_id
            self._pending_center_node_id = None
            # Don't trigger update since we're already in redraw
            self._apply_center_on_node(pending_id, trigger_update=False)

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
        """Draw canvas background with grid."""
        theme = self._theme

        # Fill background
        p.style(Style(fill=FillStyle(color=theme.background_color)))
        p.fill_rect(Rect(origin=Point(x=0, y=0), size=size))

        # Draw grid
        grid_size = 50 * self._transform.scale
        if grid_size >= 10:
            p.style(Style(fill=FillStyle(color=theme.grid_color)))

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

        # Draw border
        p.style(Style(stroke=StrokeStyle(color=theme.border_color, width=1)))
        p.stroke_rect(Rect(origin=Point(x=0, y=0), size=size))

    def _draw_empty_state(self, p: Painter, size: Size) -> None:
        """Draw placeholder when no graph is loaded."""
        # Draw instruction text
        p.style(Style(fill=FillStyle(color="#9ca3af"), font=Font(size=16)))
        text = "No graph to display"
        text_width = p.measure_text(text)
        p.fill_text(
            text,
            Point(x=(size.width - text_width) / 2, y=size.height / 2),
            None,
        )

    def _draw_node(self, p: Painter, node: NodeModel) -> None:
        """Draw a single node.

        Can be overridden in subclasses for custom node rendering.

        Args:
            p: Painter for drawing.
            node: The node to draw.
        """
        theme = self._theme
        scale = self._transform.scale

        # Determine visual state
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

        # Draw node background (hollow style)
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
        p.style(
            Style(
                fill=FillStyle(color=node_color),
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

    def _draw_edge(self, p: Painter, edge: EdgeModel) -> None:
        """Draw an edge with bezier curve.

        Can be overridden in subclasses for custom edge rendering.

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

        theme = self._theme
        scale = self._transform.scale
        is_horizontal = self._layout_config.direction in ("LR", "RL")

        # Calculate edge endpoints
        if is_horizontal:
            # Right side of source to left side of target
            start = Point(
                x=(source.position.x + source.size.width) * scale,
                y=(source.position.y + source.size.height / 2) * scale,
            )
            end = Point(
                x=target.position.x * scale,
                y=(target.position.y + target.size.height / 2) * scale,
            )
        else:
            # Bottom of source to top of target
            start = Point(
                x=(source.position.x + source.size.width / 2) * scale,
                y=(source.position.y + source.size.height) * scale,
            )
            end = Point(
                x=(target.position.x + target.size.width / 2) * scale,
                y=target.position.y * scale,
            )

        edge_color = theme.get_edge_color(edge.edge_type)

        # Draw bezier curve
        self._draw_bezier_edge(p, start, end, edge_color, scale, is_horizontal)

        # Draw arrowhead
        self._draw_arrow_head(p, end, start, edge_color, scale)

        # Draw label if present
        if edge.label:
            self._draw_edge_label(p, start, end, edge.label, scale)

    def _draw_bezier_edge(
        self,
        p: Painter,
        start: Point,
        end: Point,
        color: str,
        scale: float,
        is_horizontal: bool,
    ) -> None:
        """Draw bezier curve using small circles."""
        p.style(Style(fill=FillStyle(color=color)))

        # Control points
        if is_horizontal:
            dx = end.x - start.x
            cp1 = Point(x=start.x + dx * 0.4, y=start.y)
            cp2 = Point(x=end.x - dx * 0.4, y=end.y)
        else:
            dy = end.y - start.y
            cp1 = Point(x=start.x, y=start.y + dy * 0.4)
            cp2 = Point(x=end.x, y=end.y - dy * 0.4)

        # Calculate approximate curve length for step count
        # Use chord length + control point detour as rough estimate
        chord_len = math.sqrt((end.x - start.x) ** 2 + (end.y - start.y) ** 2)
        ctrl_detour = (
            math.sqrt((cp1.x - start.x) ** 2 + (cp1.y - start.y) ** 2)
            + math.sqrt((cp2.x - cp1.x) ** 2 + (cp2.y - cp1.y) ** 2)
            + math.sqrt((end.x - cp2.x) ** 2 + (end.y - cp2.y) ** 2)
        )
        approx_length = (chord_len + ctrl_detour) / 2

        # Calculate steps to ensure circles overlap (step < radius)
        radius = max(1.0, self._theme.edge_width * scale)
        steps = max(20, int(approx_length / (radius * 0.8)))

        for i in range(steps + 1):
            t = i / steps
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
        theme = self._theme

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
        arrow_length = theme.arrow_length * scale
        arrow_width = theme.arrow_width * scale

        # Arrow base point
        base = Point(x=tip.x - dx * arrow_length, y=tip.y - dy * arrow_length)

        # Perpendicular for arrow wings
        perp_x = -dy
        perp_y = dx

        # Draw filled triangle
        p.style(Style(fill=FillStyle(color=color)))

        # Draw as small circles
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

    def _build_elements(self) -> list[GraphNodeElement | GraphEdgeElement]:
        """Build hit-testable elements for nodes and edges."""
        elements: list[GraphNodeElement | GraphEdgeElement] = []
        if self._graph is None:
            return elements

        scale = self._transform.scale

        # Add edges first (so nodes are on top for hit testing)
        # (Edge hit testing is optional, skip for now)

        # Add nodes
        for node in self._graph.nodes:
            screen_pos = Point(
                x=node.position.x * scale + self._transform.offset.x,
                y=node.position.y * scale + self._transform.offset.y,
            )
            screen_rect = Rect(
                origin=screen_pos,
                size=Size(
                    width=node.size.width * scale,
                    height=node.size.height * scale,
                ),
            )
            elements.append(GraphNodeElement(rect=screen_rect, node_id=node.id))

        return elements

    # ========== Mouse Events ==========

    def mouse_down(self, ev: MouseEvent) -> None:
        """Handle mouse button press."""
        element = hit_test(self._elements, ev.pos)
        current_time = time.time() * 1000  # Convert to milliseconds

        if element and isinstance(element, GraphNodeElement):
            node_id = element.node_id
            time_diff = current_time - self._last_click_time

            # Check for double-click
            is_double_click = (
                self._last_click_node_id == node_id
                and time_diff < self._double_click_threshold_ms
            )

            if is_double_click:
                # Double-click detected
                if self._on_node_double_click_cb:
                    self._on_node_double_click_cb(node_id)
                # Reset to prevent triple-click being detected as double
                self._last_click_time = 0.0
                self._last_click_node_id = None
            else:
                # Single click
                self._selected_node_id = node_id
                if self._on_node_click_cb:
                    self._on_node_click_cb(node_id)
                # Record for potential double-click
                self._last_click_time = current_time
                self._last_click_node_id = node_id

        elif element and isinstance(element, GraphEdgeElement):
            if self._on_edge_click_cb:
                self._on_edge_click_cb(element.edge_id)
            # Reset double-click detection
            self._last_click_time = 0.0
            self._last_click_node_id = None
        else:
            # Start panning
            self._is_panning = True
            self._last_pan_pos = ev.pos
            # Reset double-click detection
            self._last_click_time = 0.0
            self._last_click_node_id = None

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
            if self._parent:
                self._parent.mark_paint_dirty()
                self._parent.update(completely=True)
            else:
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

    def dispatch_to_scrollable(
        self, p: Point, is_direction_x: bool
    ) -> tuple[Widget | None, Point | None]:
        """Override to receive wheel events for zoom functionality."""
        if self.contain(p):
            local_p = Point(x=p.x - self._pos.x, y=p.y - self._pos.y)
            return self, local_p
        return None, None

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
        max_x = max(n.position.x + n.size.width for n in self._graph.nodes)
        max_y = max(n.position.y + n.size.height for n in self._graph.nodes)

        self._transform.fit_to_bounds((min_x, min_y, max_x, max_y), size)

    def _notify_zoom_change(self) -> None:
        """Notify zoom change callback."""
        if self._on_zoom_change_cb:
            self._on_zoom_change_cb(self._transform.zoom_percent)
