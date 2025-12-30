"""AgentHub - Agent discovery and management dashboard.

This module provides a dashboard UI for discovering, managing, and
interacting with multiple A2A agents.

Example:
    from castella.agent import AgentHub

    hub = AgentHub()
    hub.add_agent("http://weather-agent.example.com")
    hub.add_agent("http://travel-agent.example.com")
    hub.run()
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from castella import App, Box, Column, Row, ScrollState, Text
from castella.button import Button
from castella.core import Component, Kind, ListState, SizePolicy, State
from castella.frame import Frame
from castella.input import Input
from castella.markdown import Markdown
from castella.multiline_input import MultilineInput, MultilineInputState
from castella.spacer import Spacer

if TYPE_CHECKING:
    from castella.a2a import A2AClient


class AgentHub(Component):
    """Agent discovery and management dashboard.

    Provides a split-panel interface with:
    - Left panel: List of agents with add/remove capabilities
    - Right panel: Chat interface for the selected agent

    Example:
        from castella.agent import AgentHub

        # Start empty and add agents
        hub = AgentHub()
        hub.add_agent("http://weather-agent.example.com")
        hub.run()

        # Or initialize with clients
        from castella.a2a import A2AClient

        hub = AgentHub(agents=[
            A2AClient("http://weather-agent.example.com"),
            A2AClient("http://travel-agent.example.com"),
        ])
        hub.run()
    """

    def __init__(
        self,
        agents: list["A2AClient"] | None = None,
        *,
        title: str = "Agent Hub",
        width: int = 1000,
        height: int = 700,
    ):
        """Initialize AgentHub.

        Args:
            agents: Optional list of A2AClient instances
            title: Window title for run()
            width: Window width for run()
            height: Window height for run()
        """
        super().__init__()

        self._title = title
        self._width = width
        self._height = height

        # List of agents
        self._agents: list["A2AClient"] = list(agents or [])

        # Currently selected agent index
        self._selected_index = State(-1)
        self._selected_index.attach(self)

        # URL input for adding agents
        self._url_input = State("")

        # Chat state for selected agent
        self._messages: dict[int, ListState] = {}
        self._input_states: dict[int, MultilineInputState] = {}
        self._scroll_states: dict[int, ScrollState] = {}
        self._loading_states: dict[int, State[bool]] = {}

        # Initialize state for existing agents
        for i, client in enumerate(self._agents):
            self._init_agent_chat_state(i, client)

    def _init_agent_chat_state(self, index: int, client: "A2AClient") -> None:
        """Initialize chat state for an agent."""
        initial_messages = [
            {
                "role": "system",
                "content": f"Connected to **{client.name}**. {client.description}",
            }
        ]

        messages = ListState(initial_messages)
        messages.attach(self)
        self._messages[index] = messages

        self._input_states[index] = MultilineInputState("")
        self._scroll_states[index] = ScrollState()

        loading = State(False)
        loading.attach(self)
        self._loading_states[index] = loading

    def add_agent(self, url_or_client: str | "A2AClient") -> "AgentHub":
        """Add an agent to the hub.

        Args:
            url_or_client: Agent URL string or A2AClient instance

        Returns:
            Self for method chaining

        Example:
            hub = AgentHub()
            hub.add_agent("http://agent1.example.com")
            hub.add_agent(A2AClient("http://agent2.example.com"))
        """
        from castella.a2a import A2AClient

        if isinstance(url_or_client, str):
            client = A2AClient(url_or_client)
        else:
            client = url_or_client

        index = len(self._agents)
        self._agents.append(client)  # Regular list append - no notify
        self._init_agent_chat_state(index, client)

        # Select the new agent if none selected
        if self._selected_index() < 0:
            self._selected_index.set(index)

        return self

    def remove_agent(self, index: int) -> "AgentHub":
        """Remove an agent from the hub.

        Args:
            index: Index of the agent to remove

        Returns:
            Self for method chaining
        """
        if 0 <= index < len(self._agents):
            del self._agents[index]

            # Clean up chat state
            self._messages.pop(index, None)
            self._input_states.pop(index, None)
            self._scroll_states.pop(index, None)
            self._loading_states.pop(index, None)

            # Adjust selection
            if self._selected_index() >= len(self._agents):
                self._selected_index.set(len(self._agents) - 1)

        return self

    def _add_agent_from_input(self, event=None) -> None:
        """Handle adding agent from URL input."""
        url = self._url_input().strip()
        if not url:
            return

        try:
            self.add_agent(url)
            self._url_input.set("")
        except Exception:
            # Could show error message in UI
            pass

    def _select_agent(self, index: int) -> None:
        """Select an agent by index."""
        if 0 <= index < len(self._agents):
            self._selected_index.set(index)

    def _send_message(self, index: int) -> None:
        """Send message to the selected agent."""
        input_state = self._input_states.get(index)
        messages = self._messages.get(index)
        loading = self._loading_states.get(index)
        scroll_state = self._scroll_states.get(index)

        if not all([input_state, messages, loading]):
            return

        if index >= len(self._agents):
            return

        client = self._agents[index]
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

        # Set loading
        loading.set(True)

        # Get response
        try:
            response = client.ask(text)

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

    def _build_agent_list(self, theme) -> Column:
        """Build the agent list panel."""
        items = []

        # Title
        title = (
            Text("Agents", font_size=18)
            .text_color(theme.colors.text_primary)
            .fixed_height(30)
        )
        items.append(title)

        # Agent cards (use Button for click handling)
        for i, client in enumerate(self._agents):
            is_selected = i == self._selected_index()

            card = (
                Button(f"{client.name}\n{client.description or 'No description'}")
                .on_click(lambda ev, idx=i: self._select_agent(idx))
                .fixed_height(60)
            )
            if is_selected:
                card = card.kind(Kind.INFO)
            items.append(card)

        # Empty state
        if not self._agents:
            empty_text = (
                Text("No agents added", font_size=14)
                .text_color(theme.colors.text_info)
                .fixed_height(40)
            )
            items.append(empty_text)

        # Spacer to push add section to bottom
        items.append(Spacer())

        # Add agent section
        add_section = Column(
            Text("Add Agent", font_size=14)
            .text_color(theme.colors.text_info)
            .fixed_height(24),
            Row(
                Input(self._url_input())
                .on_change(lambda t: self._url_input.set(t))
                .fixed_height(32),
                Button("Add")
                .on_click(self._add_agent_from_input)
                .fixed_width(60)
                .fixed_height(32),
            ).fixed_height(40),
        ).fixed_height(80)
        items.append(add_section)

        return (
            Column(*items)
            .bg_color(theme.colors.bg_primary)
            .width(280)
            .width_policy(SizePolicy.FIXED)
        )

    def _build_chat_view(self, index: int, theme) -> Column:
        """Build chat view for the selected agent."""
        if index < 0 or index >= len(self._agents):
            return Column(
                Text("Select an agent to start chatting").text_color(
                    theme.colors.text_info
                )
            ).bg_color(theme.colors.bg_primary)

        client = self._agents[index]
        messages = self._messages.get(index, ListState([]))
        input_state = self._input_states.get(index, MultilineInputState(""))
        scroll_state = self._scroll_states.get(index, ScrollState())
        loading = self._loading_states.get(index, State(False))

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
                role_label = client.name
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
            loading_box = (
                Box(
                    Column(
                        Text(client.name, font_size=14)
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
            .on_click(lambda _: self._send_message(index))
            .fixed_width(80)
            .fixed_height(40),
        ).fixed_height(56)

        return Column(messages_area, input_area)

    def view(self):
        from castella.theme import ThemeManager

        theme = ThemeManager().current

        # Left panel: Agent list
        agent_list = self._build_agent_list(theme)

        # Right panel: Chat view
        chat_view = self._build_chat_view(self._selected_index(), theme)

        return Row(agent_list, chat_view).bg_color(theme.colors.bg_primary)

    def run(self):
        """Run the agent hub as a standalone application.

        Example:
            hub = AgentHub()
            hub.add_agent("http://localhost:8080")
            hub.run()
        """
        App(Frame(self._title, self._width, self._height), self).run()
