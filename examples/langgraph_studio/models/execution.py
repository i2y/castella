"""Execution state models for LangGraph Studio."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ExecutionStatus(str, Enum):
    """Status of graph execution."""

    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    ERROR = "error"


class ToolCallInfo(BaseModel):
    """Information about a tool call made during execution.

    Attributes:
        tool_call_id: Unique ID of the tool call.
        tool_name: Name of the tool that was called.
        arguments: Arguments passed to the tool.
        result: Result returned by the tool.
    """

    tool_call_id: str = ""
    tool_name: str = ""
    arguments: dict[str, Any] = Field(default_factory=dict)
    result: Any = None


class StepResult(BaseModel):
    """Result of executing a single node.

    Attributes:
        node_id: ID of the executed node.
        state_before: State before execution.
        state_after: State after execution.
        duration_ms: Execution time in milliseconds.
        error: Error message if execution failed.
        tool_calls: List of tool calls made during this step.
    """

    node_id: str
    state_before: dict[str, Any] = Field(default_factory=dict)
    state_after: dict[str, Any] = Field(default_factory=dict)
    duration_ms: float = 0.0
    error: str | None = None
    tool_calls: list[ToolCallInfo] = Field(default_factory=list)


class ExecutionState(BaseModel):
    """Complete execution state.

    Attributes:
        status: Current execution status.
        current_node_id: ID of the currently executing node.
        step_history: List of completed steps.
        current_state: Current graph state.
        total_steps: Total number of steps executed.
        error_message: Error message if execution failed.
        breakpoints: Set of node IDs where execution should pause.
        paused_at_breakpoint: True if currently paused at a breakpoint.
        executed_edges: List of (source, target) node ID pairs for traversed edges.
    """

    status: ExecutionStatus = ExecutionStatus.IDLE
    current_node_id: str | None = None
    step_history: list[StepResult] = Field(default_factory=list)
    current_state: dict[str, Any] = Field(default_factory=dict)
    total_steps: int = 0
    error_message: str | None = None
    breakpoints: set[str] = Field(default_factory=set)
    paused_at_breakpoint: bool = False
    executed_edges: list[tuple[str, str]] = Field(default_factory=list)

    @property
    def is_running(self) -> bool:
        """Check if execution is currently running."""
        return self.status == ExecutionStatus.RUNNING

    @property
    def is_idle(self) -> bool:
        """Check if execution is idle."""
        return self.status == ExecutionStatus.IDLE

    @property
    def can_run(self) -> bool:
        """Check if execution can be started."""
        return self.status in (ExecutionStatus.IDLE, ExecutionStatus.COMPLETED)

    @property
    def can_stop(self) -> bool:
        """Check if execution can be stopped."""
        return self.status in (ExecutionStatus.RUNNING, ExecutionStatus.PAUSED)

    @property
    def can_pause(self) -> bool:
        """Check if execution can be paused."""
        return self.status == ExecutionStatus.RUNNING

    @property
    def can_continue(self) -> bool:
        """Check if execution can be continued."""
        return self.status == ExecutionStatus.PAUSED


def compute_state_diff(before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:
    """Compute the difference between two state dictionaries.

    Args:
        before: State before execution.
        after: State after execution.

    Returns:
        Dict with keys: added, modified, removed.
    """
    before_keys = set(before.keys())
    after_keys = set(after.keys())

    added = {k: after[k] for k in after_keys - before_keys}
    removed = {k: before[k] for k in before_keys - after_keys}
    modified = {}

    for k in before_keys & after_keys:
        if before[k] != after[k]:
            modified[k] = {"old": before[k], "new": after[k]}

    return {"added": added, "modified": modified, "removed": removed}
