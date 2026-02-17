"""Scrollable Column/Row demo.

Demonstrates that EXPANDING children are automatically downgraded to CONTENT
in scrollable containers, so users don't need to set size policies manually.
"""

from castella import App, Button, Column, Component, Row, SizePolicy, State, Text
from castella.frame import Frame


class ScrollableDemo(Component):
    def __init__(self):
        super().__init__()
        self._count = State(5)
        self._count.attach(self)

    def view(self):
        items = [
            Text(f"Item {i}", font_size=20).fixed_height(40)
            for i in range(self._count())
        ]

        return Column(
            Row(
                Button("Add item", font_size=14).on_click(self._add),
                Button("Remove item", font_size=14).on_click(self._remove),
            ).fixed_height(50),
            # Text widgets have EXPANDING height by default,
            # but scrollable Column auto-downgrades them to CONTENT.
            Column(*items, scrollable=True),
        )

    def _add(self, _):
        self._count += 1

    def _remove(self, _):
        if self._count() > 0:
            self._count -= 1


App(Frame("Scrollable Column", 400, 400), ScrollableDemo()).run()
