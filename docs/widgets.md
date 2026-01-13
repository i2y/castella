# Built-in Widgets

Castella provides a variety of built-in widgets for creating user interfaces.

<style type="text/css">
    div.demo {
        margin: 8px;
        border: solid 1px #ccc;
        resize: both;
        overflow: hidden;
        width: 300px;
        height: 300px;
    }
</style>

## Common Widget Methods

All widgets support these common methods for customization:

### Sizing

```python
widget.fixed_size(width, height)  # Fixed dimensions
widget.fixed_width(width)         # Fixed width only
widget.fixed_height(height)       # Fixed height only
widget.flex(n)                    # Flex ratio in layouts
widget.fit_content()              # Size to content
widget.fit_parent()               # Fill parent
```

### Styling

```python
widget.bg_color("#ff0000")        # Background color
widget.text_color("#ffffff")      # Text color
widget.border_color("#000000")    # Border color
widget.show_border()              # Show border with theme's default color
widget.erase_border()             # Hide border
```

### Layering

```python
widget.z_index(n)                 # Stacking order (default: 1)
```

See [Z-Index and Layering](z-index.md) for details.

## Button

Interactive button widget with click handling.

```python
App(
    Frame("Button"),
    Row(
        Column(
            Button("First"),
            Button("Second", align=TextAlign.CENTER),
            Button("Third", align=TextAlign.RIGHT),
            Button("Fourth", align=TextAlign.LEFT),
        ).spacing(10)
    ).spacing(10),
).run()
```

<div class="demo">
    <iframe width="100%" height="100%" src="../examples/button.html"></iframe>
</div>

### Click Handling

```python
Button("Click me").on_click(lambda event: print("Clicked!"))
```

## Text

Display text with various styles and alignments.

```python
App(
    Frame("Text"),
    Row(
        Column(
            Text("First", kind=Kind.NORMAL),
            Text("Second", kind=Kind.INFO, align=TextAlign.CENTER),
            Text("Third", kind=Kind.SUCCESS, align=TextAlign.RIGHT),
            Text("Fourth", kind=Kind.WARNING, align=TextAlign.LEFT),
            Text("Fifth", kind=Kind.DANGER, align=TextAlign.LEFT),
        ).spacing(10)
    ).spacing(10),
).run()

```


<div class="demo">
    <iframe width="100%" height="100%" src="../examples/text.html"></iframe>
</div>

### Font Size

```python
Text("Large text", font_size=24)
Text("Small text", font_size=12)
```

## MultilineText

Display multi-line text content with text selection support.

```python
MultilineText(
    "Line 1\nLine 2\nLine 3",
    font_size=16,
    wrap=True  # Enable text wrapping
)
```

### Features

- Line wrapping with `wrap=True`
- Mouse drag to select text
- Cmd+C / Ctrl+C to copy selected text
- Cmd+A / Ctrl+A to select all

## Input

Text input field for user input.

```python
from castella import Input, State

text = State("")

Input(text()).on_change(lambda t: text.set(t))
```

!!! warning "Input and State"
    Don't attach Input's state to the component - it causes focus loss on every keystroke. See [State Management](state.md) for details.

## MultilineInput

Multi-line text editor with scrolling support.

```python
from castella import MultilineInput, MultilineInputState

# Basic usage
editor = MultilineInput("Initial text", font_size=14)

# With state for reactive updates
state = MultilineInputState("Hello\nWorld")
editor = MultilineInput(state, font_size=14, wrap=True)

# With change callback
editor = MultilineInput("", font_size=14).on_change(lambda text: print(text))

# With fixed height (enables vertical scrolling)
editor = MultilineInput(state, font_size=14, wrap=True).fixed_height(200)
```

### Features

- Line wrapping with `wrap=True`
- Vertical scrolling when content exceeds height
- Mouse wheel scrolling
- Click to position cursor
- Scrollbar thumb dragging
- Auto-scroll to keep cursor visible
- Mouse drag to select text
- Cmd+C / Ctrl+C to copy selected text
- Cmd+X / Ctrl+X to cut selected text
- Cmd+V / Ctrl+V to paste from clipboard
- Cmd+A / Ctrl+A to select all

!!! warning "MultilineInput and State"
    Don't attach MultilineInput's state to the component - it causes focus loss on every keystroke. See [State Management](state.md) for details.

## Markdown

Rich markdown text rendering with syntax highlighting.

````python
from castella import Markdown

md = Markdown("""
# Heading

**Bold** and *italic* text.

```python
def hello():
    print("Hello!")
```
""", base_font_size=14)

# With link click handler
import webbrowser
md = Markdown(content, on_link_click=lambda url: webbrowser.open(url))
````

### Supported Features

- Headings (H1-H6)
- Text formatting: bold, italic, strikethrough
- Ordered and unordered lists
- Code blocks with syntax highlighting
- Inline code
- Tables
- Blockquotes
- Links with click handling
- LaTeX math expressions (`$E=mc^2$`)
- Horizontal rules

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `content` | str | required | Markdown content |
| `base_font_size` | int | 14 | Base font size |
| `code_theme` | str | "monokai" | Pygments theme for code |
| `enable_math` | bool | True | Enable LaTeX math |
| `on_link_click` | callable | None | Link click callback |

## Switch

Toggle switch for boolean values.

```python
App(
    Frame("Switch"),
    Switch(True),
).run()
```

<div class="demo" style="width: 100px; height: 50px">
    <iframe width="100%" height="100%" src="../examples/switch.html"></iframe>
</div>

### State Binding

```python
enabled = State(False)

Switch(enabled()).on_change(lambda v: enabled.set(v))
```

## CheckBox

Checkbox for boolean selections.

```python
from castella import CheckBox, State

checked = State(False)

CheckBox("Enable feature", checked()).on_change(lambda v: checked.set(v))
```

## RadioButtons

Radio button group for single selection from multiple options.

```python
from castella import RadioButtons, State

selected = State(0)

RadioButtons(
    ["Option A", "Option B", "Option C"],
    selected()
).on_change(lambda i: selected.set(i))
```

## Slider

Range input widget for numeric values.

```python
from castella import Slider, SliderState

# Basic usage
slider = Slider(value=50, min_val=0, max_val=100)
slider.on_change(lambda v: print(f"Value: {v}"))

# With state for reactive updates
state = SliderState(value=25, min_val=0, max_val=100)
slider = Slider(state)

# Access value
print(state.value())   # 25
print(state.ratio())   # 0.25 (normalized 0-1)
state.set(75)          # Set new value
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `value` or `state` | int/float or SliderState | required | Initial value or state |
| `min_val` | int/float | 0 | Minimum value |
| `max_val` | int/float | 100 | Maximum value |
| `kind` | Kind | NORMAL | Visual style |

## ProgressBar

Animated progress indicator for displaying progress values.

```python
from castella import ProgressBar, ProgressBarState

# Basic usage
progress = ProgressBar(value=50, min_val=0, max_val=100)

# With state for dynamic updates
state = ProgressBarState(value=0, min_val=0, max_val=100)
progress = ProgressBar(state)

# Custom colors
progress = (
    ProgressBar(state)
    .track_color("#1a1b26")
    .fill_color("#9ece6a")
    .border_radius(4)
    .fixed_height(24)
)

# Update progress
state.set(75)
```

### Animation Example

```python
from castella.animation import ValueTween, AnimationScheduler, EasingFunction

def animate_progress(state):
    state.set(0)
    AnimationScheduler.get().add(
        ValueTween(
            from_value=0,
            to_value=100,
            duration_ms=1000,
            easing=EasingFunction.EASE_OUT_CUBIC,
            on_update=lambda v: state.set(v),
        )
    )
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `value` or `state` | float or ProgressBarState | required | Initial value or state |
| `min_val` | float | 0 | Minimum value |
| `max_val` | float | 100 | Maximum value |
| `show_text` | bool | False | Show percentage text |

### Customization Methods

| Method | Description |
|--------|-------------|
| `.track_color(color)` | Set background track color |
| `.fill_color(color)` | Set fill (progress) color |
| `.border_radius(radius)` | Set corner radius |
| `.show_text(bool)` | Show/hide percentage text |

## Tabs

Tabbed navigation widget for organizing content.

```python
from castella import Tabs, TabsState, TabItem, Text

# Create tabs with TabsState
tabs_state = TabsState([
    TabItem(id="home", label="Home", content=Text("Home content")),
    TabItem(id="settings", label="Settings", content=Text("Settings content")),
], selected_id="home")

tabs = Tabs(tabs_state).on_change(lambda id: print(f"Tab: {id}"))

# Or use fluent API
tabs = (
    Tabs()
    .add_tab("home", "Home", Text("Home content"))
    .add_tab("settings", "Settings", Text("Settings content"))
)

# Programmatic selection
tabs_state.select("settings")
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `state` | TabsState | None | Tabs state with items |
| `tab_height` | int | 40 | Height of tab bar |

### TabItem Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | str | Unique tab identifier |
| `label` | str | Tab button label |
| `content` | Widget | Content widget |

## Tree

Hierarchical tree widget for displaying nested data structures.

```python
from castella import Tree, TreeState, TreeNode

# Create tree data
nodes = [
    TreeNode(id="docs", label="Documents", icon="📁", children=[
        TreeNode(id="readme", label="README.md", icon="📄"),
        TreeNode(id="license", label="LICENSE", icon="📄"),
    ]),
    TreeNode(id="src", label="Source", icon="📁", children=[
        TreeNode(id="main", label="main.py", icon="🐍"),
    ]),
]

# Create tree widget
state = TreeState(nodes, multi_select=False)
tree = Tree(state).on_select(lambda node: print(f"Selected: {node.label}"))

# Programmatic control
tree.expand_all()
tree.collapse_all()
state.expand_to("main")  # Expand ancestors to reveal node
state.select("main")
```

### TreeNode Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | str | Unique node identifier |
| `label` | str | Display text |
| `children` | list[TreeNode] | Child nodes |
| `icon` | str \| None | Custom icon (emoji) |
| `data` | Any | Optional user data |

### TreeState Methods

| Method | Description |
|--------|-------------|
| `expand(node_id)` | Expand a node |
| `collapse(node_id)` | Collapse a node |
| `toggle_expanded(node_id)` | Toggle expand/collapse |
| `expand_all()` | Expand all nodes |
| `collapse_all()` | Collapse all nodes |
| `expand_to(node_id)` | Expand ancestors to reveal node |
| `select(node_id)` | Select a node |
| `deselect(node_id)` | Deselect a node |
| `clear_selection()` | Clear all selections |
| `get_selected()` | Get selected nodes |
| `set_multi_select(bool)` | Enable/disable multi-select |

### Tree Callbacks

| Method | Description |
|--------|-------------|
| `on_select(callback)` | Called when node is selected |
| `on_expand(callback)` | Called when node is expanded |
| `on_collapse(callback)` | Called when node is collapsed |

## FileTree

File system browser widget built on Tree.

```python
from castella import FileTree, FileTreeState
from pathlib import Path

# Create file tree from directory
state = FileTreeState(
    root_path=".",
    show_hidden=False,
    dirs_first=True
)

file_tree = (
    FileTree(state)
    .on_file_select(lambda path: print(f"File: {path}"))
    .on_dir_select(lambda path: print(f"Dir: {path}"))
)

# Toggle hidden files
state.set_show_hidden(True)

# Refresh from file system
state.refresh()

# Get selected paths
paths = file_tree.get_selected_paths()
```

### FileTreeState Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `root_path` | str \| Path | None | Root directory |
| `show_hidden` | bool | False | Show hidden files |
| `dirs_first` | bool | True | Sort directories before files |
| `multi_select` | bool | False | Allow multiple selection |

### FileTree Callbacks

| Method | Description |
|--------|-------------|
| `on_file_select(callback)` | Called with Path when file selected |
| `on_dir_select(callback)` | Called with Path when directory selected |

### Automatic File Icons

FileTree automatically assigns icons based on file extension:

- Programming: `.py` 🐍, `.js` 📜, `.rs` 🦀, `.go` 🐹
- Documents: `.md` 📝, `.pdf` 📕, `.txt` 📄
- Images: `.png` 🖼️, `.jpg` 🖼️, `.svg` 🖼️
- Config: `.json` 📋, `.yaml` 📋, `.env` 🔐
- Special files: `Dockerfile` 🐳, `README` 📖, `LICENSE` ⚖️

## Modal

Modal dialog overlay for focused interactions.

```python
from castella import Modal, ModalState, Column, Button, Text

# Create modal state
modal_state = ModalState()

# Create modal with content
modal = Modal(
    content=Column(
        Text("Modal Title", font_size=18),
        Text("This is the modal content."),
        Button("Close").on_click(lambda _: modal_state.close()),
    ),
    state=modal_state,
    title="My Modal",
)

# Include modal in your view (uses z-index for overlay)
def view(self):
    return Box(
        main_content.z_index(1),
        modal,  # Rendered on top when open
    )

# Open/close programmatically
modal_state.open()
modal_state.close()
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `content` | Widget | required | Modal content widget |
| `state` | ModalState | required | Modal state (open/close) |
| `title` | str | None | Optional title bar |
| `width` | int | 400 | Modal width |
| `height` | int | 300 | Modal height |
| `close_on_backdrop_click` | bool | True | Close when clicking backdrop |
| `show_close_button` | bool | True | Show X button in title bar |

### ModalState Methods

| Method | Description |
|--------|-------------|
| `open()` | Open the modal |
| `close()` | Close the modal |
| `is_open` | Property: current state |

## DateTimeInput

Date and/or time picker widget with visual calendar grid and dropdown time selection.

### Features

- Visual calendar grid for date selection (7x6 grid)
- Month/year quick navigation with picker views
- Time picker with hour/minute dropdowns
- "Today" and preset time buttons
- Locale support (English, Japanese)
- Min/max date constraints

```python
from castella import DateTimeInput, DateTimeInputState

# Date only with calendar picker
state = DateTimeInputState(
    value="2024-12-25",
    enable_date=True,
    enable_time=False
)
date_input = DateTimeInput(state=state, label="Birthday")

# Date and time
state = DateTimeInputState(
    value="2024-12-25T14:30:00",
    enable_date=True,
    enable_time=True
)
datetime_input = DateTimeInput(state=state, label="Appointment")

# Time only
state = DateTimeInputState(
    value="14:30:00",
    enable_date=False,
    enable_time=True
)
time_input = DateTimeInput(state=state, label="Start Time")

# With constraints and locale
from datetime import date
from castella.calendar.locale import JA

date_input = DateTimeInput(
    state=state,
    label="予約日",
    min_date=date.today(),
    max_date=date(2025, 12, 31),
    first_day_of_week=0,  # 0=Sunday, 1=Monday (default)
    locale=JA,  # Japanese locale
)
```

### DateTimeInputState Methods

| Method | Description |
|--------|-------------|
| `set(value)` | Set the value (ISO format string) |
| `to_iso()` | Get value as ISO format string |
| `to_display_string()` | Get human-readable string |
| `open_picker()` | Open the picker popup |
| `close_picker()` | Close the picker popup |

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `state` | DateTimeInputState | None | State object |
| `label` | str | None | Field label |
| `value` | str | None | Initial value (ISO format) |
| `enable_date` | bool | True | Show date picker |
| `enable_time` | bool | False | Show time picker |
| `min_date` | date | None | Minimum selectable date |
| `max_date` | date | None | Maximum selectable date |
| `first_day_of_week` | int | 1 | 0=Sunday, 1=Monday |
| `locale` | CalendarLocale | EN | Locale for labels |

### Locale Support

```python
from castella.calendar.locale import EN, JA, CalendarLocale

# Use built-in locales
DateTimeInput(state, locale=EN)  # English (default)
DateTimeInput(state, locale=JA)  # Japanese

# Create custom locale
custom = CalendarLocale(
    weekday_names=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
    month_names=["Jan", "Feb", "Mar", ...],
    today_button="Today",
    done_button="Done",
    now_button="Now",
    time_label="Time:",
    placeholder="Select date",
)
```

## Image

Display images from files.

```python
from castella import Image

Image("path/to/image.png")
```

## NetImage

Display images from URLs with caching and fit mode support.

```python
from castella import NetImage, ImageFit

# Basic usage
img = NetImage("https://example.com/image.png")

# Disable cache
img = NetImage("https://example.com/image.png", use_cache=False)

# With ImageFit modes (aspect ratio preservation)
img = NetImage("https://example.com/image.png", fit=ImageFit.CONTAIN)  # Fit within bounds
img = NetImage("https://example.com/image.png", fit=ImageFit.COVER)    # Cover bounds (may crop)
img = NetImage("https://example.com/image.png", fit=ImageFit.FILL)     # Stretch to fill (default)

# Chain with fit() method
img = NetImage(url).fit(ImageFit.CONTAIN)

# With reactive URL
from castella import State
url = State("https://example.com/image.png")
img = NetImage(url)
```

### ImageFit Modes

| Mode | Description |
|------|-------------|
| `FILL` | Stretch to fill bounds (may distort aspect ratio) - default |
| `CONTAIN` | Scale to fit within bounds, maintaining aspect ratio (letterbox) |
| `COVER` | Scale to cover bounds, maintaining aspect ratio (may crop) |

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `url` | str or State[str] | required | Image URL |
| `use_cache` | bool | True | Cache downloaded images |
| `fit` | ImageFit | FILL | How image fits within bounds |

Uses CONTENT size policy by default (sizes to image dimensions).

## AsyncNetImage

Asynchronously load and display images from URLs. Unlike NetImage, this widget
renders immediately and updates when the image loads.

```python
from castella import AsyncNetImage

# Must specify dimensions (CONTENT size policy not supported)
img = (
    AsyncNetImage("https://example.com/image.png")
    .fixed_size(200, 150)
)

# With reactive URL
from castella import State
url = State("https://example.com/image.png")
img = AsyncNetImage(url).fixed_size(200, 150)
```

!!! warning "Size Policy Restriction"
    AsyncNetImage does not support `SizePolicy.CONTENT`. You must use
    `fixed_size()`, `fixed_width()`, or `fixed_height()` to set dimensions.

## Spacer

Flexible space widget for layouts.

```python
Column(
    Text("Top"),
    Spacer(),      # Takes remaining space
    Text("Bottom"),
)
```

## DataTable

High-performance data table with sorting, filtering, row selection, and column resize.

```python
from castella import (
    DataTable, DataTableState, ColumnConfig,
    SortDirection, SelectionMode,
)

# Create table state with column configs
state = DataTableState(
    columns=[
        ColumnConfig(name="Name", width=150, sortable=True),
        ColumnConfig(name="Age", width=80, sortable=True),
        ColumnConfig(name="City", width=120, sortable=True),
    ],
    rows=[
        ["Alice", 30, "Tokyo"],
        ["Bob", 25, "Osaka"],
        ["Charlie", 35, "Kyoto"],
    ],
    selection_mode=SelectionMode.MULTI,  # NONE, SINGLE, or MULTI
)

# Create table with event handlers
table = (
    DataTable(state)
    .on_sort(lambda ev: print(f"Sorted column {ev.column}"))
    .on_selection_change(lambda ev: print(f"Selected: {ev.selected_rows}"))
    .on_cell_click(lambda ev: print(f"Clicked: {ev.value}"))
)
```

### From Pydantic Models

`from_pydantic()` automatically extracts metadata from Pydantic fields:

- **`Field.title`** → Column header name
- **`Field.description`** → Column tooltip (shown on header hover)
- **`Field.annotation`** → Column width inference by type

```python
from pydantic import BaseModel, Field

class Person(BaseModel):
    name: str = Field(title="Name", description="Full name")
    age: int = Field(title="Age", description="Age in years")
    city: str = Field(title="City", description="City of residence")

people = [
    Person(name="Alice", age=30, city="Tokyo"),
    Person(name="Bob", age=25, city="Osaka"),
]

state = DataTableState.from_pydantic(people)
table = DataTable(state)
# Columns: Name (150px), Age (80px), City (150px)
# Hover headers to see tooltips from Field.description
```

**Type-based width inference:**

| Type | Width |
|------|-------|
| `int` | 80px |
| `float` | 100px |
| `str` | 150px |
| `bool` | 60px |
| `date`/`datetime` | 120px |

### Style Customization

Customize table colors with fluent API:

```python
DataTable(state)
    .header_bg_color("#3d5a80")      # Header background
    .header_text_color("#ffffff")    # Header text
    .alt_row_bg_color("#293241")     # Alternating row background
    .hover_bg_color("#415a77")       # Hover row background
    .selected_bg_color("#ee6c4d")    # Selected row background
    .grid_color("#4a5568")           # Grid line color
```

### Features

- **Sorting**: Click column headers to sort (ASC → DESC → NONE)
- **Filtering**: Global and per-column text filtering
- **Selection**: Single or multi-row selection with Shift/Ctrl
- **Column Resize**: Drag column borders to resize
- **Virtual Scrolling**: Efficient handling of 1000+ rows
- **Keyboard Navigation**: Arrow keys, Enter, Home/End, PageUp/PageDown

### DataTableState Methods

| Method | Description |
|--------|-------------|
| `from_pydantic(models)` | Create from Pydantic model list |
| `set_rows(rows)` | Replace all rows |
| `set_filter(text)` | Set global filter |
| `set_column_filter(col, text)` | Set per-column filter |
| `clear_filters()` | Clear all filters |
| `set_sort(column, direction)` | Set sort column and direction |
| `clear_selection()` | Clear row selection |

### Events

| Event | Description |
|-------|-------------|
| `on_sort(callback)` | Called when sort changes |
| `on_selection_change(callback)` | Called when selection changes |
| `on_cell_click(callback)` | Called when a cell is clicked |
| `on_filter_change(callback)` | Called when filter changes |

### Legacy TableModel (Backward Compatible)

The legacy `TableModel` API is still supported:

```python
from castella import DataTable, TableModel

model = TableModel.from_pydantic_model(people)
table = DataTable(model)  # Automatically converted to DataTableState
```

## Additional Widgets

For more widgets and examples, see:

- [Charts](chart.md) - BarChart, LineChart, PieChart
- [Examples directory](https://github.com/i2y/castella/tree/main/examples)

### Available Widgets

| Widget | Description |
|--------|-------------|
| `Text` | Single-line text display |
| `MultilineText` | Multi-line text with wrapping |
| `SimpleText` | Lightweight text widget |
| `Button` | Clickable button |
| `Input` | Text input field |
| `MultilineInput` | Multi-line text editor |
| `Markdown` | Rich markdown rendering |
| `Switch` | Toggle switch |
| `CheckBox` | Checkbox |
| `RadioButtons` | Radio button group |
| `Slider` | Range input slider |
| `Tabs` | Tabbed navigation |
| `Tree` | Hierarchical tree view |
| `FileTree` | File system browser |
| `Modal` | Modal dialog overlay |
| `DateTimeInput` | Date/time picker |
| `Image` | Image display |
| `NetImage` | Image from URL |
| `AsyncNetImage` | Async image loading |
| `NumpyImage` | Image from numpy array |
| `DataTable` | Tabular data display |
| `Column` | Vertical layout |
| `Row` | Horizontal layout |
| `Box` | Stacking layout |
| `Spacer` | Flexible space |
