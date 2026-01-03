"""Workflow canvas for LlamaIndex Workflow Studio.

This canvas extends BaseStudioCanvas with event-driven specific visualization:
- Steps with I/O slots (circles on left/right for input/output events)
- Event type labels on edges
- AND gate symbol for Collect patterns
- OR branching indicator for Union outputs
- Color-coded event categories
"""

from __future__ import annotations

import math
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
    GraphModel,
    NodeModel,
    EdgeModel,
    NodeType,
    EdgeType,
    LayoutConfig,
)
from castella.graph.theme import GraphTheme, DARK_THEME
from castella.graph.transform import CanvasTransform

from castella.studio.widgets.canvas import (
    BaseStudioCanvas,
    ACTIVE_NODE_COLOR,
    EXECUTED_EDGE_COLOR,
    BREAKPOINT_COLOR,
)

from ..models.workflow import WorkflowModel, EventEdge
from ..models.steps import StepModel, InputMode, OutputMode
from ..models.events import EventTypeModel, EventCategory, EVENT_COLORS
from ..models.execution import WorkflowExecutionState


# Slot colors
INPUT_SLOT_COLOR = "#3b82f6"   # Blue for input slots
OUTPUT_SLOT_COLOR = "#22c55e"  # Green for output slots

# Pattern indicator colors
COLLECT_GATE_COLOR = "#f59e0b"  # Amber for Collect (AND) gate
UNION_INDICATOR_COLOR = "#a855f7"  # Purple for Union (OR) indicator

# Selection highlight color
HIGHLIGHTED_EDGE_COLOR = "#fbbf24"  # Yellow/amber for highlighted edges


class WorkflowCanvas(BaseStudioCanvas):
    """Canvas for LlamaIndex Workflow visualization.

    Extends BaseStudioCanvas with event-driven specific features:
    - Steps rendered with I/O slots showing event connections
    - Event type labels on edges with category-based colors
    - Collect (AND) gate symbols for steps requiring multiple events
    - Union (OR) branching indicators for steps emitting multiple event types
    """

    def __init__(
        self,
        workflow: WorkflowModel | None = None,
        execution_state: WorkflowExecutionState | None = None,
        layout_config: LayoutConfig | None = None,
        theme: GraphTheme | None = None,
        auto_layout: bool = True,
        transform: CanvasTransform | None = None,
    ):
        """Initialize the workflow canvas.

        Args:
            workflow: Workflow model to display.
            execution_state: Current execution state for highlighting.
            layout_config: Layout configuration (defaults to LR).
            theme: Visual theme.
            auto_layout: Whether to automatically layout the graph.
            transform: Initial transform state. Creates new if None.
        """
        # Convert workflow to graph model
        graph = self._workflow_to_graph(workflow) if workflow else None

        super().__init__(
            graph=graph,
            execution_state=execution_state,
            layout_config=layout_config or LayoutConfig(direction="LR"),
            theme=theme or DARK_THEME,
            auto_layout=auto_layout,
            transform=transform,
        )

        self._workflow = workflow
        self._highlighted_event_type: str | None = None

    def set_workflow(self, workflow: WorkflowModel | None) -> Self:
        """Update the displayed workflow.

        Args:
            workflow: New workflow to display.

        Returns:
            Self for method chaining.
        """
        self._workflow = workflow
        graph = self._workflow_to_graph(workflow) if workflow else None
        self.set_graph(graph)
        return self

    def set_execution_state(self, state: WorkflowExecutionState | None) -> Self:
        """Update execution state for visualization.

        Args:
            state: Current execution state.

        Returns:
            Self for method chaining.
        """
        self._execution_state = state
        self.mark_paint_dirty()
        self.update()
        return self

    def set_highlighted_event_type(self, event_type: str | None) -> Self:
        """Set the event type to highlight on the canvas.

        Edges using this event type will be visually highlighted.

        Args:
            event_type: Event type name to highlight, or None to clear.

        Returns:
            Self for method chaining.
        """
        self._highlighted_event_type = event_type
        self.mark_paint_dirty()
        self.update()
        return self

    def _workflow_to_graph(self, workflow: WorkflowModel) -> GraphModel:
        """Convert a WorkflowModel to a GraphModel for rendering.

        Args:
            workflow: The workflow to convert.

        Returns:
            A GraphModel with nodes for steps and edges for event flow.
        """
        nodes = []
        edges = []

        # Convert steps to nodes
        for step in workflow.steps:
            node_type = self._determine_node_type(step, workflow)
            nodes.append(NodeModel(
                id=step.id,
                label=step.label,
                node_type=node_type,
                position=step.position.model_copy(),
                size=step.size.model_copy(),
                metadata={
                    "step": step,
                    "input_events": step.input_events,
                    "output_events": step.output_events,
                    "input_mode": step.input_mode,
                    "output_mode": step.output_mode,
                },
            ))

        # Add virtual START and END nodes
        nodes.append(NodeModel(
            id="__start__",
            label="START",
            node_type=NodeType.START,
            size=Size(width=80, height=40),
        ))
        nodes.append(NodeModel(
            id="__end__",
            label="END",
            node_type=NodeType.END,
            size=Size(width=80, height=40),
        ))

        # Convert event edges
        for event_edge in workflow.edges:
            source_id = event_edge.source_step_id or "__start__"
            target_id = event_edge.target_step_id or "__end__"

            edge_type = EdgeType.NORMAL
            if event_edge.is_part_of_union:
                edge_type = EdgeType.CONDITIONAL

            edges.append(EdgeModel(
                id=event_edge.id,
                source_id=source_id,
                target_id=target_id,
                edge_type=edge_type,
                label=event_edge.event_type,
                metadata={
                    "event_edge": event_edge,
                    "event_type": event_edge.event_type,
                    "is_collect": event_edge.is_part_of_collect,
                    "is_union": event_edge.is_part_of_union,
                },
            ))

        return GraphModel(
            name=workflow.name,
            nodes=nodes,
            edges=edges,
        )

    def _determine_node_type(
        self, step: StepModel, workflow: WorkflowModel
    ) -> NodeType:
        """Determine the node type for a step.

        Args:
            step: The step to analyze.
            workflow: The parent workflow.

        Returns:
            The appropriate NodeType for rendering.
        """
        # Check if this step handles StartEvent
        if workflow.start_event_type in step.input_events:
            return NodeType.START

        # Check if this step emits StopEvent
        if workflow.stop_event_type in step.output_events:
            return NodeType.END

        # Check if this is a decision/branching step (Union output)
        if step.output_mode == OutputMode.UNION and len(step.output_events) > 1:
            return NodeType.DECISION

        return NodeType.PROCESS

    def _draw_node(self, p: Painter, node: NodeModel) -> None:
        """Draw a step node with I/O slots.

        Overrides base class to add:
        - Input event slots on the left
        - Output event slots on the right
        - Collect (AND) gate indicator
        - Union (OR) branching indicator

        Args:
            p: Painter for drawing.
            node: The node to draw.
        """
        # Skip virtual start/end nodes - use base rendering
        if node.id in ("__start__", "__end__"):
            super()._draw_node(p, node)
            return

        theme = self._theme
        scale = self._transform.scale

        # Get step metadata
        step_data = node.metadata or {}
        input_events = step_data.get("input_events", [])
        output_events = step_data.get("output_events", [])
        input_mode = step_data.get("input_mode", InputMode.SINGLE)
        output_mode = step_data.get("output_mode", OutputMode.SINGLE)

        # Determine visual state
        is_active = self._is_step_active(node.id)
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
            fill_color = ACTIVE_NODE_COLOR
        else:
            fill_color = theme.background_color

        p.style(
            Style(
                fill=FillStyle(color=fill_color),
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

        # Draw I/O slots
        self._draw_input_slots(p, pos, node_size, input_events, input_mode, scale)
        self._draw_output_slots(p, pos, node_size, output_events, output_mode, scale)

        # Draw Collect gate indicator if applicable
        if input_mode == InputMode.COLLECT:
            self._draw_collect_gate(p, pos, node_size, scale)

        # Draw Union indicator if applicable
        if output_mode == OutputMode.UNION and len(output_events) > 1:
            self._draw_union_indicator(p, pos, node_size, scale)

        # Draw label
        font_size = max(10, int(theme.font_size * scale))
        text_color = theme.font_color_on_active if is_active else node_color
        p.style(
            Style(
                fill=FillStyle(color=text_color),
                font=Font(size=font_size),
            )
        )

        # Truncate label if needed
        text_width = p.measure_text(node.label)
        max_text_width = node_size.width - 32 * scale  # Extra padding for slots
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

    def _draw_input_slots(
        self,
        p: Painter,
        pos: Point,
        size: Size,
        input_events: list[str],
        input_mode: InputMode,
        scale: float,
    ) -> None:
        """Draw input event slots on the left side of the node.

        Args:
            p: Painter for drawing.
            pos: Node position (scaled).
            size: Node size (scaled).
            input_events: List of input event type names.
            input_mode: How inputs are handled.
            scale: Current zoom scale.
        """
        if not input_events:
            return

        slot_radius = 5 * scale
        slot_x = pos.x - slot_radius

        # Calculate slot positions
        if len(input_events) == 1:
            slots_y = [pos.y + size.height / 2]
        else:
            # Distribute slots vertically
            margin = 10 * scale
            available = size.height - 2 * margin
            spacing = available / (len(input_events) - 1) if len(input_events) > 1 else 0
            slots_y = [pos.y + margin + i * spacing for i in range(len(input_events))]

        for i, (event_name, slot_y) in enumerate(zip(input_events, slots_y)):
            # Get event color
            event_color = self._get_event_color(event_name)

            # Draw slot circle
            p.style(Style(fill=FillStyle(color=event_color)))
            p.fill_circle(Circle(
                center=Point(x=slot_x, y=slot_y),
                radius=slot_radius,
            ))

            # Draw connecting line to node (horizontal line using thin rect)
            line_width = max(1, 1.5 * scale)
            line_rect_width = max(0, pos.x - (slot_x + slot_radius))
            if line_rect_width > 0:
                p.style(Style(fill=FillStyle(color=event_color)))
                p.fill_rect(Rect(
                    origin=Point(x=slot_x + slot_radius, y=slot_y - line_width / 2),
                    size=Size(width=line_rect_width, height=line_width),
                ))

    def _draw_output_slots(
        self,
        p: Painter,
        pos: Point,
        size: Size,
        output_events: list[str],
        output_mode: OutputMode,
        scale: float,
    ) -> None:
        """Draw output event slots on the right side of the node.

        Args:
            p: Painter for drawing.
            pos: Node position (scaled).
            size: Node size (scaled).
            output_events: List of output event type names.
            output_mode: How outputs are handled.
            scale: Current zoom scale.
        """
        if not output_events:
            return

        slot_radius = 5 * scale
        slot_x = pos.x + size.width + slot_radius

        # Calculate slot positions
        if len(output_events) == 1:
            slots_y = [pos.y + size.height / 2]
        else:
            # Distribute slots vertically
            margin = 10 * scale
            available = size.height - 2 * margin
            spacing = available / (len(output_events) - 1) if len(output_events) > 1 else 0
            slots_y = [pos.y + margin + i * spacing for i in range(len(output_events))]

        for i, (event_name, slot_y) in enumerate(zip(output_events, slots_y)):
            # Get event color
            event_color = self._get_event_color(event_name)

            # Draw slot circle
            p.style(Style(fill=FillStyle(color=event_color)))
            p.fill_circle(Circle(
                center=Point(x=slot_x, y=slot_y),
                radius=slot_radius,
            ))

            # Draw connecting line from node (horizontal line using thin rect)
            line_width = max(1, 1.5 * scale)
            line_rect_width = max(0, (slot_x - slot_radius) - (pos.x + size.width))
            if line_rect_width > 0:
                p.style(Style(fill=FillStyle(color=event_color)))
                p.fill_rect(Rect(
                    origin=Point(x=pos.x + size.width, y=slot_y - line_width / 2),
                    size=Size(width=line_rect_width, height=line_width),
                ))

    def _draw_collect_gate(
        self, p: Painter, pos: Point, size: Size, scale: float
    ) -> None:
        """Draw Collect (AND) gate indicator.

        Shows a gate symbol indicating all inputs must be received.

        Args:
            p: Painter for drawing.
            pos: Node position (scaled).
            size: Node size (scaled).
            scale: Current zoom scale.
        """
        gate_width = 12 * scale
        gate_height = 20 * scale
        gate_x = pos.x - gate_width - 8 * scale
        gate_y = pos.y + (size.height - gate_height) / 2

        # Draw gate background
        p.style(Style(
            fill=FillStyle(color=COLLECT_GATE_COLOR),
            border_radius=2 * scale,
        ))
        p.fill_rect(Rect(
            origin=Point(x=gate_x, y=gate_y),
            size=Size(width=gate_width, height=gate_height),
        ))

        # Draw AND symbol (&)
        font_size = max(8, int(10 * scale))
        p.style(Style(
            fill=FillStyle(color="#ffffff"),
            font=Font(size=font_size),
        ))
        symbol = "&"
        symbol_width = p.measure_text(symbol)
        p.fill_text(
            symbol,
            Point(
                x=gate_x + (gate_width - symbol_width) / 2,
                y=gate_y + gate_height / 2 + font_size / 3,
            ),
            None,
        )

    def _draw_union_indicator(
        self, p: Painter, pos: Point, size: Size, scale: float
    ) -> None:
        """Draw Union (OR) branching indicator.

        Shows a branching symbol indicating one of multiple outputs.

        Args:
            p: Painter for drawing.
            pos: Node position (scaled).
            size: Node size (scaled).
            scale: Current zoom scale.
        """
        indicator_x = pos.x + size.width + 20 * scale
        indicator_y = pos.y + size.height / 2

        # Draw diamond shape for OR
        diamond_size = 6 * scale
        p.style(Style(fill=FillStyle(color=UNION_INDICATOR_COLOR)))

        # Draw as rotated square (multiple circles to approximate)
        for dx in range(-int(diamond_size), int(diamond_size) + 1):
            max_dy = diamond_size - abs(dx)
            for dy in range(-int(max_dy), int(max_dy) + 1):
                if abs(dx) + abs(dy) <= diamond_size:
                    p.fill_circle(Circle(
                        center=Point(x=indicator_x + dx, y=indicator_y + dy),
                        radius=1 * scale,
                    ))

    def _draw_edge(self, p: Painter, edge: EdgeModel) -> None:
        """Draw an edge with event type label.

        Overrides base class to add:
        - Event type name as edge label
        - Color based on event category
        - Visual distinction for union/collect edges

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
        edge_data = edge.metadata or {}
        event_type = edge_data.get("event_type", edge.label or "")
        is_union = edge_data.get("is_union", False)
        is_collect = edge_data.get("is_collect", False)

        # Check if edge was executed
        is_executed = self._is_edge_executed(edge.source_id, edge.target_id)

        # Check if edge is highlighted (selected event type)
        is_highlighted = (
            self._highlighted_event_type is not None
            and event_type == self._highlighted_event_type
        )

        # Get edge color (priority: executed > highlighted > normal)
        if is_executed:
            edge_color = EXECUTED_EDGE_COLOR
        elif is_highlighted:
            edge_color = HIGHLIGHTED_EDGE_COLOR
        else:
            edge_color = self._get_event_color(event_type)

        # Calculate edge endpoints
        direction = self._layout_config.direction if self._layout_config else "LR"
        is_horizontal = direction in ("LR", "RL")

        if is_horizontal:
            # Right side of source to left side of target
            # Adjust for slots
            start = Point(
                x=(source.position.x + source.size.width + 10) * scale,
                y=(source.position.y + source.size.height / 2) * scale,
            )
            end = Point(
                x=(target.position.x - 10) * scale,
                y=(target.position.y + target.size.height / 2) * scale,
            )
        else:
            start = Point(
                x=(source.position.x + source.size.width / 2) * scale,
                y=(source.position.y + source.size.height + 10) * scale,
            )
            end = Point(
                x=(target.position.x + target.size.width / 2) * scale,
                y=(target.position.y - 10) * scale,
            )

        # Draw bezier curve with styling based on pattern
        stroke_width_multiplier = 1.0
        if is_highlighted:
            stroke_width_multiplier = 2.0  # Thicker for highlighted edges
        elif is_union:
            stroke_width_multiplier = 0.8  # Thinner for union edges
        elif is_collect:
            stroke_width_multiplier = 1.2  # Thicker for collect edges

        self._draw_bezier_edge_styled(
            p, start, end, edge_color, scale, is_horizontal, stroke_width_multiplier
        )

        # Draw arrowhead
        self._draw_arrow_head(p, end, start, edge_color, scale)

        # Draw event type label
        if event_type:
            self._draw_event_label(p, start, end, event_type, edge_color, scale)

    def _draw_bezier_edge_styled(
        self,
        p: Painter,
        start: Point,
        end: Point,
        color: str,
        scale: float,
        is_horizontal: bool,
        width_multiplier: float = 1.0,
    ) -> None:
        """Draw bezier curve with custom width.

        Args:
            p: Painter for drawing.
            start: Start point.
            end: End point.
            color: Edge color.
            scale: Current zoom scale.
            is_horizontal: Whether layout is horizontal.
            width_multiplier: Multiplier for stroke width.
        """
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

        # Draw curve as series of circles
        steps = 30
        radius = max(1, self._theme.edge_width * scale * width_multiplier)
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

    def _draw_event_label(
        self,
        p: Painter,
        start: Point,
        end: Point,
        event_type: str,
        color: str,
        scale: float,
    ) -> None:
        """Draw event type label on edge.

        Args:
            p: Painter for drawing.
            start: Edge start point.
            end: Edge end point.
            event_type: Event type name to display.
            color: Label color.
            scale: Current zoom scale.
        """
        font_size = max(8, int(10 * scale))

        # Draw label background for readability
        mid = Point(x=(start.x + end.x) / 2, y=(start.y + end.y) / 2 - 12 * scale)
        text_width = p.measure_text(event_type)
        padding = 4 * scale

        p.style(Style(
            fill=FillStyle(color=self._theme.background_color),
            border_radius=3 * scale,
        ))
        p.fill_rect(Rect(
            origin=Point(x=mid.x - text_width / 2 - padding, y=mid.y - font_size / 2 - padding),
            size=Size(width=text_width + padding * 2, height=font_size + padding * 2),
        ))

        # Draw label text
        p.style(Style(
            fill=FillStyle(color=color),
            font=Font(size=font_size),
        ))
        p.fill_text(event_type, Point(x=mid.x - text_width / 2, y=mid.y + font_size / 3), None)

    def _get_event_color(self, event_type: str) -> str:
        """Get color for an event type based on its category.

        Args:
            event_type: The event type name.

        Returns:
            Color hex string.
        """
        if self._workflow is None:
            return EVENT_COLORS[EventCategory.USER]

        event_model = self._workflow.event_types.get(event_type)
        if event_model:
            return event_model.get_color()

        # Default colors based on name
        if event_type == "StartEvent" or event_type == self._workflow.start_event_type:
            return EVENT_COLORS[EventCategory.START]
        elif event_type == "StopEvent" or event_type == self._workflow.stop_event_type:
            return EVENT_COLORS[EventCategory.STOP]

        return EVENT_COLORS[EventCategory.USER]

    def _is_step_active(self, step_id: str) -> bool:
        """Check if a step is currently executing or paused at breakpoint.

        Args:
            step_id: The step ID to check.

        Returns:
            True if the step is currently executing or paused.
        """
        if not isinstance(self._execution_state, WorkflowExecutionState):
            return self._is_node_active(
                NodeModel(id=step_id, label="")
            )

        # Check if step is in active set OR is the current node (e.g., paused at breakpoint)
        return (
            step_id in self._execution_state.active_step_ids
            or self._execution_state.current_node_id == step_id
        )

    def _is_edge_executed(self, source_id: str, target_id: str) -> bool:
        """Check if an edge has been traversed during execution.

        Args:
            source_id: Source step ID.
            target_id: Target step ID.

        Returns:
            True if the edge has been executed.
        """
        if self._execution_state is None:
            return False

        # Check executed edges - now using __start__ and __end__ directly
        for edge_src, edge_tgt in self._execution_state.executed_edges:
            if edge_src == source_id and edge_tgt == target_id:
                return True

        return False
