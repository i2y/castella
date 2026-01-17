"""Content search tool using regex patterns."""

from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from castella.pycode.agent.coding_agent import ToolCallback


async def grep_tool(
    pattern: str,
    cwd: Path,
    on_tool_use: "ToolCallback",
    path: str = ".",
    file_pattern: str | None = None,
    max_results: int = 50,
    context_lines: int = 0,
    case_insensitive: bool = False,
) -> str:
    """Search for a pattern in files.

    Args:
        pattern: Regex pattern to search for
        cwd: Working directory
        on_tool_use: Callback to notify UI of tool use
        path: Directory or file to search in (relative to cwd)
        file_pattern: Glob pattern to filter files (e.g., "*.py")
        max_results: Maximum number of matches to return
        context_lines: Number of context lines before/after match
        case_insensitive: Case-insensitive search

    Returns:
        Matching lines with file paths and line numbers
    """
    on_tool_use(
        "grep",
        {
            "pattern": pattern,
            "path": path,
            "file_pattern": file_pattern,
        },
    )

    try:
        # Compile regex
        flags = re.IGNORECASE if case_insensitive else 0
        try:
            regex = re.compile(pattern, flags)
        except re.error as e:
            return f"Error: Invalid regex pattern: {e}"

        # Determine search path
        search_path = cwd / path if not path.startswith("/") else Path(path)

        if not search_path.exists():
            return f"Error: Path not found: {path}"

        # Collect files to search
        if search_path.is_file():
            files = [search_path]
        else:
            if file_pattern:
                files = list(search_path.rglob(file_pattern))
            else:
                # Default: search common text files
                files = []
                for ext in [
                    "*.py",
                    "*.js",
                    "*.ts",
                    "*.tsx",
                    "*.jsx",
                    "*.json",
                    "*.md",
                    "*.txt",
                    "*.yaml",
                    "*.yml",
                    "*.toml",
                    "*.rs",
                    "*.go",
                    "*.java",
                    "*.c",
                    "*.cpp",
                    "*.h",
                    "*.html",
                    "*.css",
                    "*.scss",
                    "*.sh",
                    "*.bash",
                ]:
                    files.extend(search_path.rglob(ext))

        # Search files
        results = []
        total_matches = 0

        for file_path in files:
            if not file_path.is_file():
                continue

            # Skip binary files and large files
            try:
                size = file_path.stat().st_size
                if size > 1_000_000:  # Skip files > 1MB
                    continue
            except OSError:
                continue

            try:
                content = file_path.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue

            lines = content.splitlines()

            for i, line in enumerate(lines):
                if regex.search(line):
                    total_matches += 1
                    if len(results) >= max_results:
                        continue

                    try:
                        rel_path = file_path.relative_to(cwd)
                    except ValueError:
                        rel_path = file_path

                    # Build result with optional context
                    if context_lines > 0:
                        start = max(0, i - context_lines)
                        end = min(len(lines), i + context_lines + 1)
                        context = []
                        for j in range(start, end):
                            prefix = ">" if j == i else " "
                            context.append(f"  {prefix} {j + 1}: {lines[j]}")
                        results.append(f"{rel_path}:\n" + "\n".join(context))
                    else:
                        results.append(f"{rel_path}:{i + 1}: {line}")

        if not results:
            return f"No matches found for pattern: {pattern}"

        output = "\n".join(results)
        if total_matches > max_results:
            output += f"\n\n... and {total_matches - max_results} more matches"

        return output

    except Exception as e:
        return f"Error searching: {e}"


def grep_tool_sync(
    pattern: str,
    cwd: Path,
    on_tool_use: "ToolCallback",
    path: str = ".",
    file_pattern: str | None = None,
    max_results: int = 50,
    context_lines: int = 0,
    case_insensitive: bool = False,
) -> str:
    """Synchronous version of grep_tool."""
    import asyncio

    return asyncio.get_event_loop().run_until_complete(
        grep_tool(
            pattern,
            cwd,
            on_tool_use,
            path,
            file_pattern,
            max_results,
            context_lines,
            case_insensitive,
        )
    )
