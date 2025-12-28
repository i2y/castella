"""Castella Showcase - Demonstrating widgets, layouts, and features.

This example showcases Castella's capabilities:
- Widgets: Button, Text, MultilineText, Input, CheckBox, Switch
- Layouts: Column, Row, Box, Spacer
- State management: State, Component
- Z-index: Modal dialogs
- Styling: Kind (INFO, SUCCESS, WARNING, DANGER)
"""

from castella import (
    App,
    Box,
    Button,
    CheckBox,
    Column,
    Component,
    Input,
    Kind,
    MultilineText,
    Row,
    Spacer,
    State,
    Switch,
    Text,
)
from castella.frame import Frame


class Showcase(Component):
    """Main showcase component with all features in one Component."""

    def __init__(self):
        super().__init__()
        # Tab state
        self._current_tab = State("widgets")
        # Modal state
        self._show_modal = State(False)
        # Widgets tab state
        self._counter = State(0)
        # Inputs tab state
        self._text = State("Hello")
        self._switch_on = State(True)
        # Layout tab state
        self._z_top = State(3)

        # Use attach directly to observe multiple states
        # Note: _text is NOT attached because Input manages its own state
        # and we don't want to rebuild view() on every keystroke
        self._current_tab.attach(self)
        self._show_modal.attach(self)
        self._counter.attach(self)
        self._switch_on.attach(self)
        self._z_top.attach(self)

    def view(self):
        tab = self._current_tab()

        # Navigation tabs
        nav = Row(
            Button("Widgets").on_click(lambda _: self._current_tab.set("widgets")),
            Button("Inputs").on_click(lambda _: self._current_tab.set("inputs")),
            Button("Layout").on_click(lambda _: self._current_tab.set("layout")),
            Button("Modal").on_click(lambda _: self._show_modal.set(True)),
        ).fixed_height(40)

        # Tab indicator
        indicator = Text(f"Tab: {tab.upper()}", font_size=12).fixed_height(20)

        # Content based on selected tab
        if tab == "widgets":
            content = self._widgets_content()
        elif tab == "inputs":
            content = self._inputs_content()
        else:
            content = self._layout_content()

        main = Column(nav, indicator, content).z_index(1)

        # Modal overlay
        if self._show_modal():
            modal = Column(
                Text("Modal Dialog", font_size=18),
                MultilineText(
                    "This modal uses z-index\nto appear on top.",
                    font_size=14,
                    kind=Kind.WARNING,
                ),
                Spacer(),
                Button("Close").on_click(lambda _: self._show_modal.set(False)),
            ).fixed_size(250, 180).z_index(10)

            return Box(main, modal)

        return main

    def _widgets_content(self):
        """Counter demo with Kind styling."""
        count = self._counter()

        if count > 0:
            kind, msg = Kind.SUCCESS, "Positive!"
        elif count < 0:
            kind, msg = Kind.DANGER, "Negative!"
        else:
            kind, msg = Kind.INFO, "Zero"

        return Column(
            Text("Counter Demo", font_size=16).fixed_height(25),
            Text(f"Count: {count}", font_size=24).fixed_height(35),
            MultilineText(msg, font_size=12, kind=kind).fixed_height(25),
            Row(
                Button("-5").on_click(lambda _: self._counter.set(self._counter() - 5)),
                Button("-1").on_click(lambda _: self._counter.set(self._counter() - 1)),
                Button("0").on_click(lambda _: self._counter.set(0)),
                Button("+1").on_click(lambda _: self._counter.set(self._counter() + 1)),
                Button("+5").on_click(lambda _: self._counter.set(self._counter() + 5)),
            ).fixed_height(35),
            Spacer(),
            MultilineText(
                "Click buttons to change count.\nColor changes based on value.",
                font_size=11,
                kind=Kind.INFO,
            ),
        )

    def _inputs_content(self):
        """Input, CheckBox, Switch demo."""
        return Column(
            Text("Text Input:", font_size=14).fixed_height(20),
            Input(self._text()).on_change(lambda t: self._text.set(t)).fixed_height(30),
            Text(f"You typed: {self._text()}", font_size=12).fixed_height(20),
            Spacer().fixed_height(10),
            Text("CheckBox:", font_size=14).fixed_height(20),
            Row(
                CheckBox().fixed_size(25, 25),
                Text("Option A", font_size=12),
                Spacer(),
                CheckBox().fixed_size(25, 25),
                Text("Option B", font_size=12),
                Spacer(),
            ).fixed_height(30),
            Spacer().fixed_height(10),
            Row(
                Text("Switch:", font_size=14),
                Spacer(),
                Switch(self._switch_on()).on_change(lambda v: self._switch_on.set(v)).fixed_width(50),
                Text("ON" if self._switch_on() else "OFF", font_size=12),
            ).fixed_height(25),
            Spacer(),
        )

    def _layout_content(self):
        """Flex, nested layouts, Box z-index demo."""
        top = self._z_top()

        return Column(
            Text("Flex (1:2:1)", font_size=14).fixed_height(20),
            Row(
                Button("1").flex(1),
                Button("2").flex(2),
                Button("1").flex(1),
            ).fixed_height(30),
            Spacer().fixed_height(5),
            Text("Nested Layout", font_size=14).fixed_height(20),
            Row(
                Column(Button("A1"), Button("A2")),
                Column(Button("B1"), Button("B2"), Button("B3")),
            ).fixed_height(80),
            Spacer().fixed_height(5),
            Text("Box Z-Index", font_size=14).fixed_height(20),
            Row(
                Button("Red").on_click(lambda _: self._z_top.set(1)),
                Button("Grn").on_click(lambda _: self._z_top.set(2)),
                Button("Blu").on_click(lambda _: self._z_top.set(3)),
            ).fixed_height(25),
            Box(
                MultilineText("R", font_size=14, kind=Kind.DANGER)
                .fixed_size(50, 40).z_index(3 if top == 1 else 1),
                MultilineText("G", font_size=14, kind=Kind.SUCCESS)
                .fixed_size(50, 40).z_index(3 if top == 2 else 2),
                MultilineText("B", font_size=14, kind=Kind.INFO)
                .fixed_size(50, 40).z_index(3 if top == 3 else 1),
            ).fixed_height(45),
            Spacer(),
        )


App(
    Frame("Castella Showcase", width=400, height=350),
    Showcase(),
).run()
