"""Workflow instance and activity history models.

These Pydantic models represent data from Edda's storage layer.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class InstanceStatus(str, Enum):
    """Workflow instance status values."""

    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    WAITING_FOR_EVENT = "waiting_for_event"
    WAITING_FOR_TIMER = "waiting_for_timer"
    WAITING_FOR_MESSAGE = "waiting_for_message"
    COMPENSATING = "compensating"
    CANCELLED = "cancelled"
    RECURRED = "recurred"

    @property
    def display_name(self) -> str:
        """Human-readable status name."""
        return self.value.replace("_", " ").title()

    @property
    def is_terminal(self) -> bool:
        """Whether this is a terminal (final) status."""
        return self in (
            InstanceStatus.COMPLETED,
            InstanceStatus.FAILED,
            InstanceStatus.CANCELLED,
        )

    @property
    def is_waiting(self) -> bool:
        """Whether the workflow is waiting for something."""
        return self in (
            InstanceStatus.WAITING_FOR_EVENT,
            InstanceStatus.WAITING_FOR_TIMER,
            InstanceStatus.WAITING_FOR_MESSAGE,
        )


class ActivityStatus(str, Enum):
    """Activity execution status."""

    COMPLETED = "completed"
    FAILED = "failed"
    RUNNING = "running"
    COMPENSATED = "compensated"
    COMPENSATION_FAILED = "compensation_failed"
    EVENT_RECEIVED = "event_received"


class WorkflowInstance(BaseModel):
    """Workflow instance from Edda storage."""

    instance_id: str
    workflow_name: str
    source_hash: str
    owner_service: str
    framework: str = "python"
    status: InstanceStatus
    current_activity_id: str | None = None
    started_at: datetime
    updated_at: datetime
    input_data: dict[str, Any] = Field(default_factory=dict)
    output_data: dict[str, Any] | None = None
    continued_from: str | None = None
    locked_by: str | None = None
    locked_at: datetime | None = None
    source_code: str | None = None

    @property
    def duration_seconds(self) -> float | None:
        """Calculate duration in seconds."""
        if self.updated_at and self.started_at:
            return (self.updated_at - self.started_at).total_seconds()
        return None

    @property
    def duration_display(self) -> str:
        """Human-readable duration."""
        duration = self.duration_seconds
        if duration is None:
            return "-"

        if duration < 60:
            return f"{duration:.1f}s"
        elif duration < 3600:
            minutes = int(duration // 60)
            seconds = int(duration % 60)
            return f"{minutes}m {seconds}s"
        else:
            hours = int(duration // 3600)
            minutes = int((duration % 3600) // 60)
            return f"{hours}h {minutes}m"

    @property
    def short_instance_id(self) -> str:
        """Truncated instance ID for display."""
        if len(self.instance_id) > 12:
            return self.instance_id[:12] + "..."
        return self.instance_id

    @classmethod
    def from_storage(cls, data: dict[str, Any]) -> WorkflowInstance:
        """Create instance from storage data dict."""
        # Parse datetime fields
        started_at = data.get("started_at")
        if isinstance(started_at, str):
            started_at = datetime.fromisoformat(started_at.replace("Z", "+00:00"))

        updated_at = data.get("updated_at")
        if isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))

        locked_at = data.get("locked_at")
        if isinstance(locked_at, str):
            locked_at = datetime.fromisoformat(locked_at.replace("Z", "+00:00"))

        # Parse input/output data if they're strings
        input_data = data.get("input_data", {})
        if isinstance(input_data, str):
            import json
            try:
                input_data = json.loads(input_data)
            except json.JSONDecodeError:
                input_data = {}

        output_data = data.get("output_data")
        if isinstance(output_data, str):
            import json
            try:
                output_data = json.loads(output_data)
            except json.JSONDecodeError:
                output_data = None

        # Map status string to enum
        status_str = data.get("status", "running")
        try:
            status = InstanceStatus(status_str)
        except ValueError:
            status = InstanceStatus.RUNNING

        return cls(
            instance_id=data["instance_id"],
            workflow_name=data["workflow_name"],
            source_hash=data.get("source_hash", ""),
            owner_service=data.get("owner_service", "unknown"),
            framework=data.get("framework", "python"),
            status=status,
            current_activity_id=data.get("current_activity_id"),
            started_at=started_at,
            updated_at=updated_at,
            input_data=input_data,
            output_data=output_data,
            continued_from=data.get("continued_from"),
            locked_by=data.get("locked_by"),
            locked_at=locked_at,
            source_code=data.get("source_code"),
        )


class ActivityHistory(BaseModel):
    """Single activity execution record from workflow history."""

    activity_id: str
    activity_name: str
    event_type: str
    status: ActivityStatus
    input_data: dict[str, Any] = Field(default_factory=dict)
    output_data: Any = None
    error_message: str | None = None
    error_type: str | None = None
    stack_trace: str | None = None
    executed_at: datetime

    @property
    def has_error(self) -> bool:
        """Whether this activity failed."""
        return self.status in (
            ActivityStatus.FAILED,
            ActivityStatus.COMPENSATION_FAILED,
        )

    @property
    def is_compensation(self) -> bool:
        """Whether this is a compensation activity."""
        return self.event_type in ("CompensationExecuted", "CompensationFailed")

    @classmethod
    def from_storage(cls, data: dict[str, Any]) -> ActivityHistory:
        """Create activity history from storage data dict."""
        # Parse datetime
        executed_at = data.get("executed_at") or data.get("created_at")
        if isinstance(executed_at, str):
            executed_at = datetime.fromisoformat(executed_at.replace("Z", "+00:00"))

        # Parse input/output data
        input_data = data.get("input_data", {})
        if isinstance(input_data, str):
            import json
            try:
                input_data = json.loads(input_data)
            except json.JSONDecodeError:
                input_data = {}

        output_data = data.get("output_data")
        if isinstance(output_data, str):
            import json
            try:
                output_data = json.loads(output_data)
            except json.JSONDecodeError:
                output_data = None

        # Map status string to enum
        status_str = data.get("status", "running")
        try:
            status = ActivityStatus(status_str)
        except ValueError:
            status = ActivityStatus.RUNNING

        return cls(
            activity_id=data.get("activity_id", ""),
            activity_name=data.get("activity_name", "unknown"),
            event_type=data.get("event_type", ""),
            status=status,
            input_data=input_data,
            output_data=output_data,
            error_message=data.get("error"),
            error_type=data.get("error_type"),
            stack_trace=data.get("stack_trace"),
            executed_at=executed_at,
        )


class WorkflowDefinition(BaseModel):
    """Workflow definition from storage."""

    workflow_name: str
    source_hash: str
    source_code: str
    created_at: datetime

    @classmethod
    def from_storage(cls, data: dict[str, Any]) -> WorkflowDefinition:
        """Create definition from storage data dict."""
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))

        return cls(
            workflow_name=data["workflow_name"],
            source_hash=data["source_hash"],
            source_code=data.get("source_code", ""),
            created_at=created_at,
        )


class DashboardStats(BaseModel):
    """Dashboard statistics."""

    running: int = 0
    completed: int = 0
    failed: int = 0
    waiting: int = 0
    compensating: int = 0
    cancelled: int = 0
    total: int = 0

    @classmethod
    def from_instances(cls, instances: list[WorkflowInstance]) -> DashboardStats:
        """Calculate stats from a list of instances."""
        stats = cls()
        for instance in instances:
            stats.total += 1
            if instance.status == InstanceStatus.RUNNING:
                stats.running += 1
            elif instance.status == InstanceStatus.COMPLETED:
                stats.completed += 1
            elif instance.status == InstanceStatus.FAILED:
                stats.failed += 1
            elif instance.status.is_waiting:
                stats.waiting += 1
            elif instance.status == InstanceStatus.COMPENSATING:
                stats.compensating += 1
            elif instance.status == InstanceStatus.CANCELLED:
                stats.cancelled += 1
        return stats
