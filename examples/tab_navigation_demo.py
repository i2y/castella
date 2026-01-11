"""Tab Navigation Demo

This demo shows how Tab/Shift+Tab can be used to navigate between
focusable widgets (Input, MultilineInput, Button).

Features:
- Tab: Move to next field
- Shift+Tab: Move to previous field
- Enter/Space: Click button when focused
- Focus ring: Visual indicator when widget is focused
"""

from castella import App, Box, Button, CheckBox, Column, Input, Row, Spacer, Switch, Text
from castella.core import State
from castella.frame import Frame
from castella.multiline_input import MultilineInput, MultilineInputState


class FormDemo:
    def __init__(self):
        self._name = ""
        self._email = ""
        self._message_state = MultilineInputState("")
        self._result = ""
        self._subscribe = State(False)
        self._notifications = State(True)

    def _on_submit(self, _):
        self._result = f"Submitted: {self._name}, {self._email}"
        print(self._result)

    def _on_clear(self, _):
        self._name = ""
        self._email = ""
        self._message_state._lines = [""]
        self._result = "Cleared!"
        print(self._result)

    def build(self):
        return Column(
            Text("Tab Navigation Demo").fixed_height(30),
            Spacer().fixed_height(10),
            # Form fields with explicit tab order
            Row(
                Text("Name:").fixed_width(80).fixed_height(30),
                Input(self._name)
                .tab_index(1)
                .on_change(lambda t: setattr(self, "_name", t))
                .fixed_height(30),
            ).fixed_height(30),
            Spacer().fixed_height(10),
            Row(
                Text("Email:").fixed_width(80).fixed_height(30),
                Input(self._email)
                .tab_index(2)
                .on_change(lambda t: setattr(self, "_email", t))
                .fixed_height(30),
            ).fixed_height(30),
            Spacer().fixed_height(10),
            Row(
                Text("Message:").fixed_width(80).fixed_height(60),
                MultilineInput(self._message_state, font_size=14, wrap=True)
                .tab_index(3)
                .fixed_height(60),
            ).fixed_height(60),
            Spacer().fixed_height(10),
            # CheckBox
            Row(
                Text("Subscribe:").fixed_width(100).fixed_height(30),
                CheckBox(self._subscribe).tab_index(4).fixed_size(30, 30),
                Text("Newsletter").fixed_height(30),
            ).fixed_height(30),
            Spacer().fixed_height(10),
            # Switch
            Row(
                Text("Notifications:").fixed_width(100).fixed_height(30),
                Switch(self._notifications).tab_index(5).fixed_size(50, 25),
            ).fixed_height(30),
            Spacer().fixed_height(20),
            # Buttons
            Row(
                Button("Submit").tab_index(6).on_click(self._on_submit).fixed_width(100),
                Spacer().fixed_width(10),
                Button("Clear").tab_index(7).on_click(self._on_clear).fixed_width(100),
            ).fixed_height(35),
            Spacer().fixed_height(10),
            Text("Tab: move, Enter/Space: toggle/click").fixed_height(25),
        ).fixed_size(400, 380)


def main():
    demo = FormDemo()
    frame = Frame("Tab Navigation Demo", 450, 440)
    app = App(
        frame,
        Box(demo.build()),
    )
    app.run()


if __name__ == "__main__":
    main()
