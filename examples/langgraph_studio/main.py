"""LangGraph Studio Desktop - Main entry point.

A visual development environment for LangGraph, built with Castella.

Usage:
    uv run python -m examples.langgraph_studio.main [path]

Args:
    path: Optional path - can be:
        - A Python file (.py) containing a LangGraph to load immediately
        - A directory to browse (default: current directory)
"""

from __future__ import annotations

import sys
from pathlib import Path

from castella import App
from castella.frame import Frame

from .components.studio import Studio


def main(initial_path: str = ".", initial_file: str | None = None) -> None:
    """Launch LangGraph Studio Desktop.

    Args:
        initial_path: Initial directory for file browser.
        initial_file: Optional Python file to load on startup.
    """
    # Create application
    frame = Frame("LangGraph Studio", width=1400, height=900)
    studio = Studio(initial_path=initial_path, initial_file=initial_file)
    app = App(frame, studio)

    # Run application
    app.run()


if __name__ == "__main__":
    # Get path from command line args
    arg_path = sys.argv[1] if len(sys.argv) > 1 else "."
    path = Path(arg_path)

    if not path.exists():
        print(f"Error: Path does not exist: {arg_path}")
        sys.exit(1)

    if path.is_file() and path.suffix == ".py":
        # File specified - load it directly
        main(initial_path=str(path.parent.resolve()), initial_file=str(path.resolve()))
    else:
        # Directory specified
        main(initial_path=str(path.resolve()))
