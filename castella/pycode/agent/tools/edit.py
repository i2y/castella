"""Precise file editing tool using string replacement."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from castella.pycode.agent.coding_agent import ToolCallback


async def edit_tool(
    path: str,
    old_string: str,
    new_string: str,
    cwd: Path,
    on_tool_use: "ToolCallback",
    replace_all: bool = False,
) -> str:
    """Edit a file by replacing text.

    Performs exact string replacement. The old_string must uniquely
    identify the text to replace (unless replace_all is True).

    Args:
        path: Path to the file (relative to cwd or absolute)
        old_string: Text to find and replace
        new_string: Replacement text
        cwd: Working directory
        on_tool_use: Callback to notify UI of tool use
        replace_all: Replace all occurrences (default: False)

    Returns:
        Success message or error
    """
    on_tool_use(
        "edit",
        {
            "path": path,
            "old_string": old_string[:100] + ("..." if len(old_string) > 100 else ""),
            "new_string": new_string[:100] + ("..." if len(new_string) > 100 else ""),
            "replace_all": replace_all,
        },
    )

    try:
        # Resolve path
        file_path = cwd / path if not path.startswith("/") else Path(path)

        if not file_path.exists():
            return f"Error: File not found: {path}"

        if not file_path.is_file():
            return f"Error: Not a file: {path}"

        # Read current content
        content = file_path.read_text(encoding="utf-8")

        # Count occurrences
        count = content.count(old_string)

        if count == 0:
            return f"Error: String not found in {path}:\n{old_string[:200]}"

        if count > 1 and not replace_all:
            return (
                f"Error: String found {count} times in {path}. "
                "Use replace_all=True to replace all occurrences, "
                "or provide more context to make the match unique."
            )

        # Perform replacement
        if replace_all:
            new_content = content.replace(old_string, new_string)
            return f"Replaced {count} occurrence(s) in {path}"
        else:
            new_content = content.replace(old_string, new_string, 1)

        # Write back
        file_path.write_text(new_content, encoding="utf-8")

        return f"Successfully edited {path}"

    except UnicodeDecodeError:
        return f"Error: Cannot read file as text (binary file?): {path}"
    except PermissionError:
        return f"Error: Permission denied: {path}"
    except Exception as e:
        return f"Error editing file: {e}"


def edit_tool_sync(
    path: str,
    old_string: str,
    new_string: str,
    cwd: Path,
    on_tool_use: "ToolCallback",
    replace_all: bool = False,
) -> str:
    """Synchronous version of edit_tool."""
    import asyncio

    return asyncio.get_event_loop().run_until_complete(
        edit_tool(path, old_string, new_string, cwd, on_tool_use, replace_all)
    )
