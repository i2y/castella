"""Slider Widget Demo

Demonstrates the Slider widget for range input.

Run with:
    uv run python examples/slider_demo.py
"""

from castella import App, Box, Column, Row, Slider, SliderState, Text, SizePolicy
from castella.core import Component, State
from castella.frame import Frame
from castella.theme import ThemeManager


class SliderDemo(Component):
    """Demo showcasing different slider configurations."""

    def __init__(self):
        super().__init__()
        # Basic slider
        self._basic_value = State(50.0)
        self._basic_value.attach(self)

        # Volume slider (0-100)
        self._volume = SliderState(75.0, min_val=0.0, max_val=100.0)
        self._volume.attach(self)

        # Temperature slider (-20 to 40)
        self._temperature = SliderState(22.0, min_val=-20.0, max_val=40.0)
        self._temperature.attach(self)

        # RGB sliders - need SliderState to preserve values across rebuilds
        self._red = SliderState(128, min_val=0, max_val=255)
        self._green = SliderState(64, min_val=0, max_val=255)
        self._blue = SliderState(192, min_val=0, max_val=255)

    def view(self):
        theme = ThemeManager().current

        return Column(
            # Title
            Text("Slider Widget Demo")
            .text_color(theme.colors.text_primary)
            .height(40)
            .height_policy(SizePolicy.FIXED),

            # Basic Slider
            Box(
                Column(
                    Text(f"Basic Slider: {self._basic_value():.1f}")
                    .height(24)
                    .height_policy(SizePolicy.FIXED),
                    Slider(self._basic_value(), min_val=0, max_val=100)
                    .on_change(lambda v: self._basic_value.set(v))
                    .height(40)
                    .height_policy(SizePolicy.FIXED),
                ).height_policy(SizePolicy.CONTENT)
            ).bg_color(theme.colors.bg_secondary).height(100).height_policy(SizePolicy.FIXED),

            # Volume Slider with SliderState
            Box(
                Column(
                    Text(f"Volume: {self._volume.value():.0f}%")
                    .height(24)
                    .height_policy(SizePolicy.FIXED),
                    Slider(self._volume)
                    .height(40)
                    .height_policy(SizePolicy.FIXED),
                ).height_policy(SizePolicy.CONTENT)
            ).bg_color(theme.colors.bg_tertiary).height(100).height_policy(SizePolicy.FIXED),

            # Temperature Slider with negative range
            Box(
                Column(
                    Text(f"Temperature: {self._temperature.value():.1f}°C")
                    .height(24)
                    .height_policy(SizePolicy.FIXED),
                    Slider(self._temperature)
                    .height(40)
                    .height_policy(SizePolicy.FIXED),
                ).height_policy(SizePolicy.CONTENT)
            ).bg_color(theme.colors.bg_secondary).height(100).height_policy(SizePolicy.FIXED),

            # Multiple sliders in a row
            Box(
                Row(
                    Column(
                        Text("R").height(24).height_policy(SizePolicy.FIXED),
                        Slider(self._red)
                        .height(30)
                        .height_policy(SizePolicy.FIXED),
                    ),
                    Column(
                        Text("G").height(24).height_policy(SizePolicy.FIXED),
                        Slider(self._green)
                        .height(30)
                        .height_policy(SizePolicy.FIXED),
                    ),
                    Column(
                        Text("B").height(24).height_policy(SizePolicy.FIXED),
                        Slider(self._blue)
                        .height(30)
                        .height_policy(SizePolicy.FIXED),
                    ),
                )
            ).bg_color(theme.colors.bg_tertiary).height(100).height_policy(SizePolicy.FIXED),
        ).bg_color(theme.colors.bg_primary)


def main():
    App(Frame("Slider Demo", 600, 500), SliderDemo()).run()


if __name__ == "__main__":
    main()
