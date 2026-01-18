"""Type definitions for wrks SDK integration."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class MessageRole(Enum):
    """Role of a chat message."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ToolStatus(Enum):
    """Status of a tool execution."""

    PENDING = "pending"  # Waiting for approval
    APPROVED = "approved"  # User approved
    REJECTED = "rejected"  # User rejected
    RUNNING = "running"  # Currently executing
    COMPLETED = "completed"  # Successfully completed
    FAILED = "failed"  # Execution failed


@dataclass
class ToolCall:
    """Represents a tool call from the assistant."""

    id: str  # Unique identifier for this tool call
    name: str  # Tool name (e.g., "Bash", "Read", "Write")
    arguments: dict[str, Any]  # Tool arguments
    status: ToolStatus = ToolStatus.PENDING
    result: Optional[str] = None  # Tool execution result
    error: Optional[str] = None  # Error message if failed
    timestamp: datetime = field(default_factory=datetime.now)

    @property
    def display_name(self) -> str:
        """Get a display-friendly name for the tool."""
        return self.name

    @property
    def display_args(self) -> str:
        """Get a summary of arguments for display."""
        if not self.arguments:
            return ""

        # Special handling for common tools
        if self.name == "Bash":
            cmd = self.arguments.get("command", "")
            if len(cmd) > 60:
                return cmd[:57] + "..."
            return cmd
        elif self.name == "Read":
            return self.arguments.get("file_path", "")
        elif self.name == "Write":
            return self.arguments.get("file_path", "")
        elif self.name == "Edit":
            return self.arguments.get("file_path", "")
        elif self.name == "Grep":
            pattern = self.arguments.get("pattern", "")
            return f"pattern: {pattern}"
        elif self.name == "Glob":
            pattern = self.arguments.get("pattern", "")
            return f"pattern: {pattern}"

        # Generic: show first key-value pair
        for key, value in self.arguments.items():
            value_str = str(value)
            if len(value_str) > 50:
                value_str = value_str[:47] + "..."
            return f"{key}: {value_str}"

        return ""


@dataclass
class ChatMessage:
    """Represents a message in the chat."""

    role: MessageRole
    content: str
    tool_calls: list[ToolCall] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    is_streaming: bool = False  # True if content is still being streamed
    cost_usd: Optional[float] = None  # Cost for this message if applicable
    model_name: Optional[str] = None  # Model used for this message (assistant only)
    thinking: Optional[str] = None  # Extended thinking content (Opus models)

    @property
    def is_user(self) -> bool:
        """Check if this is a user message."""
        return self.role == MessageRole.USER

    @property
    def is_assistant(self) -> bool:
        """Check if this is an assistant message."""
        return self.role == MessageRole.ASSISTANT
