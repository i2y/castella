"""Markdown Editor with Live Preview - combines MultilineInput and Markdown widgets."""

from castella import (
    App,
    Box,
    Column,
    Component,
    Markdown,
    Row,
    ScrollState,
    SizePolicy,
    Text,
)
from castella.frame import Frame
from castella.multiline_input import MultilineInput, MultilineInputState


INITIAL_MARKDOWN = """# Hello Markdown!

This is a **live preview** editor.

## Try editing:

- Add some *italic* text
- Create a list
- Write some `code`

```python
print("Hello, Castella!")
```

> Type in the left panel to see changes here!
"""


class MarkdownEditor(Component):
    """A split-view Markdown editor with live preview."""

    def __init__(self):
        super().__init__()
        self._text_state = MultilineInputState(INITIAL_MARKDOWN.strip())
        # Attach state to component - preview updates when editing finishes
        self._text_state.attach(self)
        # ScrollState to preserve preview scroll position across re-renders
        self._preview_scroll = ScrollState()

    def view(self):
        return Row(
            # Editor panel (left)
            Column(
                Text("Editor").height(30),
                MultilineInput(
                    self._text_state,
                    font_size=13,
                    padding=10,
                    line_spacing=4,
                    wrap=True,
                )
                .width_policy(SizePolicy.EXPANDING)
                .height_policy(SizePolicy.EXPANDING),
            )
            .width_policy(SizePolicy.EXPANDING)
            .height_policy(SizePolicy.EXPANDING),
            # Preview panel (right)
            Column(
                Text("Preview").height(30),
                Box(
                    Markdown(
                        self._text_state.value(),
                        base_font_size=13,
                        padding=10,
                        on_link_click=lambda url: print(f"Link: {url}"),
                    )
                    .width_policy(SizePolicy.EXPANDING)
                    .fit_content_height(),
                    scroll_state=self._preview_scroll,
                )
                .width_policy(SizePolicy.EXPANDING)
                .height_policy(SizePolicy.EXPANDING),
            )
            .width_policy(SizePolicy.EXPANDING)
            .height_policy(SizePolicy.EXPANDING),
        )


def main():
    app = App(
        Frame("Markdown Editor", width=1000, height=700),
        MarkdownEditor(),
    )
    app.run()


if __name__ == "__main__":
    main()
