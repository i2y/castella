"""Dashboard view for Edda Workflow Manager."""

from __future__ import annotations

from typing import TYPE_CHECKING, Callable

from castella import (
    Component,
    Column,
    Row,
    Button,
    Text,
    Spacer,
    State,
    Kind,
    SizePolicy,
)

from edda_workflow_manager.widgets.stats_card import StatsCard
from edda_workflow_manager.models.instance import (
    DashboardStats,
    WorkflowInstance,
)

if TYPE_CHECKING:
    from edda_workflow_manager.data.service import EddaDataService


class DashboardView(Component):
    """Dashboard with summary statistics and recent executions.

    ```
    ┌─────────────────────────────────────────────────────────────┐
    │  [Running: 5]  [Completed: 123]  [Failed: 2]  [Waiting: 3]   │
    ├─────────────────────────────────────────────────────────────┤
    │  Recent Executions                                          │
    │  ┌────────────────────────────────────────────────────────┐ │
    │  │ instance_abc  order_saga   Running    10s ago          │ │
    │  │ instance_xyz  payment_wf   Completed  1m ago           │ │
    │  └────────────────────────────────────────────────────────┘ │
    ├─────────────────────────────────────────────────────────────┤
    │  [View All Executions]  [Refresh]                           │
    └─────────────────────────────────────────────────────────────┘
    ```
    """

    def __init__(
        self,
        stats: DashboardStats | None = None,
        recent_executions: list[WorkflowInstance] | None = None,
        on_view_all: Callable[[], None] | None = None,
        on_select_instance: Callable[[str], None] | None = None,
        on_refresh: Callable[[], None] | None = None,
    ):
        """Initialize dashboard view.

        Args:
            stats: Dashboard statistics.
            recent_executions: List of recent workflow instances.
            on_view_all: Callback for "View All" button.
            on_select_instance: Callback when instance is selected.
            on_refresh: Callback for refresh button.
        """
        super().__init__()
        self._stats = stats or DashboardStats()
        self._recent = recent_executions or []
        self._on_view_all = on_view_all
        self._on_select_instance = on_select_instance
        self._on_refresh = on_refresh

    def view(self):
        """Build the dashboard view."""
        stats = self._stats

        return Column(
            # Stats row (fixed height at top)
            Row(
                StatsCard(
                    title="Running",
                    value=stats.running,
                    kind=Kind.SUCCESS,
                ),
                StatsCard(
                    title="Completed",
                    value=stats.completed,
                    kind=Kind.INFO,
                ),
                StatsCard(
                    title="Failed",
                    value=stats.failed,
                    kind=Kind.DANGER,
                ),
                StatsCard(
                    title="Waiting",
                    value=stats.waiting,
                    kind=Kind.WARNING,
                ),
                StatsCard(
                    title="Compensating",
                    value=stats.compensating,
                    kind=Kind.WARNING,
                ),
                StatsCard(
                    title="Total",
                    value=stats.total,
                    kind=Kind.NORMAL,
                ),
                Spacer(),
            ).fixed_height(100),

            # Section header
            Text("Recent Executions")
            .fixed_height(32)
            .text_color("#bb9af7"),

            # Recent executions list (expanding)
            self._build_recent_list(),

            # Action buttons (fixed height at bottom)
            Row(
                Button("View All Executions")
                .kind(Kind.INFO)
                .fixed_height(36)
                .on_click(lambda _: self._on_view_all() if self._on_view_all else None),
                Spacer().fixed_width(16),
                Button("Refresh")
                .fixed_height(36)
                .on_click(lambda _: self._on_refresh() if self._on_refresh else None),
                Spacer(),
            ).fixed_height(52),
        ).bg_color("#1a1b26").height_policy(SizePolicy.EXPANDING)

    def _build_recent_list(self) -> Column:
        """Build the recent executions list."""
        if not self._recent:
            return Column(
                Text("No recent executions")
                .text_color("#6b7280")
                .fixed_height(40),
            ).height_policy(SizePolicy.EXPANDING)

        items = [self._build_instance_row(inst) for inst in self._recent[:10]]
        return Column(*items, scrollable=True).height_policy(SizePolicy.EXPANDING)

    def _build_instance_row(self, instance: WorkflowInstance) -> Row:
        """Build a single instance row."""
        # Status indicator
        status = instance.status
        if status.value == "running":
            status_color = "#9ece6a"
            status_icon = "●"
        elif status.value == "completed":
            status_color = "#7aa2f7"
            status_icon = "✓"
        elif status.value == "failed":
            status_color = "#f7768e"
            status_icon = "✗"
        elif status.is_waiting:
            status_color = "#e0af68"
            status_icon = "◎"
        else:
            status_color = "#6b7280"
            status_icon = "○"

        return (
            Row(
                # Status indicator
                Text(status_icon)
                .fixed_width(24)
                .text_color(status_color),
                # Instance ID
                Text(instance.short_instance_id)
                .fixed_width(140)
                .text_color("#c0caf5"),
                # Workflow name
                Text(instance.workflow_name)
                .fixed_width(180)
                .text_color("#9ca3af"),
                # Status
                Text(status.display_name)
                .fixed_width(120)
                .text_color(status_color),
                # Duration
                Text(instance.duration_display)
                .fixed_width(80)
                .text_color("#6b7280"),
                # Spacer
                Spacer(),
                # View button
                Button("View")
                .fixed_height(24)
                .fixed_width(60)
                .on_click(
                    lambda _, iid=instance.instance_id: (
                        self._on_select_instance(iid)
                        if self._on_select_instance
                        else None
                    )
                ),
            )
            .fixed_height(32)
            .bg_color("#1e1f2b")
        )
