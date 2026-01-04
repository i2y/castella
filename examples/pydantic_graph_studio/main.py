#!/usr/bin/env python3
"""pydantic-graph Studio - Workflow visualization and execution tool.

A visual studio for pydantic-graph that allows you to:
- Visualize graph structure from Python files
- Execute graphs step-by-step
- Set breakpoints and inspect state
- View execution history

Usage:
    # Run with mock graph (no pydantic-graph required)
    uv run python -m examples.pydantic_graph_studio.main

    # Run with a specific Python file
    uv run python -m examples.pydantic_graph_studio.main path/to/graph.py

    # Run browsing a specific directory
    uv run python -m examples.pydantic_graph_studio.main --path ./my_graphs/
"""

from __future__ import annotations

import argparse
from pathlib import Path

from castella import App
from castella.frame import Frame

from .components.studio import PydanticGraphStudio
from .samples.mock_graph import create_mock_graph


def main():
    """Run the pydantic-graph Studio."""
    parser = argparse.ArgumentParser(
        description="pydantic-graph Studio - Workflow visualization and execution"
    )
    parser.add_argument(
        "file",
        nargs="?",
        help="Python file containing a pydantic-graph to load",
    )
    parser.add_argument(
        "--path",
        default=".",
        help="Initial directory for file browser (default: current directory)",
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Start with a mock graph for demonstration",
    )
    parser.add_argument(
        "--width",
        type=int,
        default=1200,
        help="Window width (default: 1200)",
    )
    parser.add_argument(
        "--height",
        type=int,
        default=800,
        help="Window height (default: 800)",
    )

    args = parser.parse_args()

    # Determine initial path
    initial_path = args.path
    if args.file:
        # If a file is specified, use its directory as initial path
        file_path = Path(args.file).resolve()
        if file_path.exists():
            initial_path = str(file_path.parent)

    # Resolve samples directory for file browser
    samples_dir = Path(__file__).parent / "samples"
    if initial_path == "." and samples_dir.exists():
        initial_path = str(samples_dir)

    # Create the studio component
    studio = PydanticGraphStudio(
        initial_path=initial_path,
        initial_file=args.file,
    )

    # Load mock graph if requested or if no file specified
    if args.mock or (not args.file):
        mock_graph = create_mock_graph()
        studio.load_mock_graph(mock_graph)

    # Create and run the app
    frame = Frame(
        title="pydantic-graph Studio",
        width=args.width,
        height=args.height,
    )

    app = App(frame, studio)
    app.run()


if __name__ == "__main__":
    main()
