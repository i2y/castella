"""Execution state models for LangGraph Studio.

Extends the base execution models from castella.studio with
LangGraph-specific features like tool call tracking.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

# Re-export base classes for backwards compatibility
from castella.studio.models.execution import (
    ExecutionStatus,
    BaseStepResult,
    BaseExecutionState,
    compute_state_diff,
)


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


class StepResult(BaseStepResult):
    """LangGraph-specific step result with tool call tracking.

    Extends BaseStepResult with:
        tool_calls: List of tool calls made during this step.
    """

    tool_calls: list[ToolCallInfo] = Field(default_factory=list)


class ExecutionState(BaseExecutionState):
    """LangGraph execution state with graph state tracking.

    Extends BaseExecutionState with:
        step_history: List of LangGraph StepResult objects.
        current_state: Current graph state dictionary.
    """

    step_history: list[StepResult] = Field(default_factory=list)
    current_state: dict[str, Any] = Field(default_factory=dict)


# compute_state_diff is imported from base module above
