"""
Scrollable List Example - Demonstrates scrollable layouts with preserved position.

Run with: uv run python skills/castella-core/examples/scrollable_list.py
"""

from castella import (
    App,
    Component,
    ListState,
    ScrollState,
    Column,
    Row,
    Text,
    Button,
    SizePolicy,
)
from castella.frame import Frame


class ScrollableList(Component):
    """A scrollable list with preserved scroll position."""

    def __init__(self):
        super().__init__()
        # Initialize with sample items
        self._items = ListState([f"Item {i}" for i in range(1, 51)])
        self._items.attach(self)

        # ScrollState preserves position across rebuilds
        self._scroll = ScrollState()

    def view(self):
        return Column(
            # Header
            Row(
                Text(f"Items: {len(self._items)}").font_size(16),
                Button("Add Item").on_click(self._add_item),
                Button("Clear").on_click(self._clear),
            ).fixed_height(40),
            # Scrollable list
            Column(
                *[
                    Row(
                        Text(item).fit_parent(),
                        Button("X").on_click(lambda _, i=idx: self._remove_item(i)),
                    )
                    .fixed_height(30)
                    .bg_color("#2a2a3a" if idx % 2 == 0 else "#1a1a2a")
                    for idx, item in enumerate(self._items)
                ],
                scrollable=True,
                scroll_state=self._scroll,  # Preserve scroll position
            )
            .fit_parent()
            .height_policy(SizePolicy.EXPANDING),
        ).padding(10)

    def _add_item(self, _event):
        # Scroll to bottom before adding
        self._scroll.y = 999999
        self._items.append(f"Item {len(self._items) + 1}")

    def _remove_item(self, index: int):
        if index < len(self._items):
            self._items.pop(index)

    def _clear(self, _event):
        self._scroll.y = 0  # Reset scroll
        self._items.set([])  # Atomic clear


if __name__ == "__main__":
    App(Frame("Scrollable List", 400, 500), ScrollableList()).run()
