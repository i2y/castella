"""LlamaIndex Workflow Studio - Main entry point.

Usage:
    uv run python examples/llamaindex_studio/main.py
    uv run python examples/llamaindex_studio/main.py path/to/workflow.py
"""

from __future__ import annotations

import sys
from pathlib import Path

from castella import App
from castella.frame import Frame

from examples.llamaindex_studio.components.studio import WorkflowStudio


def main():
    """Run the LlamaIndex Workflow Studio."""
    # Check for command line arguments
    initial_file = None
    if len(sys.argv) > 1:
        initial_file = sys.argv[1]

    # Default samples directory
    samples_dir = str(Path(__file__).parent / "samples")

    # Create the studio component
    studio = WorkflowStudio(
        samples_dir=samples_dir,
        initial_file=initial_file,
    )

    # Create and run the app
    app = App(
        Frame("LlamaIndex Workflow Studio", width=1200, height=800),
        studio,
    )
    app.run()


if __name__ == "__main__":
    main()
