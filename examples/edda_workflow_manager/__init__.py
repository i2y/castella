"""Edda Workflow Manager - Management GUI for Edda workflows.

This package provides a Castella-based GUI application for managing and monitoring
Edda workflow executions, including:

- Dashboard with execution statistics
- Execution list with filtering and pagination
- Execution detail view with graph visualization
- Live execution viewer
- Workflow definitions management
"""

from edda_workflow_manager.app import EddaWorkflowManager

__all__ = ["EddaWorkflowManager"]
