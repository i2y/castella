"""Agent UI components for Castella.

This module provides UI components for building agent-based applications,
including chat interfaces, tool visualization, and agent management.

Components:
    - ChatMessage: Display a single chat message
    - ChatInput: Text input with send button
    - ChatView: Scrollable list of chat messages
    - ChatContainer: Complete chat UI (messages + input)
    - ChatMessageData: Data class for chat messages
    - ToolCallData: Data class for tool calls
    - ToolCallView: Display tool/function calls
    - ToolHistoryPanel: History of tool calls
    - AgentCardView: Display A2A agent card
    - AgentListView: List of agent cards

Example:
    from castella import App, ListState
    from castella.agent import ChatContainer, ChatMessageData
    from castella.frame import Frame

    messages = ListState([])

    def on_send(text: str):
        messages.append(ChatMessageData(role="user", content=text))
        # Get response from agent...
        messages.append(ChatMessageData(role="assistant", content="Hello!"))

    chat = ChatContainer(messages, on_send=on_send, title="Chat")
    App(Frame("Agent Chat", 800, 600), chat).run()
"""

from castella.agent.agent_chat import AgentChat
from castella.agent.card_view import AgentCardView, AgentListView
from castella.agent.hub import AgentHub
from castella.agent.multi import MultiAgentChat
from castella.agent.chat import (
    ChatContainer,
    ChatInput,
    ChatMessage,
    ChatMessageData,
    ChatView,
    ToolCallData,
)
from castella.agent.tool_view import ToolCallView, ToolHistoryPanel

__all__ = [
    # High-level API
    "AgentChat",
    "AgentHub",
    "MultiAgentChat",
    # Chat components
    "ChatMessage",
    "ChatInput",
    "ChatView",
    "ChatContainer",
    # Data classes
    "ChatMessageData",
    "ToolCallData",
    # Tool visualization
    "ToolCallView",
    "ToolHistoryPanel",
    # Agent cards
    "AgentCardView",
    "AgentListView",
]
