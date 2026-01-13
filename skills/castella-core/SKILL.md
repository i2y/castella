---
name: castella-core
description: Build desktop, web, or terminal UIs with Castella. Create widgets, components, layouts, manage reactive state, handle events, and use the theme system.
---

# Castella Core UI Development

Castella is a pure Python cross-platform UI framework for desktop (GLFW/SDL2), web (PyScript/Pyodide), and terminal (prompt-toolkit) applications. Write once, run everywhere with GPU-accelerated rendering via Skia.

**When to use**: "create a Castella app", "build a Castella UI", "Castella component", "add a button/input/text", "use reactive state", "layout with Row/Column", "change the theme", "handle click events", "preserve scroll position", "animate a widget"

## Quick Start

Create a minimal Castella app:

```python
from castella import App, Text
from castella.frame import Frame

App(Frame("Hello", 800, 600), Text("Hello, Castella!")).run()
```

Install and run:

```bash
uv sync --extra glfw   # Desktop with GLFW
uv run python app.py
```

## Core Concepts

### App and Frame

- `Frame(title, width, height)` - Window/container for the UI
- `App(frame, widget)` - Application entry point with `.run()`
- Frame auto-selects platform: GLFW (desktop), Web, or Terminal

```python
from castella import App
from castella.frame import Frame

frame = Frame("My App", 800, 600)
app = App(frame, my_widget)
app.run()
```

### Widgets

Base building blocks for UI elements:

| Widget | Description | Key Methods |
|--------|-------------|-------------|
| `Text(content)` | Display text | `.font_size(n)` |
| `Button(label)` | Clickable button | `.on_click(handler)` |
| `Input(initial)` | Single-line input | `.on_change(handler)` |
| `MultilineInput(state)` | Multi-line editor | `.on_change(handler)` |
| `CheckBox(state)` | Toggle checkbox | `.on_change(handler)` |
| `Slider(state)` | Range slider | `.on_change(handler)` |
| `Image(path)` | Local image | - |
| `NetImage(url)` | Remote image | - |
| `Markdown(content)` | Rich markdown | `.on_link_click(handler)` |

### Layout Containers

Arrange widgets hierarchically:

```python
from castella import Column, Row, Box

# Vertical stack
Column(
    Text("Header"),
    Button("Click me"),
    Text("Footer"),
)

# Horizontal stack
Row(
    Button("Left"),
    Button("Right"),
)

# Overlapping (z-index support)
Box(
    main_content,
    modal_overlay.z_index(10),
)
```

## Component Pattern

Build reactive UIs with the `Component` class:

```python
from castella import Component, State, Column, Text, Button

class Counter(Component):
    def __init__(self):
        super().__init__()
        self._count = State(0)
        self._count.attach(self)  # Trigger view() on change

    def view(self):
        return Column(
            Text(f"Count: {self._count()}"),
            Button("+1").on_click(lambda _: self._count.set(self._count() + 1)),
        )
```

### State Management

`State[T]` is an observable value that triggers UI rebuilds:

```python
from castella import State

count = State(0)           # Create with initial value
value = count()            # Read current value
count.set(42)              # Set new value
count += 1                 # Operator support: +=, -=, *=, /=
```

### ListState for Collections

`ListState` is an observable list:

```python
from castella import ListState

items = ListState(["a", "b", "c"])
items.append("d")          # Triggers rebuild
items.set(["x", "y"])      # Atomic replace (single rebuild)
```

### Multiple States Pattern

When using multiple states, attach each to the component:

```python
class MultiStateComponent(Component):
    def __init__(self):
        super().__init__()
        self._tab = State("home")
        self._counter = State(0)
        # Attach each state
        self._tab.attach(self)
        self._counter.attach(self)

    def view(self):
        return Column(
            Text(f"Tab: {self._tab()}"),
            Text(f"Count: {self._counter()}"),
        )
```

## Size Policies

Control how widgets size themselves:

| Policy | Behavior |
|--------|----------|
| `SizePolicy.FIXED` | Exact size specified |
| `SizePolicy.EXPANDING` | Fill available space |
| `SizePolicy.CONTENT` | Size to fit content |

### Fluent API Shortcuts

```python
from castella import SizePolicy

# Fixed sizing
widget.fixed_width(100)
widget.fixed_height(40)
widget.fixed_size(200, 100)

# Content sizing
widget.fit_content()          # Both dimensions
widget.fit_content_width()    # Width only
widget.fit_content_height()   # Height only

# Fill parent
widget.fit_parent()
```

### Important Constraint

A Layout with `CONTENT` height_policy cannot have `EXPANDING` height children:

```python
# This will raise RuntimeError:
Column(
    Text("Hello"),  # Text defaults to EXPANDING height
).height_policy(SizePolicy.CONTENT)

# Fix by setting children to FIXED or CONTENT:
Column(
    Text("Hello").fixed_height(24),
).height_policy(SizePolicy.CONTENT)
```

## Styling

### Widget Styling Methods

Chain style methods on widgets:

```python
Text("Hello")
    .bg_color("#1a1b26")
    .text_color("#c0caf5")
    .fixed_height(40)
    .padding(10)
```

### Border Styling

```python
# Show border with theme's default color (or custom color)
widget.show_border()              # Use theme's border color
widget.show_border("#ff0000")     # Use custom color

# Hide border (make it match background)
widget.erase_border()
```

### Theme System

Access and toggle themes:

```python
from castella.theme import ThemeManager

manager = ThemeManager()
theme = manager.current           # Get current theme
manager.toggle_dark_mode()        # Toggle dark/light
manager.prefer_dark(True)         # Force dark mode
```

Built-in themes: Tokyo Night (default), Cupertino, Material Design 3

See `references/theme.md` for custom themes.

## Event Handling

### Click Events

```python
Button("Click me").on_click(lambda event: print("Clicked!"))
```

### Input Changes

```python
Input("initial").on_change(lambda text: print(f"New value: {text}"))
```

### Important: Input Widget Pattern

Do NOT attach states that Input/MultilineInput manages:

```python
class FormComponent(Component):
    def __init__(self):
        super().__init__()
        self._text = State("initial")
        # DON'T attach - causes focus loss on every keystroke
        # self._text.attach(self)

    def view(self):
        return Input(self._text()).on_change(lambda t: self._text.set(t))
```

## Animation

### AnimatedState

Values that animate smoothly on change:

```python
from castella import AnimatedState

class AnimatedCounter(Component):
    def __init__(self):
        super().__init__()
        self._value = AnimatedState(0, duration_ms=300)
        self._value.attach(self)

    def view(self):
        return Column(
            Text(f"Value: {self._value():.1f}"),
            Button("+10").on_click(lambda _: self._value.set(self._value() + 10)),
        )
```

### Widget Animation Methods

```python
# Animate to position/size
widget.animate_to(x=200, y=100, duration_ms=400)

# Slide animations
widget.slide_in("left", distance=100, duration_ms=300)
widget.slide_out("right", distance=100, duration_ms=300)
```

See `references/animation.md` for more animation patterns.

## Scrollable Containers

Make layouts scrollable:

```python
from castella import Column, ScrollState, SizePolicy

class ScrollableList(Component):
    def __init__(self, items):
        super().__init__()
        self._items = ListState(items)
        self._items.attach(self)
        self._scroll = ScrollState()  # Preserves scroll position

    def view(self):
        return Column(
            *[Text(item).fixed_height(30) for item in self._items],
            scrollable=True,
            scroll_state=self._scroll,
        ).fixed_height(300)
```

## Z-Index Stacking

Layer widgets with z-index:

```python
from castella import Box

Box(
    main_content.z_index(1),
    modal_dialog.z_index(10),  # Appears on top
)
```

## Semantic IDs for MCP

Assign semantic IDs for MCP accessibility:

```python
Button("Submit").semantic_id("submit-btn")
Input("").semantic_id("email-input")
```

## Best Practices

1. **Attach states**: Use `state.attach(self)` for each observable state
2. **Fixed heights in scrollable containers**: Use `.fixed_height()` for list items
3. **Preserve scroll**: Use `ScrollState` to maintain scroll position
4. **Atomic list updates**: Use `ListState.set(items)` for single rebuild
5. **Don't attach Input states**: Avoid attaching states managed by Input widgets
6. **Semantic IDs**: Add `.semantic_id()` for MCP integration

## Running Scripts

```bash
# Counter example
uv run python scripts/counter.py

# Hot reload during development
uv run python tools/hot_restarter.py scripts/counter.py
```

## Packaging

Package your Castella app for distribution:

```bash
# Install ux bundler
uv tool install ux-py

# Create executable
ux bundle --project . --output ./dist/
```

See `castella-packaging` skill for detailed options (macOS app bundles, code signing, cross-compilation).

## Reference

- `references/widgets.md` - Complete widget API
- `references/theme.md` - Theme system details
- `references/animation.md` - Animation patterns
- `references/state.md` - State management patterns
- `scripts/` - Executable examples (counter.py, form.py, scrollable_list.py)
