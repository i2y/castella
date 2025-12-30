"""Tool call visualization components for Castella agent framework.

This module provides components for displaying tool/function calls
in chat interfaces.

Example:
    from castella.agent import ToolCallView

    tool = ToolCallView(
        name="get_weather",
        arguments={"location": "Tokyo"},
        result="Sunny, 22°C",
    )
"""

from __future__ import annotations

import json

from castella.box import Box
from castella.button import Button
from castella.column import Column
from castella.core import Component, SizePolicy, State
from castella.text import Text


class ToolCallView(Component):
    """Display a tool/function call with expandable details.

    Shows the tool name, arguments, and optional result in a
    collapsible card format.

    Example:
        tool = ToolCallView(
            name="search",
            arguments={"query": "Python tutorials"},
            result="Found 10 results...",
        )
    """

    def __init__(
        self,
        name: str,
        arguments: dict | None = None,
        result: str | None = None,
        *,
        expanded: bool = False,
    ):
        """Initialize tool call view.

        Args:
            name: Name of the tool/function
            arguments: Tool arguments as a dictionary
            result: Optional result from the tool
            expanded: Whether to start expanded
        """
        super().__init__()
        self._name = name
        self._arguments = arguments or {}
        self._result = result
        self._expanded = State(expanded)
        self._expanded.attach(self)

    def _toggle_expanded(self, event=None):
        """Toggle expanded state."""
        self._expanded.set(not self._expanded())

    def view(self):
        from castella.theme import ThemeManager

        theme = ThemeManager().current

        # Header with tool name and expand/collapse toggle
        toggle_icon = "▼" if self._expanded() else "▶"
        status_text = "completed" if self._result is not None else "running..."

        header = (
            Button(f"{toggle_icon} {self._name}  [{status_text}]")
            .on_click(self._toggle_expanded)
            .fixed_height(28)
        )

        elements = [header]

        # Expanded content
        if self._expanded():
            # Arguments section
            if self._arguments:
                args_text = json.dumps(self._arguments, indent=2, ensure_ascii=False)
                args_lines = args_text.count("\n") + 1
                args_height = max(20, args_lines * 18)
                elements.append(
                    Box(
                        Column(
                            Text("Arguments:", font_size=14)
                            .text_color(theme.colors.text_info)
                            .fixed_height(18),
                            Text(args_text, font_size=14)
                            .text_color(theme.colors.text_primary)
                            .fixed_height(args_height),
                        ).height_policy(SizePolicy.CONTENT)
                    )
                    .bg_color(theme.colors.bg_primary)
                    .height_policy(SizePolicy.CONTENT)
                )

            # Result section
            if self._result is not None:
                result_lines = self._result.count("\n") + 1
                result_height = max(20, result_lines * 18)
                elements.append(
                    Box(
                        Column(
                            Text("Result:", font_size=14)
                            .text_color(theme.colors.text_success)
                            .fixed_height(18),
                            Text(self._result, font_size=14)
                            .text_color(theme.colors.text_primary)
                            .fixed_height(result_height),
                        ).height_policy(SizePolicy.CONTENT)
                    )
                    .bg_color(theme.colors.bg_primary)
                    .height_policy(SizePolicy.CONTENT)
                )

        return (
            Box(Column(*elements).height_policy(SizePolicy.CONTENT))
            .bg_color(theme.colors.bg_tertiary)
            .border_color(theme.colors.border_primary)
            .height_policy(SizePolicy.CONTENT)
        )


class ToolHistoryPanel(Component):
    """Panel displaying a history of tool calls.

    Example:
        history = [
            ToolCallData(id="1", name="search", arguments={"q": "test"}, result="..."),
            ToolCallData(id="2", name="fetch", arguments={"url": "..."}, result="..."),
        ]
        panel = ToolHistoryPanel(history)
    """

    def __init__(
        self,
        tool_calls: list,
        *,
        title: str = "Tool Calls",
        max_visible: int = 5,
    ):
        """Initialize tool history panel.

        Args:
            tool_calls: List of tool call data objects
            title: Panel title
            max_visible: Maximum number of visible items
        """
        super().__init__()
        self._tool_calls = tool_calls
        self._title = title
        self._max_visible = max_visible

    def view(self):
        from castella.theme import ThemeManager

        theme = ThemeManager().current

        elements = [
            Text(self._title, font_size=16)
            .text_color(theme.colors.text_primary)
            .fixed_height(24)
        ]

        if not self._tool_calls:
            elements.append(
                Text("No tool calls yet", font_size=14)
                .text_color(theme.colors.text_info)
                .fixed_height(20)
            )
        else:
            for call in self._tool_calls[-self._max_visible :]:
                elements.append(
                    ToolCallView(
                        name=call.name if hasattr(call, "name") else str(call),
                        arguments=call.arguments if hasattr(call, "arguments") else {},
                        result=call.result if hasattr(call, "result") else None,
                    )
                )

        return (
            Box(Column(*elements).height_policy(SizePolicy.CONTENT))
            .bg_color(theme.colors.bg_secondary)
            .height_policy(SizePolicy.CONTENT)
        )
