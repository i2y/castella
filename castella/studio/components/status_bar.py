"""Shared status bar component for workflow studios."""

from __future__ import annotations

from castella import Component, Row, Text, Spacer, TextAlign, SizePolicy
from castella.theme import Kind

from castella.studio.models.execution import BaseExecutionState, ExecutionStatus


# Status to Kind mapping
STATUS_KINDS = {
    ExecutionStatus.IDLE: Kind.NORMAL,  # Gray
    ExecutionStatus.RUNNING: Kind.SUCCESS,  # Green
    ExecutionStatus.PAUSED: Kind.WARNING,  # Yellow
    ExecutionStatus.ERROR: Kind.DANGER,  # Red
    ExecutionStatus.COMPLETED: Kind.INFO,  # Blue
}


class StatusBar(Component):
    """Status bar showing execution status and progress.

    Displays:
    - Status indicator (colored circle)
    - Current execution status (Idle, Running, etc.)
    - Active node/step name during execution
    - Step count
    - Error message if present
    """

    def __init__(self, execution: BaseExecutionState):
        """Initialize the status bar.

        Args:
            execution: Current execution state.
        """
        super().__init__()
        self._execution = execution

        # Fixed height for status bar
        self._size.height = 28
        self._height_policy = SizePolicy.FIXED

    def view(self):
        """Build the status bar UI."""
        execution = self._execution

        # Status text with indicator symbol
        status_text = self._get_status_text(execution)
        status_symbol = self._get_status_symbol(execution.status)
        status_kind = STATUS_KINDS.get(execution.status, Kind.NORMAL)

        # Build content with proper spacing
        parts = [
            # Left padding
            Spacer().fixed_width(12),
            # Status symbol and text with kind-based color
            Text(
                f"{status_symbol} {status_text}",
                kind=status_kind,
                align=TextAlign.LEFT,
                transparent_bg=True,
            ),
        ]

        # Add spacer before right-aligned content
        parts.append(Spacer())

        # Add step count if executed
        if execution.total_steps > 0:
            parts.append(Text(f"Steps: {execution.total_steps}"))
            parts.append(Spacer().fixed_width(16))

        # Add error message if present
        if execution.error_message:
            parts.append(Text(f"Error: {execution.error_message[:40]}..."))
            parts.append(Spacer().fixed_width(16))

        # Right padding
        parts.append(Spacer().fixed_width(12))

        return Row(*parts)

    def _get_status_symbol(self, status: ExecutionStatus) -> str:
        """Get status indicator symbol.

        Args:
            status: Current execution status.
        """
        symbols = {
            ExecutionStatus.IDLE: "●",
            ExecutionStatus.RUNNING: "▶",
            ExecutionStatus.PAUSED: "⏸",
            ExecutionStatus.ERROR: "✖",
            ExecutionStatus.COMPLETED: "✓",
        }
        return symbols.get(status, "●")

    def _get_status_text(self, execution: BaseExecutionState) -> str:
        """Get display text for status."""
        status = execution.status

        if status == ExecutionStatus.IDLE:
            return "Ready"
        elif status == ExecutionStatus.RUNNING:
            if execution.current_node_id:
                return f"Running: {execution.current_node_id}"
            return "Running..."
        elif status == ExecutionStatus.PAUSED:
            if execution.current_node_id:
                return f"Paused at: {execution.current_node_id}"
            return "Paused"
        elif status == ExecutionStatus.COMPLETED:
            return "Completed"
        elif status == ExecutionStatus.ERROR:
            return "Error"

        return status.value.title()
