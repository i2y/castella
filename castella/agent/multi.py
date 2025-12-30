"""MultiAgentChat - Chat UI for multiple A2A agents.

This module provides a tabbed chat interface for interacting with
multiple A2A agents simultaneously.

Example:
    from castella.agent import MultiAgentChat
    from castella.a2a import A2AClient

    chat = MultiAgentChat({
        "weather": A2AClient("http://weather-agent.example.com"),
        "travel": A2AClient("http://travel-agent.example.com"),
    })
    chat.run()
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from castella import App, Box, Column, Row, ScrollState, Text
from castella.button import Button
from castella.core import Component, ListState, SizePolicy, State
from castella.frame import Frame
from castella.markdown import Markdown
from castella.multiline_input import MultilineInput, MultilineInputState
from castella.tabs import Tabs, TabsState, TabItem

if TYPE_CHECKING:
    from castella.a2a import A2AClient


class MultiAgentChat(Component):
    """Tabbed chat UI for multiple A2A agents.

    Provides a tabbed interface where each tab connects to a different
    A2A agent, allowing users to switch between conversations.

    Example:
        from castella.agent import MultiAgentChat
        from castella.a2a import A2AClient

        chat = MultiAgentChat({
            "weather": A2AClient("http://weather-agent.example.com"),
            "travel": A2AClient("http://travel-agent.example.com"),
        })
        chat.run()

        # Or build incrementally
        chat = MultiAgentChat()
        chat.add_agent("weather", A2AClient("http://weather-agent.example.com"))
        chat.add_agent("travel", A2AClient("http://travel-agent.example.com"))
        chat.run()
    """

    def __init__(
        self,
        agents: dict[str, "A2AClient"] | None = None,
        *,
        title: str = "Multi-Agent Chat",
        width: int = 800,
        height: int = 600,
    ):
        """Initialize MultiAgentChat.

        Args:
            agents: Dictionary mapping agent ID to A2AClient
            title: Window title for run()
            width: Window width for run()
            height: Window height for run()
        """
        super().__init__()

        self._title = title
        self._width = width
        self._height = height

        # Agents: id -> client
        self._agents: dict[str, "A2AClient"] = agents or {}

        # Messages per agent: id -> ListState
        self._messages: dict[str, ListState] = {}

        # Input states per agent: id -> MultilineInputState
        self._input_states: dict[str, MultilineInputState] = {}

        # Scroll states per agent: id -> ScrollState
        self._scroll_states: dict[str, ScrollState] = {}

        # Loading states per agent: id -> State[bool]
        self._loading_states: dict[str, State[bool]] = {}

        # Currently selected agent
        agent_ids = list(self._agents.keys())
        self._current_agent = State(agent_ids[0] if agent_ids else "")
        self._current_agent.attach(self)

        # Initialize state for each agent
        for agent_id, client in self._agents.items():
            self._init_agent_state(agent_id, client)

    def _init_agent_state(self, agent_id: str, client: "A2AClient") -> None:
        """Initialize state for a new agent."""
        # Initial welcome message
        initial_messages = [
            {
                "role": "system",
                "content": f"Connected to **{client.name}**. {client.description}",
            }
        ]

        messages = ListState(initial_messages)
        messages.attach(self)
        self._messages[agent_id] = messages

        self._input_states[agent_id] = MultilineInputState("")
        self._scroll_states[agent_id] = ScrollState()

        loading = State(False)
        loading.attach(self)
        self._loading_states[agent_id] = loading

    def add_agent(self, agent_id: str, client: "A2AClient") -> "MultiAgentChat":
        """Add an agent to the chat.

        Args:
            agent_id: Unique identifier for this agent
            client: A2AClient instance

        Returns:
            Self for method chaining
        """
        self._agents[agent_id] = client
        self._init_agent_state(agent_id, client)

        # If this is the first agent, select it
        if not self._current_agent():
            self._current_agent.set(agent_id)

        return self

    def _send_message(self, agent_id: str):
        """Handle sending a message to an agent."""
        input_state = self._input_states.get(agent_id)
        messages = self._messages.get(agent_id)
        loading = self._loading_states.get(agent_id)
        scroll_state = self._scroll_states.get(agent_id)
        client = self._agents.get(agent_id)

        if not all([input_state, messages, loading, client]):
            return

        text = input_state.value().strip()
        if not text or loading():
            return

        # Add user message
        messages.append(
            {
                "role": "user",
                "content": text,
            }
        )

        # Clear input
        input_state.set("")

        # Set loading state
        loading.set(True)

        # Get response
        try:
            response = client.ask(text)

            # Set scroll BEFORE append
            if scroll_state:
                scroll_state.y = 999999

            messages.append(
                {
                    "role": "assistant",
                    "content": response,
                }
            )
        except Exception as e:
            if scroll_state:
                scroll_state.y = 999999
            messages.append(
                {
                    "role": "system",
                    "content": f"Error: {e}",
                }
            )
        finally:
            loading.set(False)

    def _build_chat_view(self, agent_id: str, theme) -> "Column":
        """Build chat view for a single agent."""
        messages = self._messages.get(agent_id, ListState([]))
        input_state = self._input_states.get(agent_id, MultilineInputState(""))
        scroll_state = self._scroll_states.get(agent_id, ScrollState())
        loading = self._loading_states.get(agent_id, State(False))

        # Build message widgets
        msg_widgets = []
        for msg in messages:
            role = msg["role"]
            content = msg["content"]

            if role == "user":
                role_color = theme.colors.text_primary
                bg_color = theme.colors.bg_tertiary
                role_label = "You"
            elif role == "assistant":
                role_color = theme.colors.text_info
                bg_color = theme.colors.bg_secondary
                role_label = self._agents.get(agent_id, None)
                role_label = role_label.name if role_label else "Assistant"
            else:
                role_color = theme.colors.text_warning
                bg_color = theme.colors.bg_primary
                role_label = "System"

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
        if loading():
            agent_name = self._agents.get(agent_id)
            agent_name = agent_name.name if agent_name else "Agent"
            loading_box = (
                Box(
                    Column(
                        Text(agent_name, font_size=14)
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
        messages_area = Column(
            *msg_widgets,
            scrollable=True,
            scroll_state=scroll_state,
        ).bg_color(theme.colors.bg_primary)

        # Input area
        send_label = "..." if loading() else "Send"
        input_area = Row(
            MultilineInput(input_state, font_size=14).fixed_height(40),
            Button(send_label)
            .on_click(lambda _: self._send_message(agent_id))
            .fixed_width(80)
            .fixed_height(40),
        ).fixed_height(56)

        return Column(messages_area, input_area)

    def view(self):
        from castella.theme import ThemeManager

        theme = ThemeManager().current

        if not self._agents:
            return Column(
                Text("No agents configured").text_color(theme.colors.text_info)
            ).bg_color(theme.colors.bg_primary)

        # Build tabs for each agent
        tab_items = []
        for agent_id, client in self._agents.items():
            chat_view = self._build_chat_view(agent_id, theme)
            tab_items.append(
                TabItem(
                    id=agent_id,
                    label=client.name,
                    content=chat_view,
                )
            )

        tabs_state = TabsState(tab_items, self._current_agent())
        tabs = Tabs(tabs_state).on_change(lambda id: self._current_agent.set(id))

        return Column(tabs).bg_color(theme.colors.bg_primary)

    def run(self):
        """Run the multi-agent chat as a standalone application.

        Example:
            chat = MultiAgentChat({...})
            chat.run()
        """
        App(Frame(self._title, self._width, self._height), self).run()
