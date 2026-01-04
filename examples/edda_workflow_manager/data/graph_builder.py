"""Graph builder for workflow visualization.

Builds GraphModel from Edda execution history or workflow templates.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from castella.graph.models import GraphModel, NodeModel, EdgeModel, NodeType, EdgeType
from castella.graph.layout import SugiyamaLayout, LayoutConfig

if TYPE_CHECKING:
    from edda_workflow_manager.models.instance import ActivityHistory
    from edda_workflow_manager.models.execution import EddaExecutionState


class WorkflowGraphBuilder:
    """Builds GraphModel from Edda execution history or workflow templates.

    Supports two modes:
    1. Template-based: Use activity list from historical executions
    2. Dynamic: Build from current execution history only
    """

    def __init__(self, layout_config: LayoutConfig | None = None):
        """Initialize graph builder.

        Args:
            layout_config: Optional layout configuration.
        """
        self._layout_config = layout_config or LayoutConfig(
            direction="TB",
            layer_spacing=120,
            node_spacing=80,
        )
        self._layout = SugiyamaLayout(self._layout_config)

    def build_from_template(
        self,
        template_activities: list[str],
        workflow_name: str = "",
        executed_steps: set[str] | None = None,
        current_step: str | None = None,
        failed_steps: set[str] | None = None,
    ) -> GraphModel:
        """Build workflow graph from activity template.

        Args:
            template_activities: List of activity names from historical executions.
            workflow_name: Workflow name.
            executed_steps: Set of step names that have been executed.
            current_step: Currently executing step name.
            failed_steps: Set of step names that failed.

        Returns:
            GraphModel with full workflow structure.
        """
        executed = executed_steps or set()
        failed = failed_steps or set()

        if not template_activities:
            return self._create_empty_graph(workflow_name or "Workflow")

        nodes: list[NodeModel] = []
        edges: list[EdgeModel] = []

        # Add __start__ node
        nodes.append(
            NodeModel(
                id="__start__",
                label="Start",
                node_type=NodeType.START,
            )
        )

        # Create nodes for each activity
        for activity_name in template_activities:
            # Determine node type based on execution status
            if activity_name in failed:
                node_type = NodeType.END  # Red for failed
            elif activity_name == current_step:
                node_type = NodeType.AGENT  # Blue for current (running)
            elif activity_name in executed:
                node_type = NodeType.PROCESS  # Green for executed
            else:
                node_type = NodeType.DEFAULT  # Gray for not yet executed

            nodes.append(
                NodeModel(
                    id=activity_name,
                    label=self._format_label(activity_name),
                    node_type=node_type,
                )
            )

        # Add __end__ node
        nodes.append(
            NodeModel(
                id="__end__",
                label="End",
                node_type=NodeType.END,
            )
        )

        # Build edges (linear sequence for template)
        edge_id = 0

        # Edge from __start__ to first activity
        if template_activities:
            edges.append(
                EdgeModel(
                    id=f"e_{edge_id}",
                    source_id="__start__",
                    target_id=template_activities[0],
                    edge_type=EdgeType.NORMAL,
                )
            )
            edge_id += 1

        # Edges between activities (linear for now)
        for i in range(len(template_activities) - 1):
            edges.append(
                EdgeModel(
                    id=f"e_{edge_id}",
                    source_id=template_activities[i],
                    target_id=template_activities[i + 1],
                    edge_type=EdgeType.NORMAL,
                )
            )
            edge_id += 1

        # Edge from last activity to __end__
        if template_activities:
            edges.append(
                EdgeModel(
                    id=f"e_{edge_id}",
                    source_id=template_activities[-1],
                    target_id="__end__",
                    edge_type=EdgeType.NORMAL,
                )
            )

        # Create graph
        graph = GraphModel(
            name=workflow_name,
            nodes=nodes,
            edges=edges,
        )

        # Apply layout
        self._layout.layout(graph)

        return graph

    def build_from_execution_state_with_template(
        self,
        state: "EddaExecutionState",
        template_activities: list[str],
    ) -> GraphModel:
        """Build graph combining template with execution state.

        Uses template to show full workflow structure, then overlays
        execution state to show progress.

        Args:
            state: Current execution state.
            template_activities: List of activity names from historical executions.

        Returns:
            GraphModel with full structure and execution progress.
        """
        # Extract executed steps from history
        executed_steps = {step.node_id for step in state.step_history}

        # Find current step
        current_step = state.current_node_id

        # Find failed steps
        failed_steps = {
            step.node_id for step in state.step_history
            if getattr(step, "status", None) == "failed"
        }

        return self.build_from_template(
            template_activities=template_activities,
            workflow_name=state.workflow_name,
            executed_steps=executed_steps,
            current_step=current_step,
            failed_steps=failed_steps,
        )

    def build_from_history(
        self,
        workflow_name: str,
        history: list["ActivityHistory"],
        include_start_end: bool = True,
    ) -> GraphModel:
        """Build a workflow graph from execution history.

        Strategy:
        1. Create nodes for each unique activity_name
        2. Infer edges from execution order
        3. Apply layout

        Args:
            workflow_name: Name of the workflow.
            history: List of activity history records.
            include_start_end: Whether to include __start__ and __end__ nodes.

        Returns:
            GraphModel with nodes and edges.
        """
        if not history:
            return self._create_empty_graph(workflow_name)

        nodes: list[NodeModel] = []
        edges: list[EdgeModel] = []
        activity_names: list[str] = []
        activity_set: set[str] = set()

        # Extract unique activity names in execution order
        for entry in history:
            # Skip compensation activities for the main flow
            if entry.is_compensation:
                continue

            if entry.activity_name not in activity_set:
                activity_set.add(entry.activity_name)
                activity_names.append(entry.activity_name)

        # Add __start__ node if requested
        if include_start_end:
            nodes.append(
                NodeModel(
                    id="__start__",
                    label="Start",
                    node_type=NodeType.START,
                )
            )

        # Create nodes for each activity
        for i, name in enumerate(activity_names):
            nodes.append(
                NodeModel(
                    id=name,
                    label=self._format_label(name),
                    node_type=NodeType.PROCESS,
                )
            )

        # Add __end__ node if requested
        if include_start_end:
            nodes.append(
                NodeModel(
                    id="__end__",
                    label="End",
                    node_type=NodeType.END,
                )
            )

        # Create edges
        edge_id = 0

        # Edge from __start__ to first activity
        if include_start_end and activity_names:
            edges.append(
                EdgeModel(
                    id=f"e_{edge_id}",
                    source_id="__start__",
                    target_id=activity_names[0],
                    edge_type=EdgeType.NORMAL,
                )
            )
            edge_id += 1

        # Edges between activities
        for i in range(len(activity_names) - 1):
            edges.append(
                EdgeModel(
                    id=f"e_{edge_id}",
                    source_id=activity_names[i],
                    target_id=activity_names[i + 1],
                    edge_type=EdgeType.NORMAL,
                )
            )
            edge_id += 1

        # Edge from last activity to __end__
        if include_start_end and activity_names:
            edges.append(
                EdgeModel(
                    id=f"e_{edge_id}",
                    source_id=activity_names[-1],
                    target_id="__end__",
                    edge_type=EdgeType.NORMAL,
                )
            )

        # Create graph
        graph = GraphModel(name=workflow_name, nodes=nodes, edges=edges)

        # Apply layout
        self._layout.layout(graph)

        return graph

    def build_from_execution_state(
        self,
        state: "EddaExecutionState",
        include_start_end: bool = True,
    ) -> GraphModel:
        """Build graph from execution state.

        Args:
            state: EddaExecutionState with step history.
            include_start_end: Whether to include __start__ and __end__ nodes.

        Returns:
            GraphModel with nodes and edges.
        """
        if not state.step_history:
            return self._create_empty_graph(state.workflow_name)

        nodes: list[NodeModel] = []
        edges: list[EdgeModel] = []
        activity_names: list[str] = []
        activity_set: set[str] = set()

        # Extract unique activity names from step history
        for step in state.step_history:
            # Skip compensation steps
            if getattr(step, "is_compensation", False):
                continue

            if step.node_id not in activity_set:
                activity_set.add(step.node_id)
                activity_names.append(step.node_id)

        # Add __start__ node
        if include_start_end:
            nodes.append(
                NodeModel(
                    id="__start__",
                    label="Start",
                    node_type=NodeType.START,
                )
            )

        # Create nodes with appropriate types based on status
        for name in activity_names:
            node_type = NodeType.PROCESS
            nodes.append(
                NodeModel(
                    id=name,
                    label=self._format_label(name),
                    node_type=node_type,
                )
            )

        # Add __end__ node
        if include_start_end:
            nodes.append(
                NodeModel(
                    id="__end__",
                    label="End",
                    node_type=NodeType.END,
                )
            )

        # Create edges
        edge_id = 0

        # Edge from __start__ to first activity
        if include_start_end and activity_names:
            edges.append(
                EdgeModel(
                    id=f"e_{edge_id}",
                    source_id="__start__",
                    target_id=activity_names[0],
                    edge_type=EdgeType.NORMAL,
                )
            )
            edge_id += 1

        # Use executed_edges if available, otherwise infer from order
        if state.executed_edges:
            for source, target in state.executed_edges:
                edges.append(
                    EdgeModel(
                        id=f"e_{edge_id}",
                        source_id=source,
                        target_id=target,
                        edge_type=EdgeType.NORMAL,
                    )
                )
                edge_id += 1
        else:
            # Infer edges from order
            for i in range(len(activity_names) - 1):
                edges.append(
                    EdgeModel(
                        id=f"e_{edge_id}",
                        source_id=activity_names[i],
                        target_id=activity_names[i + 1],
                        edge_type=EdgeType.NORMAL,
                    )
                )
                edge_id += 1

        # Edge from last activity to __end__ (only if completed)
        if include_start_end and activity_names:
            if state.instance_status.is_terminal:
                edges.append(
                    EdgeModel(
                        id=f"e_{edge_id}",
                        source_id=activity_names[-1],
                        target_id="__end__",
                        edge_type=EdgeType.NORMAL,
                    )
                )

        # Create graph
        graph = GraphModel(name=state.workflow_name, nodes=nodes, edges=edges)

        # Apply layout
        self._layout.layout(graph)

        return graph

    def _create_empty_graph(self, workflow_name: str) -> GraphModel:
        """Create an empty graph with just start/end nodes."""
        nodes = [
            NodeModel(id="__start__", label="Start", node_type=NodeType.START),
            NodeModel(id="__end__", label="End", node_type=NodeType.END),
        ]
        edges = [
            EdgeModel(
                id="e_0",
                source_id="__start__",
                target_id="__end__",
                edge_type=EdgeType.NORMAL,
            )
        ]
        graph = GraphModel(name=workflow_name, nodes=nodes, edges=edges)
        self._layout.layout(graph)
        return graph

    def _format_label(self, activity_name: str) -> str:
        """Format activity name for display.

        Args:
            activity_name: Raw activity name.

        Returns:
            Formatted label string.
        """
        # Convert snake_case to Title Case
        parts = activity_name.replace("_", " ").split()
        return " ".join(word.capitalize() for word in parts)
