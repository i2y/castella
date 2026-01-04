# MCP Resources Reference

Read-only data exposed by CastellaMCPServer.

## ui://tree

Complete UI tree structure.

**Response:**
```json
{
  "type": "tree",
  "root": {
    "id": "root",
    "type": "Column",
    "semantic_id": null,
    "bounds": {"x": 0, "y": 0, "width": 800, "height": 600},
    "children": [
      {
        "id": "greeting",
        "type": "Text",
        "semantic_id": "greeting",
        "value": "Hello MCP!",
        "bounds": {"x": 0, "y": 0, "width": 800, "height": 24}
      },
      {
        "id": "name-input",
        "type": "Input",
        "semantic_id": "name-input",
        "value": "",
        "interactive": true,
        "focused": false,
        "bounds": {"x": 0, "y": 24, "width": 800, "height": 40}
      }
    ]
  }
}
```

## ui://focus

Currently focused element.

**Response (focused):**
```json
{
  "type": "focus",
  "element": {
    "id": "name-input",
    "type": "Input",
    "semantic_id": "name-input",
    "value": "Alice"
  }
}
```

**Response (no focus):**
```json
{
  "type": "focus",
  "element": null
}
```

## ui://elements

List of all interactive elements.

**Response:**
```json
{
  "type": "elements",
  "elements": [
    {
      "id": "name-input",
      "type": "Input",
      "semantic_id": "name-input",
      "value": "",
      "interactive": true
    },
    {
      "id": "submit-btn",
      "type": "Button",
      "semantic_id": "submit-btn",
      "label": "Submit",
      "interactive": true
    },
    {
      "id": "newsletter-check",
      "type": "CheckBox",
      "semantic_id": "newsletter-check",
      "value": false,
      "interactive": true
    }
  ]
}
```

## ui://element/{id}

Details for a specific element.

**Request:**
```
ui://element/submit-btn
```

**Response:**
```json
{
  "type": "element",
  "element": {
    "id": "submit-btn",
    "type": "Button",
    "semantic_id": "submit-btn",
    "label": "Submit",
    "interactive": true,
    "focused": false,
    "enabled": true,
    "visible": true,
    "bounds": {
      "x": 10,
      "y": 100,
      "width": 80,
      "height": 40
    }
  }
}
```

**Error (not found):**
```json
{
  "type": "error",
  "message": "Element not found: unknown-id"
}
```

## a2ui://surfaces

A2UI surfaces (only available when A2UI renderer is provided).

**Response:**
```json
{
  "type": "surfaces",
  "surfaces": [
    {
      "id": "default",
      "root_id": "root",
      "component_count": 15,
      "data_model": {
        "/counter": 42,
        "/user/name": "Alice"
      }
    }
  ]
}
```

## Element Properties

Common properties in element responses:

| Property | Type | Description |
|----------|------|-------------|
| `id` | string | Internal widget ID |
| `semantic_id` | string | User-assigned semantic ID |
| `type` | string | Widget type (Button, Input, etc.) |
| `value` | any | Current value |
| `label` | string | Display label (buttons) |
| `interactive` | bool | Can be interacted with |
| `focused` | bool | Currently has focus |
| `enabled` | bool | Not disabled |
| `visible` | bool | Currently visible |
| `bounds` | object | Position and size |

## Bounds Object

```json
{
  "x": 10,      // X position in pixels
  "y": 100,     // Y position in pixels
  "width": 80,  // Width in pixels
  "height": 40  // Height in pixels
}
```

## Fetching Resources

Using MCP protocol:

```python
# Read resource
message = {
    "type": "read_resource",
    "params": {"uri": "ui://tree"}
}

# Send to MCP server and get response
response = send_mcp_message(message)
print(response["contents"])
```
