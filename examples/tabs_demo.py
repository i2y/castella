"""Tabs Widget Demo

Demonstrates the Tabs widget for tabbed navigation.

Run with:
    uv run python examples/tabs_demo.py
"""

from castella import (
    App, Box, Button, Column, Row, Text, Tabs, TabsState, TabItem,
    SizePolicy, Slider, SliderState,
)
from castella.core import Component, State
from castella.frame import Frame
from castella.theme import ThemeManager


class TabsDemo(Component):
    """Demo showcasing the Tabs widget."""

    def __init__(self):
        super().__init__()
        self._counter = State(0)
        self._counter.attach(self)

    def view(self):
        theme = ThemeManager().current

        # Home tab content
        home_content = Column(
            Text("Welcome to the Home Tab!")
            .text_color(theme.colors.text_primary)
            .height(40)
            .height_policy(SizePolicy.FIXED),
            Text("This is a simple demonstration of the Tabs widget.")
            .height(30)
            .height_policy(SizePolicy.FIXED),
        ).bg_color(theme.colors.bg_secondary)

        # Settings tab content
        settings_content = Column(
            Text("Settings")
            .text_color(theme.colors.text_primary)
            .height(40)
            .height_policy(SizePolicy.FIXED),
            Row(
                Text("Volume").height(30).height_policy(SizePolicy.FIXED),
                Slider(75, min_val=0, max_val=100)
                .height(30)
                .height_policy(SizePolicy.FIXED),
            ).height(40).height_policy(SizePolicy.FIXED),
            Row(
                Text("Brightness").height(30).height_policy(SizePolicy.FIXED),
                Slider(50, min_val=0, max_val=100)
                .height(30)
                .height_policy(SizePolicy.FIXED),
            ).height(40).height_policy(SizePolicy.FIXED),
        ).bg_color(theme.colors.bg_tertiary)

        # Counter tab content
        counter_content = Column(
            Text(f"Counter: {self._counter()}")
            .text_color(theme.colors.text_primary)
            .height(60)
            .height_policy(SizePolicy.FIXED),
            Row(
                Button("Increment").on_click(lambda _: self._counter.set(self._counter() + 1)),
                Button("Decrement").on_click(lambda _: self._counter.set(self._counter() - 1)),
                Button("Reset").on_click(lambda _: self._counter.set(0)),
            ).height(50).height_policy(SizePolicy.FIXED),
        ).bg_color(theme.colors.bg_secondary)

        # About tab content
        about_content = Column(
            Text("About")
            .text_color(theme.colors.text_primary)
            .height(40)
            .height_policy(SizePolicy.FIXED),
            Text("Tabs Widget Demo v1.0")
            .height(30)
            .height_policy(SizePolicy.FIXED),
            Text("Part of the Castella UI Framework")
            .height(30)
            .height_policy(SizePolicy.FIXED),
        ).bg_color(theme.colors.bg_tertiary)

        # Create tabs
        tabs = Tabs(TabsState([
            TabItem(id="home", label="Home", content=home_content),
            TabItem(id="settings", label="Settings", content=settings_content),
            TabItem(id="counter", label="Counter", content=counter_content),
            TabItem(id="about", label="About", content=about_content),
        ])).on_change(lambda tab_id: print(f"Tab changed to: {tab_id}"))

        return Column(
            Text("Tabs Widget Demo")
            .text_color(theme.colors.text_primary)
            .height(40)
            .height_policy(SizePolicy.FIXED),
            tabs,
        ).bg_color(theme.colors.bg_primary)


def main():
    App(Frame("Tabs Demo", 600, 400), TabsDemo()).run()


if __name__ == "__main__":
    main()
