"""Main LlamaIndex Workflow Studio component.

Provides the complete studio UI with workflow visualization,
execution controls, and detail panels.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from castella import (
    Component,
    Column,
    Row,
    Box,
    Text,
    Button,
    Spacer,
    State,
    SizePolicy,
    Kind,
)
from castella.tabs import Tabs, TabsState, TabItem

from castella.studio.components.toolbar import Toolbar
from castella.studio.components.status_bar import StatusBar
from castella.studio.components.file_panel import FilePanel
from castella.studio.components.content_viewer_modal import ContentViewerModal
from castella.studio.loader.module_loader import load_module, ModuleLoadError

from ..models.workflow import WorkflowModel
from ..models.execution import WorkflowExecutionState
from ..loader.workflow_extractor import (
    find_workflow_class,
    extract_workflow_model,
    WorkflowExtractionError,
)
from ..executor.runner import WorkflowExecutor
from ..widgets.workflow_canvas import WorkflowCanvas
from ..widgets.event_timeline import EventTimeline
from castella.graph.transform import CanvasTransform
from examples.llamaindex_studio.samples.mock_workflow import (
    create_mock_workflow,
    create_branching_mock_workflow,
    create_collect_mock_workflow,
)

from .event_panel import EventPanel, EventQueuePanel
from .step_panel import StepPanel, StepListPanel
from .context_inspector import ContextInspector


# Layout constants
LEFT_PANEL_WIDTH = 180
RIGHT_PANEL_WIDTH = 280
TOOLBAR_HEIGHT = 44
STATUS_BAR_HEIGHT = 28
TIMELINE_HEIGHT = 120


class WorkflowStudio(Component):
    """Main LlamaIndex Workflow Studio component.

    Layout:
    ```
    ┌─────────────────────────────────────────────────┐
    │  Toolbar [▶ Run] [⏸] [⏭ Step] [🔄] [Zoom]      │
    ├─────────┬───────────────────┬───────────────────┤
    │ Events  │   Workflow Canvas │   Right Panel     │
    │ ▶ Start │   ┌─────────┐     │   [State|Step|Hist]│
    │ ■ Stop  │   │ process │     │                   │
    │ ◆ Proc  │   └─────────┘     │   Step: process   │
    │ ◆ Valid │        │          │   in: StartEvent  │
    │         │        ▼          │   out: Processed  │
    │ Steps   │   ┌─────────┐     │                   │
    │ ⚡process│   │validate │     │   Context:        │
    │ ⚡valid  │   └─────────┘     │   {...}           │
    ├─────────┴───────────────────┴───────────────────┤
    │  Event Timeline ────●────────●────────●──────▶  │
    ├─────────────────────────────────────────────────┤
    │  Status: Running | Step 2/4 | ProcessedEvent    │
    └─────────────────────────────────────────────────┘
    ```
    """

    def __init__(
        self,
        samples_dir: str = ".",
        initial_file: str | None = None,
    ):
        """Initialize the workflow studio.

        Args:
            samples_dir: Directory containing workflow files.
            initial_file: Optional initial file to load.
        """
        super().__init__()

        self._samples_dir = samples_dir

        # State
        self._workflow_model: State[WorkflowModel | None] = State(None)
        self._execution_state: State[WorkflowExecutionState] = State(
            WorkflowExecutionState()
        )
        self._workflow_class: State[type | None] = State(None)
        self._zoom_percent: State[int] = State(100)
        self._error_message: State[str | None] = State(None)

        # Selection state
        self._selected_step_id: State[str | None] = State(None)
        self._selected_event_type: State[str | None] = State(None)

        # Current workflow type ("mock", "simple", "complex")
        self._current_workflow_type: State[str] = State("mock")

        # Right panel tab state
        self._right_panel_tabs = TabsState([
            TabItem(id="step", label="Step", content=Spacer()),
            TabItem(id="context", label="Context", content=Spacer()),
            TabItem(id="queue", label="Queue", content=Spacer()),
        ], selected_id="step")

        # Attach states
        self._workflow_model.attach(self)
        self._execution_state.attach(self)
        self._zoom_percent.attach(self)  # For toolbar display updates
        self._error_message.attach(self)
        self._selected_step_id.attach(self)
        self._selected_event_type.attach(self)
        self._current_workflow_type.attach(self)
        self._right_panel_tabs.attach(self)

        # Executor
        self._executor = WorkflowExecutor(
            on_state_update=self._on_execution_update
        )

        # Canvas transform state (persists across view rebuilds)
        self._canvas_transform = CanvasTransform()

        # Double-click detection state (persists across view rebuilds)
        self._last_click_time: float = 0.0
        self._last_click_node_id: str | None = None
        self._double_click_threshold_ms: float = 400.0

        # Canvas reference (for zoom controls)
        self._canvas: WorkflowCanvas | None = None
        self._timeline: EventTimeline | None = None

        # Shared content viewer modal
        self._content_modal = ContentViewerModal()
        self._content_modal.attach(self)

        # Load initial file if provided, otherwise load mock workflow
        if initial_file:
            self._load_workflow_file(initial_file)
        else:
            # Load a mock workflow for demonstration
            self._load_mock_workflow("simple")

    def view(self):
        """Build the studio UI."""
        workflow = self._workflow_model()
        execution = self._execution_state()

        main_content = Column(
            # Toolbar (fixed height)
            self._build_toolbar(execution),
            # Main content area (fills remaining space)
            Row(
                # Left panel (Events & Steps)
                self._build_left_panel(workflow, execution),
                # Center (Canvas)
                self._build_canvas(workflow, execution),
                # Right panel (Details)
                self._build_right_panel(workflow, execution),
            ).height_policy(SizePolicy.EXPANDING),
            # Timeline (fixed height)
            self._build_timeline(workflow, execution),
            # Status bar (fixed height)
            self._build_status_bar(execution),
        )

        # Add content viewer modal if open
        if self._content_modal.is_open:
            return Box(main_content, self._content_modal.build())

        return main_content

    def _build_toolbar(self, execution: WorkflowExecutionState) -> Toolbar:
        """Build the toolbar component."""
        # Allow running if we have either a workflow class or a workflow model (mock)
        can_run = execution.can_run and (
            self._workflow_class() is not None or self._workflow_model() is not None
        )
        return Toolbar(
            can_run=can_run,
            can_stop=execution.can_stop,
            can_pause=execution.can_pause,
            can_continue=execution.can_continue,
            zoom_percent=self._zoom_percent(),
            on_run=self._on_run,
            on_step=self._on_step,
            on_pause=self._on_pause,
            on_continue=self._on_continue,
            on_stop=self._on_stop,
            on_reset=self._on_reset,
            on_zoom_in=self._on_zoom_in,
            on_zoom_out=self._on_zoom_out,
            on_fit=self._on_fit,
        )

    def _build_left_panel(
        self,
        workflow: WorkflowModel | None,
        execution: WorkflowExecutionState,
    ) -> Column:
        """Build the left panel with workflow selector, events and steps lists."""
        return Column(
            # Workflow selector
            self._build_workflow_selector(),
            # Divider
            Box().fixed_height(1).bg_color("#2a2b3d"),
            # Event types list
            EventPanel(
                workflow=workflow,
                selected_event=self._selected_event_type(),
                on_event_select=self._on_event_select,
            ).height_policy(SizePolicy.EXPANDING),
            # Divider (use Box for colored line)
            Box().fixed_height(1).bg_color("#2a2b3d"),
            # Steps list
            StepListPanel(
                steps=workflow.steps if workflow else [],
                active_step_ids=execution.active_step_ids,
                selected_step_id=self._selected_step_id(),
                on_step_select=self._on_step_select,
            ).height_policy(SizePolicy.EXPANDING),
        ).fixed_width(LEFT_PANEL_WIDTH).height_policy(SizePolicy.EXPANDING).bg_color("#1a1b26")

    def _build_workflow_selector(self) -> Column:
        """Build the workflow type selector."""
        current = self._current_workflow_type()

        def make_btn(wf_type: str, label: str) -> Button:
            is_selected = current == wf_type
            kind = Kind.INFO if is_selected else Kind.NORMAL
            return (
                Button(label)
                .kind(kind)
                .fixed_height(24)
                .on_click(lambda _, t=wf_type: self._on_workflow_type_select(t))
            )

        return Column(
            Text("Workflow").fixed_height(20).text_color("#9ca3af"),
            Row(
                make_btn("mock", "Mock"),
                make_btn("simple", "Simple"),
                make_btn("complex", "Complex"),
            ).fixed_height(28),
        ).fixed_height(56).bg_color("#1e1f2b")

    def _build_canvas(
        self,
        workflow: WorkflowModel | None,
        execution: WorkflowExecutionState,
    ) -> WorkflowCanvas:
        """Build the workflow canvas."""
        self._canvas = WorkflowCanvas(
            workflow=workflow,
            execution_state=execution,
            auto_layout=True,
            transform=self._canvas_transform,  # Preserve zoom state across rebuilds
        )
        self._canvas.on_node_click(self._on_canvas_node_click)
        self._canvas.on_zoom_change(self._on_canvas_zoom_change)

        # Preserve highlighted event type across rebuilds
        if self._selected_event_type():
            self._canvas.set_highlighted_event_type(self._selected_event_type())

        # Canvas expands to fill available space
        self._canvas.width_policy(SizePolicy.EXPANDING)
        self._canvas.height_policy(SizePolicy.EXPANDING)

        return self._canvas

    def _build_right_panel(
        self,
        workflow: WorkflowModel | None,
        execution: WorkflowExecutionState,
    ) -> Column:
        """Build the right panel with tabbed details."""
        # Get selected step
        selected_step = None
        selected_execution = None

        if workflow and self._selected_step_id():
            selected_step = workflow.get_step(self._selected_step_id())

            # Find most recent execution of this step
            for step_exec in reversed(execution.step_history):
                if step_exec.node_id == self._selected_step_id():
                    selected_execution = step_exec
                    break

        # Build tab content based on selection
        tab_id = self._right_panel_tabs.selected_id()

        return Column(
            # Tab bar
            Row(
                self._build_tab_button("step", "Step"),
                self._build_tab_button("context", "Context"),
                self._build_tab_button("queue", "Queue"),
                Spacer(),
            ).fixed_height(32).bg_color("#1e1f2b"),
            # Content - build inline based on tab
            self._build_tab_content(tab_id, workflow, execution, selected_step, selected_execution),
        ).fixed_width(RIGHT_PANEL_WIDTH).height_policy(SizePolicy.EXPANDING).bg_color("#1a1b26")

    def _build_tab_content(
        self,
        tab_id: str,
        workflow: WorkflowModel | None,
        execution: WorkflowExecutionState,
        selected_step,
        selected_execution,
    ):
        """Build content for the selected tab."""
        if tab_id == "step":
            return StepPanel(
                step=selected_step,
                execution=selected_execution,
                on_view_docstring=self._on_view_docstring,
                on_view_source=self._on_view_source,
            ).height_policy(SizePolicy.EXPANDING)
        elif tab_id == "context":
            return ContextInspector(
                execution_state=execution,
            ).height_policy(SizePolicy.EXPANDING)
        elif tab_id == "queue":
            return EventQueuePanel(
                workflow=workflow,
                queue=execution.event_queue,
            ).height_policy(SizePolicy.EXPANDING)
        else:
            return Spacer()

    def _build_tab_button(self, tab_id: str, label: str) -> Button:
        """Build a tab button."""
        is_selected = self._right_panel_tabs.selected_id() == tab_id
        kind = Kind.INFO if is_selected else Kind.NORMAL

        return (
            Button(label)
            .kind(kind)
            .fixed_width(70)
            .fixed_height(28)
            .on_click(lambda _, tid=tab_id: self._on_tab_select(tid))
        )

    def _build_timeline(
        self,
        workflow: WorkflowModel | None,
        execution: WorkflowExecutionState,
    ) -> EventTimeline:
        """Build the event timeline."""
        self._timeline = EventTimeline(
            workflow=workflow,
            execution_state=execution,
        )
        self._timeline.on_execution_select(self._on_timeline_select)

        return self._timeline

    def _build_status_bar(self, execution: WorkflowExecutionState) -> StatusBar:
        """Build the status bar."""
        return StatusBar(execution)

    # ========== Event Handlers ==========

    def _on_run(self) -> None:
        """Handle run button click."""
        if self._workflow_class() is not None:
            # Real workflow execution
            self._executor.set_workflow(self._workflow_class())
            if self._workflow_model():
                self._executor.set_workflow_model(self._workflow_model())
            self._executor.run({})
        elif self._workflow_model() is not None:
            # Mock workflow execution (simulation)
            self._executor.set_workflow_model(self._workflow_model())
            self._executor.run_mock()

    def _on_step(self) -> None:
        """Handle step button click."""
        if self._workflow_class() is not None:
            if not self._executor.is_running:
                self._executor.set_workflow(self._workflow_class())
                if self._workflow_model():
                    self._executor.set_workflow_model(self._workflow_model())
            self._executor.step({})
        elif self._workflow_model() is not None:
            # Mock workflow step (simulation)
            if not self._executor.is_running:
                self._executor.set_workflow_model(self._workflow_model())
            self._executor.step_mock()

    def _on_pause(self) -> None:
        """Handle pause button click."""
        self._executor.pause()

    def _on_continue(self) -> None:
        """Handle continue button click."""
        self._executor.continue_execution()

    def _on_stop(self) -> None:
        """Handle stop button click."""
        self._executor.stop()

    def _on_reset(self) -> None:
        """Handle reset button click."""
        self._executor.reset()

    def _on_zoom_in(self) -> None:
        """Handle zoom in button click."""
        if self._canvas:
            self._canvas.zoom_in()

    def _on_zoom_out(self) -> None:
        """Handle zoom out button click."""
        if self._canvas:
            self._canvas.zoom_out()

    def _on_fit(self) -> None:
        """Handle fit to content button click."""
        if self._canvas:
            self._canvas.fit_to_content()

    def _on_execution_update(self, state: WorkflowExecutionState) -> None:
        """Handle execution state update from executor.

        Args:
            state: New execution state.
        """
        self._execution_state.set(state)

    def _on_canvas_node_click(self, node_id: str) -> None:
        """Handle node click on canvas.

        Implements double-click detection at the studio level to persist
        across view rebuilds (canvas is recreated each time).

        Args:
            node_id: Clicked node ID.
        """
        current_time = time.time() * 1000  # Convert to milliseconds
        time_diff = current_time - self._last_click_time

        # Check for double-click (same node within threshold)
        is_double_click = (
            self._last_click_node_id == node_id
            and time_diff < self._double_click_threshold_ms
        )

        if is_double_click:
            # Double-click detected - toggle breakpoint
            self._executor.toggle_breakpoint(node_id)
            # Reset to prevent triple-click
            self._last_click_time = 0.0
            self._last_click_node_id = None
        else:
            # Single click - select the step
            if node_id not in ("__start__", "__end__"):
                self._selected_step_id.set(node_id)
                self._right_panel_tabs.select("step")
            # Record for potential double-click
            self._last_click_time = current_time
            self._last_click_node_id = node_id

    def _on_canvas_zoom_change(self, zoom_percent: int) -> None:
        """Handle zoom change from canvas.

        Args:
            zoom_percent: New zoom level.
        """
        self._zoom_percent.set(zoom_percent)

    def _on_step_select(self, step_id: str) -> None:
        """Handle step selection from list.

        Args:
            step_id: Selected step ID.
        """
        self._selected_step_id.set(step_id)
        self._right_panel_tabs.select("step")

        # Center canvas on selected step
        if self._canvas:
            self._canvas.center_on_node(step_id)

    def _on_event_select(self, event_type: str) -> None:
        """Handle event type selection.

        Args:
            event_type: Selected event type name.
        """
        # Toggle selection - clicking same event again clears it
        if self._selected_event_type() == event_type:
            self._selected_event_type.set(None)
            if self._canvas:
                self._canvas.set_highlighted_event_type(None)
        else:
            self._selected_event_type.set(event_type)
            if self._canvas:
                self._canvas.set_highlighted_event_type(event_type)

    def _on_tab_select(self, tab_id: str) -> None:
        """Handle right panel tab selection.

        Args:
            tab_id: Selected tab ID.
        """
        self._right_panel_tabs.select(tab_id)

    def _on_timeline_select(self, execution: Any) -> None:
        """Handle execution selection on timeline.

        Args:
            execution: Selected StepExecution.
        """
        if execution:
            self._selected_step_id.set(execution.node_id)
            self._right_panel_tabs.select("step")

    def _on_file_select(self, file_path: str) -> None:
        """Handle workflow file selection.

        Args:
            file_path: Path to the selected file.
        """
        self._load_workflow_file(file_path)

    def _on_workflow_type_select(self, workflow_type: str) -> None:
        """Handle workflow type selection from selector.

        Args:
            workflow_type: Selected workflow type ("mock", "simple", "complex").
        """
        if workflow_type == self._current_workflow_type():
            return  # Already selected

        self._current_workflow_type.set(workflow_type)

        if workflow_type == "mock":
            # Load mock workflow (no llama-index required)
            self._load_mock_workflow("simple")
        elif workflow_type == "simple":
            # Load simple real LlamaIndex Workflow
            self._load_real_workflow("simple_workflow.py")
        elif workflow_type == "complex":
            # Load complex real LlamaIndex Workflow
            self._load_real_workflow("complex_workflow.py")
        else:
            self._load_mock_workflow("simple")

        # Clear selection states
        self._selected_step_id.set(None)
        self._selected_event_type.set(None)

    # ========== Modal Handlers ==========

    def _on_view_docstring(self, step_label: str, content: str) -> None:
        """Handle view full docstring request.

        Args:
            step_label: Step label for modal title.
            content: Full docstring content.
        """
        self._content_modal.open_docstring(step_label, content)

    def _on_view_source(self, step_label: str, content: str) -> None:
        """Handle view full source code request.

        Args:
            step_label: Step label for modal title.
            content: Full source code content.
        """
        self._content_modal.open_source(step_label, content)

    def _load_real_workflow(self, filename: str = "simple_workflow.py") -> None:
        """Load a real LlamaIndex Workflow from samples.

        Args:
            filename: Workflow file name in samples directory.
        """
        # Get the samples directory relative to this file
        samples_dir = Path(__file__).parent.parent / "samples"
        workflow_file = samples_dir / filename

        if workflow_file.exists():
            self._load_workflow_file(str(workflow_file))
        else:
            self._error_message.set(f"Workflow file not found: {workflow_file}")
            self._load_mock_workflow("simple")

    # ========== Workflow Loading ==========

    def _load_workflow_file(self, file_path: str) -> None:
        """Load a workflow from a Python file.

        Args:
            file_path: Path to the Python file.
        """
        try:
            # Load module
            module = load_module(Path(file_path))

            # Find Workflow class
            workflow_class = find_workflow_class(module)
            if workflow_class is None:
                self._error_message.set(f"No Workflow class found in {file_path}")
                return

            # Extract workflow model
            model = extract_workflow_model(workflow_class)

            # Update state
            self._workflow_class.set(workflow_class)
            self._workflow_model.set(model)
            self._error_message.set(None)

            # Reset execution
            self._executor.reset()

        except ModuleLoadError as e:
            self._error_message.set(f"Failed to load module: {e}")
            # Fall back to mock workflow
            self._load_mock_workflow("simple")
        except WorkflowExtractionError as e:
            error_msg = str(e)
            self._error_message.set(f"Failed to extract workflow: {e}")
            # If library not installed, fall back to mock
            if "not installed" in error_msg:
                self._load_mock_workflow("simple")
        except Exception as e:
            self._error_message.set(f"Error: {e}")
            # Fall back to mock workflow
            self._load_mock_workflow("simple")

    def load_workflow(self, workflow_class: type) -> None:
        """Load a workflow class directly.

        Args:
            workflow_class: The Workflow class to load.
        """
        try:
            model = extract_workflow_model(workflow_class)
            self._workflow_class.set(workflow_class)
            self._workflow_model.set(model)
            self._error_message.set(None)
            self._executor.reset()
        except WorkflowExtractionError as e:
            self._error_message.set(f"Failed to extract workflow: {e}")

    def _load_mock_workflow(self, workflow_type: str = "simple") -> None:
        """Load a mock workflow for demonstration.

        Args:
            workflow_type: Type of mock workflow ("simple", "branching", "collect").
        """
        if workflow_type == "branching":
            model = create_branching_mock_workflow()
        elif workflow_type == "collect":
            model = create_collect_mock_workflow()
        else:
            model = create_mock_workflow()

        self._workflow_model.set(model)
        self._workflow_class.set(None)  # No actual class for mock
        self._error_message.set(None)
        self._executor.reset()
