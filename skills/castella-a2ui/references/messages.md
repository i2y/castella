# A2UI Message Types

Reference for all A2UI message types and their usage.

## createSurface

Create a complete UI surface at once.

```python
{
    "createSurface": {
        "surfaceId": "main",
        "components": [
            {"id": "root", "component": "Column", ...},
            {"id": "text1", "component": "Text", ...}
        ],
        "rootId": "root"
    }
}
```

**Fields:**
- `surfaceId` - Unique identifier for the surface
- `components` - Array of component definitions
- `rootId` - ID of the root component

## beginRendering

Signal the start of progressive rendering.

```python
{
    "beginRendering": {
        "surfaceId": "main",
        "root": "root"
    }
}
```

**Fields:**
- `surfaceId` - Surface identifier
- `root` - Root component ID

Use with `updateComponents` for incremental UI construction.

## updateComponents

Add or update components (progressive rendering).

```python
{
    "updateComponents": {
        "surfaceId": "main",
        "components": [
            {"id": "header", "component": "Text", "text": {"literalString": "Header"}},
            {"id": "content", "component": "Column", "children": {"explicitList": ["item1"]}}
        ]
    }
}
```

**Fields:**
- `surfaceId` - Surface identifier
- `components` - Array of component definitions to add/update

Components with existing IDs are replaced.

## updateDataModel

Update data binding values.

```python
{
    "updateDataModel": {
        "surfaceId": "main",
        "data": {
            "/counter": 42,
            "/user/name": "Alice",
            "/items": [{"id": 1}, {"id": 2}]
        }
    }
}
```

**Fields:**
- `surfaceId` - Surface identifier
- `data` - Object with JSON Pointer paths as keys

All bound widgets update automatically.

## deleteSurface

Remove a surface.

```python
{
    "deleteSurface": {
        "surfaceId": "main"
    }
}
```

## Message Handling

### render_json()

Create surface from single JSON:

```python
renderer = A2UIRenderer()
widget = renderer.render_json({
    "components": [...],
    "rootId": "root"
}, initial_data={"/counter": 0})
```

### handle_message()

Process individual messages:

```python
renderer.handle_message({
    "updateDataModel": {
        "surfaceId": "default",
        "data": {"/counter": 10}
    }
})
```

### handle_jsonl()

Process JSONL string:

```python
jsonl = """
{"beginRendering": {"surfaceId": "main", "root": "root"}}
{"updateComponents": {"surfaceId": "main", "components": [...]}}
"""
surface = renderer.handle_jsonl(jsonl)
```

### handle_stream()

Process stream (file, generator):

```python
with open("ui.jsonl") as f:
    surface = renderer.handle_stream(f, on_update=callback)
```

### handle_stream_async()

Process async stream:

```python
surface = await renderer.handle_stream_async(async_stream)
```

## Surface Management

### get_surface()

Retrieve surface by ID:

```python
surface = renderer.get_surface("main")
if surface:
    widget = surface.root_widget
    data = surface.data_model
```

### Surface Properties

```python
surface.id              # Surface ID
surface.root_widget     # Root Castella widget
surface.data_model      # Current data model dict
surface.components      # Component definitions
```

## Action Messages

When user interacts with action-enabled components:

```python
def on_action(action: UserAction):
    # action.name - Action name (e.g., "submit")
    # action.source_component_id - Component ID that triggered
    # action.context - Context data from action definition

    # Respond with data update
    renderer.handle_message({
        "updateDataModel": {
            "surfaceId": "default",
            "data": {"/status": "Submitted!"}
        }
    })
```

## Progressive Rendering Sequence

Typical streaming sequence:

```
1. {"beginRendering": {"surfaceId": "chat", "root": "root"}}
2. {"updateComponents": {"surfaceId": "chat", "components": [root, header]}}
3. {"updateComponents": {"surfaceId": "chat", "components": [message1]}}
4. {"updateComponents": {"surfaceId": "chat", "components": [message2]}}
5. {"updateDataModel": {"surfaceId": "chat", "data": {"/status": "Complete"}}}
```

Each `updateComponents` triggers UI refresh with new components.
