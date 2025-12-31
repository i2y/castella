"""Modal Widget Demo

Demonstrates the Modal widget for dialog boxes.

Run with:
    uv run python examples/modal_demo.py
"""

from castella import (
    App, Box, Button, Column, Row, Text, Modal, ModalState, Input,
)
from castella.core import Component, State
from castella.frame import Frame
from castella.theme import ThemeManager


class ModalDemo(Component):
    """Demo showcasing the Modal widget."""

    def __init__(self):
        super().__init__()
        # Modal states
        self._basic_modal = ModalState(open=False)
        self._basic_modal.attach(self)

        self._confirm_modal = ModalState(open=False)
        self._confirm_modal.attach(self)

        self._form_modal = ModalState(open=False)
        self._form_modal.attach(self)

        # Form data
        self._name = State("")
        self._submitted_name = State("")
        self._submitted_name.attach(self)

    def view(self):
        theme = ThemeManager().current

        # Basic modal content
        basic_content = Column(
            Text("This is a basic modal dialog.")
            .fixed_height(40),
            Text("Click outside or the X button to close.")
            .fixed_height(30),
        )

        # Confirm modal content
        confirm_content = Column(
            Text("Are you sure you want to proceed?")
            .fixed_height(40),
            Row(
                Button("Cancel").on_click(lambda _: self._confirm_modal.close()),
                Button("Confirm").on_click(self._on_confirm),
            ).fixed_height(50),
        )

        # Form modal content
        form_content = Column(
            Text("Enter your name:")
            .fixed_height(30),
            Input(self._name())
            .on_change(lambda v: self._name.set(v))
            .fixed_height(40),
            Row(
                Button("Cancel").on_click(lambda _: self._form_modal.close()),
                Button("Submit").on_click(self._on_submit),
            ).fixed_height(50),
        )

        # Main content with buttons to open modals
        main_content = Column(
            Text("Modal Widget Demo")
            .text_color(theme.colors.text_primary)
            .fixed_height(40),

            Text(f"Submitted name: {self._submitted_name() or '(none)'}")
            .fixed_height(30),

            Row(
                Button("Basic Modal").on_click(lambda _: self._basic_modal.open()),
                Button("Confirm Dialog").on_click(lambda _: self._confirm_modal.open()),
                Button("Form Modal").on_click(lambda _: self._form_modal.open()),
            ).fixed_height(60),
        ).bg_color(theme.colors.bg_primary).z_index(1)

        # Create modals
        basic_modal = Modal(
            content=basic_content,
            state=self._basic_modal,
            title="Basic Modal",
            width=350,
            height=200,
        )

        confirm_modal = Modal(
            content=confirm_content,
            state=self._confirm_modal,
            title="Confirmation",
            width=300,
            height=180,
            show_close_button=False,
            close_on_backdrop_click=False,
        )

        form_modal = Modal(
            content=form_content,
            state=self._form_modal,
            title="Enter Name",
            width=350,
            height=220,
        )

        return Box(main_content, basic_modal, confirm_modal, form_modal)

    def _on_confirm(self, _):
        print("Confirmed!")
        self._confirm_modal.close()

    def _on_submit(self, _):
        self._submitted_name.set(self._name())
        self._form_modal.close()
        print(f"Submitted: {self._name()}")


def main():
    App(Frame("Modal Demo", 600, 400), ModalDemo()).run()


if __name__ == "__main__":
    main()
