"""Execution list view for Edda Workflow Manager."""

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
    Input,
)
from castella.table import DataTable, DataTableState, ColumnConfig

from edda_workflow_manager.models.instance import WorkflowInstance
from edda_workflow_manager.widgets.filter_bar import FilterBar

if TYPE_CHECKING:
    from edda_workflow_manager.data.service import PaginatedResult


class ExecutionListView(Component):
    """Paginated list of workflow executions.

    ```
    ┌─────────────────────────────────────────────────────────────┐
    │  [All] [Running] [Completed] [Failed]  [Search: ______]    │
    ├─────────────────────────────────────────────────────────────┤
    │  Instance ID    Workflow      Status     Started    Dur    │
    │  ──────────────────────────────────────────────────────────│
    │  abc-123...     order_saga    ● Running  10:30:00   10s   │
    │  def-456...     payment_wf    ✓ Done     10:29:00   5s    │
    │  ghi-789...     order_saga    ✗ Failed   10:28:00   3s    │
    ├─────────────────────────────────────────────────────────────┤
    │  ◄ Prev  Page 1 of 10  Next ►                              │
    └─────────────────────────────────────────────────────────────┘
    ```
    """

    def __init__(
        self,
        instances: list[WorkflowInstance] | None = None,
        status_filter: str | None = None,
        search_query: str = "",
        has_more: bool = False,
        on_status_change: Callable[[str | None], None] | None = None,
        on_search_change: Callable[[str], None] | None = None,
        on_select_instance: Callable[[str], None] | None = None,
        on_refresh: Callable[[], None] | None = None,
        on_load_more: Callable[[], None] | None = None,
    ):
        """Initialize execution list view.

        Args:
            instances: List of workflow instances.
            status_filter: Current status filter.
            search_query: Current search query.
            has_more: Whether more pages are available.
            on_status_change: Callback when status filter changes.
            on_search_change: Callback when search query changes.
            on_select_instance: Callback when instance is selected.
            on_refresh: Callback for refresh.
            on_load_more: Callback for loading more instances.
        """
        super().__init__()
        self._instances = instances or []
        self._status_filter = status_filter
        self._search_query = search_query
        self._has_more = has_more
        self._on_status_change = on_status_change
        self._on_search_change = on_search_change
        self._on_select_instance = on_select_instance
        self._on_refresh = on_refresh
        self._on_load_more = on_load_more

        # Create table state
        self._table_state = self._create_table_state()

    def _create_table_state(self) -> DataTableState:
        """Create DataTableState from instances."""
        columns = [
            ColumnConfig(name="Status", width=80, sortable=True),
            ColumnConfig(name="Instance ID", width=150, sortable=True),
            ColumnConfig(name="Workflow", width=180, sortable=True),
            ColumnConfig(name="Status Text", width=120, sortable=True),
            ColumnConfig(name="Started", width=150, sortable=True),
            ColumnConfig(name="Duration", width=80, sortable=True),
        ]

        rows = []
        for inst in self._instances:
            # Status indicator
            if inst.status.value == "running":
                status_icon = "●"
            elif inst.status.value == "completed":
                status_icon = "✓"
            elif inst.status.value == "failed":
                status_icon = "✗"
            elif inst.status.is_waiting:
                status_icon = "◎"
            else:
                status_icon = "○"

            rows.append([
                status_icon,
                inst.short_instance_id,
                inst.workflow_name,
                inst.status.display_name,
                inst.started_at.strftime("%Y-%m-%d %H:%M:%S"),
                inst.duration_display,
            ])

        return DataTableState(columns=columns, rows=rows)

    def view(self):
        """Build the execution list view."""
        # Build filter bar inline to avoid Component nesting issues
        status_buttons = []
        for status, label in [
            (None, "All"),
            ("running", "Running"),
            ("completed", "Completed"),
            ("failed", "Failed"),
            ("waiting_for_event", "Waiting"),
            ("compensating", "Compensating"),
        ]:
            is_active = self._status_filter == status
            kind = Kind.INFO if is_active else Kind.NORMAL
            btn = (
                Button(label)
                .kind(kind)
                .fixed_height(32)
                .fixed_width(100)
                .on_click(lambda _, s=status: self._on_status_change(s) if self._on_status_change else None)
            )
            status_buttons.append(btn)

        filter_bar = (
            Row(
                *status_buttons,
                Spacer(),
                Input(self._search_query)
                .fixed_width(200)
                .fixed_height(32)
                .on_change(lambda t: self._on_search_change(t) if self._on_search_change else None),
                Button("Refresh")
                .fixed_height(32)
                .fixed_width(80)
                .on_click(lambda _: self._on_refresh() if self._on_refresh else None),
            )
            .fixed_height(48)
            .bg_color("#1e1f2b")
        )

        return Column(
            # Filter bar (inline)
            filter_bar,

            # Table
            DataTable(self._table_state)
            .on_cell_click(self._on_cell_click)
            .height_policy(SizePolicy.EXPANDING),

            # Pagination
            self._build_pagination(),
        ).bg_color("#1a1b26").height_policy(SizePolicy.EXPANDING)

    def _build_pagination(self) -> Row:
        """Build pagination controls."""
        return (
            Row(
                Spacer(),
                Text(f"Showing {len(self._instances)} executions")
                .fixed_width(200)
                .text_color("#9ca3af"),
                Button("Load More")
                .kind(Kind.INFO if self._has_more else Kind.NORMAL)
                .fixed_height(32)
                .on_click(
                    lambda _: self._on_load_more() if self._on_load_more else None
                ),
                Spacer(),
            )
            .fixed_height(48)
            .bg_color("#1e1f2b")
        )

    def _on_cell_click(self, event) -> None:
        """Handle table cell click."""
        if self._on_select_instance and event.row < len(self._instances):
            instance = self._instances[event.row]
            self._on_select_instance(instance.instance_id)
