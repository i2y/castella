"""Tabs Widget Demo

Demonstrates the Tabs widget for tabbed navigation.

Run with:
    uv run python examples/tabs_demo.py
"""

from castella import (
    App, Button, Column, Row, Text, Tabs, TabsState, TabItem,
    Slider, SliderState,
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
        # TabsState is preserved to maintain tab selection
        self._tabs_state = TabsState([], selected_id="home")
        # TabsDemo observes TabsState so it rebuilds with fresh content on tab change
        self._tabs_state.attach(self)
        # SliderState is preserved to maintain slider values
        self._volume = SliderState(value=75, min_val=0, max_val=100)
        self._brightness = SliderState(value=50, min_val=0, max_val=100)

    def view(self):
        theme = ThemeManager().current

        # Home tab content
        home_content = Column(
            Text("Welcome to the Home Tab!")
            .text_color(theme.colors.text_primary)
            .fixed_height(40),
            Text("This is a simple demonstration of the Tabs widget.")
            .fixed_height(30),
        ).bg_color(theme.colors.bg_secondary)

        # Settings tab content
        settings_content = Column(
            Text("Settings")
            .text_color(theme.colors.text_primary)
            .fixed_height(40),
            Row(
                Text("Volume").fixed_height(30),
                Slider(self._volume).fixed_height(30),
            ).fixed_height(40),
            Row(
                Text("Brightness").fixed_height(30),
                Slider(self._brightness).fixed_height(30),
            ).fixed_height(40),
        ).bg_color(theme.colors.bg_tertiary)

        # Counter tab content
        counter_content = Column(
            Text(f"Counter: {self._counter()}")
            .text_color(theme.colors.text_primary)
            .fixed_height(60),
            Row(
                Button("Increment").on_click(lambda _: self._counter.set(self._counter() + 1)),
                Button("Decrement").on_click(lambda _: self._counter.set(self._counter() - 1)),
                Button("Reset").on_click(lambda _: self._counter.set(0)),
            ).fixed_height(50),
        ).bg_color(theme.colors.bg_secondary)

        # About tab content
        about_content = Column(
            Text("About")
            .text_color(theme.colors.text_primary)
            .fixed_height(40),
            Text("Tabs Widget Demo v1.0")
            .fixed_height(30),
            Text("Part of the Castella UI Framework")
            .fixed_height(30),
        ).bg_color(theme.colors.bg_tertiary)

        # The _tabs property setter automatically detaches old content widgets
        self._tabs_state._tabs = [
            TabItem(id="home", label="Home", content=home_content),
            TabItem(id="settings", label="Settings", content=settings_content),
            TabItem(id="counter", label="Counter", content=counter_content),
            TabItem(id="about", label="About", content=about_content),
        ]

        tabs = Tabs(self._tabs_state).on_change(
            lambda tab_id: print(f"Tab changed to: {tab_id}")
        )

        return Column(
            Text("Tabs Widget Demo")
            .text_color(theme.colors.text_primary)
            .fixed_height(40),
            tabs,
        ).bg_color(theme.colors.bg_primary)


def main():
    App(Frame("Tabs Demo", 600, 400), TabsDemo()).run()


if __name__ == "__main__":
    main()
