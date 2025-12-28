# Z-Index and Widget Layering

## Overview

Z-index controls the stacking order of widgets when they overlap. Higher z-index values appear visually "on top" of lower ones and receive user input (mouse events, clicks) before widgets with lower z-index values.

This feature enables common UI patterns like:

- Modal dialogs
- Popup menus and tooltips
- Floating windows
- Overlay panels

## The z_index() Method

Every widget has a `z_index` property (default: 1). Use the `.z_index(n)` method to set it:

```python
widget = Column(...).z_index(10)
```

**Requirements:**

- Values must be positive integers (>= 1)
- Passing a value less than 1 raises a `ValueError`

**The method returns `self`**, allowing fluent method chaining:

```python
dialog = Column(
    Text("Title"),
    content,
).fixed_size(300, 200).z_index(10)
```

## How Z-Index Works

### Rendering Order

Widgets are rendered in **ascending z-index order** (lower values first):

1. z-index 1 widgets are rendered first (at the back)
2. z-index 10 widgets are rendered on top of z-index 1 widgets
3. Higher z-index widgets appear visually in front

### Event Handling Order

Events are dispatched in **descending z-index order** (higher values first):

1. z-index 10 widgets receive click events first
2. If not handled, z-index 1 widgets receive the event
3. This ensures higher z-index widgets can block clicks to lower ones

## Using Box for Overlapping Widgets

The `Box` container is designed for stacking widgets at the same position. When combined with z-index, it enables layered UIs:

```python
from castella import Box, Column

main_content = Column(...).z_index(1)
modal_dialog = Column(...).z_index(10)

# Both widgets overlap - modal appears on top
return Box(main_content, modal_dialog)
```

## Modal Dialog Pattern

A common pattern for modal dialogs:

```python
from castella import (
    App, Box, Button, Column, Component,
    MultilineText, Row, Spacer, State, Text, Kind
)
from castella.frame import Frame


class ModalDemo(Component):
    def __init__(self):
        super().__init__()
        self._show_modal = State(False)
        self.model(self._show_modal)

    def view(self):
        # Main content with low z-index
        main_content = Column(
            Text("Main Content", font_size=24),
            Spacer(),
            Row(
                Spacer(),
                Button("Open Modal").on_click(
                    lambda _: self._show_modal.set(True)
                ),
                Spacer(),
            ).fixed_height(50),
            Spacer(),
        ).z_index(1)

        if self._show_modal():
            # Modal with high z-index
            modal = Column(
                MultilineText(
                    "Modal Dialog\n\nThis appears on top!",
                    font_size=16,
                    kind=Kind.WARNING,
                ),
                Spacer(),
                Button("Close").on_click(
                    lambda _: self._show_modal.set(False)
                ),
            ).fixed_size(300, 200).z_index(10)

            return Box(main_content, modal)

        return main_content


App(
    Frame("Modal Demo", width=600, height=400),
    ModalDemo(),
).run()
```

## Stacked Windows Example

For multiple overlapping widgets with dynamic stacking order:

```python
from castella import (
    App, Box, Button, Column, Component,
    MultilineText, Row, Spacer, State, Text, Kind
)
from castella.frame import Frame


class StackedDialogs(Component):
    def __init__(self):
        super().__init__()
        # Track order: [back, ..., front]
        self._order = State([1, 2, 3])
        self.model(self._order)

    def _bring_to_front(self, dialog_num):
        order = list(self._order())
        order.remove(dialog_num)
        order.append(dialog_num)
        self._order.set(order)

    def view(self):
        order = self._order()
        # Calculate z-index from position in order
        z1 = order.index(1) + 1
        z2 = order.index(2) + 1
        z3 = order.index(3) + 1

        dialog1 = Column(
            Text(f"Dialog 1 (z: {z1})"),
            Button("Bring to Front").on_click(
                lambda _: self._bring_to_front(1)
            ),
        ).fixed_size(200, 150).z_index(z1)

        dialog2 = Column(
            Text(f"Dialog 2 (z: {z2})"),
            Button("Bring to Front").on_click(
                lambda _: self._bring_to_front(2)
            ),
        ).fixed_size(180, 130).z_index(z2)

        dialog3 = Column(
            Text(f"Dialog 3 (z: {z3})"),
            Button("Bring to Front").on_click(
                lambda _: self._bring_to_front(3)
            ),
        ).fixed_size(160, 110).z_index(z3)

        return Box(dialog1, dialog2, dialog3)


App(
    Frame("Stacked Dialogs", width=400, height=300),
    StackedDialogs(),
).run()
```

## Best Practices

1. **Use consistent z-index values**: Keep a simple layering system
   - `1` for normal content
   - `10` for modals and popups
   - `100` for critical overlays (rare)

2. **Always use Box for overlapping widgets**: Box properly handles z-index stacking and ensures correct redraw behavior

3. **Keep z-index values simple**: Avoid complex z-index hierarchies. Most apps only need 2-3 layers.

4. **Consider event blocking**: Higher z-index widgets will intercept clicks. Ensure your modal/popup can be dismissed.
