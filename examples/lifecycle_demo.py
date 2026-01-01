"""Demo: Widget Lifecycle Hooks (on_mount/on_unmount)

This demo showcases lifecycle hooks:
- on_mount(): Called when widget is added to the tree
- on_unmount(): Called when widget is removed from the tree

Try:
- Click "Add Item" to add new timed items (on_mount starts timer)
- Click "Remove" on an item (on_unmount stops timer)
- Toggle "Hide Items" off (all timers stop via on_unmount)
"""

import threading
import time
from dataclasses import dataclass

from castella import App, Button, Column, Row, Text
from castella.core import (
    Component,
    ListState,
    Painter,
    Point,
    Size,
    SizePolicy,
    State,
    Widget,
)
from castella.frame import Frame


@dataclass
class TodoItem:
    id: int
    name: str


class TimerWidget(Widget):
    """A widget that counts up while mounted.

    Demonstrates lifecycle hooks:
    - on_mount(): Starts a background timer
    - on_unmount(): Stops the timer and cleans up
    """

    def __init__(self, item_id: int, name: str):
        super().__init__(
            state=None,
            pos=Point(x=0, y=0),
            pos_policy=None,
            size=Size(width=0, height=0),
            width_policy=SizePolicy.EXPANDING,
            height_policy=SizePolicy.FIXED,
        )
        self._item_id = item_id
        self._name = name
        self._count = 0
        self._timer_running = False
        self._timer_thread = None
        self.height(40)

    def on_mount(self) -> None:
        """Called when widget is added to the tree. Start the timer."""
        print(f"[on_mount] {self._name} (id={self._item_id})")
        self._timer_running = True
        self._timer_thread = threading.Thread(target=self._timer_loop, daemon=True)
        self._timer_thread.start()

    def on_unmount(self) -> None:
        """Called when widget is removed from the tree. Stop the timer."""
        print(f"[on_unmount] {self._name} (id={self._item_id}) - count was {self._count}")
        self._timer_running = False

    def _timer_loop(self):
        while self._timer_running:
            time.sleep(1)
            if self._timer_running:
                self._count += 1
                self.dirty(True)
                app = App.get()
                if app:
                    app.post_update(self, completely=True)

    def redraw(self, p: Painter, completely: bool) -> None:
        from castella.core import FillStyle, Font, Rect, Style

        size = self.get_size()
        rect = Rect(origin=Point(x=0, y=0), size=size)

        # Background
        p.style(Style(fill=FillStyle(color="#2d2d3d")))
        p.fill_rect(rect)

        # Text
        p.style(Style(fill=FillStyle(color="#e0e0e0"), font=Font(family="", size=14)))
        text = f"{self._name}: {self._count}s"
        p.fill_text(text, Point(x=10, y=25), max_width=size.width - 100)


class LifecycleDemo(Component):
    """Main demo component."""

    def __init__(self):
        super().__init__()
        self._items = ListState[TodoItem]([
            TodoItem(id=1, name="Task A"),
            TodoItem(id=2, name="Task B"),
            TodoItem(id=3, name="Task C"),
        ])
        self._items.attach(self)

        self._show_items = State(True)
        self._show_items.attach(self)

        self._next_id = 4

    def _add_item(self, _):
        new_item = TodoItem(id=self._next_id, name=f"Task {chr(64 + self._next_id)}")
        self._next_id += 1
        self._items.append(new_item)

    def _remove_item(self, item_id: int):
        for item in list(self._items):
            if item.id == item_id:
                self._items.remove(item)
                break

    def _toggle_show(self, _):
        self._show_items.set(not self._show_items())

    def view(self) -> Widget:
        header = Column(
            Text("Lifecycle Hooks Demo").fixed_height(40),
            Row(
                Button("Add Item").on_click(self._add_item).fixed_width(100),
                Button(
                    "Hide Items" if self._show_items() else "Show Items"
                ).on_click(self._toggle_show).fixed_width(120),
            ).fixed_height(50),
            Text("Watch console for on_mount/on_unmount messages").fixed_height(30),
        ).fixed_height(130)

        if self._show_items():
            item_rows = [
                Row(
                    TimerWidget(item.id, item.name),
                    Button("Remove")
                    .on_click(lambda _, i=item.id: self._remove_item(i))
                    .fixed_width(80),
                ).fixed_height(45)
                for item in self._items
            ]
            items_list = Column(*item_rows, scrollable=True)
        else:
            items_list = Column(
                Text("Items hidden - timers stopped (on_unmount called)")
            )

        return Column(header, items_list)


def main():
    print("=" * 60)
    print("Widget Lifecycle Hooks Demo")
    print("=" * 60)
    print()
    print("Watch the console for on_mount/on_unmount messages:")
    print("- Add item: on_mount called, timer starts")
    print("- Remove item: on_unmount called, timer stops")
    print("- Hide all: on_unmount called for each item")
    print()

    app = App(Frame("Lifecycle Demo", 500, 400), LifecycleDemo())
    app.run()


if __name__ == "__main__":
    main()
