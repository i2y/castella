"""Agent Chat Demo

This example demonstrates the chat UI components for building
conversational interfaces with AI agents.

Run with:
    uv run python examples/agent_chat_demo.py
"""

import sys
from datetime import datetime

from castella import App, Column, Text, Button, Box, Row
from castella.core import ListState, SizePolicy, Component, State
from castella.frame import Frame
from castella.markdown import Markdown
from castella.multiline_input import MultilineInput, MultilineInputState
from castella.theme import ThemeManager


class SimpleChatDemo(Component):
    """Simple chat demo using basic Castella components."""

    def __init__(self):
        super().__init__()
        self._messages = ListState([
            {"role": "system", "content": "Welcome! Try saying 'hello' or ask about 'weather'."},
        ])
        self._messages.attach(self)
        self._input_state = MultilineInputState("")

    def _send_message(self, event=None):
        text = self._input_state.value().strip()
        if not text:
            return

        # Add user message
        self._messages.append({"role": "user", "content": text})

        # Generate response
        text_lower = text.lower()
        if "hello" in text_lower or "hi" in text_lower:
            response = "Hello! How can I help you today?"
        elif "weather" in text_lower:
            response = "The weather is **sunny** and 22°C today!"
        elif "markdown" in text_lower:
            response = "# Markdown Test\n\n**Bold** and *italic* work!\n\n- Item 1\n- Item 2"
        else:
            response = f"You said: *{text}*"

        self._messages.append({"role": "assistant", "content": response})

        # Clear input
        self._input_state.set("")

    def view(self):
        theme = ThemeManager().current

        # Build message widgets
        msg_widgets = []
        for msg in self._messages:
            role = msg["role"]
            content = msg["content"]

            # Role label color
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

            # Use Markdown for all messages (supports formatting)
            content_widget = Markdown(content, base_font_size=14)

            msg_box = Box(
                Column(
                    Text(role_label)
                    .text_color(role_color)
                    .height(20)
                    .height_policy(SizePolicy.FIXED),
                    content_widget,
                ).height_policy(SizePolicy.CONTENT)
            ).bg_color(bg_color).height_policy(SizePolicy.CONTENT)

            msg_widgets.append(msg_box)

        # Main layout
        return Column(
            # Title
            Text("Agent Chat Demo")
            .text_color(theme.colors.text_primary)
            .height(32)
            .height_policy(SizePolicy.FIXED),

            # Message area (scrollable)
            Column(
                *msg_widgets,
                scrollable=True,
            ).bg_color(theme.colors.bg_primary),

            # Input area
            Row(
                MultilineInput(self._input_state, font_size=14)
                .height(40)
                .height_policy(SizePolicy.FIXED),
                Button("Send")
                .on_click(self._send_message)
                .width(80)
                .width_policy(SizePolicy.FIXED)
                .height(40)
                .height_policy(SizePolicy.FIXED),
            ).height(56).height_policy(SizePolicy.FIXED),
        )


def main():
    App(Frame("Agent Chat Demo", 600, 500), SimpleChatDemo()).run()


if __name__ == "__main__":
    main()
