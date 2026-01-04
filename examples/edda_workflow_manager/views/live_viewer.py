"""Live viewer for real-time workflow monitoring."""

from __future__ import annotations

from typing import TYPE_CHECKING, Callable

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
from castella.graph.canvas import GraphCanvas
from castella.graph.transform import CanvasTransform

from edda_workflow_manager.models.instance import WorkflowInstance
from edda_workflow_manager.models.execution import EddaExecutionState
from edda_workflow_manager.data.graph_builder import WorkflowGraphBuilder

if TYPE_CHECKING:
    pass


class LiveViewer(Component):
    """Real-time workflow execution viewer.

    Similar to the LlamaIndex Studio but connected to Edda database
    with fast polling for live updates.

    ```
    ┌─────────────────────────────────────────────────────────────┐
    │  [Select Instance ▼]  [Stop] [Refresh]  Polling: 1s        │
    ├─────────┬───────────────────────────────┬───────────────────┤
    │ Running │      Workflow Graph           │   Live Status     │
    │ ● inst1 │   ┌──────────────┐            │                   │
    │ ● inst2 │   │ receive_order│ ✓          │   Instance: abc   │
    │ ○ inst3 │   └──────┬───────┘            │   Step: 2/3       │
    │         │          │                    │   Current: proc   │
    │         │   ┌──────┴───────┐            │                   │
    │         │   │process_payment│ ●         │   Duration: 5.2s  │
    │         │   └──────────────┘            │                   │
    ├─────────┴───────────────────────────────┴───────────────────┤
    │  Status: Running | Step 2/3 | Activity: process_payment    │
    └─────────────────────────────────────────────────────────────┘
    ```
    """

    def __init__(
        self,
        running_instances: list[WorkflowInstance] | None = None,
        selected_instance: WorkflowInstance | None = None,
        execution_state: EddaExecutionState | None = None,
        workflow_template: list[str] | None = None,
        on_select_instance: Callable[[str], None] | None = None,
        on_stop: Callable[[str], None] | None = None,
        on_refresh: Callable[[], None] | None = None,
    ):
        """Initialize live viewer.

        Args:
            running_instances: List of currently running instances.
            selected_instance: Currently selected instance.
            execution_state: Execution state of selected instance.
            workflow_template: List of activity names from historical executions.
            on_select_instance: Callback when instance is selected.
            on_stop: Callback to stop an instance.
            on_refresh: Callback for refresh.
        """
        super().__init__()
        self._running_instances = running_instances or []
        self._selected_instance = selected_instance
        self._execution_state = execution_state
        self._workflow_template = workflow_template or []
        self._on_select_instance = on_select_instance
        self._on_stop = on_stop
        self._on_refresh = on_refresh

        # Canvas transform
        self._canvas_transform = CanvasTransform()

        # Graph builder
        self._graph_builder = WorkflowGraphBuilder()

    def view(self):
        """Build the live viewer."""
        return Column(
            # Toolbar
            self._build_toolbar(),

            # Main content
            Row(
                # Left: Running instances list
                self._build_instance_list(),

                # Center: Graph canvas
                self._build_canvas(),

                # Right: Live status
                self._build_status_panel(),
            ).height_policy(SizePolicy.EXPANDING),

            # Status bar
            (
                StatusBar(self._execution_state)
                if self._execution_state
                else Spacer().fixed_height(28)
            ),
        ).bg_color("#1a1b26")

    def _build_toolbar(self) -> Row:
        """Build the toolbar."""
        instance = self._selected_instance

        return (
            Row(
                # Instance selector label
                Text("Selected:")
                .fixed_width(70)
                .text_color("#9ca3af"),

                Text(
                    instance.short_instance_id if instance else "None"
                )
                .fixed_width(150)
                .text_color("#c0caf5"),

                Spacer().fixed_width(16),

                # Stop button
                Button("Stop")
                .kind(Kind.DANGER)
                .fixed_height(32)
                .on_click(
                    lambda _: (
                        self._on_stop(instance.instance_id)
                        if self._on_stop and instance
                        else None
                    )
                ),

                Spacer().fixed_width(16),

                # Refresh button
                Button("Refresh")
                .fixed_height(32)
                .on_click(
                    lambda _: self._on_refresh() if self._on_refresh else None
                ),

                Spacer(),

                # Polling indicator
                Text("Polling: 1s")
                .fixed_width(100)
                .text_color("#9ece6a"),
            )
            .fixed_height(48)
            .bg_color("#1e1f2b")
        )

    def _build_instance_list(self) -> Column:
        """Build the running instances list."""
        items = []

        # Header
        items.append(
            Text("Running Instances")
            .fixed_height(28)
            .text_color("#bb9af7")
        )

        if not self._running_instances:
            items.append(
                Text("No running instances")
                .fixed_height(32)
                .text_color("#6b7280")
            )
        else:
            for inst in self._running_instances[:20]:
                is_selected = (
                    self._selected_instance
                    and self._selected_instance.instance_id == inst.instance_id
                )
                items.append(self._build_instance_item(inst, is_selected))

        return (
            Column(*items, scrollable=True)
            .fixed_width(200)
            .height_policy(SizePolicy.EXPANDING)
            .bg_color("#1a1b26")
        )

    def _build_instance_item(
        self, instance: WorkflowInstance, is_selected: bool
    ) -> Row:
        """Build a single instance item."""
        status = instance.status

        if status.value == "running":
            icon = "●"
            color = "#9ece6a"
        elif status.is_waiting:
            icon = "◎"
            color = "#e0af68"
        else:
            icon = "○"
            color = "#6b7280"

        bg_color = "#2a2b3d" if is_selected else "#1e1f2b"

        # Use Button for clickable item
        label = f"{icon} {instance.short_instance_id}"
        return (
            Button(label)
            .fixed_height(28)
            .bg_color(bg_color)
            .text_color("#c0caf5")
            .on_click(
                lambda _, iid=instance.instance_id: (
                    self._on_select_instance(iid)
                    if self._on_select_instance
                    else None
                )
            )
        )

    def _build_canvas(self) -> GraphCanvas:
        """Build the graph canvas."""
        # If we have a workflow template, use it for the full graph
        if self._workflow_template:
            if self._execution_state:
                # Combine template with execution progress
                graph = self._graph_builder.build_from_execution_state_with_template(
                    self._execution_state,
                    self._workflow_template,
                )
            else:
                # Show template graph before execution starts
                workflow_name = (
                    self._selected_instance.workflow_name
                    if self._selected_instance
                    else "Workflow"
                )
                graph = self._graph_builder.build_from_template(
                    self._workflow_template,
                    workflow_name,
                )
        elif self._execution_state:
            # Fallback: build from execution history only
            graph = self._graph_builder.build_from_execution_state(
                self._execution_state
            )
        else:
            # No template or execution state
            return (
                Column(
                    Text("Select an instance to view").text_color("#6b7280"),
                )
                .width_policy(SizePolicy.EXPANDING)
                .height_policy(SizePolicy.EXPANDING)
            )

        canvas = GraphCanvas(graph, transform=self._canvas_transform)
        canvas.width_policy(SizePolicy.EXPANDING)
        canvas.height_policy(SizePolicy.EXPANDING)

        return canvas

    def _build_status_panel(self) -> Column:
        """Build the live status panel."""
        instance = self._selected_instance
        execution = self._execution_state

        if not instance:
            return (
                Column(
                    Text("No instance selected").text_color("#6b7280"),
                )
                .fixed_width(250)
                .height_policy(SizePolicy.EXPANDING)
                .bg_color("#1e1f2b")
            )

        # Status color
        status = instance.status
        if status.value == "running":
            status_color = "#9ece6a"
        elif status.value == "completed":
            status_color = "#7aa2f7"
        elif status.value == "failed":
            status_color = "#f7768e"
        else:
            status_color = "#e0af68"

        return (
            Column(
                Text("Live Status").text_color("#bb9af7").fixed_height(28),

                Spacer().fixed_height(8),

                Text(f"Instance: {instance.short_instance_id}")
                .text_color("#c0caf5"),

                Text(f"Workflow: {instance.workflow_name}")
                .text_color("#9ca3af"),

                Text(f"Status: {status.display_name}")
                .text_color(status_color),

                Spacer().fixed_height(16),

                (
                    Column(
                        Text(f"Step: {execution.total_steps}")
                        .text_color("#c0caf5"),
                        Text(
                            f"Current: {execution.current_activity_name or 'None'}"
                        ).text_color("#9ca3af"),
                    )
                    if execution
                    else Spacer().fixed_height(1)
                ),

                Spacer().fixed_height(16),

                Text(f"Duration: {instance.duration_display}")
                .text_color("#9ca3af"),

                Spacer(),
            )
            .fixed_width(250)
            .height_policy(SizePolicy.EXPANDING)
            .bg_color("#1e1f2b")
        )
