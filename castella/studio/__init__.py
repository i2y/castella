"""Castella Studio - Shared abstractions for workflow visualization studios.

This module provides base classes and shared components that can be used
by both LangGraph Desktop and LlamaIndex Workflow Studio.
"""

from castella.studio.models.execution import (
    BaseExecutionState,
    BaseStepResult,
    ExecutionStatus,
    compute_state_diff,
)
from castella.studio.executor.base import BaseWorkflowExecutor
from castella.studio.widgets.canvas import BaseStudioCanvas

__all__ = [
    # Models
    "BaseExecutionState",
    "BaseStepResult",
    "ExecutionStatus",
    "compute_state_diff",
    # Executor
    "BaseWorkflowExecutor",
    # Widgets
    "BaseStudioCanvas",
]
