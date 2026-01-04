# MCP Tools Reference

Actions available via CastellaMCPServer.

## click

Click or tap an element.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `element_id` | string | Yes | Semantic ID of element |

**Example:**
```json
{
  "type": "call_tool",
  "params": {
    "name": "click",
    "arguments": {
      "element_id": "submit-btn"
    }
  }
}
```

**Response:**
```json
{
  "type": "tool_result",
  "content": {"success": true, "element_id": "submit-btn"}
}
```

## type_text

Type text into an input field.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `element_id` | string | Yes | Semantic ID of input |
| `text` | string | Yes | Text to type |
| `replace` | bool | No | Replace existing text (default: false) |

**Example (replace):**
```json
{
  "type": "call_tool",
  "params": {
    "name": "type_text",
    "arguments": {
      "element_id": "name-input",
      "text": "Alice Smith",
      "replace": true
    }
  }
}
```

**Example (append):**
```json
{
  "type": "call_tool",
  "params": {
    "name": "type_text",
    "arguments": {
      "element_id": "name-input",
      "text": " Jr.",
      "replace": false
    }
  }
}
```

## focus

Set focus to an element.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `element_id` | string | Yes | Semantic ID of element |

**Example:**
```json
{
  "type": "call_tool",
  "params": {
    "name": "focus",
    "arguments": {
      "element_id": "search-input"
    }
  }
}
```

## scroll

Scroll a container.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `element_id` | string | Yes | Semantic ID of scrollable |
| `direction` | string | Yes | "up", "down", "left", "right" |
| `amount` | number | No | Pixels to scroll (default: 100) |

**Example:**
```json
{
  "type": "call_tool",
  "params": {
    "name": "scroll",
    "arguments": {
      "element_id": "message-list",
      "direction": "down",
      "amount": 200
    }
  }
}
```

## toggle

Toggle a checkbox or switch.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `element_id` | string | Yes | Semantic ID of checkbox/switch |

**Example:**
```json
{
  "type": "call_tool",
  "params": {
    "name": "toggle",
    "arguments": {
      "element_id": "dark-mode-switch"
    }
  }
}
```

**Response:**
```json
{
  "type": "tool_result",
  "content": {"success": true, "new_value": true}
}
```

## select

Select a value in picker, radio buttons, or tabs.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `element_id` | string | Yes | Semantic ID of selector |
| `value` | string | Yes | Value to select |

**Example (tabs):**
```json
{
  "type": "call_tool",
  "params": {
    "name": "select",
    "arguments": {
      "element_id": "main-tabs",
      "value": "settings"
    }
  }
}
```

**Example (radio):**
```json
{
  "type": "call_tool",
  "params": {
    "name": "select",
    "arguments": {
      "element_id": "size-picker",
      "value": "Large"
    }
  }
}
```

## list_actionable

List all interactive elements.

**Parameters:** None

**Example:**
```json
{
  "type": "call_tool",
  "params": {
    "name": "list_actionable",
    "arguments": {}
  }
}
```

**Response:**
```json
{
  "type": "tool_result",
  "content": {
    "elements": [
      {"id": "name-input", "type": "Input", "actions": ["type_text", "focus"]},
      {"id": "submit-btn", "type": "Button", "actions": ["click"]},
      {"id": "dark-mode", "type": "Switch", "actions": ["toggle"]},
      {"id": "main-tabs", "type": "Tabs", "actions": ["select"]}
    ]
  }
}
```

## send_a2ui

Send A2UI message (only available when A2UI renderer is provided).

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `message` | object | Yes | A2UI message |

**Example (update data):**
```json
{
  "type": "call_tool",
  "params": {
    "name": "send_a2ui",
    "arguments": {
      "message": {
        "updateDataModel": {
          "surfaceId": "default",
          "data": {
            "/counter": 42,
            "/status": "Updated!"
          }
        }
      }
    }
  }
}
```

**Example (update components):**
```json
{
  "type": "call_tool",
  "params": {
    "name": "send_a2ui",
    "arguments": {
      "message": {
        "updateComponents": {
          "surfaceId": "default",
          "components": [
            {"id": "status", "component": "Text", "text": {"literalString": "Done!"}}
          ]
        }
      }
    }
  }
}
```

## Error Responses

**Element not found:**
```json
{
  "type": "tool_result",
  "isError": true,
  "content": {"error": "Element not found: unknown-id"}
}
```

**Invalid action:**
```json
{
  "type": "tool_result",
  "isError": true,
  "content": {"error": "Element 'greeting' does not support 'click'"}
}
```

**Invalid parameters:**
```json
{
  "type": "tool_result",
  "isError": true,
  "content": {"error": "Missing required parameter: element_id"}
}
```
