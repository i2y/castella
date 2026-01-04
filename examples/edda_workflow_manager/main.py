"""Edda Workflow Manager - Main entry point.

A Castella-based GUI application for managing Edda workflow executions
with workflow visualization, execution history, and live monitoring.

Usage:
    # Read-only mode (no Start Execution button)
    uv run python examples/edda_workflow_manager/main.py \
        --db sqlite+aiosqlite:///path/to/edda.db

    # Direct execution mode (import workflow modules)
    uv run python examples/edda_workflow_manager/main.py \
        --db sqlite+aiosqlite:///path/to/edda.db \
        --import-module my_app.workflows

    # CloudEvent mode (send to external Edda server)
    uv run python examples/edda_workflow_manager/main.py \
        --db sqlite+aiosqlite:///path/to/edda.db \
        --edda-url http://localhost:8001

    # Both modes (user can choose)
    uv run python examples/edda_workflow_manager/main.py \
        --db sqlite+aiosqlite:///path/to/edda.db \
        --import-module my_app.workflows \
        --edda-url http://localhost:8001
"""

from __future__ import annotations

import argparse
import importlib
import sys
from pathlib import Path


def main():
    """Run the Edda Workflow Manager."""
    parser = argparse.ArgumentParser(
        description="Edda Workflow Manager - GUI for managing workflow executions",
    )
    parser.add_argument(
        "--db",
        type=str,
        required=True,
        help="Database connection string (e.g., sqlite:///path/to/edda.db)",
    )
    parser.add_argument(
        "--edda-url",
        type=str,
        default=None,
        help="Edda app URL for CloudEvent-based workflow start (e.g., http://localhost:8001)",
    )
    parser.add_argument(
        "--import-module",
        type=str,
        action="append",
        default=[],
        help="Import workflow module for direct execution (can be specified multiple times)",
    )
    parser.add_argument(
        "--width",
        type=int,
        default=1400,
        help="Window width (default: 1400)",
    )
    parser.add_argument(
        "--height",
        type=int,
        default=900,
        help="Window height (default: 900)",
    )

    args = parser.parse_args()

    # Add script directory to path for local imports FIRST
    # This is needed for both edda_workflow_manager imports and --import-module
    script_dir = Path(__file__).parent.parent
    if str(script_dir) not in sys.path:
        sys.path.insert(0, str(script_dir))

    # Initialize Edda
    try:
        from edda import EddaApp
    except ImportError as e:
        print(f"Error: Could not import edda: {e}")
        sys.exit(1)

    # Initialize the persistent event loop for Edda operations
    from edda_workflow_manager.runtime import (
        init_edda_loop,
        run_in_edda_loop,
        shutdown_edda_loop,
    )

    init_edda_loop()

    # Create EddaApp (handles storage internally)
    edda_app = EddaApp(
        service_name="edda-workflow-manager",
        db_url=args.db,
    )

    # Initialize EddaApp in the persistent loop
    run_in_edda_loop(edda_app.initialize())

    # Import workflow modules after EddaApp is initialized (in the same loop context)
    for module_path in args.import_module:
        try:
            importlib.import_module(module_path)
            print(f"Imported workflow module: {module_path}")
        except ImportError as e:
            print(f"Warning: Could not import module '{module_path}': {e}")

    # Import Castella
    from castella import App
    from castella.frame import Frame

    from edda_workflow_manager.app import EddaWorkflowManager

    # Create the manager component
    manager = EddaWorkflowManager(
        storage=edda_app.storage,
        edda_app_url=args.edda_url,
        can_start_direct=bool(args.import_module),
    )

    # Create and run the app
    app = App(
        Frame(
            "Edda Workflow Manager",
            width=args.width,
            height=args.height,
        ),
        manager,
    )

    try:
        app.run()
    finally:
        # Clean up: shutdown Edda and stop the event loop
        run_in_edda_loop(edda_app.shutdown())
        shutdown_edda_loop()


if __name__ == "__main__":
    main()
