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

Display multi-line text content.

```python
MultilineText(
    "Line 1\nLine 2\nLine 3",
    font_size=16,
    wrap=True  # Enable text wrapping
)
```

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
from castella import MultilineInput, MultilineInputState, SizePolicy

# Basic usage
editor = MultilineInput("Initial text", font_size=14)

# With state for reactive updates
state = MultilineInputState("Hello\nWorld")
editor = MultilineInput(state, font_size=14, wrap=True)

# With change callback
editor = MultilineInput("", font_size=14).on_change(lambda text: print(text))

# With fixed height (enables vertical scrolling)
editor = (
    MultilineInput(state, font_size=14, wrap=True)
    .height(200)
    .height_policy(SizePolicy.FIXED)
)
```

### Features

- Line wrapping with `wrap=True`
- Vertical scrolling when content exceeds height
- Mouse wheel scrolling
- Click to position cursor
- Scrollbar thumb dragging
- Auto-scroll to keep cursor visible

!!! warning "MultilineInput and State"
    Don't attach MultilineInput's state to the component - it causes focus loss on every keystroke. See [State Management](state.md) for details.

## Markdown

Rich markdown text rendering with syntax highlighting.

```python
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
```

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

## Image

Display images from files.

```python
from castella import Image

Image("path/to/image.png")
```

## NetImage

Display images from URLs with caching support.

```python
from castella import NetImage

# Basic usage
img = NetImage("https://example.com/image.png")

# Disable cache
img = NetImage("https://example.com/image.png", use_cache=False)

# With reactive URL
from castella import State
url = State("https://example.com/image.png")
img = NetImage(url)
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `url` | str or State[str] | required | Image URL |
| `use_cache` | bool | True | Cache downloaded images |

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

Display tabular data with headers.

```python
from castella import DataTable, TableModel
from pydantic import BaseModel, Field

# Create from Pydantic models
class Person(BaseModel):
    name: str = Field(title="Name")
    age: int = Field(title="Age")
    city: str = Field(title="City")

people = [
    Person(name="Alice", age=30, city="Tokyo"),
    Person(name="Bob", age=25, city="Osaka"),
]

model = TableModel.from_pydantic_model(people)
table = DataTable(model)

# Create manually
model = TableModel(
    column_names=["Name", "Age", "City"],
    data=[
        ["Alice", 30, "Tokyo"],
        ["Bob", 25, "Osaka"],
    ]
)
table = DataTable(model)
```

### TableModel Methods

| Method | Description |
|--------|-------------|
| `from_pydantic_model(models)` | Create from Pydantic model list |
| `reflect_pydantic_model(models)` | Update data from Pydantic models |
| `get_value_at(row, col)` | Get cell value |
| `set_value_at(value, row, col)` | Set cell value |
| `add_row(row_data)` | Add a new row |
| `remove_row(row_index)` | Remove a row |
| `add_column(name, data)` | Add a new column |
| `remove_column(col_index)` | Remove a column |
| `attach(observer)` | Listen for changes |

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
| `Image` | Image display |
| `NetImage` | Image from URL |
| `AsyncNetImage` | Async image loading |
| `NumpyImage` | Image from numpy array |
| `DataTable` | Tabular data display |
| `Column` | Vertical layout |
| `Row` | Horizontal layout |
| `Box` | Stacking layout |
| `Spacer` | Flexible space |
