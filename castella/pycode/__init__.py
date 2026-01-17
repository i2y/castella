"""pycode - Python AI Coding Assistant.

A pi/opencode-style AI coding assistant built with Castella and pydantic-ai.

Example:
    # Run the assistant
    uv run python -m castella.pycode

    # Run in a specific directory
    uv run python -m castella.pycode --cwd /path/to/project

    # Run with mock agent (no API key needed)
    uv run python -m castella.pycode --mock
"""

from __future__ import annotations

__all__ = [
    "run",
    "CodingAgent",
    "CodingDeps",
    "Config",
]


def run(cwd: str | None = None, mock: bool = False) -> None:
    """Run the pycode assistant.

    Args:
        cwd: Working directory (defaults to current directory)
        mock: Use mock agent instead of real LLM
    """
    from castella.pycode.app import main

    main(cwd=cwd, mock=mock)


# Lazy imports to avoid circular dependencies
def __getattr__(name: str):
    if name == "CodingAgent":
        from castella.pycode.agent.coding_agent import CodingAgent

        return CodingAgent
    if name == "CodingDeps":
        from castella.pycode.agent.coding_agent import CodingDeps

        return CodingDeps
    if name == "Config":
        from castella.pycode.config import Config

        return Config
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
