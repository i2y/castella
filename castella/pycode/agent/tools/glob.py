"""File pattern matching tool using glob."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from castella.pycode.agent.coding_agent import ToolCallback


async def glob_tool(
    pattern: str,
    cwd: Path,
    on_tool_use: "ToolCallback",
    max_results: int = 100,
) -> str:
    """Find files matching a glob pattern.

    Args:
        pattern: Glob pattern (e.g., "**/*.py", "src/**/*.ts")
        cwd: Working directory
        on_tool_use: Callback to notify UI of tool use
        max_results: Maximum number of results to return

    Returns:
        List of matching files
    """
    on_tool_use("glob", {"pattern": pattern})

    try:
        # Find matching files
        matches = list(cwd.glob(pattern))

        # Sort by modification time (newest first)
        matches.sort(key=lambda p: p.stat().st_mtime if p.exists() else 0, reverse=True)

        # Limit results
        total = len(matches)
        matches = matches[:max_results]

        if not matches:
            return f"No files found matching pattern: {pattern}"

        # Format results
        results = []
        for match in matches:
            try:
                rel_path = match.relative_to(cwd)
            except ValueError:
                rel_path = match
            results.append(str(rel_path))

        output = "\n".join(results)
        if total > max_results:
            output += f"\n\n... and {total - max_results} more files"

        return output

    except Exception as e:
        return f"Error searching files: {e}"


def glob_tool_sync(
    pattern: str,
    cwd: Path,
    on_tool_use: "ToolCallback",
    max_results: int = 100,
) -> str:
    """Synchronous version of glob_tool."""
    import asyncio

    return asyncio.get_event_loop().run_until_complete(
        glob_tool(pattern, cwd, on_tool_use, max_results)
    )
