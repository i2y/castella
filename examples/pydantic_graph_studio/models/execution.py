"""Execution state models for pydantic-graph Studio."""

from __future__ import annotations

from typing import Any

from pydantic import Field

from castella.studio.models.execution import (
    BaseExecutionState,
    BaseStepResult,
)


class GraphStepResult(BaseStepResult):
    """pydantic-graph specific step result.

    Extends BaseStepResult with:
        node_class: The class name of the node that executed.
        node_data: The node instance data (fields).
        returned_type: The type name of the returned value.
        is_end: Whether this step returned End[T].
    """

    node_class: str = ""
    node_data: dict[str, Any] = Field(default_factory=dict)
    returned_type: str = ""
    is_end: bool = False


class GraphExecutionState(BaseExecutionState):
    """pydantic-graph execution state.

    Extends BaseExecutionState with:
        step_history: List of GraphStepResult.
        current_graph_state: Current StateT value.
        current_deps: Current DepsT value.
        result: Final End[T] value if completed.
    """

    step_history: list[GraphStepResult] = Field(default_factory=list)
    current_graph_state: dict[str, Any] = Field(default_factory=dict)
    current_deps: dict[str, Any] = Field(default_factory=dict)
    result: Any = None
