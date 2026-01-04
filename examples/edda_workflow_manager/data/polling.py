"""Polling manager for real-time updates.

Provides background polling of Edda storage with configurable intervals.
"""

from __future__ import annotations

import asyncio
import logging
import threading
from datetime import datetime
from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from edda_workflow_manager.data.service import EddaDataService
    from edda_workflow_manager.models.instance import (
        WorkflowInstance,
        DashboardStats,
    )
    from edda_workflow_manager.models.execution import EddaExecutionState

logger = logging.getLogger(__name__)


class PollingManager:
    """Manages periodic data polling with configurable intervals.

    Runs polling in a background thread to avoid blocking the UI.
    Supports multiple polling modes:
    - List mode: Poll for instance list updates
    - Detail mode: Poll for single instance updates
    - Stats mode: Poll for dashboard statistics

    Example:
        ```python
        manager = PollingManager(data_service, on_update)
        manager.set_mode_list(status_filter="running")
        manager.start()

        # Later...
        manager.stop()
        ```
    """

    def __init__(
        self,
        data_service: "EddaDataService",
        on_update: Callable[[Any], None],
        interval_ms: int = 2000,
    ):
        """Initialize polling manager.

        Args:
            data_service: EddaDataService instance.
            on_update: Callback function called with new data.
            interval_ms: Polling interval in milliseconds.
        """
        self._service = data_service
        self._on_update = on_update
        self._interval_ms = interval_ms

        # Polling state
        self._running = False
        self._thread: threading.Thread | None = None
        self._loop: asyncio.AbstractEventLoop | None = None
        self._stop_event = threading.Event()

        # Polling mode
        self._mode: str = "list"  # "list", "detail", "stats"
        self._instance_id: str | None = None
        self._status_filter: str | None = None
        self._workflow_filter: str | None = None

        # Cache for change detection
        self._last_data_hash: int | None = None

    def set_interval(self, interval_ms: int) -> None:
        """Update polling interval.

        Args:
            interval_ms: New interval in milliseconds.
        """
        self._interval_ms = interval_ms

    def set_mode_list(
        self,
        status_filter: str | None = None,
        workflow_filter: str | None = None,
    ) -> None:
        """Set polling to list mode.

        Args:
            status_filter: Optional status filter.
            workflow_filter: Optional workflow name filter.
        """
        self._mode = "list"
        self._instance_id = None
        self._status_filter = status_filter
        self._workflow_filter = workflow_filter
        self._last_data_hash = None

    def set_mode_detail(self, instance_id: str) -> None:
        """Set polling to detail mode for a single instance.

        Args:
            instance_id: Workflow instance ID to poll.
        """
        self._mode = "detail"
        self._instance_id = instance_id
        self._status_filter = None
        self._workflow_filter = None
        self._last_data_hash = None

    def set_mode_stats(self) -> None:
        """Set polling to stats mode for dashboard."""
        self._mode = "stats"
        self._instance_id = None
        self._status_filter = None
        self._workflow_filter = None
        self._last_data_hash = None

    def start(self) -> None:
        """Start polling in background thread."""
        if self._running:
            return

        self._running = True
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        logger.debug("Polling started with interval %dms", self._interval_ms)

    def stop(self) -> None:
        """Stop polling."""
        if not self._running:
            return

        self._running = False
        self._stop_event.set()

        if self._thread:
            self._thread.join(timeout=2.0)
            self._thread = None

        logger.debug("Polling stopped")

    def is_running(self) -> bool:
        """Check if polling is running."""
        return self._running

    def _run_loop(self) -> None:
        """Background thread loop."""
        from edda_workflow_manager.runtime import get_edda_loop

        edda_loop = get_edda_loop()

        while self._running and not self._stop_event.is_set():
            try:
                # Run poll in the shared Edda event loop
                future = asyncio.run_coroutine_threadsafe(self._poll(), edda_loop)
                future.result(timeout=10.0)  # Wait for completion with timeout
            except Exception as e:
                logger.error("Polling error: %s", e)

            # Wait for interval
            self._stop_event.wait(timeout=self._interval_ms / 1000.0)

    async def _poll(self) -> None:
        """Execute single poll based on current mode."""
        try:
            if self._mode == "list":
                await self._poll_list()
            elif self._mode == "detail":
                await self._poll_detail()
            elif self._mode == "stats":
                await self._poll_stats()
        except Exception as e:
            logger.error("Poll failed: %s", e)

    async def _poll_list(self) -> None:
        """Poll for instance list updates."""
        result = await self._service.list_instances(
            limit=100,
            status_filter=self._status_filter,
            workflow_filter=self._workflow_filter,
        )

        # Check for changes
        data_hash = self._compute_list_hash(result.items)
        if data_hash != self._last_data_hash:
            self._last_data_hash = data_hash
            self._on_update(result.items)

    async def _poll_detail(self) -> None:
        """Poll for single instance updates."""
        if not self._instance_id:
            return

        execution_state = await self._service.get_execution_state(self._instance_id)
        if execution_state:
            # Check for changes
            data_hash = self._compute_state_hash(execution_state)
            if data_hash != self._last_data_hash:
                self._last_data_hash = data_hash
                self._on_update(execution_state)

    async def _poll_stats(self) -> None:
        """Poll for dashboard statistics."""
        stats = await self._service.get_statistics()

        # Check for changes
        data_hash = hash(
            (stats.running, stats.completed, stats.failed, stats.waiting)
        )
        if data_hash != self._last_data_hash:
            self._last_data_hash = data_hash
            self._on_update(stats)

    def _compute_list_hash(
        self, instances: list["WorkflowInstance"]
    ) -> int:
        """Compute hash of instance list for change detection."""
        # Hash based on instance IDs, statuses, and update times
        return hash(
            tuple(
                (i.instance_id, i.status.value, i.updated_at.isoformat())
                for i in instances
            )
        )

    def _compute_state_hash(self, state: "EddaExecutionState") -> int:
        """Compute hash of execution state for change detection."""
        return hash(
            (
                state.instance_id,
                state.instance_status.value,
                state.total_steps,
                state.current_node_id,
                tuple(s.node_id for s in state.step_history),
            )
        )


class PollingContext:
    """Context manager for scoped polling.

    Example:
        ```python
        async with PollingContext(manager, mode="detail", instance_id="abc"):
            # Polling is active
            pass
        # Polling is stopped
        ```
    """

    def __init__(
        self,
        manager: PollingManager,
        mode: str = "list",
        instance_id: str | None = None,
        status_filter: str | None = None,
        interval_ms: int | None = None,
    ):
        self._manager = manager
        self._mode = mode
        self._instance_id = instance_id
        self._status_filter = status_filter
        self._interval_ms = interval_ms
        self._prev_interval: int | None = None

    def __enter__(self) -> PollingManager:
        if self._interval_ms:
            self._prev_interval = self._manager._interval_ms
            self._manager.set_interval(self._interval_ms)

        if self._mode == "list":
            self._manager.set_mode_list(status_filter=self._status_filter)
        elif self._mode == "detail" and self._instance_id:
            self._manager.set_mode_detail(self._instance_id)
        elif self._mode == "stats":
            self._manager.set_mode_stats()

        self._manager.start()
        return self._manager

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self._manager.stop()
        if self._prev_interval:
            self._manager.set_interval(self._prev_interval)
