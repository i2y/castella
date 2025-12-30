"""Chat UI components for Castella agent framework.

This module provides chat interface components for building
conversational UIs with AI agents.

Example:
    from castella.agent import ChatMessage, ChatInput, ChatView

    # Create a simple chat interface
    messages = ListState([
        ChatMessageData(role="user", content="Hello!"),
        ChatMessageData(role="assistant", content="Hi there!"),
    ])

    chat = Column(
        ChatView(messages),
        ChatInput(on_submit=lambda text: messages.append(...)),
    )
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Callable, Literal

from castella.box import Box
from castella.button import Button
from castella.column import Column
from castella.core import Component, ListState, ScrollState, SizePolicy
from castella.markdown import Markdown
from castella.multiline_input import MultilineInput, MultilineInputState
from castella.row import Row
from castella.spacer import Spacer
from castella.text import Text

if TYPE_CHECKING:
    from castella.a2ui import A2UIRenderer


@dataclass
class ToolCallData:
    """Data for a tool/function call."""

    id: str
    name: str
    arguments: dict = field(default_factory=dict)
    result: str | None = None


@dataclass
class ChatMessageData:
    """Data for a chat message."""

    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    a2ui_json: dict | None = None
    tool_calls: list[ToolCallData] | None = None


class ChatMessage(Component):
    """A single chat message component.

    Displays a chat message with appropriate styling based on the role.
    Supports markdown rendering for assistant messages and A2UI
    rendering for structured responses.

    Example:
        msg = ChatMessage(
            role="assistant",
            content="Here's the weather: **Sunny, 22°C**",
        )
    """

    def __init__(
        self,
        role: str,
        content: str,
        *,
        a2ui_json: dict | None = None,
        a2ui_renderer: "A2UIRenderer | None" = None,
        tool_calls: list[ToolCallData] | None = None,
        timestamp: datetime | None = None,
        show_timestamp: bool = False,
        show_role_label: bool = True,
    ):
        """Initialize a chat message.

        Args:
            role: Message role ("user", "assistant", "system")
            content: Message text content
            a2ui_json: Optional A2UI JSON for rich rendering
            a2ui_renderer: Optional A2UIRenderer for A2UI content
            tool_calls: Optional list of tool calls
            timestamp: Optional message timestamp
            show_timestamp: Whether to show timestamp
            show_role_label: Whether to show role label
        """
        super().__init__()
        self._role = role
        self._content = content
        self._a2ui_json = a2ui_json
        self._a2ui_renderer = a2ui_renderer
        self._tool_calls = tool_calls or []
        self._timestamp = timestamp or datetime.now()
        self._show_timestamp = show_timestamp
        self._show_role_label = show_role_label

    def view(self):
        from castella.theme import ThemeManager

        theme = ThemeManager().current

        # Role-based styling
        if self._role == "user":
            bg_color = theme.colors.bg_tertiary
            role_label = "You"
            role_color = theme.colors.text_primary
        elif self._role == "assistant":
            bg_color = theme.colors.bg_secondary
            role_label = "Assistant"
            role_color = theme.colors.text_info
        else:  # system
            bg_color = theme.colors.bg_primary
            role_label = "System"
            role_color = theme.colors.text_warning

        elements = []

        # Role label
        if self._show_role_label:
            header_parts = [
                Text(role_label, font_size=14).text_color(role_color).fixed_height(20)
            ]

            if self._show_timestamp:
                time_str = self._timestamp.strftime("%H:%M")
                header_parts.append(Spacer())
                header_parts.append(
                    Text(time_str, font_size=12)
                    .text_color(theme.colors.text_info)
                    .fixed_height(16)
                )

            elements.append(Row(*header_parts).fixed_height(24))

        # Content - use Markdown for assistant, plain Text for user/system
        if self._a2ui_json and self._a2ui_renderer:
            # Render A2UI content
            try:
                a2ui_widget = self._a2ui_renderer.render_json(self._a2ui_json)
                elements.append(a2ui_widget)
            except Exception:
                # Fallback to text content
                elements.append(self._create_content_widget(theme))
        else:
            elements.append(self._create_content_widget(theme))

        # Tool calls
        if self._tool_calls:
            from castella.agent.tool_view import ToolCallView

            for tool_call in self._tool_calls:
                elements.append(
                    ToolCallView(
                        name=tool_call.name,
                        arguments=tool_call.arguments,
                        result=tool_call.result,
                    )
                )

        return (
            Box(Column(*elements).height_policy(SizePolicy.CONTENT))
            .bg_color(bg_color)
            .height_policy(SizePolicy.CONTENT)
        )

    def _create_content_widget(self, theme):
        """Create the content widget based on role."""
        if self._role == "assistant":
            # Use Markdown for assistant messages
            return Markdown(
                self._content,
                base_font_size=14,
            ).height_policy(SizePolicy.CONTENT)
        else:
            # Plain text for user/system - estimate height based on content
            line_count = self._content.count("\n") + 1
            estimated_height = max(24, line_count * 20)
            return (
                Text(self._content, font_size=14)
                .text_color(theme.colors.text_primary)
                .fixed_height(estimated_height)
            )


class ChatInput(Component):
    """Chat input component with text field and send button.

    Example:
        def handle_send(text: str):
            print(f"User sent: {text}")

        input_widget = ChatInput(on_submit=handle_send)
    """

    def __init__(
        self,
        on_submit: Callable[[str], None],
        *,
        placeholder: str = "Type a message...",
        send_label: str = "Send",
        min_height: int = 40,
        max_height: int = 120,
    ):
        """Initialize chat input.

        Args:
            on_submit: Callback when message is submitted
            placeholder: Placeholder text for input
            send_label: Label for send button
            min_height: Minimum height of input area
            max_height: Maximum height of input area
        """
        super().__init__()
        self._on_submit = on_submit
        self._placeholder = placeholder
        self._send_label = send_label
        self._min_height = min_height
        self._max_height = max_height
        self._input_state = MultilineInputState("")

    def _handle_send(self, event=None):
        """Handle send button click."""
        text = self._input_state.value().strip()
        if text:
            self._on_submit(text)
            self._input_state.set("")

    def view(self):
        return Row(
            MultilineInput(
                self._input_state,
                font_size=14,
                wrap=True,
            ).fixed_height(self._min_height),
            Button(self._send_label)
            .on_click(self._handle_send)
            .fixed_width(80)
            .fixed_height(self._min_height),
        ).fixed_height(self._min_height + 16)


class ChatView(Component):
    """Scrollable chat message list.

    Displays a list of chat messages with automatic scrolling
    to the latest message.

    Example:
        messages = ListState([
            ChatMessageData(role="user", content="Hello"),
            ChatMessageData(role="assistant", content="Hi!"),
        ])
        chat_view = ChatView(messages)
    """

    def __init__(
        self,
        messages: ListState[ChatMessageData],
        *,
        a2ui_renderer: "A2UIRenderer | None" = None,
        show_timestamps: bool = False,
        auto_scroll: bool = True,
    ):
        """Initialize chat view.

        Args:
            messages: ListState containing ChatMessageData items
            a2ui_renderer: Optional renderer for A2UI content
            show_timestamps: Whether to show message timestamps
            auto_scroll: Whether to auto-scroll to new messages
        """
        super().__init__()
        self._messages = messages
        self._messages.attach(self)
        self._a2ui_renderer = a2ui_renderer
        self._show_timestamps = show_timestamps
        self._auto_scroll = auto_scroll
        self._scroll_state = ScrollState()

    def view(self):
        from castella.theme import ThemeManager

        theme = ThemeManager().current

        if not self._messages:
            return Box(
                Text("No messages yet", font_size=14)
                .text_color(theme.colors.text_info)
                .fixed_height(40)
            ).bg_color(theme.colors.bg_primary)

        message_widgets = []
        for msg in self._messages:
            # Wrap ChatMessage in Box with CONTENT height for scrollable Column
            msg_widget = ChatMessage(
                role=msg.role,
                content=msg.content,
                a2ui_json=msg.a2ui_json,
                a2ui_renderer=self._a2ui_renderer,
                tool_calls=msg.tool_calls,
                timestamp=msg.timestamp,
                show_timestamp=self._show_timestamps,
            )
            # Set height policy on the Component wrapper
            msg_widget.height_policy(SizePolicy.CONTENT)
            message_widgets.append(msg_widget)
            # Add small spacer between messages
            message_widgets.append(Spacer().fixed_height(8))

        return Column(
            *message_widgets,
            scrollable=True,
            scroll_state=self._scroll_state,
        ).bg_color(theme.colors.bg_primary)


class ChatContainer(Component):
    """Complete chat interface with message list and input.

    Combines ChatView and ChatInput into a complete chat UI.

    Example:
        def handle_message(text: str):
            # Process message and get response
            messages.append(ChatMessageData(role="user", content=text))
            response = agent.ask(text)
            messages.append(ChatMessageData(role="assistant", content=response))

        chat = ChatContainer(messages, on_send=handle_message)
    """

    def __init__(
        self,
        messages: ListState[ChatMessageData],
        on_send: Callable[[str], None],
        *,
        a2ui_renderer: "A2UIRenderer | None" = None,
        title: str | None = None,
        placeholder: str = "Type a message...",
        show_timestamps: bool = False,
    ):
        """Initialize chat container.

        Args:
            messages: ListState containing ChatMessageData items
            on_send: Callback when user sends a message
            a2ui_renderer: Optional renderer for A2UI content
            title: Optional title for the chat
            placeholder: Placeholder for input field
            show_timestamps: Whether to show message timestamps
        """
        super().__init__()
        self._messages = messages
        self._messages.attach(self)
        self._on_send = on_send
        self._a2ui_renderer = a2ui_renderer
        self._title = title
        self._placeholder = placeholder
        self._show_timestamps = show_timestamps

    def view(self):
        from castella.theme import ThemeManager

        theme = ThemeManager().current

        elements = []

        # Title bar (optional)
        if self._title:
            elements.append(
                Box(
                    Text(self._title, font_size=16)
                    .text_color(theme.colors.text_primary)
                    .fixed_height(24)
                )
                .bg_color(theme.colors.bg_secondary)
                .fixed_height(40)
            )

        # Message list - use Box to ensure proper sizing
        chat_view = ChatView(
            self._messages,
            a2ui_renderer=self._a2ui_renderer,
            show_timestamps=self._show_timestamps,
        )
        elements.append(chat_view)

        # Input area
        chat_input = ChatInput(
            on_submit=self._on_send,
            placeholder=self._placeholder,
        )
        elements.append(chat_input)

        return Column(*elements).bg_color(theme.colors.bg_primary)
