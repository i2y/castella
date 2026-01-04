"""View components for Edda Workflow Manager."""

from edda_workflow_manager.views.dashboard import DashboardView
from edda_workflow_manager.views.execution_list import ExecutionListView
from edda_workflow_manager.views.execution_detail import ExecutionDetailView
from edda_workflow_manager.views.live_viewer import LiveViewer
from edda_workflow_manager.views.definitions import DefinitionsView

__all__ = [
    "DashboardView",
    "ExecutionListView",
    "ExecutionDetailView",
    "LiveViewer",
    "DefinitionsView",
]
