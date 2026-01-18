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

        return Row(
            Spacer().fixed_width(8),
            Text(icon, font_size=11).text_color(theme.colors.text_primary).bg_color(theme.colors.bg_tertiary).fixed_size(32, 24),
            Spacer().fixed_width(8),
            Column(
                Text(tool.display_name, font_size=12).text_color(theme.colors.text_primary),
                Text(tool.display_args, font_size=11).text_color(theme.colors.border_secondary) if tool.display_args else Spacer().fixed_height(1),
            ),
            Spacer(),
            Text(status_text, font_size=11).text_color(status_color).bg_color(theme.colors.bg_tertiary).fixed_size(80, 24),
            Spacer().fixed_width(8),
        ).height(48).height_policy(SizePolicy.FIXED).bg_color(theme.colors.bg_secondary)


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
