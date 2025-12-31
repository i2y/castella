"""Slider Widget Demo

Demonstrates the Slider widget for range input.

Run with:
    uv run python examples/slider_demo.py
"""

from castella import App, Box, Column, Row, Slider, SliderState, Text
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
            .fixed_height(40),

            # Basic Slider
            Box(
                Column(
                    Text(f"Basic Slider: {self._basic_value():.1f}")
                    .fixed_height(24),
                    Slider(self._basic_value(), min_val=0, max_val=100)
                    .on_change(lambda v: self._basic_value.set(v))
                    .fixed_height(40),
                ).fit_content_height()
            ).bg_color(theme.colors.bg_secondary).fixed_height(100),

            # Volume Slider with SliderState
            Box(
                Column(
                    Text(f"Volume: {self._volume.value():.0f}%")
                    .fixed_height(24),
                    Slider(self._volume)
                    .fixed_height(40),
                ).fit_content_height()
            ).bg_color(theme.colors.bg_tertiary).fixed_height(100),

            # Temperature Slider with negative range
            Box(
                Column(
                    Text(f"Temperature: {self._temperature.value():.1f}°C")
                    .fixed_height(24),
                    Slider(self._temperature)
                    .fixed_height(40),
                ).fit_content_height()
            ).bg_color(theme.colors.bg_secondary).fixed_height(100),

            # Multiple sliders in a row
            Box(
                Row(
                    Column(
                        Text("R").fixed_height(24),
                        Slider(self._red)
                        .fixed_height(30),
                    ),
                    Column(
                        Text("G").fixed_height(24),
                        Slider(self._green)
                        .fixed_height(30),
                    ),
                    Column(
                        Text("B").fixed_height(24),
                        Slider(self._blue)
                        .fixed_height(30),
                    ),
                )
            ).bg_color(theme.colors.bg_tertiary).fixed_height(100),
        ).bg_color(theme.colors.bg_primary)


def main():
    App(Frame("Slider Demo", 600, 500), SliderDemo()).run()


if __name__ == "__main__":
    main()
