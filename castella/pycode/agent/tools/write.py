"""File writing tool."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from castella.pycode.agent.coding_agent import ToolCallback


async def write_tool(
    path: str,
    content: str,
    cwd: Path,
    on_tool_use: "ToolCallback",
) -> str:
    """Write content to a file.

    Args:
        path: Path to the file (relative to cwd or absolute)
        content: Content to write
        cwd: Working directory
        on_tool_use: Callback to notify UI of tool use

    Returns:
        Success message or error
    """
    on_tool_use("write", {"path": path, "content_length": len(content)})

    try:
        # Resolve path
        file_path = cwd / path if not path.startswith("/") else Path(path)

        # Ensure parent directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Write file
        file_path.write_text(content, encoding="utf-8")

        return f"Successfully wrote {len(content)} bytes to {path}"

    except PermissionError:
        return f"Error: Permission denied: {path}"
    except Exception as e:
        return f"Error writing file: {e}"


def write_tool_sync(
    path: str,
    content: str,
    cwd: Path,
    on_tool_use: "ToolCallback",
) -> str:
    """Synchronous version of write_tool."""
    import asyncio

    return asyncio.get_event_loop().run_until_complete(
        write_tool(path, content, cwd, on_tool_use)
    )
