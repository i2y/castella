"""Event timeline widget for LlamaIndex Workflow Studio.

Provides a horizontal time-series visualization of workflow execution:
- Horizontal time axis with zoom
- Vertical lanes for each step
- Event markers (●) at emit time
- Step execution bars with duration
- Click to select for details
"""

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

from ..models.workflow import WorkflowModel
from ..models.events import EventCategory, EVENT_COLORS
from ..models.execution import WorkflowExecutionState, StepExecution


# Timeline colors
LANE_BG_COLOR = "#1a1b26"
LANE_ALT_BG_COLOR = "#1e1f2b"
LANE_BORDER_COLOR = "#2a2b3d"
TIME_AXIS_COLOR = "#4a4b5d"
EXECUTION_BAR_COLOR = "#3b82f6"
ERROR_BAR_COLOR = "#ef4444"
EVENT_MARKER_BORDER = "#ffffff"
TIMELINE_BG_COLOR = "#13141c"


class EventTimeline(Widget):
    """Horizontal timeline visualization of workflow execution.

    Features:
    - Horizontal time axis (0 to current execution time)
    - Vertical lanes for each step
    - Event markers showing event emissions
    - Step execution bars with duration
    - Zoom and pan support
    - Click to select step/event for details
    """

    def __init__(
        self,
        workflow: WorkflowModel | None = None,
        execution_state: WorkflowExecutionState | None = None,
    ):
        """Initialize the event timeline.

        Args:
            workflow: Workflow model defining steps.
            execution_state: Current execution state with history.
        """
        super().__init__(
            state=None,
            pos=Point(x=0, y=0),
            pos_policy=None,
            size=Size(width=0, height=0),
            width_policy=SizePolicy.EXPANDING,
            height_policy=SizePolicy.FIXED,
        )
        self._height_val = 120
        self._size.height = self._height_val

        self._workflow = workflow
        self._execution_state = execution_state

        # Timeline view state
        self._time_scale = 1.0  # pixels per millisecond
        self._time_offset = 0.0  # time offset for scrolling
        self._lane_height = 24.0
        self._header_height = 24.0

        # Interaction state
        self._is_panning = False
        self._last_pan_x = 0.0
        self._hovered_execution: StepExecution | None = None
        self._selected_execution: StepExecution | None = None

        # Callbacks
        self._on_execution_select_cb: Callable[[StepExecution | None], None] | None = None
        self._on_event_select_cb: Callable[[str, float], None] | None = None

        # Recalculate height based on workflow
        if self._workflow is not None:
            self._recalculate_height()

    # ========== Configuration ==========

    def set_workflow(self, workflow: WorkflowModel | None) -> Self:
        """Update the workflow model.

        Args:
            workflow: New workflow model.

        Returns:
            Self for method chaining.
        """
        self._workflow = workflow
        self._recalculate_height()
        self.mark_paint_dirty()
        self.update()
        return self

    def set_execution_state(self, state: WorkflowExecutionState | None) -> Self:
        """Update execution state.

        Args:
            state: New execution state.

        Returns:
            Self for method chaining.
        """
        self._execution_state = state
        self._auto_fit_time_range()
        self.mark_paint_dirty()
        self.update()
        return self

    def on_execution_select(
        self, callback: Callable[[StepExecution | None], None]
    ) -> Self:
        """Set callback for execution selection.

        Args:
            callback: Function called with selected StepExecution.

        Returns:
            Self for method chaining.
        """
        self._on_execution_select_cb = callback
        return self

    def on_event_select(
        self, callback: Callable[[str, float], None]
    ) -> Self:
        """Set callback for event marker selection.

        Args:
            callback: Function called with (event_type, timestamp).

        Returns:
            Self for method chaining.
        """
        self._on_event_select_cb = callback
        return self

    # ========== Layout ==========

    def _recalculate_height(self) -> None:
        """Recalculate timeline height based on number of steps."""
        if self._workflow is None:
            lane_count = 1
        else:
            # +2 for START and END lanes
            lane_count = max(1, len(self._workflow.steps) + 2)

        self._height_val = self._header_height + lane_count * self._lane_height + 10
        self._size.height = self._height_val

    def _auto_fit_time_range(self) -> None:
        """Auto-fit the time scale to show all execution."""
        if self._execution_state is None:
            return

        if not self._execution_state.step_history:
            return

        size = self.get_size()
        if size.width <= 0:
            return

        # Find time range
        max_time = self._execution_state.current_time_ms
        if max_time <= 0:
            return

        # Calculate scale to fit (with padding)
        available_width = size.width - 80  # Left margin for labels
        self._time_scale = available_width / max_time if max_time > 0 else 1.0
        self._time_offset = 0

    # ========== Rendering ==========

    def redraw(self, p: Painter, completely: bool) -> None:
        """Render the timeline.

        Args:
            p: Painter for drawing.
            completely: Whether to do a complete redraw.
        """
        size = self.get_size()
        if size.width <= 0 or size.height <= 0:
            return

        # Draw background
        p.style(Style(fill=FillStyle(color=TIMELINE_BG_COLOR)))
        p.fill_rect(Rect(origin=Point(x=0, y=0), size=size))

        # Draw lanes
        self._draw_lanes(p, size)

        # Draw time axis
        self._draw_time_axis(p, size)

        # Draw execution bars and event markers
        if self._execution_state:
            self._draw_executions(p, size)

        # Draw border
        p.style(Style(stroke=StrokeStyle(color=LANE_BORDER_COLOR, width=1)))
        p.stroke_rect(Rect(origin=Point(x=0, y=0), size=size))

    def _draw_lanes(self, p: Painter, size: Size) -> None:
        """Draw step lanes with labels.

        Args:
            p: Painter for drawing.
            size: Widget size.
        """
        if self._workflow is None:
            return

        label_width = 70
        y = self._header_height

        # Build lane list: START + steps + END
        lanes = [("__start__", "START")] + \
                [(step.id, step.label) for step in self._workflow.steps] + \
                [("__end__", "END")]

        for i, (lane_id, lane_label) in enumerate(lanes):
            # Alternate lane background
            lane_color = LANE_BG_COLOR if i % 2 == 0 else LANE_ALT_BG_COLOR
            p.style(Style(fill=FillStyle(color=lane_color)))
            p.fill_rect(Rect(
                origin=Point(x=0, y=y),
                size=Size(width=size.width, height=self._lane_height),
            ))

            # Lane border (horizontal line using thin rect)
            p.style(Style(fill=FillStyle(color=LANE_BORDER_COLOR)))
            p.fill_rect(Rect(
                origin=Point(x=0, y=y + self._lane_height),
                size=Size(width=size.width, height=1),
            ))

            # Step label - use different color for START/END
            if lane_id == "__start__":
                label_color = EVENT_COLORS[EventCategory.START]
            elif lane_id == "__end__":
                label_color = EVENT_COLORS[EventCategory.STOP]
            else:
                label_color = "#9ca3af"

            p.style(Style(
                fill=FillStyle(color=label_color),
                font=Font(size=10),
            ))

            # Truncate label if needed
            label = lane_label
            while p.measure_text(label) > label_width - 10 and len(label) > 3:
                label = label[:-4] + "..."

            p.fill_text(
                label,
                Point(x=5, y=y + self._lane_height / 2 + 4),
                None,
            )

            y += self._lane_height

        # Label column border (vertical line using thin rect)
        p.style(Style(fill=FillStyle(color=LANE_BORDER_COLOR)))
        p.fill_rect(Rect(
            origin=Point(x=label_width, y=self._header_height),
            size=Size(width=1, height=size.height - self._header_height),
        ))

    def _draw_time_axis(self, p: Painter, size: Size) -> None:
        """Draw time axis with tick marks.

        Args:
            p: Painter for drawing.
            size: Widget size.
        """
        label_width = 70

        # Draw header background
        p.style(Style(fill=FillStyle(color=LANE_ALT_BG_COLOR)))
        p.fill_rect(Rect(
            origin=Point(x=0, y=0),
            size=Size(width=size.width, height=self._header_height),
        ))

        # Calculate tick interval
        if self._time_scale <= 0:
            return

        # Choose appropriate tick interval
        pixels_per_tick = 50
        time_per_tick = pixels_per_tick / self._time_scale

        # Round to nice values
        if time_per_tick <= 100:
            tick_interval = 100  # 100ms
        elif time_per_tick <= 500:
            tick_interval = 500  # 500ms
        elif time_per_tick <= 1000:
            tick_interval = 1000  # 1s
        elif time_per_tick <= 5000:
            tick_interval = 5000  # 5s
        else:
            tick_interval = 10000  # 10s

        # Draw ticks
        p.style(Style(
            fill=FillStyle(color=TIME_AXIS_COLOR),
            font=Font(size=9),
        ))

        start_time = int(self._time_offset / tick_interval) * tick_interval
        max_time = self._time_offset + (size.width - label_width) / self._time_scale

        t = start_time
        while t <= max_time:
            x = label_width + (t - self._time_offset) * self._time_scale

            if x >= label_width and x <= size.width:
                # Tick mark (vertical line using thin rect)
                p.style(Style(fill=FillStyle(color=TIME_AXIS_COLOR)))
                p.fill_rect(Rect(
                    origin=Point(x=x, y=self._header_height - 5),
                    size=Size(width=1, height=5),
                ))

                # Time label
                p.style(Style(fill=FillStyle(color="#6b7280"), font=Font(size=9)))
                if tick_interval >= 1000:
                    label = f"{t / 1000:.1f}s"
                else:
                    label = f"{int(t)}ms"

                text_width = p.measure_text(label)
                p.fill_text(label, Point(x=x - text_width / 2, y=self._header_height - 8), None)

            t += tick_interval

        # Header bottom border (horizontal line using thin rect)
        p.style(Style(fill=FillStyle(color=LANE_BORDER_COLOR)))
        p.fill_rect(Rect(
            origin=Point(x=0, y=self._header_height),
            size=Size(width=size.width, height=1),
        ))

    def _draw_executions(self, p: Painter, size: Size) -> None:
        """Draw execution bars and event markers.

        Args:
            p: Painter for drawing.
            size: Widget size.
        """
        if self._workflow is None or self._execution_state is None:
            return

        label_width = 70

        # Build step index map: START=0, steps=1..N, END=N+1
        step_indices: dict[str, int] = {"__start__": 0}
        for i, step in enumerate(self._workflow.steps):
            step_indices[step.id] = i + 1
        step_indices["__end__"] = len(self._workflow.steps) + 1

        for execution in self._execution_state.step_history:
            step_idx = step_indices.get(execution.node_id)
            if step_idx is None:
                continue

            # Calculate position
            lane_y = self._header_height + step_idx * self._lane_height

            # Calculate time position
            start_time = execution.started_at_ms - self._execution_state.start_time_ms
            end_time = start_time + execution.duration_ms

            start_x = label_width + (start_time - self._time_offset) * self._time_scale
            end_x = label_width + (end_time - self._time_offset) * self._time_scale

            # Skip if outside visible range
            if end_x < label_width or start_x > size.width:
                continue

            # Clamp to visible range
            start_x = max(label_width, start_x)
            end_x = min(size.width, end_x)

            bar_width = max(4, end_x - start_x)
            bar_height = self._lane_height - 8
            bar_y = lane_y + 4

            # Determine color
            is_selected = execution == self._selected_execution
            is_hovered = execution == self._hovered_execution

            if execution.error:
                bar_color = ERROR_BAR_COLOR
            else:
                bar_color = EXECUTION_BAR_COLOR

            if is_hovered or is_selected:
                # Lighten color
                bar_color = self._lighten_color(bar_color, 0.2)

            # Draw execution bar
            p.style(Style(
                fill=FillStyle(color=bar_color),
                border_radius=3,
            ))
            p.fill_rect(Rect(
                origin=Point(x=start_x, y=bar_y),
                size=Size(width=bar_width, height=bar_height),
            ))

            # Draw border if selected
            if is_selected:
                p.style(Style(
                    stroke=StrokeStyle(color="#ffffff", width=2),
                    border_radius=3,
                ))
                p.stroke_rect(Rect(
                    origin=Point(x=start_x, y=bar_y),
                    size=Size(width=bar_width, height=bar_height),
                ))

            # Draw input event marker at start
            if execution.input_event_type:
                event_color = self._get_event_color(execution.input_event_type)
                marker_x = start_x
                marker_y = lane_y + self._lane_height / 2

                # Event marker circle
                p.style(Style(fill=FillStyle(color=event_color)))
                p.fill_circle(Circle(
                    center=Point(x=marker_x, y=marker_y),
                    radius=4,
                ))

                # White border
                p.style(Style(stroke=StrokeStyle(color=EVENT_MARKER_BORDER, width=1)))
                p.stroke_circle(Circle(
                    center=Point(x=marker_x, y=marker_y),
                    radius=4,
                ))

            # Draw output event marker at end
            if execution.output_event_type:
                event_color = self._get_event_color(execution.output_event_type)
                marker_x = end_x
                marker_y = lane_y + self._lane_height / 2

                # Event marker circle
                p.style(Style(fill=FillStyle(color=event_color)))
                p.fill_circle(Circle(
                    center=Point(x=marker_x, y=marker_y),
                    radius=4,
                ))

                # White border
                p.style(Style(stroke=StrokeStyle(color=EVENT_MARKER_BORDER, width=1)))
                p.stroke_circle(Circle(
                    center=Point(x=marker_x, y=marker_y),
                    radius=4,
                ))

    def _get_event_color(self, event_type: str) -> str:
        """Get color for an event type.

        Args:
            event_type: Event type name.

        Returns:
            Color hex string.
        """
        if self._workflow is None:
            return EVENT_COLORS[EventCategory.USER]

        event_model = self._workflow.event_types.get(event_type)
        if event_model:
            return event_model.get_color()

        if event_type == "StartEvent" or event_type == self._workflow.start_event_type:
            return EVENT_COLORS[EventCategory.START]
        elif event_type == "StopEvent" or event_type == self._workflow.stop_event_type:
            return EVENT_COLORS[EventCategory.STOP]

        return EVENT_COLORS[EventCategory.USER]

    def _lighten_color(self, color: str, amount: float) -> str:
        """Lighten a hex color.

        Args:
            color: Hex color string.
            amount: Amount to lighten (0-1).

        Returns:
            Lightened hex color.
        """
        # Parse hex color
        color = color.lstrip("#")
        r = int(color[0:2], 16)
        g = int(color[2:4], 16)
        b = int(color[4:6], 16)

        # Lighten
        r = min(255, int(r + (255 - r) * amount))
        g = min(255, int(g + (255 - g) * amount))
        b = min(255, int(b + (255 - b) * amount))

        return f"#{r:02x}{g:02x}{b:02x}"

    # ========== Mouse Events ==========

    def mouse_down(self, ev: MouseEvent) -> None:
        """Handle mouse button press."""
        # Check if clicking on an execution bar
        execution = self._hit_test_execution(ev.pos)
        if execution:
            self._selected_execution = execution
            if self._on_execution_select_cb:
                self._on_execution_select_cb(execution)
        else:
            # Start panning
            self._is_panning = True
            self._last_pan_x = ev.pos.x

        self.mark_paint_dirty()
        self.update()

    def mouse_up(self, ev: MouseEvent) -> None:
        """Handle mouse button release."""
        self._is_panning = False

    def mouse_drag(self, ev: MouseEvent) -> None:
        """Handle mouse drag for panning."""
        if self._is_panning:
            delta_x = ev.pos.x - self._last_pan_x
            self._time_offset -= delta_x / self._time_scale
            self._time_offset = max(0, self._time_offset)
            self._last_pan_x = ev.pos.x
            self.mark_paint_dirty()
            self.update()

    def cursor_pos(self, ev: MouseEvent) -> None:
        """Handle mouse movement for hover detection."""
        if self._is_panning:
            return

        execution = self._hit_test_execution(ev.pos)
        if execution != self._hovered_execution:
            self._hovered_execution = execution
            self.mark_paint_dirty()
            self.update()

    def mouse_wheel(self, ev: WheelEvent) -> None:
        """Handle mouse wheel for time zoom."""
        # Zoom factor
        factor = 1.2 if ev.y_offset > 0 else 0.8

        # Get time at mouse position
        label_width = 70
        time_at_mouse = (ev.pos.x - label_width) / self._time_scale + self._time_offset

        # Apply zoom
        self._time_scale *= factor
        self._time_scale = max(0.01, min(10.0, self._time_scale))

        # Adjust offset to keep time at mouse position
        self._time_offset = time_at_mouse - (ev.pos.x - label_width) / self._time_scale
        self._time_offset = max(0, self._time_offset)

        self.mark_paint_dirty()
        self.update()

    def _hit_test_execution(self, pos: Point) -> StepExecution | None:
        """Hit test for execution bars.

        Args:
            pos: Mouse position.

        Returns:
            StepExecution if hit, None otherwise.
        """
        if self._workflow is None or self._execution_state is None:
            return None

        label_width = 70

        # Check if in lanes area
        if pos.x < label_width or pos.y < self._header_height:
            return None

        # Build step index map: START=0, steps=1..N, END=N+1
        step_indices: dict[str, int] = {"__start__": 0}
        for i, step in enumerate(self._workflow.steps):
            step_indices[step.id] = i + 1
        step_indices["__end__"] = len(self._workflow.steps) + 1

        for execution in self._execution_state.step_history:
            step_idx = step_indices.get(execution.node_id)
            if step_idx is None:
                continue

            lane_y = self._header_height + step_idx * self._lane_height

            # Check Y
            if not (lane_y + 4 <= pos.y <= lane_y + self._lane_height - 4):
                continue

            # Calculate X range
            start_time = execution.started_at_ms - self._execution_state.start_time_ms
            end_time = start_time + execution.duration_ms

            start_x = label_width + (start_time - self._time_offset) * self._time_scale
            end_x = label_width + (end_time - self._time_offset) * self._time_scale

            # Check X
            if start_x <= pos.x <= max(end_x, start_x + 4):
                return execution

        return None

    # ========== Public Methods ==========

    def zoom_in(self) -> None:
        """Zoom in on the timeline."""
        size = self.get_size()
        center_time = self._time_offset + (size.width / 2 - 70) / self._time_scale

        self._time_scale *= 1.2
        self._time_scale = min(10.0, self._time_scale)

        # Adjust offset to keep center
        self._time_offset = center_time - (size.width / 2 - 70) / self._time_scale
        self._time_offset = max(0, self._time_offset)

        self.mark_paint_dirty()
        self.update()

    def zoom_out(self) -> None:
        """Zoom out on the timeline."""
        size = self.get_size()
        center_time = self._time_offset + (size.width / 2 - 70) / self._time_scale

        self._time_scale *= 0.8
        self._time_scale = max(0.01, self._time_scale)

        # Adjust offset to keep center
        self._time_offset = center_time - (size.width / 2 - 70) / self._time_scale
        self._time_offset = max(0, self._time_offset)

        self.mark_paint_dirty()
        self.update()

    def fit_to_content(self) -> None:
        """Fit timeline to show all execution history."""
        self._auto_fit_time_range()
        self.mark_paint_dirty()
        self.update()

    def scroll_to_time(self, time_ms: float) -> None:
        """Scroll to a specific time.

        Args:
            time_ms: Time in milliseconds to scroll to.
        """
        size = self.get_size()
        label_width = 70
        center_offset = (size.width - label_width) / 2 / self._time_scale

        self._time_offset = max(0, time_ms - center_offset)
        self.mark_paint_dirty()
        self.update()

    @property
    def selected_execution(self) -> StepExecution | None:
        """Get the currently selected execution."""
        return self._selected_execution

    def clear_selection(self) -> None:
        """Clear the current selection."""
        self._selected_execution = None
        if self._on_execution_select_cb:
            self._on_execution_select_cb(None)
        self.mark_paint_dirty()
        self.update()
