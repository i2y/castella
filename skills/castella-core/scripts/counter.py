"""
Basic Counter Example - Demonstrates Component pattern with State.

Run with: uv run python skills/castella-core/examples/counter.py
"""

from castella import App, Component, State, Column, Row, Text, Button
from castella.frame import Frame


class Counter(Component):
    """A simple counter component demonstrating State and event handling."""

    def __init__(self):
        super().__init__()
        self._count = State(0)
        self._count.attach(self)  # Trigger view() on state change

    def view(self):
        return Column(
            Text(f"Count: {self._count()}").font_size(24),
            Row(
                Button("-1").on_click(self._decrement).fixed_width(80),
                Button("+1").on_click(self._increment).fixed_width(80),
            ),
            Button("Reset").on_click(self._reset),
        ).padding(20)

    def _increment(self, _event):
        self._count += 1

    def _decrement(self, _event):
        self._count -= 1

    def _reset(self, _event):
        self._count.set(0)


if __name__ == "__main__":
    App(Frame("Counter", 400, 200), Counter()).run()
