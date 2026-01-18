"""Active session state management for parallel sessions."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Optional
from uuid import uuid4

from castella.core import ListState, ScrollState, State
from castella.multiline_input import MultilineInputState

if TYPE_CHECKING:
    from castella.wrks.sdk import WrksClient
    from castella.wrks.sdk.types import ChatMessage, ToolCall
    from castella.wrks.storage import Project, SessionMetadata


@dataclass
class ActiveSession:
    """Represents an active session tab with all its state.

    Each active session maintains its own:
    - Project and session references
    - SDK client instance
    - Message history
    - Tool calls
    - Context files
    - Input state
    - Scroll position
    - Cost tracking
    """

    # Unique ID for this active session (for tab identification)
    id: str = field(default_factory=lambda: str(uuid4()))

    # Project and session info
    project: Optional["Project"] = None
    session_metadata: Optional["SessionMetadata"] = None

    # Display name for the tab
    @property
    def tab_name(self) -> str:
        """Get the display name for this tab."""
        if self.project is None:
            return "New"
        proj_name = self.project.display_name
        if self.session_metadata:
            summary = self.session_metadata.summary[:15]
            if len(self.session_metadata.summary) > 15:
                summary += "..."
            return f"{proj_name}/{summary}"
        return f"{proj_name}/new"

    # SDK client (created lazily)
    client: Optional["WrksClient"] = None

    # Message state
    messages: ListState["ChatMessage"] = field(default_factory=lambda: ListState([]))
    streaming_text: State[str] = field(default_factory=lambda: State(""))
    is_loading: State[bool] = field(default_factory=lambda: State(False))
    current_thinking: State[str] = field(default_factory=lambda: State(""))  # Opus thinking

    # Tool state
    current_tools: ListState["ToolCall"] = field(default_factory=lambda: ListState([]))
    pending_tool: State[Optional["ToolCall"]] = field(default_factory=lambda: State(None))

    # Context files
    context_files: ListState[dict[str, Any]] = field(default_factory=lambda: ListState([]))

    # Input state (don't attach to component)
    input_state: MultilineInputState = field(default_factory=lambda: MultilineInputState(""))

    # Scroll state (don't attach to component)
    scroll_state: ScrollState = field(default_factory=ScrollState)

    # Cost tracking
    total_cost: State[float] = field(default_factory=lambda: State(0.0))

    # Session ID from SDK
    session_id: State[Optional[str]] = field(default_factory=lambda: State(None))

    def attach_states(self, component) -> None:
        """Attach all reactive states to a component."""
        self.messages.attach(component)
        self.streaming_text.attach(component)
        self.is_loading.attach(component)
        self.current_thinking.attach(component)
        self.current_tools.attach(component)
        self.pending_tool.attach(component)
        self.context_files.attach(component)

    def detach_states(self, component) -> None:
        """Detach all reactive states from a component."""
        self.messages.detach(component)
        self.streaming_text.detach(component)
        self.is_loading.detach(component)
        self.current_thinking.detach(component)
        self.current_tools.detach(component)
        self.pending_tool.detach(component)
        self.context_files.detach(component)

    def reset(self) -> None:
        """Reset the session state for a new conversation."""
        self.client = None
        self.messages.set([])
        self.streaming_text.set("")
        self.is_loading.set(False)
        self.current_thinking.set("")
        self.current_tools.set([])
        self.pending_tool.set(None)
        self.context_files.set([])
        self.total_cost.set(0.0)
        self.session_id.set(None)
        self.input_state.set("")
        self.scroll_state.y = 0
