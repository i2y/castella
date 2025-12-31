# MCP (Model Context Protocol) Support

Castella provides built-in support for [MCP (Model Context Protocol)](https://modelcontextprotocol.github.io/), enabling AI agents to introspect and control Castella UIs programmatically.

## Overview

MCP is a standard protocol for AI-UI interaction. With Castella's MCP support, AI agents can:

- **Introspect** the UI tree to understand what elements exist
- **Read** element properties (labels, values, states)
- **Control** widgets (click buttons, type text, toggle checkboxes)
- **Integrate with A2UI** for bidirectional AI-generated UIs

## Installation

Install Castella with MCP support:

```bash
uv add "castella[mcp]"
# or
pip install "castella[mcp]"
```

## Quick Start

### Basic MCP Server

```python
from castella import App, Column, Button, Input, Text
from castella.frame import Frame
from castella.mcp import CastellaMCPServer

def build_ui():
    return Column(
        Text("Hello MCP!"),
        Input("").semantic_id("name-input"),
        Button("Submit").semantic_id("submit-btn"),
    )

app = App(Frame("MCP Demo", 800, 600), build_ui())
mcp = CastellaMCPServer(app, name="my-app")

# Run SSE server for HTTP clients
mcp.run_sse_in_background(host="localhost", port=8765)

app.run()
```

### Controlling from a Client

```python
import json
import urllib.request

def call_tool(name: str, **kwargs) -> dict:
    message = {"type": "call_tool", "params": {"name": name, "arguments": kwargs}}
    data = json.dumps(message).encode("utf-8")
    req = urllib.request.Request(
        "http://localhost:8765/message",
        data=data,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read())

# Type into the input field
result = call_tool("type_text", element_id="name-input", text="Hello", replace=True)
print(f"Type result: {result}")

# Click the submit button
result = call_tool("click", element_id="submit-btn")
print(f"Click result: {result}")
```

## Semantic IDs

Widgets can be assigned stable semantic IDs that persist across UI rebuilds:

```python
# Assign semantic IDs using the fluent API
Button("Submit").semantic_id("submit-btn")
Input("").semantic_id("name-input")
CheckBox(checked_state).semantic_id("newsletter-opt-in")

# Without semantic IDs, auto-generated IDs are used:
# button_0, input_1, checkbox_2, etc.
```

Semantic IDs are crucial for reliable AI agent interaction - they provide stable identifiers that don't change when the UI is rebuilt.

## Transport Options

### SSE Transport (HTTP)

The SSE (Server-Sent Events) transport is ideal for connecting to already-running Castella applications:

```python
mcp = CastellaMCPServer(app, name="my-app")

# Run SSE server on a specific port
mcp.run_sse_in_background(host="localhost", port=8765)
```

**SSE Endpoints:**

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/sse` | GET | SSE event stream |
| `/message` | POST | Send MCP messages |
| `/health` | GET | Health check |

### stdio Transport

For integration with Claude Desktop or other MCP clients that use stdio:

```python
mcp = CastellaMCPServer(app, name="my-app")

# Run stdio server in background thread
mcp.run_in_background()
```

## MCP Resources

Resources provide read-only access to UI state:

| URI | Description |
|-----|-------------|
| `ui://tree` | Complete UI tree with semantic IDs and properties |
| `ui://focus` | Currently focused element |
| `ui://elements` | List of all interactive elements |
| `ui://element/{id}` | Detailed information about a specific element |
| `a2ui://surfaces` | A2UI surfaces (when A2UI renderer is provided) |

### Reading Resources

```python
def read_resource(uri: str) -> dict:
    return send_message("read_resource", {"uri": uri})

# Get the complete UI tree
tree = read_resource("ui://tree")

# Get all interactive elements
elements = read_resource("ui://elements")
```

## MCP Tools

Tools allow AI agents to interact with the UI:

| Tool | Parameters | Description |
|------|------------|-------------|
| `click(element_id)` | `element_id: str` | Click/tap an element |
| `type_text(element_id, text, replace)` | `element_id: str`, `text: str`, `replace: bool = False` | Type into an input field |
| `focus(element_id)` | `element_id: str` | Set focus to an element |
| `scroll(element_id, direction, amount)` | `element_id: str`, `direction: str`, `amount: int = 100` | Scroll (up/down/left/right) |
| `toggle(element_id)` | `element_id: str` | Toggle a checkbox or switch |
| `select(element_id, value)` | `element_id: str`, `value: str` | Select value in picker/radio/tabs |
| `list_actionable()` | (none) | List all interactive elements |
| `send_a2ui(message)` | `message: dict` | Send A2UI message (when A2UI renderer provided) |

### Tool Examples

```python
# Click a button
call_tool("click", element_id="submit-btn")

# Type text (replace existing content)
call_tool("type_text", element_id="search-input", text="python", replace=True)

# Type text (append to existing)
call_tool("type_text", element_id="notes-input", text=" more text", replace=False)

# Toggle a checkbox
call_tool("toggle", element_id="agree-checkbox")

# Scroll down
call_tool("scroll", element_id="content-list", direction="down", amount=200)

# Select a tab
call_tool("select", element_id="main-tabs", value="settings")
```

## A2UI + MCP Integration

Castella's MCP support integrates seamlessly with A2UI for bidirectional AI-UI interaction:

```python
from castella import App
from castella.a2ui import A2UIRenderer, A2UIComponent, UserAction
from castella.frame import Frame
from castella.mcp import CastellaMCPServer

# A2UI JSON definition
A2UI_JSON = {
    "components": [
        {"id": "root", "component": "Column", "children": {"explicitList": ["input", "btn"]}},
        {"id": "input", "component": "TextField", "text": {"path": "/name"}},
        {"id": "btn", "component": "Button", "text": {"literalString": "Submit"},
         "action": {"name": "submit", "context": []}},
    ],
    "rootId": "root",
}

# Create A2UI renderer with action handler
def on_action(action: UserAction):
    if action.name == "submit":
        surface = renderer.get_surface("default")
        name = surface.data_model.get("name", "")
        print(f"Submitted: {name}")

renderer = A2UIRenderer(on_action=on_action)
renderer.render_json(A2UI_JSON, initial_data={"/name": ""})

surface = renderer.get_surface("default")
app = App(Frame("A2UI + MCP", 800, 600), A2UIComponent(surface))

# MCP server with A2UI renderer for bidirectional integration
mcp = CastellaMCPServer(app, a2ui_renderer=renderer)
mcp.run_sse_in_background(host="localhost", port=8766)

app.run()
```

**Key Features:**

- A2UI component IDs are automatically used as MCP semantic IDs
- MCP tools can control A2UI-generated widgets
- User actions are properly routed through A2UI's action system
- Data bindings are maintained across MCP operations

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      AI Agent (Claude, etc.)                │
│                            ↓↑                               │
│                         MCP Client                          │
└─────────────────────────────────────────────────────────────┘
                            ↓↑ SSE/stdio (JSON-RPC)
┌─────────────────────────────────────────────────────────────┐
│                   Castella Application                      │
│  ┌─────────────────────────────────────────────────────┐   │
│  │        CastellaMCPServer (background thread)         │   │
│  │  ┌────────────────┐  ┌────────────────────────────┐ │   │
│  │  │   Resources    │  │         Tools              │ │   │
│  │  │  ui://tree     │  │  click(), type_text()      │ │   │
│  │  │  ui://focus    │  │  scroll(), toggle()        │ │   │
│  │  │  ui://elements │  │  send_a2ui()               │ │   │
│  │  └────────────────┘  └────────────────────────────┘ │   │
│  └─────────────────────────────────────────────────────┘   │
│                            ↓↑                               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  SemanticWidgetRegistry + WidgetIntrospector        │   │
│  │  - Stable semantic ID management                     │   │
│  │  - A2UI ID integration                               │   │
│  └─────────────────────────────────────────────────────┘   │
│                            ↓↑                               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Widget Tree (main thread)               │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Examples

Run the included examples to see MCP in action:

```bash
# Basic MCP SSE server
uv run python examples/mcp_sse_server.py

# MCP SSE client (in another terminal)
uv run python examples/mcp_sse_client.py

# A2UI + MCP server
uv run python examples/mcp_a2ui_server.py

# A2UI + MCP client (in another terminal)
uv run python examples/mcp_a2ui_client.py
```

## Module Reference

### `castella.mcp`

| Class/Function | Description |
|----------------|-------------|
| `CastellaMCPServer` | Main MCP server class |
| `SemanticWidgetRegistry` | Widget ID registry |
| `WidgetIntrospector` | UI tree introspection |
| `ElementInfo` | Element information model |
| `UITreeNode` | Tree node model |
| `ActionResult` | Tool result model |

### CastellaMCPServer API

```python
class CastellaMCPServer:
    def __init__(
        self,
        app: App,
        name: str = "castella-ui",
        a2ui_renderer: A2UIRenderer | None = None,
    ): ...

    def run(self) -> None:
        """Run MCP server (blocking, stdio transport)."""

    def run_in_background(self) -> threading.Thread:
        """Run MCP server in background thread (stdio transport)."""

    def run_sse_in_background(
        self,
        host: str = "localhost",
        port: int = 8765,
    ) -> threading.Thread:
        """Run SSE server in background thread."""

    def refresh_registry(self) -> None:
        """Refresh the widget registry from the current UI tree."""
```

## Best Practices

1. **Use Semantic IDs** - Always assign meaningful semantic IDs to interactive elements for reliable AI agent interaction.

2. **Handle Actions Properly** - When using A2UI integration, implement proper action handlers to respond to AI-initiated interactions.

3. **Keep UI Simple** - Complex UIs with many nested elements can be harder for AI agents to navigate. Consider flattening the structure where possible.

4. **Test with Clients** - Use the provided example clients to verify your MCP integration works correctly.

5. **Error Handling** - Check the `success` field in tool results and handle failures gracefully.
