# Castella State Management

Reactive state patterns for building dynamic UIs.

## State[T]

Observable value wrapper that triggers UI rebuilds:

```python
from castella import State

# Create state
count = State(0)
name = State("Alice")
items = State([1, 2, 3])

# Read value
current = count()

# Set value (triggers rebuild)
count.set(42)

# Operator shortcuts
count += 1    # Increment
count -= 1    # Decrement
count *= 2    # Multiply
count /= 2    # Divide
```

## Attaching State to Components

States must be attached to trigger `view()` rebuilds:

```python
from castella import Component, State

class Counter(Component):
    def __init__(self):
        super().__init__()
        self._count = State(0)
        self._count.attach(self)  # Required!

    def view(self):
        return Text(f"Count: {self._count()}")
```

### Multiple States

Attach each state individually:

```python
class MultiStateComponent(Component):
    def __init__(self):
        super().__init__()
        self._name = State("Alice")
        self._age = State(30)
        # Attach each one
        self._name.attach(self)
        self._age.attach(self)
```

### Alternative: model() for Single State

For single-state components:

```python
class Counter(Component):
    def __init__(self):
        super().__init__()
        self._count = State(0)
        self.model(self._count)  # Shortcut for single state
```

## ListState

Observable list for collections:

```python
from castella import ListState

items = ListState(["a", "b", "c"])

# Mutations (each triggers rebuild)
items.append("d")
items.insert(0, "first")
items.remove("b")
items.pop()
items.clear()

# Iteration
for item in items:
    print(item)

# Length
print(len(items))

# Indexing
print(items[0])
items[0] = "modified"
```

### Atomic Updates with set()

Use `set()` for batch updates (single rebuild):

```python
# BAD: Multiple rebuilds
items.clear()
for item in new_items:
    items.append(item)

# GOOD: Single rebuild
items.set(new_items)
```

### Cached Widget Mapping

Preserve widget instances across rebuilds:

```python
class TodoList(Component):
    def __init__(self):
        super().__init__()
        self._items = ListState([...])
        self._items.attach(self)

    def view(self):
        # Widgets cached by item.id
        widgets = self._items.map_cached(
            lambda item: TodoItemWidget(item.id, item.text)
        )
        return Column(*widgets)
```

Custom key function:

```python
widgets = self._items.map_cached(
    factory=lambda item: MyWidget(item),
    key_fn=lambda item: item.uuid,
)
```

## Component.cache()

Alternative caching on the component:

```python
class MyComponent(Component):
    def view(self):
        # Cache identified by source location
        widgets = self.cache(
            self._items,
            lambda item: TimerWidget(item.id, item.name),
        )
        return Column(*widgets)
```

**When to use which:**
- `ListState.map_cached()` - Simpler API, cache on ListState
- `Component.cache()` - Multiple caches in same view()

## ScrollState

Preserve scroll position across rebuilds:

```python
from castella import ScrollState, Column, SizePolicy

class ScrollableList(Component):
    def __init__(self):
        super().__init__()
        self._items = ListState([...])
        self._items.attach(self)
        self._scroll = ScrollState()  # NOT attached!

    def view(self):
        return Column(
            *[Text(item).fixed_height(30) for item in self._items],
            scrollable=True,
            scroll_state=self._scroll,  # Position preserved
        ).fixed_height(300)
```

### ScrollState Properties

```python
scroll = ScrollState()

scroll.x      # Horizontal scroll position
scroll.y      # Vertical scroll position
scroll.x = 0  # Reset horizontal scroll
scroll.y = 0  # Reset vertical scroll
```

## Input Widget State Pattern

Important: Do NOT attach states managed by Input widgets:

```python
class FormComponent(Component):
    def __init__(self):
        super().__init__()
        self._text = State("initial")
        # DON'T attach - causes focus loss!
        # self._text.attach(self)

    def view(self):
        return Input(self._text()).on_change(
            lambda t: self._text.set(t)
        )
```

Same for MultilineInput:

```python
self._editor = MultilineInputState("content")
# DON'T attach
# self._editor.attach(self)
```

## SliderState

State for Slider widget:

```python
from castella import SliderState

state = SliderState(value=50, min_val=0, max_val=100)

print(state.value())   # 50
print(state.ratio())   # 0.5 (normalized 0-1)
state.set(75)
```

## ProgressBarState

State for ProgressBar widget:

```python
from castella import ProgressBarState

state = ProgressBarState(value=0, min_val=0, max_val=100)
state.set(50)  # Update progress
```

## TabsState

State for Tabs widget:

```python
from castella import TabsState, TabItem

state = TabsState([
    TabItem(id="home", label="Home", content=home_widget),
    TabItem(id="settings", label="Settings", content=settings_widget),
], selected_id="home")

state.select("settings")  # Programmatic selection
```

## ModalState

State for Modal widget:

```python
from castella import ModalState

state = ModalState()
state.open()   # Show modal
state.close()  # Hide modal
```

## TreeState

State for Tree widget:

```python
from castella import TreeState, TreeNode

state = TreeState(nodes, multi_select=False)
state.select("node-id")       # Select node
state.expand_to("node-id")    # Expand to reveal node
```

## State Observation Pattern

States implement observer pattern:

```python
from castella.core import State

count = State(0)

# Add observer
def on_change(new_value):
    print(f"Value changed to: {new_value}")

count.add_observer(on_change)

# Remove observer
count.remove_observer(on_change)
```

## Lazy State Attachment

For components created before App exists:

```python
class MyComponent(Component):
    def __init__(self):
        super().__init__()
        self._state = State(0)
        self._attached = False
        # DON'T attach here

    def view(self):
        # Attach lazily when view() called
        if not self._attached:
            self._state.attach(self)
            self._attached = True
        return Text(str(self._state()))
```
