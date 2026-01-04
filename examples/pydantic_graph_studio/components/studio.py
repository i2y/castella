"""Main Studio component for pydantic-graph Studio."""

from __future__ import annotations

from typing import Any

from castella import Box, Column, Component, Row, Spacer, State, Text
from castella.multiline_text import MultilineText

from castella.graph import GraphModel
from castella.studio.components.file_panel import FilePanel
from castella.studio.components.status_bar import StatusBar
from castella.studio.components.toolbar import Toolbar
from castella.studio.loader.module_loader import ModuleLoadError, load_module

from ..executor.runner import GraphExecutor
from ..loader.graph_extractor import (
    GraphExtractionError,
    extract_graph_model,
    find_pydantic_graph,
    to_castella_graph_model,
)
from ..models.execution import GraphExecutionState
from ..models.graph import GraphAPIType, PydanticGraphModel
from ..widgets.graph_canvas import PydanticGraphCanvas
from .right_panel import RightPanel


class PydanticGraphStudio(Component):
    """Main Studio application component for pydantic-graph.

    Orchestrates all sub-components:
    - Toolbar for execution controls
    - FilePanel for file selection
    - PydanticGraphCanvas for graph visualization
    - RightPanel for state/node/history
    - StatusBar for execution status
    """

    def __init__(self, initial_path: str = ".", initial_file: str | None = None):
        """Initialize the studio.

        Args:
            initial_path: Initial directory for file browser.
            initial_file: Optional Python file to load on startup.
        """
        super().__init__()

        # Core state
        self._graph_model = State[PydanticGraphModel | None](None)
        self._castella_graph = State[GraphModel | None](None)
        self._execution = State[GraphExecutionState](GraphExecutionState())
        self._selected_file = State[str | None](None)
        self._error_message = State[str | None](None)
        self._zoom_percent = State[int](100)
        self._selected_node_id = State[str | None](None)

        # Attach all states
        self._graph_model.attach(self)
        self._castella_graph.attach(self)
        self._execution.attach(self)
        self._selected_file.attach(self)
        self._error_message.attach(self)
        self._zoom_percent.attach(self)
        self._selected_node_id.attach(self)

        # Initial path for file browser
        self._initial_path = initial_path

        # Initial file to load on startup
        self._initial_file = initial_file

        # pydantic-graph reference (for execution)
        self._pydantic_graph: Any = None
        self._api_type: GraphAPIType = GraphAPIType.MOCK

        # Executor (updates state via callback)
        self._executor = GraphExecutor(
            on_state_update=lambda s: self._execution.set(s)
        )

        # Canvas - created once to preserve transform state
        self._canvas = PydanticGraphCanvas(graph=None, execution_state=None)
        self._canvas = self._canvas.on_node_click(self._on_node_click)
        self._canvas = self._canvas.on_zoom_change(self._on_zoom_change)

        # Load initial file if specified (store for first view)
        self._pending_initial_load: tuple | None = None
        self._pending_error: str | None = None
        if self._initial_file:
            self._load_initial_file()

    def _load_initial_file(self) -> None:
        """Pre-load initial file data without triggering state updates."""
        try:
            module = load_module(self._initial_file)
            pydantic_graph, api_type = find_pydantic_graph(module)
            pg_model = extract_graph_model(pydantic_graph, api_type)
            castella_graph = to_castella_graph_model(pg_model)
            # Store for first view() call
            self._pending_initial_load = (pydantic_graph, api_type, pg_model, castella_graph)
        except Exception as e:
            self._pending_initial_load = None
            # Store error for display (will be applied in first view())
            self._pending_error = str(e)

    def view(self):
        """Build the Studio UI."""
        # Apply pending error if any
        if self._pending_error is not None:
            self._error_message._value = self._pending_error
            self._pending_error = None

        # Apply pending initial load on first view
        if self._pending_initial_load is not None:
            pydantic_graph, api_type, pg_model, castella_graph = self._pending_initial_load
            self._pending_initial_load = None
            self._pydantic_graph = pydantic_graph
            self._api_type = api_type
            # Set internal values directly to avoid rebuild during view()
            self._graph_model._value = pg_model
            self._castella_graph._value = castella_graph
            # Set executor's graph
            self._executor.set_workflow(pydantic_graph)
            self._executor.set_graph_model(pg_model)

        graph_model = self._graph_model()
        castella_graph = self._castella_graph()
        execution = self._execution()
        zoom = self._zoom_percent()

        # Update canvas with current state
        self._canvas.update_graph(castella_graph)
        self._canvas.set_execution_state(execution)

        # Determine button states
        can_run = castella_graph is not None and execution.can_run
        can_stop = execution.can_stop
        can_pause = execution.can_pause
        can_continue = execution.can_continue

        return Column(
            # Toolbar (shared component with fixed_height=44)
            Toolbar(
                can_run=can_run,
                can_stop=can_stop,
                can_pause=can_pause,
                can_continue=can_continue,
                zoom_percent=zoom,
                on_run=self._on_run,
                on_step=self._on_step,
                on_pause=self._on_pause,
                on_continue=self._on_continue,
                on_stop=self._on_stop,
                on_reset=self._on_reset,
                on_zoom_in=self._on_zoom_in,
                on_zoom_out=self._on_zoom_out,
                on_fit=self._on_fit,
            ),
            # Main content area
            Row(
                # Left panel: File browser
                FilePanel(
                    root_path=self._initial_path,
                    on_file_select=self._on_file_select,
                ).fixed_width(200),
                # Center: Graph canvas with error overlay
                self._build_center_panel(castella_graph),
                # Right panel: Tabbed state/node/history
                RightPanel(
                    execution=execution,
                    graph_model=graph_model,
                    selected_node_id=self._selected_node_id(),
                ).fixed_width(300),
            ),
            # Bottom: Status bar (shared component with fixed_height=28)
            StatusBar(execution),
        )

    def _build_center_panel(self, castella_graph: GraphModel | None):
        """Build center panel with canvas or error message.

        Args:
            castella_graph: The graph model to display.
        """
        error = self._error_message()

        if error and castella_graph is None:
            # Show error message overlay
            return Box(
                self._canvas,
                Column(
                    Spacer(),
                    Row(
                        Spacer(),
                        Column(
                            Text("⚠ Error Loading Graph").fixed_height(30),
                            Spacer().fixed_height(8),
                            MultilineText(error, font_size=12, wrap=True).fixed_height(80),
                            Spacer().fixed_height(16),
                            Text("Check if pydantic-graph is installed:").fixed_height(20),
                            Text("  pip install pydantic-graph").fixed_height(20),
                        ).fixed_width(500).fixed_height(200),
                        Spacer(),
                    ).fixed_height(200),
                    Spacer(),
                ).z_index(10),
            )
        else:
            return self._canvas

    # ========== File Handling ==========

    def _on_file_select(self, path: str) -> None:
        """Handle file selection from file panel.

        Args:
            path: Path to the selected Python file.
        """
        self._selected_file.set(path)
        self._error_message.set(None)

        try:
            # Load module
            module = load_module(path)

            # Find pydantic-graph
            pydantic_graph, api_type = find_pydantic_graph(module)
            self._pydantic_graph = pydantic_graph
            self._api_type = api_type

            # Extract graph model
            pg_model = extract_graph_model(pydantic_graph, api_type)
            self._graph_model.set(pg_model)

            # Convert to Castella GraphModel for visualization
            castella_graph = to_castella_graph_model(pg_model)
            self._castella_graph.set(castella_graph)

            # Set up executor
            self._executor.set_workflow(pydantic_graph)
            self._executor.set_graph_model(pg_model)

            # Reset execution state
            self._execution.set(GraphExecutionState())

        except (ModuleLoadError, GraphExtractionError) as e:
            self._error_message.set(str(e))
            self._graph_model.set(None)
            self._castella_graph.set(None)
            self._pydantic_graph = None

        except Exception as e:
            self._error_message.set(f"Unexpected error: {e}")
            self._graph_model.set(None)
            self._castella_graph.set(None)
            self._pydantic_graph = None

    # ========== Execution Controls ==========

    def _on_run(self) -> None:
        """Handle run button click."""
        if self._pydantic_graph is None and self._api_type != GraphAPIType.MOCK:
            return
        self._executor.run({})

    def _on_step(self) -> None:
        """Handle step button click."""
        if self._pydantic_graph is None and self._api_type != GraphAPIType.MOCK:
            return
        self._executor.step({})

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

    # ========== Canvas Controls ==========

    def _on_node_click(self, node_id: str) -> None:
        """Handle node click in canvas.

        Toggles breakpoint and selects node for details view.

        Args:
            node_id: ID of the clicked node.
        """
        # Toggle breakpoint on the node
        self._executor.toggle_breakpoint(node_id)

        # Select node for the right panel details view
        self._selected_node_id.set(node_id)

    def _on_zoom_change(self, percent: int) -> None:
        """Handle zoom level change.

        Args:
            percent: New zoom percentage.
        """
        self._zoom_percent.set(percent)

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

    # ========== Mock Mode ==========

    def load_mock_graph(self, pg_model: PydanticGraphModel) -> None:
        """Load a mock graph for demonstration.

        Args:
            pg_model: The PydanticGraphModel to display.
        """
        self._pydantic_graph = None
        self._api_type = GraphAPIType.MOCK

        castella_graph = to_castella_graph_model(pg_model)
        self._graph_model.set(pg_model)
        self._castella_graph.set(castella_graph)

        # Update canvas immediately
        self._canvas.update_graph(castella_graph)

        # Set up executor for mock mode
        self._executor.set_workflow(None)
        self._executor.set_graph_model(pg_model)

        self._execution.set(GraphExecutionState())
