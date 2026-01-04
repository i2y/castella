"""Main Edda Workflow Manager application component."""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Any

from castella import (
    Component,
    Column,
    Row,
    Box,
    Button,
    Text,
    Spacer,
    State,
    Kind,
    SizePolicy,
)

from edda_workflow_manager.widgets.start_execution_modal import StartExecutionModal

from edda_workflow_manager.views.dashboard import DashboardView
from edda_workflow_manager.views.execution_list import ExecutionListView
from edda_workflow_manager.views.execution_detail import ExecutionDetailView
from edda_workflow_manager.views.live_viewer import LiveViewer
from edda_workflow_manager.views.definitions import DefinitionsView
from edda_workflow_manager.data.service import EddaDataService
from edda_workflow_manager.data.polling import PollingManager
from edda_workflow_manager.models.instance import (
    WorkflowInstance,
    WorkflowDefinition,
    DashboardStats,
)
from edda_workflow_manager.models.execution import EddaExecutionState

if TYPE_CHECKING:
    from edda.storage.protocol import StorageProtocol

logger = logging.getLogger(__name__)


class EddaWorkflowManager(Component):
    """Main Edda Workflow Manager application component.

    Provides a tabbed interface for:
    - Dashboard: Statistics and recent executions
    - Executions: List and detail views
    - Live Viewer: Real-time execution monitoring
    - Definitions: Workflow definition management
    """

    def __init__(
        self,
        storage: "StorageProtocol",
        edda_app_url: str | None = None,
        can_start_direct: bool = False,
    ):
        """Initialize the workflow manager.

        Args:
            storage: Edda StorageProtocol instance.
            edda_app_url: Optional Edda app URL for CloudEvent workflow start.
            can_start_direct: Whether direct execution is available (--import-module).
        """
        super().__init__()

        # Store configuration
        self._edda_app_url = edda_app_url
        self._can_start_direct = can_start_direct

        # Data layer
        self._data_service = EddaDataService(storage)
        self._polling = PollingManager(
            self._data_service,
            self._on_polling_update,
            interval_ms=2000,
        )

        # Navigation state
        self._current_view: State[str] = State("dashboard")
        self._current_view.attach(self)

        # Selected instance for detail view
        self._selected_instance_id: State[str | None] = State(None)
        self._selected_instance_id.attach(self)

        # Data states
        self._stats: State[DashboardStats] = State(DashboardStats())
        self._stats.attach(self)

        self._instances: State[list[WorkflowInstance]] = State([])
        self._instances.attach(self)

        self._running_instances: State[list[WorkflowInstance]] = State([])
        self._running_instances.attach(self)

        self._selected_instance: State[WorkflowInstance | None] = State(None)
        self._selected_instance.attach(self)

        self._execution_state: State[EddaExecutionState | None] = State(None)
        self._execution_state.attach(self)

        self._workflow_template: State[list[str]] = State([])
        self._workflow_template.attach(self)

        self._definitions: State[list[WorkflowDefinition]] = State([])
        self._definitions.attach(self)

        self._definition_templates: State[dict[str, list[str]]] = State({})
        self._definition_templates.attach(self)

        self._has_more: State[bool] = State(False)
        self._has_more.attach(self)

        # Filter states
        self._status_filter: State[str | None] = State(None)
        self._status_filter.attach(self)

        # Note: Don't attach _search_query - Input manages its own state
        # Attaching would cause focus loss on every keystroke
        self._search_query: State[str] = State("")

        # Loading/error states
        self._loading: State[bool] = State(False)
        self._loading.attach(self)

        # Pending workflow to auto-select (set by workflow start, consumed by polling)
        self._pending_workflow_name: str | None = None
        self._known_instance_ids: set[str] = set()

        # Flag to prevent duplicate execution state loads
        self._loading_execution_state: bool = False

        self._error: State[str | None] = State(None)
        self._error.attach(self)

        # Start execution modal
        self._start_modal = StartExecutionModal(
            on_execute=self._on_execute_workflow,
            on_close=self._on_close_start_modal,
        )
        self._start_modal.attach(self)

        # Initial data load
        self._load_initial_data()

    def _load_initial_data(self) -> None:
        """Load initial data in background."""
        from edda_workflow_manager.runtime import get_edda_loop

        loop = get_edda_loop()
        asyncio.run_coroutine_threadsafe(self._async_load_initial(), loop)

    async def _async_load_initial(self) -> None:
        """Async initial data load."""
        try:
            # Load stats
            stats = await self._data_service.get_statistics()
            self._stats.set(stats)

            # Load recent instances
            result = await self._data_service.list_instances(limit=50)
            self._instances.set(result.items)
            self._has_more.set(result.has_more)

            # Load running instances
            running = await self._data_service.get_running_instances()
            self._running_instances.set(running)

            # Load definitions
            definitions = await self._data_service.list_definitions()
            self._definitions.set(definitions)

            # Load templates for each definition
            templates: dict[str, list[str]] = {}
            for defn in definitions:
                template = await self._data_service.get_workflow_template(
                    defn.workflow_name
                )
                if template:
                    templates[defn.workflow_name] = template
            self._definition_templates.set(templates)

        except Exception as e:
            logger.error("Failed to load initial data: %s", e)
            self._error.set(str(e))

    def view(self):
        """Build the main application UI."""
        current = self._current_view()

        main_content = Column(
            # Navigation bar (fixed height) - inline to avoid Component nesting issues
            Row(
                Text("Edda Workflow Manager").text_color("#bb9af7"),
                Spacer().fixed_width(40),
                self._build_nav_button("dashboard", "Dashboard", current),
                self._build_nav_button("executions", "Executions", current),
                self._build_nav_button("live", "Live Viewer", current),
                self._build_nav_button("definitions", "Definitions", current),
                Spacer(),
            ).fixed_height(48).bg_color("#1e1f2b"),

            # Main content (fills remaining space)
            self._build_content(current),
        ).bg_color("#1a1b26")

        # Show start execution modal if open
        if self._start_modal.is_open:
            return Box(main_content, self._start_modal.build())

        return main_content

    def _build_nav_button(self, tab_id: str, label: str, current: str) -> Button:
        """Build a navigation button."""
        is_active = current == tab_id
        kind = Kind.INFO if is_active else Kind.NORMAL
        return (
            Button(label)
            .kind(kind)
            .fixed_height(36)
            .fixed_width(100)
            .on_click(lambda _, tid=tab_id: self._on_view_change(tid))
        )

    def _build_content(self, view_id: str) -> Component:
        """Build content for the current view."""
        if view_id == "dashboard":
            return DashboardView(
                stats=self._stats(),
                recent_executions=self._instances()[:10],
                on_view_all=lambda: self._on_view_change("executions"),
                on_select_instance=self._on_select_instance,
                on_refresh=self._refresh_data,
            )

        elif view_id == "executions":
            # Show detail view if instance is selected
            if self._selected_instance_id():
                return ExecutionDetailView(
                    instance=self._selected_instance(),
                    history=[],  # TODO: Load history
                    execution_state=self._execution_state(),
                    on_back=self._on_back_to_list,
                    on_cancel=self._on_cancel_instance,
                    on_step_select=lambda step: None,
                )
            else:
                return ExecutionListView(
                    instances=self._instances(),
                    status_filter=self._status_filter(),
                    search_query=self._search_query(),
                    has_more=self._has_more(),
                    on_status_change=self._on_status_change,
                    on_search_change=self._on_search_change,
                    on_select_instance=self._on_select_instance,
                    on_refresh=self._refresh_data,
                    on_load_more=self._load_more,
                )

        elif view_id == "live":
            return LiveViewer(
                running_instances=self._running_instances(),
                selected_instance=self._selected_instance(),
                execution_state=self._execution_state(),
                workflow_template=self._workflow_template(),
                on_select_instance=self._on_select_instance,
                on_stop=self._on_cancel_instance,
                on_refresh=self._refresh_running,
            )

        elif view_id == "definitions":
            return DefinitionsView(
                definitions=self._definitions(),
                workflow_templates=self._definition_templates(),
                on_view_source=self._on_view_source,
                on_start_execution=self._on_start_execution,
                on_refresh=self._refresh_definitions,
                can_start_execution=bool(self._edda_app_url or self._can_start_direct),
            )

        else:
            return Column(
                Text(f"Unknown view: {view_id}").text_color("#f7768e"),
            )

    # -------------------------------------------------------------------------
    # Navigation
    # -------------------------------------------------------------------------

    def _on_view_change(self, view_id: str) -> None:
        """Handle navigation to a different view."""
        self._current_view.set(view_id)
        self._selected_instance_id.set(None)
        self._selected_instance.set(None)
        self._execution_state.set(None)
        self._workflow_template.set([])

        # Start/stop polling based on view
        self._polling.stop()

        if view_id == "dashboard":
            self._polling.set_mode_stats()
            self._polling.set_interval(5000)
            self._polling.start()
        elif view_id == "executions":
            self._polling.set_mode_list(status_filter=self._status_filter())
            self._polling.set_interval(2000)
            self._polling.start()
        elif view_id == "live":
            self._polling.set_mode_list(status_filter="running")
            self._polling.set_interval(1000)
            self._polling.start()

    def _on_back_to_list(self) -> None:
        """Navigate back to execution list."""
        self._selected_instance_id.set(None)
        self._selected_instance.set(None)
        self._execution_state.set(None)

    # -------------------------------------------------------------------------
    # Instance Selection
    # -------------------------------------------------------------------------

    def _on_select_instance(self, instance_id: str) -> None:
        """Handle instance selection."""
        self._selected_instance_id.set(instance_id)

        # If in Live Viewer, stay there and keep list polling
        if self._current_view() == "live":
            self._on_select_instance_live(instance_id)
            return

        # Navigate to executions view to show detail
        self._current_view.set("executions")

        # Load instance details in background
        from edda_workflow_manager.runtime import get_edda_loop

        loop = get_edda_loop()
        asyncio.run_coroutine_threadsafe(self._async_load_instance(instance_id), loop)

        # Update polling to focus on this instance
        self._polling.stop()
        self._polling.set_mode_detail(instance_id)
        self._polling.set_interval(1000)
        self._polling.start()

    def _on_select_instance_live(self, instance_id: str) -> None:
        """Handle instance selection in Live Viewer (keeps list polling active)."""
        from edda_workflow_manager.runtime import get_edda_loop

        # Load instance details in background
        loop = get_edda_loop()
        asyncio.run_coroutine_threadsafe(self._async_load_instance(instance_id), loop)

        # Keep polling in list mode for running instances
        # The execution state will be loaded separately

    async def _async_load_execution_state(self, instance_id: str) -> None:
        """Load execution state for an instance."""
        try:
            execution_state = await self._data_service.get_execution_state(instance_id)
            if execution_state:
                self._execution_state.set(execution_state)
        except Exception as e:
            logger.error("Failed to load execution state: %s", e)

    async def _async_load_execution_state_with_flag(self, instance_id: str) -> None:
        """Load execution state with loading flag management."""
        try:
            execution_state = await self._data_service.get_execution_state(instance_id)
            if execution_state:
                self._execution_state.set(execution_state)
                # Also update selected_instance status if it's the same instance
                current_instance = self._selected_instance()
                if current_instance and current_instance.instance_id == instance_id:
                    current_instance.status = execution_state.instance_status
                    self._selected_instance.set(current_instance)
        except Exception as e:
            logger.error("Failed to load execution state: %s", e)
        finally:
            self._loading_execution_state = False

    async def _async_load_instance(self, instance_id: str) -> None:
        """Load instance details async."""
        try:
            instance = await self._data_service.get_instance(instance_id)
            if instance:
                self._selected_instance.set(instance)

                # Load workflow template from historical executions
                template = await self._data_service.get_workflow_template(
                    instance.workflow_name
                )
                self._workflow_template.set(template)

            execution_state = await self._data_service.get_execution_state(
                instance_id
            )
            if execution_state:
                self._execution_state.set(execution_state)

        except Exception as e:
            logger.error("Failed to load instance: %s", e)
            self._error.set(str(e))

    # -------------------------------------------------------------------------
    # Filtering
    # -------------------------------------------------------------------------

    def _on_status_change(self, status: str | None) -> None:
        """Handle status filter change."""
        self._status_filter.set(status)
        self._refresh_data()

    def _on_search_change(self, query: str) -> None:
        """Handle search query change."""
        self._search_query.set(query)
        # Don't refresh immediately, wait for user to stop typing

    # -------------------------------------------------------------------------
    # Actions
    # -------------------------------------------------------------------------

    def _on_cancel_instance(self, instance_id: str | None = None) -> None:
        """Cancel a workflow instance."""
        target_id = instance_id or self._selected_instance_id()
        if not target_id or not self._edda_app_url:
            return

        from edda_workflow_manager.runtime import get_edda_loop

        async def cancel():
            try:
                success, message = await self._data_service.cancel_instance(
                    target_id, self._edda_app_url
                )
                if not success:
                    self._error.set(message)
            except Exception as e:
                self._error.set(str(e))

        loop = get_edda_loop()
        asyncio.run_coroutine_threadsafe(cancel(), loop)

    def _on_view_source(self, workflow_name: str, source_hash: str) -> None:
        """View source code for a workflow."""
        # This would open a modal with the source code
        pass

    def _on_start_execution(self, workflow_name: str) -> None:
        """Open start execution modal for a workflow."""
        if not self._edda_app_url and not self._can_start_direct:
            self._error.set("No execution method available. Use --edda-url or --import-module")
            return

        # Open the modal
        self._start_modal.open(
            workflow_name,
            can_direct=self._can_start_direct,
            can_cloudevent=bool(self._edda_app_url),
        )

    def _on_execute_workflow(
        self,
        workflow_name: str,
        params: dict,
        use_direct: bool,
    ) -> None:
        """Execute a workflow with the given parameters.

        Args:
            workflow_name: Workflow name to execute.
            params: Workflow parameters.
            use_direct: If True, use direct execution; otherwise use CloudEvent.
        """
        from edda_workflow_manager.runtime import get_edda_loop

        # Close modal and navigate to Live Viewer immediately (on main thread)
        self._start_modal.close()
        # Navigate without resetting instance (don't use _on_view_change)
        self._current_view.set("live")

        # Remember current known instance IDs before starting
        current_instances = self._running_instances()
        self._known_instance_ids = {inst.instance_id for inst in current_instances}

        # Set pending workflow name to find the new instance
        self._pending_workflow_name = workflow_name

        # Start polling for running instances
        self._polling.stop()
        self._polling.set_mode_list(status_filter="running")
        self._polling.set_interval(500)  # Poll faster while waiting for new instance
        self._polling.start()

        async def execute():
            try:
                if use_direct:
                    # Start workflow without waiting for completion
                    success, message, _ = await self._data_service.start_workflow_direct_async(
                        workflow_name, params
                    )
                else:
                    success, message, _ = await self._data_service.start_workflow(
                        workflow_name, params, self._edda_app_url
                    )

                if not success:
                    self._error.set(f"Failed to start workflow: {message}")
                    self._pending_workflow_name = None
            except Exception as e:
                self._error.set(f"Failed to start workflow: {e}")
                self._pending_workflow_name = None

        loop = get_edda_loop()
        asyncio.run_coroutine_threadsafe(execute(), loop)

    def _on_close_start_modal(self) -> None:
        """Close the start execution modal."""
        # Modal handles its own close, this is just for any additional cleanup
        pass

    # -------------------------------------------------------------------------
    # Data Loading
    # -------------------------------------------------------------------------

    def _refresh_data(self) -> None:
        """Refresh current view data."""
        from edda_workflow_manager.runtime import get_edda_loop

        loop = get_edda_loop()
        asyncio.run_coroutine_threadsafe(self._async_refresh(), loop)

    async def _async_refresh(self) -> None:
        """Async data refresh."""
        try:
            result = await self._data_service.list_instances(
                limit=50,
                status_filter=self._status_filter(),
                search_query=self._search_query() or None,
            )
            self._instances.set(result.items)
            self._has_more.set(result.has_more)

            stats = await self._data_service.get_statistics()
            self._stats.set(stats)

        except Exception as e:
            logger.error("Failed to refresh data: %s", e)
            self._error.set(str(e))

    def _refresh_running(self) -> None:
        """Refresh running instances."""
        from edda_workflow_manager.runtime import get_edda_loop

        async def refresh():
            try:
                running = await self._data_service.get_running_instances()
                self._running_instances.set(running)
            except Exception as e:
                logger.error("Failed to refresh running: %s", e)

        loop = get_edda_loop()
        asyncio.run_coroutine_threadsafe(refresh(), loop)

    def _refresh_definitions(self) -> None:
        """Refresh workflow definitions and templates."""
        from edda_workflow_manager.runtime import get_edda_loop

        async def refresh():
            try:
                definitions = await self._data_service.list_definitions()
                self._definitions.set(definitions)

                # Load templates for each definition
                templates: dict[str, list[str]] = {}
                for defn in definitions:
                    template = await self._data_service.get_workflow_template(
                        defn.workflow_name
                    )
                    if template:
                        templates[defn.workflow_name] = template
                self._definition_templates.set(templates)
            except Exception as e:
                logger.error("Failed to refresh definitions: %s", e)

        loop = get_edda_loop()
        asyncio.run_coroutine_threadsafe(refresh(), loop)

    def _load_more(self) -> None:
        """Load more instances (pagination)."""
        # TODO: Implement pagination with page tokens
        pass

    # -------------------------------------------------------------------------
    # Polling Callback
    # -------------------------------------------------------------------------

    def _on_polling_update(self, data: Any) -> None:
        """Handle polling update from background thread."""
        if isinstance(data, DashboardStats):
            self._stats.set(data)
        elif isinstance(data, EddaExecutionState):
            self._execution_state.set(data)
            # Also update selected_instance status from execution state
            current_instance = self._selected_instance()
            if current_instance and data.instance_id == current_instance.instance_id:
                # Update the instance with new status
                current_instance.status = data.instance_status
                self._selected_instance.set(current_instance)
        elif isinstance(data, list):
            if data and isinstance(data[0], WorkflowInstance):
                # Check current mode
                if self._current_view() == "live":
                    self._running_instances.set(data)

                    # Check for pending workflow to auto-select (do this first)
                    if self._pending_workflow_name:
                        for inst in data:
                            # Find a new instance with the pending workflow name
                            if (inst.workflow_name == self._pending_workflow_name and
                                inst.instance_id not in self._known_instance_ids):
                                # Found the new instance - select it
                                self._pending_workflow_name = None
                                self._known_instance_ids.clear()
                                self._polling.set_interval(1000)  # Reset to normal polling speed
                                self._on_select_instance(inst.instance_id)
                                return  # Exit early, selection will trigger its own state load

                    # Update selected instance from the list if we have one selected
                    selected_id = self._selected_instance_id()
                    if selected_id:
                        for inst in data:
                            if inst.instance_id == selected_id:
                                self._selected_instance.set(inst)
                                break

                        # Load execution state for the selected instance
                        # (only if not already loading - avoid duplicate loads)
                        if not self._loading_execution_state:
                            self._loading_execution_state = True
                            from edda_workflow_manager.runtime import get_edda_loop
                            loop = get_edda_loop()
                            asyncio.run_coroutine_threadsafe(
                                self._async_load_execution_state_with_flag(selected_id), loop
                            )
                else:
                    self._instances.set(data)
