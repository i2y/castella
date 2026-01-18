"""Tool display and approval widgets for wrks."""

import json
from typing import Callable, Optional

from castella import (
    Column,
    Row,
    Text,
    Button,
    Spacer,
    Modal,
    ModalState,
    Widget,
    SizePolicy,
)
from castella.core import Component
from castella.theme import ThemeManager

from castella.wrks.sdk.types import ToolCall, ToolStatus
from castella.wrks.ui.diff_view import DiffView, is_diff_output


class ToolCallView(Component):
    """Displays a single tool call with its status."""

    def __init__(self, tool_call: ToolCall):
        """Initialize the tool call view."""
        super().__init__()
        self._tool_call = tool_call

    def view(self) -> Widget:
        """Build the tool call view."""
        theme = ThemeManager().current
        tool = self._tool_call

        status_color = {
            ToolStatus.PENDING: theme.colors.text_warning,
            ToolStatus.APPROVED: theme.colors.text_info,
            ToolStatus.REJECTED: theme.colors.text_danger,
            ToolStatus.RUNNING: theme.colors.text_info,
            ToolStatus.COMPLETED: theme.colors.text_success,
            ToolStatus.FAILED: theme.colors.text_danger,
        }.get(tool.status, theme.colors.border_secondary)

        status_text = tool.status.value.capitalize()

        icon = {
            "Bash": ">",
            "Read": "R",
            "Write": "W",
            "Edit": "E",
            "Grep": "G",
            "Glob": "*",
            "Task": "T",
            "WebFetch": "W",
            "WebSearch": "S",
        }.get(tool.name, "?")

        # Header row with tool name and status
        header_row = Row(
            Spacer().fixed_width(8),
            Text(icon, font_size=11).text_color(theme.colors.text_primary).bg_color(theme.colors.bg_tertiary).fixed_size(32, 24),
            Spacer().fixed_width(8),
            Column(
                Text(tool.display_name, font_size=12).text_color(theme.colors.text_primary).fixed_height(20).height_policy(SizePolicy.FIXED),
                Text(tool.display_args, font_size=11).text_color(theme.colors.border_secondary).fixed_height(16).height_policy(SizePolicy.FIXED) if tool.display_args else Spacer().fixed_height(1),
            ).height_policy(SizePolicy.CONTENT),
            Spacer().fixed_width(8),
            Text(status_text, font_size=11).text_color(status_color).bg_color(theme.colors.bg_tertiary).fixed_size(80, 24),
            Spacer().fixed_width(8),
        ).fixed_height(48).height_policy(SizePolicy.FIXED)

        column_items: list[Widget] = [header_row]

        # Show result if available
        if tool.result and tool.status == ToolStatus.COMPLETED:
            result_text = tool.result
            # Check if result is diff output
            if is_diff_output(result_text):
                diff_view = DiffView(result_text, max_lines=100)
                diff_view.height_policy(SizePolicy.CONTENT)
                column_items.append(diff_view)
            else:
                # Regular text result with line numbers
                lines = result_text.split("\n")
                max_lines = 150
                if len(lines) > max_lines:
                    lines = lines[:max_lines]
                    lines.append("... (truncated)")

                line_widgets: list[Widget] = []
                for i, line in enumerate(lines):
                    line_num = str(i + 1).rjust(4)
                    line_widgets.append(
                        Row(
                            Text(line_num, font_size=10)
                            .text_color(theme.colors.border_secondary)
                            .fixed_width(36)
                            .fixed_height(18)
                            .height_policy(SizePolicy.FIXED),
                            Text(line if line else " ", font_size=11)
                            .text_color(theme.colors.text_primary)
                            .fixed_height(18)
                            .height_policy(SizePolicy.FIXED),
                        )
                        .bg_color(theme.colors.bg_tertiary)
                        .fixed_height(18)
                        .height_policy(SizePolicy.FIXED)
                    )
                column_items.append(
                    Column(*line_widgets).height_policy(SizePolicy.CONTENT)
                )

        return (
            Column(*column_items)
            .height_policy(SizePolicy.CONTENT)
            .bg_color(theme.colors.bg_secondary)
        )


class ToolApprovalModal(Component):
    """Modal dialog for tool approval."""

    def __init__(
        self,
        tool_call: ToolCall,
        modal_state: ModalState,
        on_approve: Optional[Callable[[], None]] = None,
        on_reject: Optional[Callable[[], None]] = None,
    ):
        """Initialize the approval modal."""
        super().__init__()
        self._tool_call = tool_call
        self._modal_state = modal_state
        self._on_approve = on_approve
        self._on_reject = on_reject

    def _handle_approve(self, _) -> None:
        """Handle approve button click."""
        self._modal_state.close()
        if self._on_approve:
            self._on_approve()

    def _handle_reject(self, _) -> None:
        """Handle reject button click."""
        self._modal_state.close()
        if self._on_reject:
            self._on_reject()

    def view(self) -> Widget:
        """Build the approval modal view."""
        theme = ThemeManager().current
        tool = self._tool_call

        try:
            args_text = json.dumps(tool.arguments, indent=2)
        except Exception:
            args_text = str(tool.arguments)

        if len(args_text) > 1000:
            args_text = args_text[:997] + "..."

        content = Column(
            Text(f"Tool: {tool.display_name}", font_size=16).text_color(theme.colors.text_primary),
            Spacer().fixed_height(16),
            Text("Arguments:", font_size=12).text_color(theme.colors.border_secondary),
            Spacer().fixed_height(4),
            Text(args_text, font_size=11).text_color(theme.colors.text_primary).bg_color(theme.colors.bg_tertiary),
            Spacer(),
            Row(
                Button("Reject").on_click(self._handle_reject).bg_color(theme.colors.bg_danger),
                Spacer(),
                Button("Approve").on_click(self._handle_approve).bg_color(theme.colors.bg_success),
            ).height(40).height_policy(SizePolicy.FIXED),
        )

        return Modal(
            content=content,
            state=self._modal_state,
            title="Tool Approval Required",
        )
