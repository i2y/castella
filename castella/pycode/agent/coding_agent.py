"""Coding agent implementation using pydantic-ai.

This module provides the main coding agent that can help with
software engineering tasks using various tools.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from pydantic_ai import Agent, RunContext

# Type alias for tool use callback
ToolCallback = Callable[[str, dict[str, Any]], None]


@dataclass
class CodingDeps:
    """Dependencies for the coding agent.

    This dataclass holds the context needed by the agent's tools.
    """

    cwd: Path
    """Working directory for file operations."""

    on_tool_use: ToolCallback = field(default=lambda name, args: None)
    """Callback when a tool is invoked (for UI updates)."""

    on_tool_result: Callable[[str, str], None] = field(
        default=lambda name, result: None
    )
    """Callback when a tool completes (for UI updates)."""


SYSTEM_PROMPT = """You are an expert software engineering assistant. Your job is to help users with coding tasks including:

- Writing and modifying code
- Debugging issues
- Explaining code
- Refactoring
- Adding features
- Writing tests

You have access to several tools:

1. **bash**: Execute shell commands. Use this for running tests, installing packages, git operations, etc.
2. **read_file**: Read the contents of a file. Always read files before modifying them.
3. **write_file**: Write content to a file. Creates the file if it doesn't exist.
4. **edit_file**: Make precise edits to a file by replacing specific text. The old_string must be unique in the file.
5. **glob_files**: Find files matching a pattern (e.g., "**/*.py" for all Python files).
6. **grep**: Search for patterns in files. Supports regex.

## Guidelines

1. **Read before writing**: Always read a file before modifying it to understand the context.
2. **Explain your actions**: Tell the user what you're going to do before doing it.
3. **Be precise with edits**: When using edit_file, include enough context to make the match unique.
4. **Handle errors gracefully**: If a tool fails, explain what happened and suggest alternatives.
5. **Keep it simple**: Make minimal changes to accomplish the task. Don't refactor code unless asked.
6. **Follow existing patterns**: Match the coding style and conventions of the existing codebase.

## Security

- Never execute commands that could harm the system
- Be cautious with file operations outside the working directory
- Don't expose sensitive information like API keys or passwords"""


def _create_coding_agent(model: str) -> Agent[CodingDeps, str]:
    """Create a coding agent with all tools registered.

    Args:
        model: The pydantic-ai model string

    Returns:
        Configured Agent instance
    """
    from castella.pycode.agent.tools.bash import bash_tool
    from castella.pycode.agent.tools.edit import edit_tool
    from castella.pycode.agent.tools.glob import glob_tool
    from castella.pycode.agent.tools.grep import grep_tool
    from castella.pycode.agent.tools.read import read_tool
    from castella.pycode.agent.tools.write import write_tool

    agent: Agent[CodingDeps, str] = Agent(
        model,
        deps_type=CodingDeps,
        system_prompt=SYSTEM_PROMPT,
    )

    @agent.tool
    async def bash(
        ctx: RunContext[CodingDeps], command: str, timeout: int = 120
    ) -> str:
        """Execute a bash command.

        Args:
            command: The bash command to execute
            timeout: Command timeout in seconds (default: 120)
        """
        result = await bash_tool(command, ctx.deps.cwd, ctx.deps.on_tool_use, timeout)
        ctx.deps.on_tool_result("bash", result)
        return result

    @agent.tool
    async def read_file(
        ctx: RunContext[CodingDeps],
        path: str,
        offset: int = 0,
        limit: int = 2000,
    ) -> str:
        """Read the contents of a file.

        Args:
            path: Path to the file (relative to working directory or absolute)
            offset: Line number to start reading from (0-based)
            limit: Maximum number of lines to read
        """
        result = await read_tool(
            path, ctx.deps.cwd, ctx.deps.on_tool_use, offset, limit
        )
        ctx.deps.on_tool_result("read", result)
        return result

    @agent.tool
    async def write_file(
        ctx: RunContext[CodingDeps],
        path: str,
        content: str,
    ) -> str:
        """Write content to a file. Creates the file if it doesn't exist.

        Args:
            path: Path to the file (relative to working directory or absolute)
            content: Content to write to the file
        """
        result = await write_tool(path, content, ctx.deps.cwd, ctx.deps.on_tool_use)
        ctx.deps.on_tool_result("write", result)
        return result

    @agent.tool
    async def edit_file(
        ctx: RunContext[CodingDeps],
        path: str,
        old_string: str,
        new_string: str,
        replace_all: bool = False,
    ) -> str:
        """Edit a file by replacing text. The old_string must uniquely identify the text to replace.

        Args:
            path: Path to the file (relative to working directory or absolute)
            old_string: The exact text to find and replace
            new_string: The replacement text
            replace_all: If True, replace all occurrences; if False, old_string must be unique
        """
        result = await edit_tool(
            path,
            old_string,
            new_string,
            ctx.deps.cwd,
            ctx.deps.on_tool_use,
            replace_all,
        )
        ctx.deps.on_tool_result("edit", result)
        return result

    @agent.tool
    async def glob_files(
        ctx: RunContext[CodingDeps],
        pattern: str,
        max_results: int = 100,
    ) -> str:
        """Find files matching a glob pattern.

        Args:
            pattern: Glob pattern (e.g., "**/*.py" for all Python files)
            max_results: Maximum number of results to return
        """
        result = await glob_tool(
            pattern, ctx.deps.cwd, ctx.deps.on_tool_use, max_results
        )
        ctx.deps.on_tool_result("glob", result)
        return result

    @agent.tool
    async def grep(
        ctx: RunContext[CodingDeps],
        pattern: str,
        path: str = ".",
        file_pattern: str | None = None,
        max_results: int = 50,
        context_lines: int = 0,
        case_insensitive: bool = False,
    ) -> str:
        """Search for a pattern in files using regex.

        Args:
            pattern: Regex pattern to search for
            path: Directory or file to search in
            file_pattern: Glob pattern to filter files (e.g., "*.py")
            max_results: Maximum number of matches to return
            context_lines: Number of context lines before/after each match
            case_insensitive: If True, perform case-insensitive search
        """
        result = await grep_tool(
            pattern,
            ctx.deps.cwd,
            ctx.deps.on_tool_use,
            path,
            file_pattern,
            max_results,
            context_lines,
            case_insensitive,
        )
        ctx.deps.on_tool_result("grep", result)
        return result

    return agent


class CodingAgent:
    """A coding assistant agent using pydantic-ai.

    Example:
        from pathlib import Path
        from castella.pycode.agent import CodingAgent, CodingDeps

        agent = CodingAgent()
        deps = CodingDeps(
            cwd=Path.cwd(),
            on_tool_use=lambda name, args: print(f"Using {name}"),
        )

        # Run synchronously
        result = agent.run_sync("Read the main.py file", deps)
        print(result)

        # Or run with streaming
        async for chunk in agent.run_stream("Fix the bug", deps):
            print(chunk, end="")
    """

    def __init__(self, model: str = "anthropic:claude-sonnet-4-20250514"):
        """Initialize the coding agent.

        Args:
            model: The pydantic-ai model string (e.g., "anthropic:claude-sonnet-4-0")
        """
        self._model = model
        self._agent = _create_coding_agent(model)
        self._message_history: list[Any] = []

    def run_sync(
        self,
        message: str,
        deps: CodingDeps,
        images: list[dict] | None = None,
    ) -> str:
        """Run the agent synchronously.

        Args:
            message: User message
            deps: Agent dependencies
            images: Optional list of image data dicts with keys:
                    - name: str
                    - base64: str (base64 encoded image)
                    - mime_type: str (e.g., "image/png")

        Returns:
            Agent response text
        """
        # Build user prompt with images if provided
        if images:
            from pydantic_ai.messages import BinaryContent

            # Create multimodal prompt parts
            prompt_parts: list[str | BinaryContent] = []

            # Add images first
            for img in images:
                import base64 as b64

                img_bytes = b64.b64decode(img["base64"])
                prompt_parts.append(
                    BinaryContent(data=img_bytes, media_type=img["mime_type"])
                )

            # Add text message
            prompt_parts.append(message)

            result = self._agent.run_sync(
                prompt_parts,
                deps=deps,
                message_history=self._message_history,
            )
        else:
            result = self._agent.run_sync(
                message,
                deps=deps,
                message_history=self._message_history,
            )

        self._message_history = result.new_messages()
        return result.output

    async def run(
        self,
        message: str,
        deps: CodingDeps,
    ) -> str:
        """Run the agent asynchronously.

        Args:
            message: User message
            deps: Agent dependencies

        Returns:
            Agent response text
        """
        result = await self._agent.run(
            message,
            deps=deps,
            message_history=self._message_history,
        )
        self._message_history = result.new_messages()
        return result.output

    async def run_stream(
        self,
        message: str,
        deps: CodingDeps,
    ):
        """Run the agent with streaming output.

        Args:
            message: User message
            deps: Agent dependencies

        Yields:
            Text chunks as they are generated
        """
        async with self._agent.run_stream(
            message,
            deps=deps,
            message_history=self._message_history,
        ) as result:
            async for chunk in result.stream_text(delta=True):
                yield chunk
            self._message_history = result.new_messages()

    def clear_history(self):
        """Clear the conversation history."""
        self._message_history = []

    @property
    def model(self) -> str:
        """Get the current model string."""
        return self._model

    def set_model(self, model: str):
        """Change the model.

        Args:
            model: New pydantic-ai model string
        """
        self._model = model
        self._agent = _create_coding_agent(model)
        self._message_history = []


class MockCodingAgent:
    """A mock coding agent for testing UI without API calls.

    Returns predefined responses for demonstration purposes.
    """

    def __init__(self, model: str = "mock:test"):
        self._model = model
        self._message_history: list[dict] = []
        self._response_count = 0

    def run_sync(
        self,
        message: str,
        deps: CodingDeps,
        images: list[dict] | None = None,
    ) -> str:
        """Return a mock response."""
        self._response_count += 1
        self._message_history.append({"role": "user", "content": message})

        # Simulate tool usage
        if "read" in message.lower() or "file" in message.lower():
            deps.on_tool_use("read", {"path": "example.py"})
            deps.on_tool_result("read", "# Example file content\nprint('hello')")

        if "search" in message.lower() or "find" in message.lower():
            deps.on_tool_use("glob", {"pattern": "**/*.py"})
            deps.on_tool_result("glob", "main.py\ntest.py\nutils.py")

        # Handle images in mock
        image_info = ""
        if images:
            image_info = f"\n\n**Images received:** {len(images)} image(s)\n"
            for img in images:
                image_info += f"- {img['name']} ({img['mime_type']})\n"

        response = f"""I understand you want to: {message}{image_info}

Here's what I would do:

1. First, I'd analyze the request
2. Then, I'd use the appropriate tools
3. Finally, I'd provide a solution

This is a mock response #{self._response_count}. In production, I would use the actual LLM to generate a helpful response and use tools as needed.

Let me know if you have any questions!"""

        self._message_history.append({"role": "assistant", "content": response})
        return response

    async def run(
        self,
        message: str,
        deps: CodingDeps,
    ) -> str:
        """Return a mock response asynchronously."""
        return self.run_sync(message, deps)

    async def run_stream(
        self,
        message: str,
        deps: CodingDeps,
    ):
        """Stream mock response."""
        import asyncio

        response = self.run_sync(message, deps)
        # Simulate streaming by yielding character by character
        for char in response:
            yield char
            await asyncio.sleep(0.01)

    def clear_history(self):
        """Clear the conversation history."""
        self._message_history = []

    @property
    def model(self) -> str:
        """Get the current model string."""
        return self._model

    def set_model(self, model: str):
        """Change the model (no-op for mock)."""
        self._model = model
