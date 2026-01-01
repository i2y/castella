"""Demo: State Preservation with Component.cache()

This demo shows how to preserve widget state using the Component.cache() method.
cache() automatically reuses widget instances across view() rebuilds.

Pattern:
- Use self.cache(items, factory) in view()
- Widget instances are cached by item.id (or hash, or id())
- Removed items are automatically cleaned up

Try:
- Click "Shuffle" - timer counts are PRESERVED because widgets are reused!
- Click "Add Item" - new timer starts
- Click "Remove" - timer stops and widget is cleaned up
"""

import random
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
    Widget,
)
from castella.frame import Frame


@dataclass
class TodoItem:
    id: int
    name: str


class TimerWidget(Widget):
    """A widget that counts up while mounted."""

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
        print(f"[on_mount] {self._name} (id={self._item_id})")
        self._timer_running = True
        self._timer_thread = threading.Thread(target=self._timer_loop, daemon=True)
        self._timer_thread.start()

    def on_unmount(self) -> None:
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

        p.style(Style(fill=FillStyle(color="#2d2d3d")))
        p.fill_rect(rect)

        p.style(Style(fill=FillStyle(color="#e0e0e0"), font=Font(family="", size=14)))
        text = f"{self._name}: {self._count}s"
        p.fill_text(text, Point(x=10, y=25), max_width=size.width - 100)


class StatefulDemo(Component):
    """Demo using Component.cache() for state preservation."""

    def __init__(self):
        super().__init__()
        self._items = ListState[TodoItem]([
            TodoItem(id=1, name="Task A"),
            TodoItem(id=2, name="Task B"),
            TodoItem(id=3, name="Task C"),
        ])
        self._items.attach(self)

        self._next_id = 4

    def _add_item(self, _):
        new_item = TodoItem(id=self._next_id, name=f"Task {chr(64 + self._next_id)}")
        self._next_id += 1
        self._items.append(new_item)

    def _shuffle_items(self, _):
        items = list(self._items)
        random.shuffle(items)
        # Use set() for atomic update (single notify, preserves cache)
        self._items.set(items)
        print("[Shuffle] Widgets reused - counts preserved!")

    def _remove_item(self, item_id: int):
        for item in list(self._items):
            if item.id == item_id:
                self._items.remove(item)
                break

    def view(self) -> Widget:
        header = Column(
            Text("State Preservation Demo (Component.cache)").fixed_height(40),
            Row(
                Button("Add Item").on_click(self._add_item).fixed_width(100),
                Button("Shuffle").on_click(self._shuffle_items).fixed_width(100),
            ).fixed_height(50),
            Text("Shuffle to see counts preserved!").fixed_height(30),
        ).fixed_height(130)

        # Use Component.cache() to reuse widget instances across view() rebuilds
        # The timer counts are preserved because widgets are reused!
        timer_widgets = self.cache(
            self._items,
            lambda item: TimerWidget(item.id, item.name),
        )

        item_rows = [
            Row(
                timer,
                Button("Remove")
                .on_click(lambda _, i=item.id: self._remove_item(i))
                .fixed_width(80),
            ).fixed_height(45)
            for item, timer in zip(self._items, timer_widgets)
        ]
        items_list = Column(*item_rows, scrollable=True)

        return Column(header, items_list)


def main():
    print("=" * 60)
    print("State Preservation Demo (Component.cache())")
    print("=" * 60)
    print()
    print("This demo uses Component.cache() to preserve widget state")
    print("across view() rebuilds without manual caching.")
    print()
    print("Try 'Shuffle' - timer counts will be preserved!")
    print()

    app = App(Frame("State Preservation Demo", 500, 400), StatefulDemo())
    app.run()


if __name__ == "__main__":
    main()
