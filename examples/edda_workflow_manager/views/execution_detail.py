"""Execution detail view for Edda Workflow Manager."""

from __future__ import annotations

from typing import TYPE_CHECKING, Callable, Any

from castella import (
    Component,
    Column,
    Row,
    Box,
    Button,
    Text,
    Spacer,
    State,
    Kind,
    SizePolicy,
)
from castella.studio.components.status_bar import StatusBar
from castella.studio.components.content_viewer_modal import ContentViewerModal
from castella.graph.models import GraphModel
from castella.graph.canvas import GraphCanvas
from castella.graph.transform import CanvasTransform

from edda_workflow_manager.models.instance import (
    WorkflowInstance,
    ActivityHistory,
)
from edda_workflow_manager.models.execution import EddaExecutionState
from edda_workflow_manager.data.graph_builder import WorkflowGraphBuilder

if TYPE_CHECKING:
    pass


class ExecutionDetailView(Component):
    """Detailed view of a single workflow execution.

    ```
    ┌─────────────────────────────────────────────────────────────┐
    │  [← Back]  Instance: abc-123  Status: ● Running            │
    ├────────────────────────────┬────────────────────────────────┤
    │   Workflow Graph           │  [Details] [Timeline] [I/O]   │
    │   ┌──────────────┐         │                               │
    │   │ receive_order│ ✓       │  Step: process_payment        │
    │   └──────┬───────┘         │  Status: Running              │
    │          │                 │  Duration: 5.2s               │
    │   ┌──────┴───────┐         │                               │
    │   │process_payment│ ●      │  Input:                       │
    │   └──────┬───────┘         │  {"order_id": "123"}          │
    │          │                 │                               │
    │   ┌──────┴───────┐         │  Output:                      │
    │   │send_confirm  │ ○       │  (pending)                    │
    │   └──────────────┘         │                               │
    ├────────────────────────────┴────────────────────────────────┤
    │  Status: Running | Step 2/3 | Activity: process_payment    │
    └─────────────────────────────────────────────────────────────┘
    ```
    """

    def __init__(
        self,
        instance: WorkflowInstance | None = None,
        history: list[ActivityHistory] | None = None,
        execution_state: EddaExecutionState | None = None,
        on_back: Callable[[], None] | None = None,
        on_cancel: Callable[[], None] | None = None,
        on_step_select: Callable[[str], None] | None = None,
    ):
        """Initialize execution detail view.

        Args:
            instance: Workflow instance.
            history: Activity history.
            execution_state: Execution state for visualization.
            on_back: Callback for back button.
            on_cancel: Callback for cancel button.
            on_step_select: Callback when step is selected.
        """
        super().__init__()
        self._instance = instance
        self._history = history or []
        self._execution_state = execution_state
        self._on_back = on_back
        self._on_cancel = on_cancel
        self._on_step_select = on_step_select

        # Selected step
        self._selected_step: State[str | None] = State(None)
        self._selected_step.attach(self)

        # Right panel tab
        self._right_tab: State[str] = State("details")
        self._right_tab.attach(self)

        # Canvas transform (persist zoom/pan)
        self._canvas_transform = CanvasTransform()

        # Content viewer modal
        self._content_modal = ContentViewerModal()
        self._content_modal.attach(self)

        # Graph builder
        self._graph_builder = WorkflowGraphBuilder()

    def view(self):
        """Build the execution detail view."""
        instance = self._instance
        execution = self._execution_state

        if not instance:
            return Column(
                Text("Instance not found").text_color("#f7768e"),
            ).bg_color("#1a1b26")

        main_content = Column(
            # Header
            self._build_header(instance),

            # Main content
            Row(
                # Left: Graph canvas
                self._build_canvas(),

                # Right: Detail panels
                self._build_right_panel(),
            ).height_policy(SizePolicy.EXPANDING),

            # Status bar
            StatusBar(execution) if execution else Spacer().fixed_height(28),
        )

        # Add modal if open
        if self._content_modal.is_open:
            return Box(main_content, self._content_modal.build())

        return main_content

    def _build_header(self, instance: WorkflowInstance) -> Row:
        """Build the header row."""
        # Status indicator
        status = instance.status
        if status.value == "running":
            status_color = "#9ece6a"
            status_icon = "●"
        elif status.value == "completed":
            status_color = "#7aa2f7"
            status_icon = "✓"
        elif status.value == "failed":
            status_color = "#f7768e"
            status_icon = "✗"
        elif status.is_waiting:
            status_color = "#e0af68"
            status_icon = "◎"
        else:
            status_color = "#6b7280"
            status_icon = "○"

        return (
            Row(
                # Back button
                Button("← Back")
                .fixed_height(32)
                .on_click(lambda _: self._on_back() if self._on_back else None),

                Spacer().fixed_width(16),

                # Instance info
                Text(f"Instance: {instance.short_instance_id}")
                .fixed_width(200)
                .text_color("#c0caf5"),

                Text(f"Workflow: {instance.workflow_name}")
                .fixed_width(200)
                .text_color("#9ca3af"),

                Text(f"{status_icon} {status.display_name}")
                .fixed_width(150)
                .text_color(status_color),

                Spacer(),

                # Cancel button (only for running/waiting)
                (
                    Button("Cancel")
                    .kind(Kind.DANGER)
                    .fixed_height(32)
                    .on_click(lambda _: self._on_cancel() if self._on_cancel else None)
                    if not status.is_terminal
                    else Spacer().fixed_width(1)
                ),
            )
            .fixed_height(52)
            .bg_color("#1e1f2b")
        )

    def _build_canvas(self) -> GraphCanvas:
        """Build the graph canvas."""
        # Build graph from execution state
        graph: GraphModel | None = None
        if self._execution_state:
            graph = self._graph_builder.build_from_execution_state(
                self._execution_state
            )
        elif self._history:
            graph = self._graph_builder.build_from_history(
                self._instance.workflow_name if self._instance else "Workflow",
                self._history,
            )

        if not graph:
            return (
                Text("No workflow data")
                .text_color("#6b7280")
                .width_policy(SizePolicy.EXPANDING)
                .height_policy(SizePolicy.EXPANDING)
            )

        canvas = GraphCanvas(graph, transform=self._canvas_transform)
        canvas.on_node_click(self._on_node_click)
        canvas.width_policy(SizePolicy.EXPANDING)
        canvas.height_policy(SizePolicy.EXPANDING)

        # Set selected node for highlighting
        selected = self._selected_step()
        if selected:
            canvas.selected_node_id = selected

        return canvas

    def _build_right_panel(self) -> Column:
        """Build the right detail panel."""
        tab = self._right_tab()

        return (
            Column(
                # Tab buttons
                Row(
                    self._build_tab_button("details", "Details"),
                    self._build_tab_button("timeline", "Timeline"),
                    self._build_tab_button("io", "I/O"),
                    Spacer(),
                ).fixed_height(36),

                # Tab content
                self._build_tab_content(tab),
            )
            .fixed_width(300)
            .height_policy(SizePolicy.EXPANDING)
            .bg_color("#1e1f2b")
        )

    def _build_tab_button(self, tab_id: str, label: str) -> Button:
        """Build a tab button."""
        is_active = self._right_tab() == tab_id
        kind = Kind.INFO if is_active else Kind.NORMAL

        return (
            Button(label)
            .kind(kind)
            .fixed_height(28)
            .fixed_width(80)
            .on_click(lambda _, tid=tab_id: self._right_tab.set(tid))
        )

    def _build_tab_content(self, tab_id: str) -> Column:
        """Build content for the selected tab."""
        if tab_id == "details":
            return self._build_details_panel()
        elif tab_id == "timeline":
            return self._build_timeline_panel()
        elif tab_id == "io":
            return self._build_io_panel()
        else:
            return Column(Text("Unknown tab"))

    def _build_details_panel(self) -> Column:
        """Build the details panel."""
        selected = self._selected_step()
        if not selected:
            return Column(
                Text("Select a step to view details")
                .text_color("#6b7280"),
            ).height_policy(SizePolicy.EXPANDING)

        # Find the selected step in execution state
        step = None
        if self._execution_state:
            for s in self._execution_state.step_history:
                if s.node_id == selected or getattr(s, 'activity_name', '') == selected:
                    step = s
                    break

        if not step:
            return Column(
                Text(f"Step: {selected}").text_color("#c0caf5"),
                Text("No execution data yet").text_color("#6b7280"),
            ).height_policy(SizePolicy.EXPANDING)

        # Status color based on error
        if step.error:
            status_color = "#f7768e"
            status_text = "Failed"
        else:
            status_color = "#9ece6a"
            status_text = "Completed"

        # Get metadata
        metadata = step.metadata or {}
        event_type = getattr(step, 'event_type', 'Unknown')

        items = [
            Text(f"Step: {selected}").text_color("#bb9af7"),
            Spacer().fixed_height(8),
            Text(f"Status: {status_text}").text_color(status_color),
            Text(f"Event: {event_type}").text_color("#9ca3af"),
        ]

        if step.error:
            items.append(Spacer().fixed_height(16))
            items.append(Text("Error:").text_color("#f7768e"))
            items.append(Text(step.error).text_color("#f7768e"))

        return Column(*items).height_policy(SizePolicy.EXPANDING)

    def _build_timeline_panel(self) -> Column:
        """Build the timeline panel."""
        step_history = self._execution_state.step_history if self._execution_state else []

        if not step_history:
            return Column(
                Text("No execution history").text_color("#6b7280"),
            ).height_policy(SizePolicy.EXPANDING)

        items = []
        for i, step in enumerate(step_history):
            # Status indicator
            if step.error:
                icon = "✗"
                color = "#f7768e"
            else:
                icon = "✓"
                color = "#9ece6a"

            activity_name = getattr(step, 'activity_name', step.node_id)
            items.append(
                Row(
                    Text(f"{i+1}. {icon}").fixed_width(40).text_color(color),
                    Text(activity_name).text_color("#c0caf5"),
                ).fixed_height(24)
            )

        return (
            Column(*items, scrollable=True)
            .height_policy(SizePolicy.EXPANDING)
        )

    def _build_io_panel(self) -> Column:
        """Build the I/O panel."""
        selected = self._selected_step()
        if not selected:
            return Column(
                Text("Select a step to view I/O").text_color("#6b7280"),
            ).height_policy(SizePolicy.EXPANDING)

        # Find the selected step in execution state
        step = None
        if self._execution_state:
            for s in self._execution_state.step_history:
                if s.node_id == selected or getattr(s, 'activity_name', '') == selected:
                    step = s
                    break

        if not step:
            return Column(
                Text("No I/O data").text_color("#6b7280"),
            ).height_policy(SizePolicy.EXPANDING)

        import json
        from castella.multiline_text import MultilineText

        # Get input/output from metadata
        metadata = step.metadata or {}
        input_data = metadata.get("input", {})
        output_data = metadata.get("output")

        input_str = json.dumps(input_data, indent=2, default=str)
        output_str = json.dumps(output_data, indent=2, default=str) if output_data else "null"

        return (
            Column(
                Text("Input:").text_color("#bb9af7").fixed_height(24),
                MultilineText(input_str, font_size=11, wrap=True)
                .text_color("#c0caf5")
                .bg_color("#1a1b26")
                .height_policy(SizePolicy.EXPANDING),
                Spacer().fixed_height(8),
                Text("Output:").text_color("#bb9af7").fixed_height(24),
                MultilineText(output_str, font_size=11, wrap=True)
                .text_color("#c0caf5")
                .bg_color("#1a1b26")
                .height_policy(SizePolicy.EXPANDING),
            )
            .height_policy(SizePolicy.EXPANDING)
        )

    def _on_node_click(self, node_id: str) -> None:
        """Handle node click on canvas."""
        if node_id not in ("__start__", "__end__"):
            self._selected_step.set(node_id)
            if self._on_step_select:
                self._on_step_select(node_id)
