"""Data service for Edda Workflow Manager.

Provides access to Edda storage for workflow instances, history, and definitions.
Adapted from edda/viewer_ui/data_service.py.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import TYPE_CHECKING, Any

from edda_workflow_manager.models.instance import (
    WorkflowInstance,
    ActivityHistory,
    WorkflowDefinition,
    DashboardStats,
    ActivityStatus,
)
from edda_workflow_manager.models.execution import EddaExecutionState

if TYPE_CHECKING:
    from edda.storage.protocol import StorageProtocol

logger = logging.getLogger(__name__)


class PaginatedResult:
    """Result of a paginated query."""

    def __init__(
        self,
        items: list[WorkflowInstance],
        next_page_token: str | None,
        has_more: bool,
    ):
        self.items = items
        self.next_page_token = next_page_token
        self.has_more = has_more


class EddaDataService:
    """Service for accessing Edda storage data.

    This service wraps the Edda StorageProtocol and provides typed access
    to workflow instances, history, and definitions using Pydantic models.
    """

    def __init__(self, storage: "StorageProtocol"):
        """Initialize data service.

        Args:
            storage: Storage instance implementing StorageProtocol.
        """
        self.storage = storage

    # -------------------------------------------------------------------------
    # Instance Methods
    # -------------------------------------------------------------------------

    async def list_instances(
        self,
        limit: int = 50,
        page_token: str | None = None,
        status_filter: str | None = None,
        workflow_filter: str | None = None,
        search_query: str | None = None,
        started_after: datetime | None = None,
        started_before: datetime | None = None,
    ) -> PaginatedResult:
        """List workflow instances with filtering and pagination.

        Args:
            limit: Maximum number of instances to return.
            page_token: Cursor for pagination.
            status_filter: Filter by status (e.g., "running", "completed").
            workflow_filter: Filter by workflow name (partial match).
            search_query: Search by workflow name or instance ID.
            started_after: Filter instances started after this datetime.
            started_before: Filter instances started before this datetime.

        Returns:
            PaginatedResult with WorkflowInstance items.
        """
        result = await self.storage.list_instances(
            limit=limit,
            page_token=page_token,
            status_filter=status_filter,
            workflow_name_filter=workflow_filter or search_query,
            instance_id_filter=search_query,
            started_after=started_after,
            started_before=started_before,
        )

        instances = [
            WorkflowInstance.from_storage(data)
            for data in result.get("instances", [])
        ]

        return PaginatedResult(
            items=instances,
            next_page_token=result.get("next_page_token"),
            has_more=result.get("has_more", False),
        )

    async def get_instance(self, instance_id: str) -> WorkflowInstance | None:
        """Get a single workflow instance by ID.

        Args:
            instance_id: Workflow instance ID.

        Returns:
            WorkflowInstance or None if not found.
        """
        data = await self.storage.get_instance(instance_id)
        if not data:
            return None
        return WorkflowInstance.from_storage(data)

    async def get_instance_history(
        self, instance_id: str
    ) -> list[ActivityHistory]:
        """Get execution history for a workflow instance.

        Args:
            instance_id: Workflow instance ID.

        Returns:
            List of ActivityHistory records.
        """
        instance = await self.storage.get_instance(instance_id)
        if not instance:
            return []

        history_rows = await self.storage.get_history(instance_id)
        workflow_name = instance.get("workflow_name", "unknown")

        history = []
        for row in history_rows:
            event_data = row.get("event_data", {})
            event_type = row.get("event_type", "")

            # Determine status from event_type
            if event_type == "ActivityCompleted":
                status = ActivityStatus.COMPLETED
            elif event_type == "ActivityFailed":
                status = ActivityStatus.FAILED
            elif event_type == "CompensationExecuted":
                status = ActivityStatus.COMPENSATED
            elif event_type == "CompensationFailed":
                status = ActivityStatus.COMPENSATION_FAILED
            elif event_type == "EventReceived":
                status = ActivityStatus.EVENT_RECEIVED
            else:
                status = ActivityStatus.RUNNING

            # Prepare activity name
            activity_id = row.get("activity_id", "")
            activity_name = event_data.get("activity_name", activity_id or "unknown")

            # For LlamaIndex Workflow: extract actual step name from input args
            # The _run_step activity stores the step name in input.args[1]
            if activity_name == "_run_step":
                input_args = event_data.get("input", {}).get("args", [])
                if len(input_args) >= 2:
                    activity_name = input_args[1]  # Step name (e.g., "receive_order")

            if event_type in ("CompensationExecuted", "CompensationFailed"):
                activity_name = f"Compensate: {activity_name}"

            # Parse input/output
            input_data = event_data.get("input", event_data.get("kwargs", {}))
            if isinstance(input_data, str):
                try:
                    input_data = json.loads(input_data)
                except json.JSONDecodeError:
                    input_data = {}

            output_data = event_data.get("result")

            # Parse datetime
            executed_at = row.get("created_at")
            if isinstance(executed_at, str):
                executed_at = datetime.fromisoformat(
                    executed_at.replace("Z", "+00:00")
                )

            history.append(
                ActivityHistory(
                    activity_id=activity_id,
                    activity_name=activity_name,
                    event_type=event_type,
                    status=status,
                    input_data=input_data,
                    output_data=output_data,
                    error_message=event_data.get("error_message"),
                    error_type=event_data.get("error_type"),
                    stack_trace=event_data.get("stack_trace"),
                    executed_at=executed_at,
                )
            )

        return history

    async def get_instance_compensations(
        self, instance_id: str
    ) -> dict[str, dict[str, Any]]:
        """Get registered compensations for a workflow instance.

        Args:
            instance_id: Workflow instance ID.

        Returns:
            Dict mapping activity_id to compensation info.
        """
        compensations_list = await self.storage.get_compensations(instance_id)

        compensations_map: dict[str, dict[str, Any]] = {}
        for comp in compensations_list:
            activity_id = comp.get("activity_id")
            if activity_id is not None:
                compensations_map[activity_id] = {
                    "activity_name": comp.get("activity_name"),
                    "args": comp.get("args", {}),
                }

        return compensations_map

    async def get_instance_detail(
        self, instance_id: str
    ) -> tuple[WorkflowInstance | None, list[ActivityHistory], dict[str, Any]]:
        """Get complete instance detail including history and compensations.

        Args:
            instance_id: Workflow instance ID.

        Returns:
            Tuple of (instance, history, compensations).
        """
        instance = await self.get_instance(instance_id)
        if not instance:
            return None, [], {}

        history = await self.get_instance_history(instance_id)
        compensations = await self.get_instance_compensations(instance_id)

        return instance, history, compensations

    async def get_execution_state(
        self, instance_id: str
    ) -> EddaExecutionState | None:
        """Get execution state for graph visualization.

        Args:
            instance_id: Workflow instance ID.

        Returns:
            EddaExecutionState or None if not found.
        """
        instance, history, compensations = await self.get_instance_detail(instance_id)
        if not instance:
            return None

        return EddaExecutionState.from_instance(
            instance_id=instance.instance_id,
            workflow_name=instance.workflow_name,
            status=instance.status,
            history=history,
            current_activity_id=instance.current_activity_id,
            compensations=compensations,
        )

    # -------------------------------------------------------------------------
    # Statistics Methods
    # -------------------------------------------------------------------------

    async def get_statistics(self) -> DashboardStats:
        """Get dashboard statistics.

        Returns:
            DashboardStats with counts by status.
        """
        # Get all instances (up to 1000 for stats)
        result = await self.list_instances(limit=1000)
        return DashboardStats.from_instances(result.items)

    async def get_recent_executions(
        self, limit: int = 10
    ) -> list[WorkflowInstance]:
        """Get most recent workflow executions.

        Args:
            limit: Maximum number of instances to return.

        Returns:
            List of recent WorkflowInstance records.
        """
        result = await self.list_instances(limit=limit)
        return result.items

    async def get_running_instances(self) -> list[WorkflowInstance]:
        """Get currently running workflow instances.

        Returns:
            List of running WorkflowInstance records.
        """
        result = await self.list_instances(limit=100, status_filter="running")
        return result.items

    # -------------------------------------------------------------------------
    # Workflow Template Methods (from historical executions)
    # -------------------------------------------------------------------------

    async def get_workflow_template(
        self, workflow_name: str
    ) -> list[str]:
        """Get workflow activity template from historical executions.

        Analyzes completed executions to build a list of all known activities
        in execution order. This is used to show the full workflow graph
        before execution starts.

        Args:
            workflow_name: Name of the workflow.

        Returns:
            List of activity names in execution order.
        """
        # Get completed instances of this workflow
        result = await self.storage.list_instances(
            limit=10,  # Check last 10 executions
            status_filter="completed",
            workflow_name_filter=workflow_name,
        )

        all_activities: list[str] = []
        seen: set[str] = set()

        for instance_data in result.get("instances", []):
            instance_id = instance_data.get("instance_id")
            if not instance_id:
                continue

            # Get history for this instance
            history_rows = await self.storage.get_history(instance_id)

            for row in history_rows:
                event_type = row.get("event_type", "")
                event_data = row.get("event_data", {})

                # Skip non-activity events
                if event_type not in ("ActivityCompleted", "ActivityFailed"):
                    continue

                # Get activity name
                activity_id = row.get("activity_id", "")
                activity_name = event_data.get("activity_name", activity_id or "unknown")

                # For LlamaIndex Workflow: extract step name from input args
                if activity_name == "_run_step":
                    input_args = event_data.get("input", {}).get("args", [])
                    if len(input_args) >= 2:
                        activity_name = input_args[1]

                # Skip compensation activities
                if activity_name.startswith("Compensate:"):
                    continue

                # Add to list if not seen
                if activity_name not in seen:
                    seen.add(activity_name)
                    all_activities.append(activity_name)

        return all_activities

    # -------------------------------------------------------------------------
    # Definition Methods
    # -------------------------------------------------------------------------

    async def list_definitions(self) -> list[WorkflowDefinition]:
        """List all workflow definitions.

        Note: This queries unique workflow_name + source_hash combinations.

        Returns:
            List of WorkflowDefinition records.
        """
        # Get definitions from storage
        # Note: StorageProtocol doesn't have a list_definitions method,
        # so we extract unique definitions from instances
        result = await self.storage.list_instances(limit=1000)

        seen: set[tuple[str, str]] = set()
        definitions: list[WorkflowDefinition] = []

        for instance_data in result.get("instances", []):
            key = (instance_data["workflow_name"], instance_data.get("source_hash", ""))
            if key not in seen:
                seen.add(key)

                # Try to get full definition with source code
                definition_data = await self.storage.get_workflow_definition(
                    instance_data["workflow_name"],
                    instance_data.get("source_hash", ""),
                )

                if definition_data:
                    definitions.append(WorkflowDefinition.from_storage(definition_data))
                else:
                    # Create from instance data (without source code)
                    started_at = instance_data.get("started_at")
                    if isinstance(started_at, str):
                        started_at = datetime.fromisoformat(
                            started_at.replace("Z", "+00:00")
                        )

                    definitions.append(
                        WorkflowDefinition(
                            workflow_name=instance_data["workflow_name"],
                            source_hash=instance_data.get("source_hash", ""),
                            source_code=instance_data.get("source_code", ""),
                            created_at=started_at,
                        )
                    )

        return definitions

    async def get_definition_source(
        self, workflow_name: str, source_hash: str
    ) -> str | None:
        """Get source code for a workflow definition.

        Args:
            workflow_name: Workflow name.
            source_hash: Source hash.

        Returns:
            Source code string or None if not found.
        """
        definition = await self.storage.get_workflow_definition(
            workflow_name, source_hash
        )
        if definition:
            return definition.get("source_code")
        return None

    # -------------------------------------------------------------------------
    # Action Methods
    # -------------------------------------------------------------------------

    async def cancel_instance(
        self, instance_id: str, edda_app_url: str
    ) -> tuple[bool, str]:
        """Cancel a workflow instance via Edda API.

        Args:
            instance_id: Workflow instance ID.
            edda_app_url: Edda app API URL.

        Returns:
            Tuple of (success, message).
        """
        try:
            import httpx

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{edda_app_url}/cancel/{instance_id}",
                    timeout=10.0,
                )

                if 200 <= response.status_code < 300:
                    return True, "Workflow cancelled successfully"
                elif response.status_code == 400:
                    error_msg = response.json().get("error", "Unknown error")
                    return False, f"Cannot cancel: {error_msg}"
                elif response.status_code == 404:
                    return False, "Workflow not found"
                else:
                    return False, f"Server error: HTTP {response.status_code}"

        except Exception as e:
            logger.error("Failed to cancel workflow: %s", e)
            return False, f"Error: {e}"

    async def start_workflow(
        self,
        workflow_name: str,
        params: dict[str, Any],
        edda_app_url: str,
    ) -> tuple[bool, str, str | None]:
        """Start a new workflow execution via CloudEvent.

        Args:
            workflow_name: Workflow name (event type).
            params: Workflow parameters (event data).
            edda_app_url: Edda app API URL.

        Returns:
            Tuple of (success, message, instance_id or None).
        """
        try:
            import uuid
            import httpx
            from cloudevents.conversion import to_structured
            from cloudevents.http import CloudEvent

            attributes = {
                "type": workflow_name,
                "source": "edda.workflow_manager",
                "id": str(uuid.uuid4()),
            }
            event = CloudEvent(attributes, data=params)
            headers, body = to_structured(event)

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    edda_app_url,
                    headers=headers,
                    content=body,
                    timeout=10.0,
                )

                if 200 <= response.status_code < 300:
                    return True, f"Workflow '{workflow_name}' started", None
                else:
                    return False, f"Server error: HTTP {response.status_code}", None

        except ImportError:
            return False, "cloudevents package not installed", None
        except Exception as e:
            logger.error("Failed to start workflow: %s", e)
            return False, f"Error: {e}", None

    async def start_workflow_direct(
        self,
        workflow_name: str,
        params: dict[str, Any],
    ) -> tuple[bool, str, str | None]:
        """Start a new workflow execution directly (in-process).

        Requires that workflow modules have been imported via --import-module.
        NOTE: This waits for the workflow to complete.

        Args:
            workflow_name: Workflow name (must match registered workflow).
            params: Workflow parameters.

        Returns:
            Tuple of (success, message, instance_id or None).
        """
        try:
            # Import edda's workflow registry
            from edda.workflow import get_all_workflows

            workflows = get_all_workflows()
            if workflow_name not in workflows:
                available = ", ".join(workflows.keys()) if workflows else "none"
                return (
                    False,
                    f"Workflow '{workflow_name}' not found. Available: {available}",
                    None,
                )

            workflow_func = workflows[workflow_name]

            # Start the workflow
            instance_id = await workflow_func.start(**params)

            return True, f"Workflow '{workflow_name}' started", instance_id

        except ImportError as e:
            logger.error("Failed to import edda workflow module: %s", e)
            return False, f"Import error: {e}", None
        except Exception as e:
            logger.error("Failed to start workflow directly: %s", e)
            return False, f"Error: {e}", None

    async def start_workflow_direct_async(
        self,
        workflow_name: str,
        params: dict[str, Any],
    ) -> tuple[bool, str, str | None]:
        """Start a new workflow execution directly without waiting for completion.

        Requires that workflow modules have been imported via --import-module.
        The workflow runs in the background.

        Args:
            workflow_name: Workflow name (must match registered workflow).
            params: Workflow parameters.

        Returns:
            Tuple of (success, message, workflow_name to find the instance).
        """
        try:
            import asyncio

            # Import edda's workflow registry
            from edda.workflow import get_all_workflows

            workflows = get_all_workflows()
            if workflow_name not in workflows:
                available = ", ".join(workflows.keys()) if workflows else "none"
                return (
                    False,
                    f"Workflow '{workflow_name}' not found. Available: {available}",
                    None,
                )

            workflow_func = workflows[workflow_name]

            # Start the workflow in the background without waiting
            async def run_workflow():
                try:
                    await workflow_func.start(**params)
                except Exception as e:
                    logger.error("Workflow execution failed: %s", e)

            asyncio.create_task(run_workflow())

            # Return workflow_name instead of instance_id (we'll find it by name)
            return True, f"Workflow '{workflow_name}' started", workflow_name

        except ImportError as e:
            logger.error("Failed to import edda workflow module: %s", e)
            return False, f"Import error: {e}", None
        except Exception as e:
            logger.error("Failed to start workflow directly: %s", e)
            return False, f"Error: {e}", None
