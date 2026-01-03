"""Base execution state models for workflow studios.

These models provide a common foundation for tracking workflow execution
state across different frameworks (LangGraph, LlamaIndex Workflow, etc.).
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ExecutionStatus(str, Enum):
    """Status of workflow execution."""

    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    ERROR = "error"


class BaseStepResult(BaseModel):
    """Base result of executing a single node/step.

    Attributes:
        node_id: ID of the executed node/step.
        state_before: State before execution.
        state_after: State after execution.
        started_at_ms: Timestamp when step started (epoch ms).
        duration_ms: Execution time in milliseconds.
        error: Error message if execution failed.
        metadata: Framework-specific metadata (e.g., tool calls, events).
    """

    node_id: str
    state_before: dict[str, Any] = Field(default_factory=dict)
    state_after: dict[str, Any] = Field(default_factory=dict)
    started_at_ms: float = 0.0
    duration_ms: float = 0.0
    error: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class BaseExecutionState(BaseModel):
    """Base execution state for workflow studios.

    Attributes:
        status: Current execution status.
        current_node_id: ID of the currently executing node/step.
        step_history: List of completed steps.
        total_steps: Total number of steps executed.
        error_message: Error message if execution failed.
        breakpoints: Set of node/step IDs where execution should pause.
        paused_at_breakpoint: True if currently paused at a breakpoint.
        executed_edges: List of (source, target) node ID pairs for traversed edges.
    """

    status: ExecutionStatus = ExecutionStatus.IDLE
    current_node_id: str | None = None
    step_history: list[BaseStepResult] = Field(default_factory=list)
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
