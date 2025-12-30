"""Demo for text selection and copy/cut/paste functionality."""

from castella import App, Column, Component, Row, Text
from castella.core import SizePolicy
from castella.frame import Frame
from castella.multiline_input import MultilineInput, MultilineInputState
from castella.multiline_text import MultilineText


class TextSelectionDemo(Component):
    def __init__(self):
        super().__init__()
        self._input_state = MultilineInputState(
            "Select text with mouse drag.\n"
            "Try Cmd+C (or Ctrl+C) to copy.\n"
            "Cmd+X to cut, Cmd+V to paste.\n"
            "Cmd+A to select all."
        )

    def view(self):
        return Column(
            Text("Text Selection Demo", font_size=24)
            .height(40)
            .height_policy(SizePolicy.FIXED),
            Text("MultilineInput (editable - copy/cut/paste):", font_size=14)
            .height(24)
            .height_policy(SizePolicy.FIXED),
            MultilineInput(self._input_state, font_size=14, wrap=True)
            .height(150)
            .height_policy(SizePolicy.FIXED),
            Text("MultilineText (read-only - copy only):", font_size=14)
            .height(24)
            .height_policy(SizePolicy.FIXED),
            MultilineText(
                "This is read-only text.\n"
                "You can select and copy (Cmd+C).\n"
                "But cut and paste are disabled.\n"
                "Try Cmd+A to select all.",
                font_size=14,
                wrap=True,
            )
            .height(150)
            .height_policy(SizePolicy.FIXED),
        )


if __name__ == "__main__":
    App(Frame("Text Selection Demo", 600, 500), TextSelectionDemo()).run()
