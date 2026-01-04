# Castella Widget Reference

Complete API reference for all Castella widgets.

## Text Widgets

### Text
Display single-line text.

```python
from castella import Text

text = Text("Hello, World!")
text = Text("Styled").font_size(18).text_color("#ffffff")
```

**Methods:**
- `.font_size(size: int)` - Set font size in pixels
- `.text_color(color: str)` - Set text color (hex or named)
- `.bg_color(color: str)` - Set background color

### SimpleText
Lightweight text for performance-critical lists.

```python
from castella import SimpleText

text = SimpleText("Fast text", font_size=14)
```

### MultilineText
Read-only multi-line text with selection support.

```python
from castella.multiline_text import MultilineText

text = MultilineText("Line 1\nLine 2\nLine 3", font_size=14, wrap=True)
```

**Features:**
- Mouse drag to select text
- Cmd+C/Ctrl+C to copy
- Cmd+A/Ctrl+A to select all

## Input Widgets

### Input
Single-line text input with cursor positioning.

```python
from castella import Input
from castella.core import State

text = State("")
input_widget = Input(text()).on_change(lambda t: text.set(t))
```

**Methods:**
- `.on_change(handler: Callable[[str], None])` - Text change callback
- `.placeholder(text: str)` - Placeholder text

### MultilineInput
Multi-line text editor with scrolling.

```python
from castella.multiline_input import MultilineInput, MultilineInputState

state = MultilineInputState("Initial text")
editor = MultilineInput(state, font_size=14, wrap=True)
editor = editor.height(200).height_policy(SizePolicy.FIXED)
```

**Features:**
- Scrollbar for overflow content
- Mouse wheel scrolling
- Click to position cursor
- Text selection with mouse drag
- Copy/Cut/Paste (Cmd/Ctrl+C/X/V)
- Select all (Cmd/Ctrl+A)

## Button Widgets

### Button
Clickable button with semantic kinds.

```python
from castella import Button, Kind

button = Button("Click me").on_click(lambda e: print("Clicked"))
button = Button("Danger", kind=Kind.DANGER)
```

**Kinds:**
- `Kind.NORMAL` - Default styling
- `Kind.INFO` - Blue/cyan
- `Kind.SUCCESS` - Green
- `Kind.WARNING` - Yellow/orange
- `Kind.DANGER` - Red

### CheckBox
Toggle checkbox with optional labels.

```python
from castella import CheckBox
from castella.core import State

checked = State(False)
checkbox = CheckBox(checked).on_change(lambda v: print(f"Checked: {v}"))
checkbox = CheckBox(checked, on_label="ON", off_label="OFF")
checkbox = CheckBox(checked, is_circle=True)  # Circle style
```

### Switch
Toggle switch (same API as CheckBox).

```python
from castella import Switch
from castella.core import State

enabled = State(True)
switch = Switch(enabled).on_change(lambda v: print(f"Enabled: {v}"))
```

### RadioButtons
Single-select from options.

```python
from castella import RadioButtons
from castella.core import State

selected = State("option1")
radios = RadioButtons(
    ["option1", "option2", "option3"],
    selected,
).on_change(lambda v: print(f"Selected: {v}"))
```

## Slider Widget

### Slider
Range slider with state.

```python
from castella import Slider, SliderState

state = SliderState(value=50, min_val=0, max_val=100)
slider = Slider(state).on_change(lambda v: print(f"Value: {v}"))

# Access value
print(state.value())   # 50
print(state.ratio())   # 0.5 (normalized 0-1)
state.set(75)
```

## Progress Widget

### ProgressBar
Progress indicator.

```python
from castella import ProgressBar, ProgressBarState

state = ProgressBarState(value=0, min_val=0, max_val=100)
progress = ProgressBar(state)
progress = progress.track_color("#1a1b26").fill_color("#9ece6a")

state.set(75)  # Update progress
```

## Date/Time Widget

### DateTimeInput
Date and time picker with calendar.

```python
from castella import DateTimeInput, DateTimeInputState
from datetime import date

state = DateTimeInputState(
    value="2024-12-25T14:30:00",
    enable_date=True,
    enable_time=True,
)
picker = DateTimeInput(
    state=state,
    label="Appointment",
    min_date=date.today(),
)

# Get values
print(state.to_display_string())  # "2024-12-25 14:30"
print(state.to_iso())             # "2024-12-25T14:30:00"
```

## Image Widgets

### Image
Display local image.

```python
from castella import Image

img = Image("path/to/image.png")
```

### NetImage
Display remote image.

```python
from castella import NetImage

img = NetImage("https://example.com/image.png")
```

### AsyncNetImage
Async-loading remote image.

```python
from castella import AsyncNetImage

img = AsyncNetImage("https://example.com/image.png")
```

### NumpyImage
Display numpy array as image.

```python
from castella import NumpyImage
import numpy as np

array = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
img = NumpyImage(array)
```

## Layout Containers

### Column
Vertical layout.

```python
from castella import Column

col = Column(
    widget1,
    widget2,
    scrollable=True,      # Enable scrolling
    scroll_state=state,   # Preserve scroll position
)
```

### Row
Horizontal layout.

```python
from castella import Row

row = Row(widget1, widget2, widget3)
```

### Box
Overlapping layout with z-index.

```python
from castella import Box

box = Box(
    background.z_index(1),
    foreground.z_index(10),
)
```

## Navigation Widgets

### Tabs
Tabbed navigation.

```python
from castella import Tabs, TabsState, TabItem

state = TabsState([
    TabItem(id="home", label="Home", content=home_widget),
    TabItem(id="settings", label="Settings", content=settings_widget),
], selected_id="home")

tabs = Tabs(state).on_change(lambda id: print(f"Tab: {id}"))
state.select("settings")  # Programmatic selection
```

### Tree
Hierarchical tree view.

```python
from castella import Tree, TreeState, TreeNode

nodes = [
    TreeNode(id="docs", label="Documents", icon="📁", children=[
        TreeNode(id="readme", label="README.md", icon="📄"),
    ]),
]
state = TreeState(nodes, multi_select=False)
tree = Tree(state).on_select(lambda node: print(node.label))
```

### FileTree
File system tree.

```python
from castella import FileTree, FileTreeState

state = FileTreeState(root_path=".", show_hidden=False, dirs_first=True)
file_tree = FileTree(state).on_file_select(lambda path: print(path))
```

## Overlay Widget

### Modal
Modal dialog overlay.

```python
from castella import Modal, ModalState, Column, Button, Text

modal_state = ModalState()
modal = Modal(
    content=Column(
        Text("Modal Content"),
        Button("Close").on_click(lambda _: modal_state.close()),
    ),
    state=modal_state,
    title="My Modal",
)

modal_state.open()   # Open modal
modal_state.close()  # Close modal
```

## Data Display

### DataTable
High-performance data table.

```python
from castella import DataTable, DataTableState, ColumnConfig

state = DataTableState(
    columns=[
        ColumnConfig(name="Name", width=150, sortable=True),
        ColumnConfig(name="Age", width=80, sortable=True),
    ],
    rows=[["Alice", 30], ["Bob", 25]],
)
table = DataTable(state).on_sort(lambda e: print(e.column, e.direction))
```

### Markdown
Rich markdown rendering.

```python
from castella import Markdown

md = Markdown("""
# Heading
**Bold** and *italic*.

```python
print("Hello")
```
""", base_font_size=14, on_link_click=lambda url: print(url))
```

## Common Widget Methods

All widgets support these methods:

```python
widget
    .width(100)
    .height(50)
    .width_policy(SizePolicy.FIXED)
    .height_policy(SizePolicy.EXPANDING)
    .fixed_width(100)
    .fixed_height(50)
    .fixed_size(100, 50)
    .fit_content()
    .fit_parent()
    .bg_color("#ffffff")
    .z_index(10)
    .semantic_id("my-widget")
    .padding(10)
```
