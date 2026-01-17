"""Bash command execution tool."""

from __future__ import annotations

import asyncio
import subprocess
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

    from castella.pycode.agent.coding_agent import ToolCallback


@dataclass
class BashResult:
    """Result of a bash command execution."""

    exit_code: int
    stdout: str
    stderr: str

    @property
    def success(self) -> bool:
        return self.exit_code == 0

    def __str__(self) -> str:
        output = []
        if self.stdout:
            output.append(self.stdout)
        if self.stderr:
            output.append(f"[stderr]\n{self.stderr}")
        if not output:
            return f"(exit code: {self.exit_code})"
        result = "\n".join(output)
        if self.exit_code != 0:
            result += f"\n(exit code: {self.exit_code})"
        return result


async def bash_tool(
    command: str,
    cwd: "Path",
    on_tool_use: "ToolCallback",
    timeout: int = 120,
) -> str:
    """Execute a bash command.

    Args:
        command: The bash command to execute
        cwd: Working directory
        on_tool_use: Callback to notify UI of tool use
        timeout: Command timeout in seconds

    Returns:
        Command output (stdout + stderr)
    """
    # Notify UI
    on_tool_use("bash", {"command": command, "timeout": timeout})

    try:
        # Run command asynchronously
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(cwd),
        )

        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout,
            )
        except asyncio.TimeoutError:
            process.kill()
            await process.wait()
            return f"Command timed out after {timeout} seconds"

        result = BashResult(
            exit_code=process.returncode or 0,
            stdout=stdout.decode("utf-8", errors="replace"),
            stderr=stderr.decode("utf-8", errors="replace"),
        )
        return str(result)

    except Exception as e:
        return f"Error executing command: {e}"


def bash_tool_sync(
    command: str,
    cwd: "Path",
    on_tool_use: "ToolCallback",
    timeout: int = 120,
) -> str:
    """Synchronous version of bash_tool.

    Args:
        command: The bash command to execute
        cwd: Working directory
        on_tool_use: Callback to notify UI of tool use
        timeout: Command timeout in seconds

    Returns:
        Command output (stdout + stderr)
    """
    on_tool_use("bash", {"command": command, "timeout": timeout})

    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            cwd=str(cwd),
            timeout=timeout,
        )

        bash_result = BashResult(
            exit_code=result.returncode,
            stdout=result.stdout.decode("utf-8", errors="replace"),
            stderr=result.stderr.decode("utf-8", errors="replace"),
        )
        return str(bash_result)

    except subprocess.TimeoutExpired:
        return f"Command timed out after {timeout} seconds"
    except Exception as e:
        return f"Error executing command: {e}"
