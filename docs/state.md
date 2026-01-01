# State Management

Castella uses reactive state management. When state changes, the UI automatically updates.

## State[T]

`State[T]` wraps a value and notifies observers when it changes.

### Basic Usage

```python
from castella import State

# Create state
count = State(0)

# Get current value (two ways)
print(count())      # Using __call__
print(count.value())  # Using value() method

# Set new value
count.set(5)
```

### Operator Support

State supports augmented assignment operators that automatically trigger UI updates:

```python
count = State(0)
count += 1  # Adds and notifies observers
count -= 1  # Subtracts and notifies observers
count *= 2  # Multiplies and notifies observers
count /= 2  # Divides and notifies observers
```

### Binding State to Components

Use `model()` to bind a single state to a component. When the state changes, `view()` is automatically called:

```python
from castella import App, Button, Column, Component, State, Text
from castella.frame import Frame


class Counter(Component):
    def __init__(self):
        super().__init__()
        self._count = State(0)
        self.model(self._count)  # Bind state to component

    def view(self):
        return Column(
            Text(f"Count: {self._count()}"),
            Button("+1").on_click(lambda _: self._count.set(self._count() + 1)),
            Button("-1").on_click(lambda _: self._count.set(self._count() - 1)),
        )


App(Frame("Counter", 300, 200), Counter()).run()
```

### Multiple States

When a component has multiple states that should trigger `view()` rebuild, use `attach()` instead of `model()`:

```python
class MultiStateComponent(Component):
    def __init__(self):
        super().__init__()
        self._tab = State("tab1")
        self._counter = State(0)
        # Use attach() for multiple states
        self._tab.attach(self)
        self._counter.attach(self)

    def view(self):
        # Both states trigger view() when changed
        return Column(
            Text(f"Tab: {self._tab()}"),
            Text(f"Count: {self._counter()}"),
        )
```

!!! warning "model() only keeps one state"
    Calling `model()` multiple times replaces the previous state. Use `attach()` when you need multiple states to trigger rebuilds.

### on_update Callback

You can register a callback that runs whenever a state changes:

```python
my_state = State(0)
my_state.on_update(lambda ev: print(f"State changed to: {my_state()}"))

my_state.set(5)  # Prints: "State changed to: 5"
```

## ListState

`ListState` is a reactive list. All mutations automatically notify observers and trigger UI updates.

### Basic Usage

```python
from castella import ListState

items = ListState(["a", "b", "c"])
print(items[0])  # "a"
print(len(items))  # 3
```

### Reactive Mutations

All standard list operations notify observers:

```python
items = ListState([1, 2, 3])

# Adding items
items.append(4)        # Notifies observers
items.extend([5, 6])   # Notifies observers
items.insert(0, 0)     # Notifies observers

# Removing items
items.pop()            # Notifies observers
items.remove(0)        # Notifies observers
items.clear()          # Notifies observers

# Modifying items
items[0] = 100         # Notifies observers
del items[0]           # Notifies observers

# Sorting
items.sort()           # Notifies observers
items.reverse()        # Notifies observers
```

### Example: Dynamic List

```python
from castella import App, Button, Column, Component, ListState, Row, Text
from castella.frame import Frame


class TodoList(Component):
    def __init__(self):
        super().__init__()
        self._items = ListState(["Task 1", "Task 2"])
        self.model(self._items)

    def view(self):
        item_widgets = [Text(item) for item in self._items]
        return Column(
            *item_widgets,
            Row(
                Button("Add").on_click(
                    lambda _: self._items.append(f"Task {len(self._items) + 1}")
                ),
                Button("Remove Last").on_click(
                    lambda _: self._items.pop() if self._items else None
                ),
            ).fixed_height(40),
        )


App(Frame("Todo", 300, 300), TodoList()).run()
```

## ScrollState

`ScrollState` preserves scroll position across view rebuilds. When a component's `view()` method is called, normally the scroll position would reset. `ScrollState` solves this by storing the position outside the widget tree.

### Basic Usage

```python
from castella import ScrollState, Column, Component, ListState, Text

class MessageList(Component):
    def __init__(self):
        super().__init__()
        self._messages = ListState(["Message 1", "Message 2", "Message 3"])
        self._messages.attach(self)
        self._scroll = ScrollState()  # Survives view rebuilds

    def view(self):
        return Column(
            *[Text(msg).fixed_height(30) for msg in self._messages],
            scrollable=True,
            scroll_state=self._scroll,  # Scroll position preserved!
        )
```

### When to Use ScrollState

- **Dynamic lists**: Lists that update frequently (chat messages, feeds)
- **Form views**: Long forms where users scroll while filling fields
- **Any scrollable container**: When scroll position should persist across state changes

### API

```python
scroll = ScrollState()        # Create with position (0, 0)
scroll = ScrollState(x=0, y=100)  # Create with specific position

# Get current position
x = scroll.x
y = scroll.y

# Set position
scroll.set(x=0, y=200)
scroll.set(y=50)  # Only change y
```

## Best Practices

1. **Use `model()` for single state**: Simple components with one state source.

2. **Use `attach()` for multiple states**: When multiple states should trigger rebuilds.

3. **Avoid attaching Input's state**: Don't attach states managed by Input widget - it causes focus loss on every keystroke:

    ```python
    # DON'T do this - causes focus issues
    self._text = State("")
    self._text.attach(self)  # Bad!

    # DO this instead - let Input manage internally
    def view(self):
        return Input(self._text()).on_change(lambda t: self._text.set(t))
    ```

4. **Use operators for numeric states**: `count += 1` is cleaner than `count.set(count() + 1)`.

5. **Use `set()` for atomic list updates**: When shuffling or replacing all items, use `set()` instead of `clear()` + multiple `append()`:

    ```python
    # DON'T do this - triggers multiple rebuilds
    items.clear()
    for item in new_items:
        items.append(item)

    # DO this instead - single rebuild
    items.set(new_items)
    ```

## Widget Lifecycle Hooks

Widgets can override `on_mount()` and `on_unmount()` to perform setup and cleanup when added to or removed from the widget tree.

### on_mount / on_unmount

```python
from castella import Widget

class TimerWidget(Widget):
    def on_mount(self):
        """Called when widget is added to the tree."""
        self._timer = start_timer(self._tick)

    def on_unmount(self):
        """Called when widget is removed from the tree."""
        self._timer.stop()

    def is_mounted(self) -> bool:
        """Check if currently in the tree."""
        return self._mounted
```

### Use Cases

- **Starting/stopping timers**: Begin background tasks when mounted, stop when unmounted
- **Subscribing to events**: Subscribe on mount, unsubscribe on unmount
- **Resource management**: Acquire resources on mount, release on unmount

## State Preservation with Caching

When a `Component.view()` is called, widgets are normally recreated. This can cause loss of internal state like timer counts, scroll positions, or animation progress. Castella provides caching APIs to preserve widget state across rebuilds.

### ListState.map_cached()

Use `map_cached()` to create widgets from list items while preserving their state:

```python
from castella import Column, Component, ListState

class TodoList(Component):
    def __init__(self):
        super().__init__()
        self._items = ListState([...])
        self._items.attach(self)

    def view(self):
        # Widgets are cached by item.id - state is preserved!
        timer_widgets = self._items.map_cached(
            lambda item: TimerWidget(item.id, item.name)
        )
        return Column(*timer_widgets)
```

**Key features:**

- Widgets are cached by `item.id` (or hash, or `id()`)
- Reused widgets keep their internal state (timers, counts, etc.)
- Removed items automatically trigger `on_unmount()`
- New items create new widgets with `on_mount()` called

**Custom key function:**

```python
# Use a custom key extraction function
widgets = self._items.map_cached(
    factory=lambda item: MyWidget(item),
    key_fn=lambda item: item.uuid,  # Use custom key
)
```

### Component.cache()

Alternative API that identifies caches by source code location:

```python
class MyComponent(Component):
    def view(self):
        # Cache identified by file + line number
        widgets = self.cache(
            self._items,
            lambda item: TimerWidget(item.id, item.name),
        )
        return Column(*widgets)
```

**When to use which:**

- `ListState.map_cached()`: Simpler API, cache lives on the ListState
- `Component.cache()`: Allows multiple caches in same view(), cache lives on Component

### Example: Shuffle with State Preservation

```python
from dataclasses import dataclass
from castella import App, Button, Column, Component, ListState, Row
from castella.frame import Frame

@dataclass
class Item:
    id: int
    name: str

class ShuffleDemo(Component):
    def __init__(self):
        super().__init__()
        self._items = ListState([Item(1, "A"), Item(2, "B"), Item(3, "C")])
        self._items.attach(self)

    def _shuffle(self, _):
        import random
        items = list(self._items)
        random.shuffle(items)
        self._items.set(items)  # Atomic update

    def view(self):
        widgets = self._items.map_cached(lambda i: TimerWidget(i.id, i.name))
        return Column(
            Button("Shuffle").on_click(self._shuffle),
            *[Row(w) for w in widgets],
        )

App(Frame("Demo", 400, 300), ShuffleDemo()).run()
```

When shuffled, timer widgets maintain their counts because the same widget instances are reused.
