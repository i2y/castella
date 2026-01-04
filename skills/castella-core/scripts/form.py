"""
Form Example - Demonstrates Input, CheckBox, and Button widgets.

Run with: uv run python skills/castella-core/examples/form.py
"""

from castella import (
    App,
    Component,
    State,
    Column,
    Row,
    Text,
    Button,
    Input,
    CheckBox,
    SizePolicy,
)
from castella.frame import Frame


class FormExample(Component):
    """A form demonstrating various input widgets."""

    def __init__(self):
        super().__init__()
        # Input states - do NOT attach to avoid focus issues
        self._name = State("")
        self._email = State("")
        self._subscribe = State(False)

        # Result state - attach for display updates
        self._result = State("")
        self._result.attach(self)

    def view(self):
        return Column(
            Text("Registration Form").font_size(20),
            # Name field
            Row(
                Text("Name:").fixed_width(80),
                Input(self._name())
                .on_change(lambda t: self._name.set(t))
                .fit_parent(),
            ).fixed_height(40),
            # Email field
            Row(
                Text("Email:").fixed_width(80),
                Input(self._email())
                .on_change(lambda t: self._email.set(t))
                .fit_parent(),
            ).fixed_height(40),
            # Subscribe checkbox
            Row(
                Text("Subscribe:").fixed_width(80),
                CheckBox(self._subscribe).on_change(
                    lambda v: self._subscribe.set(v)
                ),
            ).fixed_height(40),
            # Submit button
            Button("Submit").on_click(self._submit).fixed_height(40),
            # Result display
            Text(self._result()).text_color("#00ff00"),
        ).padding(20).width(400).width_policy(SizePolicy.FIXED)

    def _submit(self, _event):
        name = self._name()
        email = self._email()
        subscribe = "Yes" if self._subscribe() else "No"
        self._result.set(f"Submitted: {name}, {email}, Subscribe: {subscribe}")


if __name__ == "__main__":
    App(Frame("Form Example", 500, 350), FormExample()).run()
