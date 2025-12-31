"""Chat-like interface with Markdown message rendering."""

from castella import (
    App,
    Box,
    Button,
    Column,
    Component,
    Input,
    ListState,
    Markdown,
    Row,
    ScrollState,
    SizePolicy,
    State,
    Text,
)
from castella.frame import Frame


SAMPLE_MESSAGES = [
    {
        "sender": "Alice",
        "content": "Hey! Have you tried the new **Castella** framework?",
    },
    {
        "sender": "Bob",
        "content": """Yes! It's great for building UIs. Here's a quick example:

```python
from castella import App, Text
App(Frame(), Text("Hello!")).run()
```

Super simple!""",
    },
    {
        "sender": "Alice",
        "content": "Nice! Does it support:\n- Lists\n- *Formatting*\n- `Code`?",
    },
    {
        "sender": "Bob",
        "content": "All of the above! Plus:\n\n| Feature | Status |\n|---------|--------|\n| Tables | ✓ |\n| Math | ✓ |\n| Images | ✓ |",
    },
]


class ChatApp(Component):
    """A chat application with Markdown message support."""

    def __init__(self):
        super().__init__()
        self._messages = ListState(list(SAMPLE_MESSAGES))
        self._messages.attach(self)
        self._input_text = State("")
        # ScrollState preserves scroll position across view rebuilds
        self._scroll = ScrollState()

    def _send_message(self, _):
        text = self._input_text()
        if text.strip():
            self._messages.append({"sender": "You", "content": text})
            self._input_text.set("")

    def view(self):
        # Build message widgets directly
        message_widgets = []
        for msg in self._messages:
            message_widgets.append(
                Column(
                    Text(msg["sender"]).fixed_height(24),
                    Markdown(msg["content"], base_font_size=13, padding=8),
                ).fit_content_height()
            )

        return Column(
            # Header
            Text("Markdown Chat").height(40),
            # Messages area - use Box with scroll_state to preserve position
            Box(
                Column(*message_widgets).fit_content_height(),
                scroll_state=self._scroll,  # Preserves scroll position on re-render
            )
            .width_policy(SizePolicy.EXPANDING)
            .height_policy(SizePolicy.EXPANDING),
            # Input area
            Row(
                Input(self._input_text(), font_size=14)
                .on_change(lambda t: self._input_text.set(t))
                .width_policy(SizePolicy.EXPANDING)
                .height(40),
                Button("Send", font_size=14)
                .on_click(self._send_message)
                .width(80)
                .height(40),
            ).height(50),
        )


def main():
    app = App(
        Frame("Markdown Chat", width=600, height=700),
        ChatApp(),
    )
    app.run()


if __name__ == "__main__":
    main()
