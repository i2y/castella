#!/usr/bin/env python
"""Demo script for pycode - Python AI Coding Assistant.

Usage:
    # Mock mode (no API key needed)
    uv run python examples/pycode_demo.py --mock

    # With Anthropic API key
    ANTHROPIC_API_KEY=your-key uv run python examples/pycode_demo.py

    # With OpenAI API key
    OPENAI_API_KEY=your-key uv run python examples/pycode_demo.py --model gpt-4o

    # Specify working directory
    uv run python examples/pycode_demo.py --cwd /path/to/project --mock
"""

import sys

# Add the parent directory to the path for development
sys.path.insert(0, str(__file__).rsplit("/", 2)[0])

from castella.pycode import run

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="pycode demo")
    parser.add_argument("--mock", action="store_true", help="Use mock agent")
    parser.add_argument("--cwd", type=str, default=None, help="Working directory")
    parser.add_argument("--model", type=str, default=None, help="Model to use")

    args = parser.parse_args()

    # Set model via environment if specified
    if args.model:
        import os

        os.environ["PYCODE_MODEL"] = args.model

    run(cwd=args.cwd, mock=args.mock)
