"""Agent Chat Demo

This example demonstrates the chat UI components for building
conversational interfaces with AI agents.

Run with:
    uv run python examples/agent_chat_demo.py
"""


from castella import App, Column, Text, Button, Box, Row, ScrollState
from castella.core import ListState, StatefulComponent
from castella.frame import Frame
from castella.markdown import Markdown
from castella.multiline_input import MultilineInput, MultilineInputState
from castella.theme import ThemeManager


class SimpleChatDemo(StatefulComponent):
    """Simple chat demo using basic Castella components."""

    def __init__(self):
        self._messages = ListState([
            {"role": "system", "content": "Welcome! Try saying 'hello' or ask about 'weather'."},
        ])
        super().__init__(self._messages)
        self._input_state = MultilineInputState("")
        self._scroll_state = ScrollState()
        # Don't attach - manual scrolling works better without re-renders

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

        # Set scroll to bottom BEFORE adding message (so re-render picks it up)
        self._scroll_state.y = 999999

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
                    .fixed_height(20),
                    content_widget,
                ).fit_content_height()
            ).bg_color(bg_color).fit_content_height()

            msg_widgets.append(msg_box)

        # Main layout
        return Column(
            # Title
            Text("Agent Chat Demo")
            .text_color(theme.colors.text_primary)
            .fixed_height(32),

            # Message area (scrollable with preserved position)
            Column(
                *msg_widgets,
                scrollable=True,
                scroll_state=self._scroll_state,
            ).bg_color(theme.colors.bg_primary),

            # Input area
            Row(
                MultilineInput(self._input_state, font_size=14)
                .fixed_height(40),
                Button("Send")
                .on_click(self._send_message)
                .fixed_width(80)
                .fixed_height(40),
            ).fixed_height(56),
        )


def main():
    App(Frame("Agent Chat Demo", 600, 500), SimpleChatDemo()).run()


if __name__ == "__main__":
    main()
