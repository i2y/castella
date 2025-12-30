"""AgentChat - High-level chat UI for AI agents.

This module provides a simple, high-level API for creating chat interfaces
that connect to A2A agents or custom backends.

Example (3 lines):
    from castella.agent import AgentChat

    chat = AgentChat.from_a2a("http://localhost:8080")
    chat.run()

Example with custom handler:
    def my_handler(message: str) -> str:
        return f"You said: {message}"

    chat = AgentChat(handler=my_handler, title="My Bot")
    chat.run()
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Callable

from castella import App, Box, Column, Row, ScrollState, Text
from castella.core import Component, ListState, SizePolicy, State
from castella.frame import Frame
from castella.markdown import Markdown
from castella.multiline_input import MultilineInput, MultilineInputState

if TYPE_CHECKING:
    from castella.a2a import A2AClient
    from castella.a2ui import A2UIRenderer


class AgentChat(Component):
    """High-level chat UI component for AI agents.

    Provides a complete chat interface with minimal setup. Supports:
    - A2A agents via from_a2a() factory
    - Custom message handlers
    - Loading indicators
    - Agent card display (for A2A)

    Example:
        # Connect to A2A agent
        chat = AgentChat.from_a2a("http://localhost:8080")
        chat.run()

        # Custom handler
        chat = AgentChat(
            handler=lambda msg: f"Echo: {msg}",
            title="Echo Bot",
        )
        chat.run()
    """

    def __init__(
        self,
        *,
        # Backend options (provide one)
        a2a_client: "A2AClient | None" = None,
        handler: Callable[[str], str] | None = None,
        # UI options
        title: str | None = None,
        placeholder: str = "Type a message...",
        system_message: str | None = None,
        show_agent_card: bool = True,
        a2ui_renderer: "A2UIRenderer | None" = None,
        # Window options (for run())
        width: int = 700,
        height: int = 550,
    ):
        """Initialize AgentChat.

        Args:
            a2a_client: A2A client for remote agent
            handler: Custom message handler function
            title: Chat window title
            placeholder: Input placeholder text
            system_message: Initial system message
            show_agent_card: Show agent card for A2A agents
            a2ui_renderer: Optional A2UI renderer
            width: Window width for run()
            height: Window height for run()
        """
        super().__init__()

        self._a2a_client = a2a_client
        self._handler = handler
        self._title = title
        self._placeholder = placeholder
        self._show_agent_card = show_agent_card
        self._a2ui_renderer = a2ui_renderer
        self._width = width
        self._height = height

        # Determine title from A2A agent if not provided
        if self._title is None and self._a2a_client is not None:
            self._title = f"Chat with {self._a2a_client.name}"
        elif self._title is None:
            self._title = "Agent Chat"

        # Initialize state - add initial messages BEFORE attaching
        initial_messages = []
        if system_message:
            initial_messages.append(
                {
                    "role": "system",
                    "content": system_message,
                }
            )
        elif self._a2a_client is not None:
            # Add welcome message from agent
            initial_messages.append(
                {
                    "role": "system",
                    "content": f"Connected to **{self._a2a_client.name}**. {self._a2a_client.description}",
                }
            )

        self._messages: ListState[dict] = ListState(initial_messages)
        self._messages.attach(self)

        self._input_state = MultilineInputState("")
        self._scroll_state = ScrollState()
        # Don't attach - manual scrolling works better without re-renders

        self._is_loading = State(False)
        self._is_loading.attach(self)

    @classmethod
    def from_a2a(
        cls,
        agent_url: str,
        **kwargs,
    ) -> "AgentChat":
        """Create AgentChat from A2A agent URL.

        Args:
            agent_url: URL of the A2A agent (e.g., "http://localhost:8080")
            **kwargs: Additional arguments for AgentChat

        Returns:
            AgentChat instance connected to the agent

        Example:
            chat = AgentChat.from_a2a("http://localhost:8080")
            chat.run()
        """
        from castella.a2a import A2AClient

        client = A2AClient(agent_url)
        return cls(a2a_client=client, **kwargs)

    def _send_message(self, event=None):
        """Handle sending a message."""
        text = self._input_state.value().strip()
        if not text or self._is_loading():
            return

        # Add user message
        self._messages.append(
            {
                "role": "user",
                "content": text,
            }
        )

        # Clear input
        self._input_state.set("")

        # Set loading state
        self._is_loading.set(True)

        # Get response
        try:
            if self._a2a_client is not None:
                response = self._a2a_client.ask(text)
            elif self._handler is not None:
                response = self._handler(text)
            else:
                response = "No handler configured."

            # Set scroll BEFORE append so re-render picks it up
            self._scroll_state.y = 999999
            self._messages.append(
                {
                    "role": "assistant",
                    "content": response,
                }
            )
        except Exception as e:
            self._scroll_state.y = 999999
            self._messages.append(
                {
                    "role": "system",
                    "content": f"Error: {e}",
                }
            )
        finally:
            self._is_loading.set(False)

    def view(self):
        from castella.theme import ThemeManager

        theme = ThemeManager().current

        elements = []

        # Agent card (for A2A agents)
        if self._show_agent_card and self._a2a_client is not None:
            from castella.agent import AgentCardView

            try:
                card = self._a2a_client.agent_card
                elements.append(AgentCardView(card, show_skills=True, compact=True))
            except Exception:
                pass  # Skip if agent card not available

        # Build message widgets
        msg_widgets = []
        for msg in self._messages:
            role = msg["role"]
            content = msg["content"]

            # Role-based styling
            if role == "user":
                role_color = theme.colors.text_primary
                bg_color = theme.colors.bg_tertiary
                role_label = "You"
            elif role == "assistant":
                role_color = theme.colors.text_info
                bg_color = theme.colors.bg_secondary
                role_label = "Assistant"
            else:
                role_color = theme.colors.text_warning
                bg_color = theme.colors.bg_primary
                role_label = "System"

            # Use Markdown for content
            content_widget = Markdown(content, base_font_size=14)

            msg_box = (
                Box(
                    Column(
                        Text(role_label, font_size=14)
                        .text_color(role_color)
                        .fixed_height(20),
                        content_widget,
                    ).height_policy(SizePolicy.CONTENT)
                )
                .bg_color(bg_color)
                .height_policy(SizePolicy.CONTENT)
            )

            msg_widgets.append(msg_box)

        # Loading indicator
        if self._is_loading():
            loading_box = (
                Box(
                    Column(
                        Text("Assistant", font_size=14)
                        .text_color(theme.colors.text_info)
                        .fixed_height(20),
                        Text("Thinking...", font_size=14)
                        .text_color(theme.colors.text_info)
                        .fixed_height(24),
                    ).height_policy(SizePolicy.CONTENT)
                )
                .bg_color(theme.colors.bg_secondary)
                .height_policy(SizePolicy.CONTENT)
            )
            msg_widgets.append(loading_box)

        # Message area
        elements.append(
            Column(
                *msg_widgets,
                scrollable=True,
                scroll_state=self._scroll_state,
            ).bg_color(theme.colors.bg_primary)
        )

        # Input area
        elements.append(
            Row(
                MultilineInput(self._input_state, font_size=14).fixed_height(40),
                self._create_send_button(theme),
            ).fixed_height(56)
        )

        return Column(*elements)

    def _create_send_button(self, theme):
        """Create the send button with loading state."""
        from castella.button import Button

        label = "..." if self._is_loading() else "Send"
        return (
            Button(label).on_click(self._send_message).fixed_width(80).fixed_height(40)
        )

    def run(self):
        """Run the chat as a standalone application.

        Example:
            chat = AgentChat.from_a2a("http://localhost:8080")
            chat.run()
        """
        App(Frame(self._title, self._width, self._height), self).run()
