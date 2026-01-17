"""File reading tool."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

    from castella.pycode.agent.coding_agent import ToolCallback


async def read_tool(
    path: str,
    cwd: "Path",
    on_tool_use: "ToolCallback",
    offset: int = 0,
    limit: int = 2000,
) -> str:
    """Read contents of a file.

    Args:
        path: Path to the file (relative to cwd or absolute)
        cwd: Working directory
        on_tool_use: Callback to notify UI of tool use
        offset: Line number to start reading from (0-based)
        limit: Maximum number of lines to read

    Returns:
        File contents with line numbers
    """
    on_tool_use("read", {"path": path, "offset": offset, "limit": limit})

    try:
        # Resolve path
        file_path = (
            cwd / path if not path.startswith("/") else __import__("pathlib").Path(path)
        )

        if not file_path.exists():
            return f"Error: File not found: {path}"

        if not file_path.is_file():
            return f"Error: Not a file: {path}"

        # Read file
        content = file_path.read_text(encoding="utf-8", errors="replace")
        lines = content.splitlines()

        # Apply offset and limit
        total_lines = len(lines)
        start = offset
        end = min(offset + limit, total_lines)

        if start >= total_lines:
            return f"Error: Offset {offset} exceeds file length ({total_lines} lines)"

        selected_lines = lines[start:end]

        # Format with line numbers (1-based for display)
        formatted_lines = []
        for i, line in enumerate(selected_lines, start=start + 1):
            # Truncate long lines
            if len(line) > 2000:
                line = line[:2000] + "... (truncated)"
            formatted_lines.append(f"{i:6}\t{line}")

        result = "\n".join(formatted_lines)

        # Add info header
        header = f"File: {path} (lines {start + 1}-{end} of {total_lines})"
        return f"{header}\n{'=' * len(header)}\n{result}"

    except UnicodeDecodeError:
        return f"Error: Cannot read file as text (binary file?): {path}"
    except PermissionError:
        return f"Error: Permission denied: {path}"
    except Exception as e:
        return f"Error reading file: {e}"


def read_tool_sync(
    path: str,
    cwd: "Path",
    on_tool_use: "ToolCallback",
    offset: int = 0,
    limit: int = 2000,
) -> str:
    """Synchronous version of read_tool."""
    import asyncio

    return asyncio.get_event_loop().run_until_complete(
        read_tool(path, cwd, on_tool_use, offset, limit)
    )
