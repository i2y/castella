"""Executor for pydantic-graph with async support."""

from __future__ import annotations

import asyncio
import time
from typing import Any, Callable

from castella.studio.executor.base import BaseWorkflowExecutor
from castella.studio.models.execution import ExecutionStatus

from ..models.execution import GraphExecutionState, GraphStepResult
from ..models.graph import GraphAPIType, PydanticGraphModel


class GraphExecutor(BaseWorkflowExecutor):
    """Executor for pydantic-graph.

    Supports both BaseNode API (using graph.iter()) and GraphBuilder API.
    Also supports mock execution mode for demonstration without pydantic-graph.
    """

    def __init__(self, on_state_update: Callable[[GraphExecutionState], None]):
        self._graph: Any = None
        self._graph_model: PydanticGraphModel | None = None
        self._api_type: GraphAPIType = GraphAPIType.MOCK
        self._asyncio_loop: asyncio.AbstractEventLoop | None = None
        super().__init__(on_state_update)

    def _create_initial_state(self) -> GraphExecutionState:
        """Create initial execution state."""
        return GraphExecutionState()

    def set_workflow(self, workflow: Any) -> None:
        """Set the graph to execute.

        Args:
            workflow: The Graph instance to execute.
        """
        self.stop()
        self._graph = workflow

    def set_graph_model(self, model: PydanticGraphModel) -> None:
        """Set the graph model for visualization and mock execution.

        Args:
            model: The PydanticGraphModel extracted from the graph.
        """
        self._graph_model = model
        self._api_type = model.api_type

    def _execute_loop(self, initial_state: dict[str, Any]) -> None:
        """Main execution loop in background thread.

        Creates an asyncio event loop and runs the appropriate
        execution method based on API type.
        """
        self._asyncio_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._asyncio_loop)

        try:
            if self._api_type == GraphAPIType.MOCK:
                self._asyncio_loop.run_until_complete(
                    self._execute_mock(initial_state)
                )
            elif self._api_type == GraphAPIType.BASE_NODE:
                self._asyncio_loop.run_until_complete(
                    self._execute_basenode(initial_state)
                )
            elif self._api_type == GraphAPIType.GRAPH_BUILDER:
                self._asyncio_loop.run_until_complete(
                    self._execute_builder(initial_state)
                )
        except Exception as e:
            self._set_error(f"Execution error: {e}")
            self._notify_update()
        finally:
            self._asyncio_loop.close()
            self._asyncio_loop = None

    async def _execute_basenode(self, initial_state: dict[str, Any]) -> None:
        """Execute pydantic-graph using BaseNode API with graph.iter().

        Uses the graph.iter() context manager for step-by-step execution,
        allowing breakpoints and step mode.
        """
        if self._graph is None:
            self._set_error("No graph set")
            self._notify_update()
            return

        if self._graph_model is None:
            self._set_error("No graph model set")
            self._notify_update()
            return

        # Reset state
        state = self._state
        if isinstance(state, GraphExecutionState):
            state.step_history = []
            state.executed_edges = []
            state.current_graph_state = initial_state.copy()

        self._set_status(ExecutionStatus.RUNNING)
        self._notify_update()

        try:
            # Find start node class
            start_node_class = self._get_start_node_class()
            if start_node_class is None:
                self._set_error("No start node found in graph")
                self._notify_update()
                return

            # Create start node instance
            start_node = start_node_class()

            # Show __start__ node
            last_node_id = "__start__"
            self._set_current_node("__start__")
            self._notify_update()
            await asyncio.sleep(0.2)

            # Use graph.iter() for step-by-step execution
            async with self._graph.iter(start_node, state=initial_state) as graph_run:
                while True:
                    if self._check_should_stop():
                        break

                    next_node = graph_run.next_node
                    if next_node is None:
                        break

                    node_id = type(next_node).__name__

                    # Check breakpoint
                    if not self._check_breakpoint(node_id):
                        break

                    # Wait for manual pause
                    if not self._wait_for_pause():
                        break

                    # Wait for step in step mode
                    if not self._wait_for_step():
                        break

                    # Record edge from last node
                    self._record_edge(last_node_id, node_id)

                    # Set current node and update UI
                    self._set_current_node(node_id)
                    self._set_status(ExecutionStatus.RUNNING)
                    self._notify_update()

                    # Execute the node
                    start_time = time.perf_counter()
                    state_before = self._extract_state(graph_run)

                    result = await graph_run.next(next_node)

                    duration_ms = (time.perf_counter() - start_time) * 1000
                    state_after = self._extract_state(graph_run)

                    # Check if End was returned
                    is_end = self._is_end_result(result)

                    # Record step
                    step_result = GraphStepResult(
                        node_id=node_id,
                        node_class=type(next_node).__name__,
                        node_data=self._extract_node_data(next_node),
                        state_before=state_before,
                        state_after=state_after,
                        started_at_ms=time.time() * 1000 - duration_ms,
                        duration_ms=duration_ms,
                        returned_type=type(result).__name__ if result else "",
                        is_end=is_end,
                    )
                    self._record_step(step_result)

                    # Update current graph state
                    if isinstance(self._state, GraphExecutionState):
                        self._state.current_graph_state = state_after

                    last_node_id = node_id
                    self._notify_update()

                    await asyncio.sleep(0.1)

                    if is_end:
                        # Store result
                        if isinstance(self._state, GraphExecutionState):
                            self._state.result = self._extract_end_data(result)
                        break

            # Show __end__ node
            if not self._check_should_stop():
                self._record_edge(last_node_id, "__end__")
                self._set_current_node("__end__")
                self._notify_update()
                await asyncio.sleep(0.2)

                self._set_status(ExecutionStatus.COMPLETED)
            else:
                self._set_status(ExecutionStatus.IDLE)

            self._set_current_node(None)
            self._notify_update()

        except Exception as e:
            self._set_error(f"Execution error: {e}")
            self._notify_update()

    async def _execute_builder(self, initial_state: dict[str, Any]) -> None:
        """Execute pydantic-graph using GraphBuilder API.

        The GraphBuilder API may have different execution patterns.
        For now, we use mock execution as a fallback.
        """
        # GraphBuilder execution is similar to mock for now
        # as the API details may vary
        await self._execute_mock(initial_state)

    async def _execute_mock(self, initial_state: dict[str, Any]) -> None:
        """Execute mock graph for demonstration.

        Simulates execution by visiting nodes in order without
        actually running any code.
        """
        if self._graph_model is None:
            self._set_error("No graph model set")
            self._notify_update()
            return

        # Reset state
        state = self._state
        if isinstance(state, GraphExecutionState):
            state.step_history = []
            state.executed_edges = []
            state.current_graph_state = initial_state.copy()

        self._set_status(ExecutionStatus.RUNNING)
        self._notify_update()

        # Get execution order (simple topological order)
        node_order = self._get_mock_execution_order()

        last_node_id = "__start__"

        # Show __start__
        self._set_current_node("__start__")
        self._notify_update()
        await asyncio.sleep(0.3)

        for node_id in node_order:
            if self._check_should_stop():
                break

            # Check breakpoint
            if not self._check_breakpoint(node_id):
                break

            # Wait for step in step mode
            if not self._wait_for_step():
                break

            # Wait for manual pause
            if not self._wait_for_pause():
                break

            # Record edge and set current
            self._record_edge(last_node_id, node_id)
            self._set_current_node(node_id)
            self._set_status(ExecutionStatus.RUNNING)
            self._notify_update()

            # Simulate execution time
            await asyncio.sleep(0.4)

            # Record step
            step_result = GraphStepResult(
                node_id=node_id,
                node_class=node_id,
                started_at_ms=time.time() * 1000,
                duration_ms=400,
            )
            self._record_step(step_result)

            last_node_id = node_id
            self._notify_update()

        # Show __end__
        if not self._check_should_stop():
            self._record_edge(last_node_id, "__end__")
            self._set_current_node("__end__")
            self._notify_update()
            await asyncio.sleep(0.3)

            self._set_status(ExecutionStatus.COMPLETED)
        else:
            self._set_status(ExecutionStatus.IDLE)

        self._set_current_node(None)
        self._notify_update()

    def _get_start_node_class(self) -> type | None:
        """Get the start node class from the graph.

        Returns:
            The start node class, or None if not found.
        """
        if self._graph is None or self._graph_model is None:
            return None

        # Find start nodes from model
        start_nodes = [
            n for n in self._graph_model.nodes
            if n.is_start and n.id != "__start__"
        ]

        if not start_nodes:
            return None

        # Get the node class from graph's node_defs
        node_defs = getattr(self._graph, "node_defs", {})
        if not node_defs:
            node_defs = getattr(self._graph, "_node_defs", {})

        if not node_defs:
            # Try _nodes tuple
            nodes = getattr(self._graph, "_nodes", ())
            if nodes:
                node_defs = {n.__name__: n for n in nodes if isinstance(n, type)}

        # Return the first start node class
        start_id = start_nodes[0].id
        node_def = node_defs.get(start_id)

        if node_def is None:
            return None

        # Extract actual node class from NodeDef if needed
        if hasattr(node_def, "node"):
            return node_def.node
        elif isinstance(node_def, type):
            return node_def
        else:
            return None

    def _get_mock_execution_order(self) -> list[str]:
        """Get node execution order for mock mode.

        Uses simple BFS from start nodes to determine order.
        """
        if self._graph_model is None:
            return []

        # Find start nodes (excluding __start__)
        start_ids = [
            n.id for n in self._graph_model.nodes
            if n.is_start and n.id != "__start__"
        ]

        if not start_ids:
            # Fallback: use nodes connected from __start__
            start_ids = [
                e.target_id for e in self._graph_model.edges
                if e.source_id == "__start__"
            ]

        # BFS to get order
        visited: set[str] = set()
        order: list[str] = []
        queue = list(start_ids)

        while queue:
            node_id = queue.pop(0)
            if node_id in visited or node_id in ("__start__", "__end__"):
                continue

            visited.add(node_id)
            order.append(node_id)

            # Add successors
            for edge in self._graph_model.edges:
                if edge.source_id == node_id and edge.target_id not in visited:
                    queue.append(edge.target_id)

        return order

    def _extract_state(self, graph_run: Any) -> dict[str, Any]:
        """Extract state from a graph run object."""
        if hasattr(graph_run, "state"):
            state = graph_run.state
            if isinstance(state, dict):
                return state.copy()
            elif hasattr(state, "model_dump"):
                return state.model_dump()
            elif hasattr(state, "__dict__"):
                return dict(state.__dict__)
        return {}

    def _extract_node_data(self, node: Any) -> dict[str, Any]:
        """Extract node instance data (dataclass fields)."""
        if hasattr(node, "__dataclass_fields__"):
            return {
                name: getattr(node, name, None)
                for name in node.__dataclass_fields__
            }
        return {}

    def _is_end_result(self, result: Any) -> bool:
        """Check if result is End[T]."""
        if result is None:
            return False
        type_name = type(result).__name__
        return type_name == "End"

    def _extract_end_data(self, result: Any) -> Any:
        """Extract data from End[T] result."""
        if result is None:
            return None
        if hasattr(result, "data"):
            return result.data
        return result
