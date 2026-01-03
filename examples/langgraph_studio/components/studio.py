"""Main Studio component for LangGraph Studio."""

from __future__ import annotations

from typing import Any

from castella import Component, Column, Row, State

from ..models.graph import GraphModel
from ..models.execution import ExecutionState
from ..widgets.graph_canvas import GraphCanvas
from ..loader.module_loader import load_module_from_path, ModuleLoadError
from ..loader.graph_extractor import (
    find_compiled_graph,
    extract_graph_model,
    extract_node_functions,
    GraphExtractionError,
)
from ..executor.runner import GraphExecutor

# Use shared components from castella.studio
from castella.studio.components.toolbar import Toolbar
from castella.studio.components.status_bar import StatusBar

from .file_panel import FilePanel
from .right_panel import RightPanel
from .initial_state_editor import InitialStateEditor


class Studio(Component):
    """Main Studio application component.

    Orchestrates all sub-components:
    - Toolbar for controls
    - FilePanel for file selection
    - GraphCanvas for graph visualization
    - StateInspector for state display
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
        self._graph = State[GraphModel | None](None)
        self._execution = State[ExecutionState](ExecutionState())
        self._selected_file = State[str | None](None)
        self._error_message = State[str | None](None)
        self._zoom_percent = State[int](100)
        self._initial_state = State[dict]({})
        self._selected_node_id = State[str | None](None)

        # Attach all states
        self._graph.attach(self)
        self._execution.attach(self)
        self._selected_file.attach(self)
        self._error_message.attach(self)
        self._zoom_percent.attach(self)
        self._selected_node_id.attach(self)
        # Note: don't attach _initial_state - the editor manages its own state

        # Initial path for file browser
        self._initial_path = initial_path

        # Initial file to load on startup
        self._initial_file = initial_file

        # Compiled graph reference (for execution)
        self._compiled_graph: Any = None

        # Node functions for source code display
        self._node_functions: dict = {}

        # Executor (updates state via callback)
        self._executor = GraphExecutor(
            on_state_update=lambda s: self._execution.set(s)
        )

        # Canvas - created once to preserve transform state
        self._canvas = GraphCanvas(graph=None, execution_state=None)
        self._canvas = self._canvas.on_node_click(self._on_node_click)
        self._canvas = self._canvas.on_zoom_change(self._on_zoom_change)

        # Initial state editor reference
        self._state_editor: InitialStateEditor | None = None

        # Load initial file if specified (store data for first view)
        self._pending_initial_load: tuple | None = None
        if self._initial_file:
            self._load_initial_file()

    def _load_initial_file(self) -> None:
        """Pre-load initial file data without triggering state updates."""
        try:
            module = load_module_from_path(self._initial_file)
            compiled_graph = find_compiled_graph(module)
            graph_model = extract_graph_model(compiled_graph)
            node_functions = extract_node_functions(compiled_graph)
            # Store for first view() call
            self._pending_initial_load = (compiled_graph, graph_model, node_functions)
        except Exception:
            self._pending_initial_load = None

    def view(self):
        """Build the Studio UI."""
        # Apply pending initial load on first view (set values without notify)
        if self._pending_initial_load is not None:
            compiled_graph, graph_model, node_functions = self._pending_initial_load
            self._pending_initial_load = None
            self._compiled_graph = compiled_graph
            self._node_functions = node_functions
            # Set internal values directly to avoid triggering rebuild during view()
            self._graph._value = graph_model
            # Set executor's graph directly without notify
            self._executor._compiled_graph = compiled_graph
            self._executor._state = ExecutionState()

        graph = self._graph()
        execution = self._execution()
        zoom = self._zoom_percent()

        # Update canvas with current state (preserve transform)
        self._canvas._graph = graph
        self._canvas._execution_state = execution

        # Determine button states
        can_run = graph is not None and execution.can_run
        can_stop = execution.can_stop
        can_pause = execution.can_pause
        can_continue = execution.can_continue

        # Build initial state editor
        state_editor = InitialStateEditor(
            on_state_change=self._on_initial_state_change,
            collapsed=True,
        )
        self._state_editor = state_editor

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
                # Center: Graph canvas
                self._canvas,
                # Right panel: Tabbed state/node/history
                RightPanel(
                    execution=execution,
                    graph=graph,
                    selected_node_id=self._selected_node_id(),
                    node_functions=self._node_functions,
                ).fixed_width(300),
            ),
            # Initial state editor (collapsible)
            state_editor,
            # Bottom: Status bar (shared component with fixed_height=28)
            StatusBar(execution),
        )

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
            module = load_module_from_path(path)

            # Find compiled graph
            compiled_graph = find_compiled_graph(module)
            self._compiled_graph = compiled_graph

            # Extract graph model for visualization
            graph_model = extract_graph_model(compiled_graph)
            self._graph.set(graph_model)

            # Extract node functions for source code display
            self._node_functions = extract_node_functions(compiled_graph)

            # Set up executor with the graph
            self._executor.set_graph(compiled_graph)

            # Reset execution state
            self._execution.set(ExecutionState())

        except (ModuleLoadError, GraphExtractionError) as e:
            self._error_message.set(str(e))
            self._graph.set(None)
            self._compiled_graph = None
            self._node_functions = {}

        except Exception as e:
            self._error_message.set(f"Unexpected error: {e}")
            self._graph.set(None)
            self._compiled_graph = None
            self._node_functions = {}

    # ========== Execution Controls ==========

    def _on_initial_state_change(self, state: dict) -> None:
        """Handle initial state change from editor.

        Args:
            state: Parsed JSON state from editor.
        """
        self._initial_state.set(state)

    def _on_run(self) -> None:
        """Handle run button click."""
        if self._compiled_graph is None:
            return

        # Get initial state from editor
        initial_state = self._get_initial_state()
        self._executor.run(initial_state)

    def _on_step(self) -> None:
        """Handle step button click."""
        if self._compiled_graph is None:
            return

        initial_state = self._get_initial_state()

        self._executor.step(initial_state)

    def _get_initial_state(self) -> dict:
        """Get initial state from editor.

        Returns:
            Initial state dict.
        """
        if self._state_editor:
            return self._state_editor.get_state()
        return {}

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
