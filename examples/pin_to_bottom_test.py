"""Test script for pin_to_bottom feature.

This demonstrates a chat-like UI where new messages are added dynamically
and the scroll position stays pinned to the bottom.

Features tested:
- pin_to_bottom=True keeps scroll at bottom as content is added
- Manual scroll (wheel or drag) disables pin_to_bottom
- on_user_scroll callback is called when user scrolls
- "Scroll to Bottom" button re-enables pin_to_bottom
"""

from castella import (
    App,
    Button,
    Column,
    Component,
    Row,
    ScrollState,
    State,
    Text,
)
from castella.frame import Frame


class ChatDemo(Component):
    """Demo chat UI with pin_to_bottom feature."""

    def __init__(self):
        super().__init__()
        self._messages = State([
            "Hello! Welcome to the chat demo.",
            "This demonstrates the pin_to_bottom feature.",
            "Try scrolling up with your mouse wheel.",
            "Then click 'Add Message' to see the behavior.",
        ])
        self._messages.attach(self)
        self._scroll = ScrollState()
        self._pinned = State(True)
        self._pinned.attach(self)
        self._status = State("Pinned to bottom")
        self._status.attach(self)
        self._message_count = 4

    def _on_user_scroll(self):
        self._pinned.set(False)
        self._status.set("User scrolled - unpinned")

    def _add_message(self, _):
        self._message_count += 1
        messages = list(self._messages())
        messages.append(f"New message #{self._message_count}")
        self._messages.set(messages)
        if self._pinned():
            self._status.set("Pinned to bottom")
        else:
            self._status.set("Not pinned - new message added")

    def _scroll_to_bottom(self, _):
        self._pinned.set(True)
        self._status.set("Pinned to bottom")

    def view(self):
        # Build message widgets
        message_widgets = [
            Text(text).fixed_height(50)
            for text in self._messages()
        ]

        return Column(
            # Header
            Row(
                Text("Chat Demo").fixed_height(30),
                Text(self._status()).fixed_height(30),
            ).fixed_height(40),
            # Messages area
            Column(
                *message_widgets,
                scrollable=True,
                scroll_state=self._scroll,
                pin_to_bottom=self._pinned(),
                on_user_scroll=self._on_user_scroll,
            ).spacing(8),
            # Controls
            Row(
                Button("Add Message").on_click(self._add_message),
                Button("Scroll to Bottom").on_click(self._scroll_to_bottom),
            ).fixed_height(50),
        )


def main():
    app = App(Frame("Pin to Bottom Test", 400, 600), ChatDemo())
    app.run()


if __name__ == "__main__":
    main()
