# MCP Type Reference

Data types used in Castella MCP integration.

## ElementInfo

Information about a UI element.

```python
from castella.mcp import ElementInfo

element = ElementInfo(
    id="submit-btn",
    semantic_id="submit-btn",
    widget_type="Button",
    label="Submit",
    value=None,
    interactive=True,
    focused=False,
    enabled=True,
    visible=True,
    bounds=Rect(x=10, y=100, width=80, height=40),
)
```

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `id` | str | Internal widget ID |
| `semantic_id` | str | User-assigned semantic ID |
| `widget_type` | str | Widget type name |
| `label` | str | Display label |
| `value` | Any | Current value |
| `interactive` | bool | Supports interaction |
| `focused` | bool | Has focus |
| `enabled` | bool | Not disabled |
| `visible` | bool | Currently visible |
| `bounds` | Rect | Position and size |

## UITreeNode

Node in the UI tree hierarchy.

```python
from castella.mcp import UITreeNode

node = UITreeNode(
    id="root",
    widget_type="Column",
    semantic_id=None,
    bounds=Rect(x=0, y=0, width=800, height=600),
    children=[
        UITreeNode(id="greeting", ...),
        UITreeNode(id="input", ...),
    ],
)
```

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `id` | str | Widget ID |
| `widget_type` | str | Widget type |
| `semantic_id` | str | Semantic ID |
| `bounds` | Rect | Position and size |
| `value` | Any | Current value |
| `label` | str | Display label |
| `interactive` | bool | Supports interaction |
| `focused` | bool | Has focus |
| `children` | list[UITreeNode] | Child nodes |

## ActionResult

Result from tool execution.

```python
from castella.mcp import ActionResult

# Success
result = ActionResult(
    success=True,
    element_id="submit-btn",
    new_value=None,
)

# Error
result = ActionResult(
    success=False,
    error="Element not found: unknown-id",
)
```

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `success` | bool | Action succeeded |
| `element_id` | str | Target element |
| `new_value` | Any | Updated value (for toggle) |
| `error` | str | Error message |

## SemanticWidgetRegistry

Maps semantic IDs to widgets.

```python
from castella.mcp import SemanticWidgetRegistry

registry = SemanticWidgetRegistry()

# Register widget
registry.register("submit-btn", button_widget)

# Lookup
widget = registry.get("submit-btn")

# List all
all_widgets = registry.all()
```

## WidgetIntrospector

Traverses UI tree and collects element info.

```python
from castella.mcp import WidgetIntrospector

introspector = WidgetIntrospector(app)

# Get tree
tree = introspector.get_tree()

# Get focused
focused = introspector.get_focused()

# Get all interactive
elements = introspector.get_interactive_elements()

# Get specific element
element = introspector.get_element("submit-btn")
```

## CastellaMCPServer

Main MCP server class.

```python
from castella.mcp import CastellaMCPServer

server = CastellaMCPServer(
    app: App,                    # Castella App
    name: str = "castella",      # Server name
    version: str = "1.0.0",      # Version
    a2ui_renderer: A2UIRenderer = None,  # Optional A2UI
)
```

### Methods

| Method | Description |
|--------|-------------|
| `run()` | Run stdio transport (blocks) |
| `run_in_background()` | Run stdio in thread |
| `run_sse(host, port)` | Run SSE transport (blocks) |
| `run_sse_in_background(host, port)` | Run SSE in thread |
| `refresh_registry()` | Refresh widget registry |
| `stop()` | Stop server |

## Rect

Bounds rectangle.

```python
from castella.models.geometry import Rect, Point, Size

bounds = Rect(
    origin=Point(x=10, y=100),
    size=Size(width=80, height=40),
)

# Access
print(bounds.x)       # 10
print(bounds.y)       # 100
print(bounds.width)   # 80
print(bounds.height)  # 40
```

## JSON Serialization

All types serialize to JSON for MCP messages:

```python
element_dict = {
    "id": "submit-btn",
    "type": "Button",
    "semantic_id": "submit-btn",
    "label": "Submit",
    "value": None,
    "interactive": True,
    "focused": False,
    "enabled": True,
    "visible": True,
    "bounds": {
        "x": 10,
        "y": 100,
        "width": 80,
        "height": 40
    }
}
```
