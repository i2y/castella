# Agent UI

Castella provides comprehensive support for building AI agent interfaces with A2A (Agent-to-Agent) and A2UI (Agent-to-User Interface) protocols.

!!! tip "MCP Support"
    Castella also supports [MCP (Model Context Protocol)](mcp.md) for AI agents to introspect and control UIs programmatically. See the [MCP documentation](mcp.md) for details.

## Quick Start

The simplest way to create a chat UI for an AI agent:

```python
from castella.agent import AgentChat

# Connect to an A2A-compatible agent
chat = AgentChat.from_a2a("http://localhost:8080")
chat.run()
```

Or with a custom handler:

```python
from castella.agent import AgentChat

chat = AgentChat(
    handler=lambda msg: f"You said: {msg}",
    title="My Bot",
    system_message="Welcome! How can I help you?",
)
chat.run()
```

## Installation

Agent features require the `agent` extra:

```bash
uv add "castella[agent,glfw]"
# or
pip install "castella[agent,glfw]"
```

## AgentChat

`AgentChat` is a high-level component that provides a complete chat interface with minimal setup.

### Constructor Options

```python
AgentChat(
    # Backend options (provide one)
    a2a_client: A2AClient | None = None,  # A2A client for remote agent
    handler: Callable[[str], str] | None = None,  # Custom message handler

    # UI options
    title: str | None = None,  # Window title
    placeholder: str = "Type a message...",  # Input placeholder
    system_message: str | None = None,  # Initial system message
    show_agent_card: bool = True,  # Show agent card for A2A agents
    a2ui_renderer: A2UIRenderer | None = None,  # Optional A2UI renderer

    # Window options (for run())
    width: int = 700,
    height: int = 550,
)
```

### Factory Methods

```python
# Create from A2A agent URL
chat = AgentChat.from_a2a("http://localhost:8080")
```

### Running the Chat

```python
chat.run()  # Opens a window and runs the chat
```

## A2A Client

The `A2AClient` class connects to A2A-compatible agents.

```python
from castella.a2a import A2AClient

# Connect to an agent
client = A2AClient("http://localhost:8080")

# Access agent metadata
print(f"Name: {client.name}")
print(f"Description: {client.description}")
print(f"Skills: {[s.name for s in client.skills]}")

# Send messages
response = client.ask("What's the weather in Tokyo?")
print(response)

# Async support
async def main():
    response = await client.ask_async("Hello!")
```

### Agent Card

```python
from castella.a2a import A2AClient

client = A2AClient("http://agent.example.com")

# Access the agent card
card = client.agent_card
print(f"Name: {card.name}")
print(f"Description: {card.description}")
print(f"Version: {card.version}")
print(f"URL: {card.url}")

# Skills
for skill in card.skills:
    print(f"  - {skill.name}: {skill.description}")
```

## A2UI Client

The `A2UIClient` class connects to A2A agents that support the A2UI extension, automatically handling protocol negotiation and UI generation.

```python
from castella import App
from castella.a2ui import A2UIClient, A2UIComponent, UserAction
from castella.frame import Frame

# Create client with action handler
def on_action(action: UserAction):
    print(f"Action: {action.name}")
    print(f"Source: {action.source_component_id}")
    print(f"Context: {action.context}")

client = A2UIClient("http://localhost:10002", on_action=on_action)

# Send message and get A2UI surface
surface = client.send("Find me restaurants in Tokyo")

if surface:
    # Render in Castella app
    App(Frame("Demo", 800, 600), A2UIComponent(surface)).run()
```

### Async Usage

```python
async def main():
    client = A2UIClient("http://localhost:10002")
    surface = await client.send_async("Hello!")

    # Send user actions back to agent
    if surface:
        action = UserAction(
            name="book_restaurant",
            source_component_id="book-button",
            context={"restaurant": "Sushi Place"}
        )
        await client.send_action_async(action)
```

### Features

- Connects to A2A Protocol agents with A2UI extension
- Handles A2UI extension negotiation automatically
- Extracts A2UI messages from A2A responses
- Integrates with `A2UIRenderer` for widget generation
- Supports both sync and async operations
- Maintains conversation context across messages

### Displaying Agent Card

```python
from castella.agent import AgentCardView, AgentListView
from castella.a2a import A2AClient

client = A2AClient("http://agent.example.com")

# Single agent card
card_view = AgentCardView(
    client.agent_card,
    show_skills=True,
    compact=False,
)

# List of agents
agents = [
    A2AClient("http://agent1.example.com").agent_card,
    A2AClient("http://agent2.example.com").agent_card,
]
list_view = AgentListView(agents)
```

## A2UI Renderer

The `A2UIRenderer` converts A2UI JSON specifications into native Castella widgets.

```python
from castella.a2ui import A2UIRenderer, UserAction

# Create renderer with action handler
def on_action(action: UserAction):
    print(f"Action: {action.name}")
    print(f"Source: {action.source_component_id}")
    print(f"Context: {action.context}")

renderer = A2UIRenderer(on_action=on_action)

# Render A2UI JSON
widget = renderer.render_json({
    "components": [
        {"id": "root", "component": "Column", "children": {"explicitList": ["title", "btn"]}},
        {"id": "title", "component": "Text", "text": {"literalString": "Hello A2UI!"}},
        {"id": "btn", "component": "Button", "text": {"literalString": "Click Me"},
         "action": {"name": "clicked", "context": []}}
    ],
    "rootId": "root"
})
```

### Supported A2UI Components

Castella supports 17 standard A2UI components:

| A2UI Component | Castella Widget | Notes |
|----------------|-----------------|-------|
| Text | Text | Supports usageHint (h1-h5, body, caption) |
| Button | Button | Supports action with context |
| TextField | Input/MultilineInput | usageHint: password (masked), multiline |
| CheckBox | CheckBox | Two-way data binding |
| Slider | Slider | Range input with min/max |
| DateTimeInput | DateTimeInput | Date/time picker |
| ChoicePicker | RadioButtons/Column | Single or multiple selection |
| Image | NetImage | URL-based images with aspect ratio preservation |
| Icon | Text | Material Icons mapped to emoji/symbols |
| Divider | Spacer | Horizontal/vertical |
| Row | Row | Horizontal layout |
| Column | Column | Vertical layout |
| Card | Column | Container with styling |
| List | Column (scrollable) | Dynamic list with TemplateChildren |
| Tabs | Tabs | Tabbed navigation |
| Modal | Modal | Overlay dialog |
| Markdown | Markdown | Castella extension |

### A2UI 0.9 Specification Compatibility

Castella supports both the official A2UI 0.9 spec format and its internal format. The `castella.a2ui.compat` module automatically normalizes messages:

```python
# A2UI 0.9 spec format (plain values - used by Google's sample agents)
{"text": "Hello", "children": ["a", "b"], "usageHint": "shortText"}

# Castella internal format (wrapped values)
{"text": {"literalString": "Hello"}, "children": {"explicitList": ["a", "b"]}}

# Both formats are accepted - normalization is automatic
```

Key format differences handled:

- `text: "Hello"` → `text: {literalString: "Hello"}`
- `children: ["a", "b"]` → `children: {explicitList: ["a", "b"]}`
- `child: "id"` → `children: {explicitList: ["id"]}`
- `usageHint: "shortText"` → `usageHint: "text"`
- `usageHint: "obscured"` → `usageHint: "password"`
- `updateDataModel: {path, op, value}` → `updateDataModel: {data: {path: value}}`

### Custom Components

```python
from castella.a2ui import ComponentCatalog, A2UIRenderer

def create_custom_chart(component, data_model, action_handler):
    # Return a Castella widget
    return MyCustomChart(...)

catalog = ComponentCatalog()
catalog.register("CustomChart", create_custom_chart)

renderer = A2UIRenderer(catalog=catalog)
```

### A2UI Streaming

A2UI supports progressive rendering via JSONL (newline-delimited JSON) streams. This enables real-time UI updates as components arrive from AI agents.

#### JSONL Parsing

```python
from castella.a2ui import A2UIRenderer

renderer = A2UIRenderer()

# Parse JSONL string directly
jsonl = '''
{"beginRendering": {"surfaceId": "main", "root": "root"}}
{"updateComponents": {"surfaceId": "main", "components": [{"id": "root", "component": "Column", "children": {"explicitList": ["text1"]}}]}}
{"updateComponents": {"surfaceId": "main", "components": [{"id": "text1", "component": "Text", "text": {"literalString": "Hello!"}}]}}
'''
surface = renderer.handle_jsonl(jsonl)
if surface:
    widget = surface.root_widget
```

#### Streaming from Files

```python
with open("ui.jsonl") as f:
    surface = renderer.handle_stream(f, on_update=lambda s: app.redraw())
```

#### SSE (Server-Sent Events)

```python
from castella.a2ui.transports import sse_stream

# Requires httpx: pip install httpx
async def connect_sse():
    surface = await renderer.handle_stream_async(
        await sse_stream("http://agent.example.com/ui")
    )
    return surface.root_widget
```

#### WebSocket

```python
from castella.a2ui.transports import websocket_stream

# Requires websockets: pip install websockets
async def connect_websocket():
    surface = await renderer.handle_stream_async(
        await websocket_stream("ws://agent.example.com/ui")
    )
    return surface.root_widget
```

#### A2UI Message Types

| Message | Purpose |
|---------|---------|
| `beginRendering` | Signal start of progressive rendering, specify root ID |
| `updateComponents` | Add/update components incrementally |
| `createSurface` | Create complete surface at once |
| `updateDataModel` | Update data binding values |
| `deleteSurface` | Remove a surface |

### A2UIComponent (Reactive Updates)

Use `A2UIComponent` to automatically rebuild the UI when `updateDataModel` is received:

```python
from castella import App
from castella.a2ui import A2UIComponent, A2UIRenderer, UserAction
from castella.frame import Frame

renderer = A2UIRenderer()

def on_action(action: UserAction):
    if action.name == "increment":
        # Send updateDataModel to update the UI
        renderer.handle_message({
            "updateDataModel": {
                "surfaceId": "default",
                "data": {"/counter": "Counter: 1"},
            }
        })

renderer._on_action = on_action

# Render initial UI
renderer.render_json(a2ui_json, initial_data={"/counter": "Counter: 0"})

# Wrap surface in A2UIComponent for auto-update
surface = renderer.get_surface("default")
component = A2UIComponent(surface)

App(Frame("App", 800, 600), component).run()
```

### TextField usageHint

TextField supports special input types via `usageHint`:

```python
# Password field (masked input ●●●●)
{"id": "password", "component": "TextField",
 "text": {"literalString": ""},
 "usageHint": "password"}

# Multiline field (uses MultilineInput)
{"id": "comments", "component": "TextField",
 "text": {"literalString": ""},
 "usageHint": "multiline"}

# Other hints (text, email, number, phone, url) use standard Input
{"id": "email", "component": "TextField",
 "text": {"literalString": ""},
 "usageHint": "email"}
```

## Chat Components

For building custom chat UIs, Castella provides lower-level components.

### ChatMessage

```python
from castella.agent import ChatMessage

# Create message widget
widget = ChatMessage(
    role="assistant",
    content="Hello! How can I help you?",
)

# With optional parameters
widget = ChatMessage(
    role="assistant",
    content="Hello!",
    show_timestamp=True,
    show_role_label=True,
)
```

### ChatInput

```python
from castella.agent import ChatInput

def handle_send(text: str):
    print(f"User sent: {text}")

# Basic usage
input_widget = ChatInput(on_submit=handle_send)

# With all options
input_widget = ChatInput(
    on_submit=handle_send,
    placeholder="Type a message...",
    send_label="Send",
    min_height=40,
    max_height=120,
)
```

### ChatView

```python
from castella.agent import ChatView, ChatMessageData
from castella.core import ListState

messages = ListState([
    ChatMessageData(role="system", content="Welcome!"),
])

# Basic usage
view = ChatView(messages)

# With all options
view = ChatView(
    messages,
    show_timestamps=False,
    auto_scroll=True,
)
```

### ChatContainer

A complete chat UI combining ChatView and ChatInput:

```python
from castella.agent import ChatContainer, ChatMessageData
from castella.core import ListState

messages = ListState([
    ChatMessageData(role="system", content="Welcome!"),
])

def on_send(text: str):
    messages.append(ChatMessageData(role="user", content=text))
    # Get response from agent...
    messages.append(ChatMessageData(role="assistant", content="Hello!"))

chat = ChatContainer(messages, on_send=on_send, title="Chat")
```

## Tool Call Visualization

Display tool/function calls from AI agents:

```python
from castella.agent import ToolCallView, ToolCallData

# Create tool call data
tool = ToolCallData(
    id="call_123",
    name="get_weather",
    arguments={"location": "Tokyo"},
    result="Sunny, 22C",
)

# Display tool call (collapsible)
view = ToolCallView(
    name=tool.name,
    arguments=tool.arguments,
    result=tool.result,
)
```

### Tool History Panel

```python
from castella.agent import ToolHistoryPanel
from castella.core import ListState

tool_calls = ListState([
    ToolCallData(id="1", name="search", arguments={"q": "Python"}, result="..."),
    ToolCallData(id="2", name="calculate", arguments={"expr": "2+2"}, result="4"),
])

panel = ToolHistoryPanel(tool_calls)
```

## Creating an A2A Server

Use `python-a2a` directly to create A2A-compatible servers:

```python
from python_a2a import A2AServer, skill, run_server, TaskState, TaskStatus

class WeatherAgent(A2AServer):
    @skill(name="get_weather", description="Get current weather")
    def get_weather(self, location: str) -> str:
        return f"Weather in {location}: Sunny, 22C"

    def handle_task(self, task):
        # Extract message from task
        message = task.message["parts"][0]["text"]

        # Route to appropriate skill
        response = self.get_weather("Tokyo")

        # Return response
        task.artifacts = [{"parts": [{"type": "text", "text": response}]}]
        task.status = TaskStatus(state=TaskState.COMPLETED)
        return task

agent = WeatherAgent(
    name="Weather Agent",
    description="Provides weather information",
    version="1.0.0",
    url="http://localhost:8080",
)
run_server(agent, port=8080)
```

## Examples

See the examples directory for working demos:

- `examples/agent_chat_demo.py` - Basic chat demo with custom responses
- `examples/agent_chat_a2a_demo.py` - A2A agent connection demo
- `examples/a2ui_demo.py` - A2UI rendering examples (all components)
- `examples/a2ui_streaming_demo.py` - A2UI streaming/progressive rendering demo
- `examples/a2ui_mock_server.py` - Mock A2UI server with SSE streaming
- `examples/a2ui_sse_client_demo.py` - SSE client that connects to A2UI server
- `examples/a2a_demo.py` - A2A client/server demo
- `examples/a2ui_mock_test.py` - Mock tests for all A2UI components
- `examples/a2ui_google_agent_demo.py` - Connect to Google's A2UI sample agents

### Testing with Google's Sample Agents

Castella has been tested with Google's official A2UI sample agents:

```bash
# Clone Google's A2UI repository
git clone https://github.com/google/A2UI /tmp/a2ui

# Run the restaurant_finder agent (requires GEMINI_API_KEY)
cd /tmp/a2ui/samples/agent/adk/restaurant_finder
export GEMINI_API_KEY="your-key"
uv run .

# In another terminal, connect with Castella
uv run python examples/a2ui_google_agent_demo.py
```

Mock tests are available for all components:

```bash
uv run python examples/a2ui_mock_test.py restaurant  # Restaurant list with images
uv run python examples/a2ui_mock_test.py form        # Form with TextField, DateTimeInput
uv run python examples/a2ui_mock_test.py tabs        # Tabs navigation
uv run python examples/a2ui_mock_test.py icon        # Icon component (emoji mapping)
uv run python examples/a2ui_mock_test.py modal       # Modal dialog
uv run python examples/a2ui_mock_test.py choice      # ChoicePicker (radio/checkbox)
```

## References

- [A2A Protocol](https://a2a-protocol.org/) - Google's Agent-to-Agent protocol
- [A2UI Specification](https://a2ui.org/specification/v0.9-a2ui/) - Agent-to-User Interface specification
- [python-a2a](https://github.com/themanojdesai/python-a2a) - Python A2A library
