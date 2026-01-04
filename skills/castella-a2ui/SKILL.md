---
name: castella-a2ui
description: Render A2UI JSON as native Castella widgets. Parse A2UI messages, handle actions, progressive rendering, data binding, and connect to A2UI-enabled agents.
---

# Castella A2UI Integration

A2UI (Agent-to-User Interface) enables AI agents to generate rich, interactive UIs by outputting JSON component descriptions. Castella renders these natively across desktop, web, and terminal platforms.

**When to use**: "render A2UI JSON", "A2UI component", "A2UIRenderer", "A2UI data binding", "A2UI streaming", "connect to A2UI agent", "updateDataModel", "A2UIClient"

## Quick Start

Render A2UI JSON to a Castella widget:

```python
from castella import App
from castella.a2ui import A2UIRenderer, A2UIComponent
from castella.frame import Frame

renderer = A2UIRenderer()
widget = renderer.render_json({
    "components": [
        {"id": "root", "component": "Column", "children": {"explicitList": ["text1"]}},
        {"id": "text1", "component": "Text", "text": {"literalString": "Hello A2UI!"}}
    ],
    "rootId": "root"
})

App(Frame("A2UI Demo", 800, 600), widget).run()
```

## Core Concepts

### A2UIRenderer

The main class for converting A2UI messages to Castella widgets:

```python
from castella.a2ui import A2UIRenderer, UserAction

def on_action(action: UserAction):
    print(f"Action: {action.name}")
    print(f"Source: {action.source_component_id}")
    print(f"Context: {action.context}")

renderer = A2UIRenderer(on_action=on_action)
```

### Value Types

A2UI uses typed values for properties:

```python
# Literal values (static)
{"text": {"literalString": "Hello"}}
{"value": {"literalNumber": 42}}
{"checked": {"literalBoolean": True}}

# Data binding (dynamic, JSON Pointer RFC 6901)
{"text": {"path": "/user/name"}}
{"value": {"path": "/counter"}}
```

Helper functions:

```python
from castella.a2ui import literal, binding

literal("Hello")      # {"literalString": "Hello"}
literal(42)           # {"literalNumber": 42}
literal(True)         # {"literalBoolean": True}
binding("/counter")   # {"path": "/counter"}
```

## Supported Components

| A2UI Component | Castella Widget | Notes |
|----------------|-----------------|-------|
| Text | Text | usageHint: h1-h5, body, caption |
| Button | Button | action with context |
| TextField | Input/MultilineInput | usageHint: password, multiline |
| CheckBox | CheckBox | Two-way binding |
| Slider | Slider | min/max range |
| DateTimeInput | DateTimeInput | Date/time picker |
| ChoicePicker | RadioButtons/Column | Single/multiple selection |
| Image | NetImage | URL-based images |
| Icon | Text | Material Icons → emoji |
| Divider | Spacer | Horizontal/vertical |
| Row | Row | Horizontal layout |
| Column | Column | Vertical layout |
| Card | Column | Container with styling |
| List | Column | TemplateChildren support |
| Tabs | Tabs | Tabbed navigation |
| Modal | Modal | Overlay dialog |
| Markdown | Markdown | Rich text (Castella extension) |

See `references/components.md` for detailed component reference.

## Data Binding

Bind widget values to a data model using JSON Pointer paths:

```python
a2ui_json = {
    "components": [
        {"id": "root", "component": "Column", "children": {"explicitList": ["greeting"]}},
        {"id": "greeting", "component": "Text", "text": {"path": "/message"}}
    ],
    "rootId": "root"
}

# Provide initial data
initial_data = {"/message": "Hello, World!"}
widget = renderer.render_json(a2ui_json, initial_data=initial_data)
```

## Actions

Handle user interactions via actions:

```python
{
    "id": "submit_btn",
    "component": "Button",
    "text": {"literalString": "Submit"},
    "action": {"name": "submit", "context": ["/formData"]}
}
```

Action handler receives `UserAction`:

```python
def on_action(action: UserAction):
    print(action.name)                  # "submit"
    print(action.source_component_id)   # "submit_btn"
    print(action.context)               # ["/formData"]
```

## updateDataModel

Update bound values dynamically:

```python
renderer.handle_message({
    "updateDataModel": {
        "surfaceId": "default",
        "data": {"/message": "Updated message!"}
    }
})
```

## A2UIComponent (Reactive)

Wrap surface in A2UIComponent for automatic UI updates:

```python
from castella.a2ui import A2UIComponent

renderer.render_json(a2ui_json, initial_data=initial_data)
surface = renderer.get_surface("default")
component = A2UIComponent(surface)  # Auto-updates on data changes

App(Frame("A2UI", 800, 600), component).run()
```

## TemplateChildren (Dynamic Lists)

Render lists from data arrays:

```python
a2ui_json = {
    "components": [
        {"id": "root", "component": "Column", "children": {"explicitList": ["user_list"]}},
        {"id": "user_list", "component": "List", "children": {
            "path": "/users",           # JSON Pointer to array
            "componentId": "user_item"  # Template component
        }},
        {"id": "user_item", "component": "Text", "text": {"path": "name"}}  # Relative path
    ],
    "rootId": "root"
}

initial_data = {"/users": [{"name": "Alice"}, {"name": "Bob"}, {"name": "Charlie"}]}
widget = renderer.render_json(a2ui_json, initial_data=initial_data)
```

## ChoicePicker

Single or multiple selection:

```python
# Single selection (renders as RadioButtons)
{
    "id": "color_picker",
    "component": "ChoicePicker",
    "choices": [
        {"literalString": "Red"},
        {"literalString": "Green"},
        {"literalString": "Blue"}
    ],
    "selected": {"literalString": "Red"},
    "allowMultiple": False
}

# Multiple selection (renders as CheckBox list)
{
    "id": "toppings",
    "component": "ChoicePicker",
    "choices": [
        {"literalString": "Cheese"},
        {"literalString": "Pepperoni"},
        {"literalString": "Mushrooms"}
    ],
    "selected": {"path": "/selectedToppings"},
    "allowMultiple": True
}
```

## Progressive Rendering (Streaming)

Handle JSONL streams for incremental UI updates:

```python
# From JSONL string
jsonl_content = """
{"beginRendering": {"surfaceId": "main", "root": "root"}}
{"updateComponents": {"surfaceId": "main", "components": [...]}}
"""
surface = renderer.handle_jsonl(jsonl_content)

# From file
with open("ui.jsonl") as f:
    surface = renderer.handle_stream(f, on_update=lambda s: app.redraw())

# From async SSE stream
from castella.a2ui.transports import sse_stream
surface = await renderer.handle_stream_async(await sse_stream(url))
```

Message sequence:
1. `beginRendering` - Start progressive render
2. `updateComponents` - Add/update components
3. `updateDataModel` - Update data values

See `references/streaming.md` for transport details.

## A2UIClient

Connect to A2A agents with A2UI extension:

```python
from castella.a2ui import A2UIClient, A2UIComponent, UserAction

def on_action(action: UserAction):
    print(f"Action: {action.name}")

client = A2UIClient("http://localhost:10002", on_action=on_action)
surface = client.send("Find restaurants in Tokyo")

if surface:
    App(Frame("Restaurant Finder", 800, 600), A2UIComponent(surface)).run()
```

Async usage:

```python
async def main():
    client = A2UIClient("http://localhost:10002")
    surface = await client.send_async("Hello!")

    if surface:
        # Send action back to agent
        await client.send_action_async(action)
```

## A2UI 0.9 Compatibility

Castella auto-normalizes A2UI 0.9 spec format:

```python
# A2UI 0.9 format (plain values) - accepted
{"text": "Hello", "children": ["a", "b"]}

# Castella internal format (wrapped) - also accepted
{"text": {"literalString": "Hello"}, "children": {"explicitList": ["a", "b"]}}
```

Key normalizations:
- `text: "Hello"` → `text: {literalString: "Hello"}`
- `children: ["a", "b"]` → `children: {explicitList: ["a", "b"]}`
- `usageHint: "shortText"` → `usageHint: "text"`
- `usageHint: "obscured"` → `usageHint: "password"`

## TextField usageHint

```python
# Password field (masked ●●●●)
{"id": "password", "component": "TextField", "usageHint": "password"}

# Multiline field
{"id": "comments", "component": "TextField", "usageHint": "multiline"}
```

## Best Practices

1. **Use A2UIComponent wrapper** for reactive data binding
2. **Provide initial_data** for TemplateChildren/List components
3. **Handle actions** to update data model dynamically
4. **Use semantic IDs** - A2UI component IDs become MCP semantic IDs
5. **Test with mock data** before connecting to live agents

## Installation

```bash
uv sync --extra agent   # A2UI + A2A support
```

## Reference

- `references/components.md` - Complete A2UI component reference
- `references/messages.md` - A2UI message types
- `references/streaming.md` - Streaming and transports
- `scripts/` - Executable examples (basic_a2ui.py, a2ui_form.py, a2ui_list.py)
- A2UI Specification: https://a2ui.org/specification/v0.9-a2ui/
