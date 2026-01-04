---
name: castella-agent-ui
description: Build chat interfaces and agent management UIs with Castella. Create chat components, display tool calls, manage multiple agents, and build agent hubs.
---

# Castella Agent UI Components

High-level components for building conversational interfaces and agent management UIs.

**When to use**: "create a chat UI", "AgentChat", "chat with agent", "display tool calls", "multi-agent chat", "AgentHub", "message history", "MultiAgentChat"

## Quick Start (3 Lines)

Create a chat UI connected to an A2A agent:

```python
from castella.agent import AgentChat

chat = AgentChat.from_a2a("http://localhost:8080")
chat.run()
```

## Installation

```bash
uv sync --extra agent   # Agent UI + A2A + A2UI support
```

## AgentChat

High-level chat component with minimal setup:

```python
from castella.agent import AgentChat

# Connect to A2A agent
chat = AgentChat.from_a2a("http://localhost:8080")
chat.run()

# Or use custom handler function
chat = AgentChat(
    handler=lambda msg: f"Echo: {msg}",
    title="Echo Bot",
    system_message="Welcome! How can I help?",
)
chat.run()
```

### Parameters

```python
AgentChat(
    a2a_client=None,           # A2AClient instance
    handler=None,              # Custom handler: (str) -> str
    title="Agent Chat",        # Window title
    placeholder="Type...",     # Input placeholder
    system_message=None,       # Initial system message
    show_agent_card=True,      # Show agent card for A2A
    width=700,                 # Window width
    height=550,                # Window height
)
```

### Factory Methods

```python
# From A2A agent URL
chat = AgentChat.from_a2a("http://localhost:8080")

# From A2A client
from castella.a2a import A2AClient
client = A2AClient("http://localhost:8080")
chat = AgentChat.from_a2a(client)
```

## Chat Components

Build custom chat UIs with lower-level components.

### ChatContainer

Complete chat UI (messages + input):

```python
from castella.agent import ChatContainer, ChatMessageData
from castella.core import ListState

messages = ListState([])

def on_send(text: str):
    messages.append(ChatMessageData(role="user", content=text))
    # Get response from agent...
    response = get_response(text)
    messages.append(ChatMessageData(role="assistant", content=response))

container = ChatContainer(
    messages,
    on_send=on_send,
    title="My Chat",
    placeholder="Type a message...",
)
```

### ChatMessage

Display a single message:

```python
from castella.agent import ChatMessage, ChatMessageData

msg = ChatMessageData(
    role="assistant",  # "user", "assistant", or "system"
    content="Hello! How can I help you today?",
)
widget = ChatMessage(msg)
```

### ChatInput

Text input with send button:

```python
from castella.agent import ChatInput

input_widget = ChatInput(
    placeholder="Type a message...",
    on_send=lambda text: print(f"Sent: {text}"),
)
```

### ChatView

Scrollable message list:

```python
from castella.agent import ChatView
from castella.core import ScrollState

scroll_state = ScrollState()
view = ChatView(messages, scroll_state=scroll_state)
```

## ChatMessageData

Message data structure:

```python
from castella.agent import ChatMessageData, ToolCallData

msg = ChatMessageData(
    role="assistant",
    content="Let me check the weather for you.",
    tool_calls=[
        ToolCallData(
            id="call_1",
            name="get_weather",
            arguments={"location": "Tokyo"},
            result="Sunny, 22°C",
        )
    ],
)
```

## Tool Call Visualization

### ToolCallView

Display a single tool call:

```python
from castella.agent import ToolCallView

tool = ToolCallView(
    name="get_weather",
    arguments={"location": "Tokyo"},
    result="Sunny, 22°C",
)
```

### ToolHistoryPanel

Display history of tool calls:

```python
from castella.agent import ToolHistoryPanel
from castella.core import ListState

tool_calls = ListState([...])
panel = ToolHistoryPanel(tool_calls)
```

## Agent Card Display

### AgentCardView

Show agent information:

```python
from castella.agent import AgentCardView
from castella.a2a import A2AClient

client = A2AClient("http://agent.example.com")
card_view = AgentCardView(
    client.agent_card,
    show_skills=True,
    compact=False,
)
```

### AgentListView

Display multiple agents:

```python
from castella.agent import AgentListView

agent_list = AgentListView(
    agents=[client1.agent_card, client2.agent_card],
    on_select=lambda card: print(f"Selected: {card.name}"),
)
```

## MultiAgentChat

Tabbed interface for multiple agents:

```python
from castella.agent import MultiAgentChat
from castella.a2a import A2AClient

chat = MultiAgentChat({
    "weather": A2AClient("http://localhost:8081"),
    "travel": A2AClient("http://localhost:8082"),
    "restaurant": A2AClient("http://localhost:8083"),
})
chat.run()
```

Each agent gets its own chat tab with independent message history.

## AgentHub

Agent discovery and management dashboard:

```python
from castella.agent import AgentHub
from castella.a2a import A2AClient

# Create hub
hub = AgentHub(title="Agent Hub")

# Add agents
hub.add_agent("http://localhost:8081")
hub.add_agent(A2AClient("http://localhost:8082"))

hub.run()
```

Or initialize with agents:

```python
hub = AgentHub(agents=[
    A2AClient("http://agent1.example.com"),
    A2AClient("http://agent2.example.com"),
])
```

Features:
- Left panel: List of agents with add/remove
- Right panel: Chat with selected agent
- URL input to add new agents at runtime

## Scroll Position Pattern

Important pattern for chat UIs - set scroll before adding message:

```python
class ChatComponent(Component):
    def __init__(self):
        super().__init__()
        self._messages = ListState([])
        self._messages.attach(self)
        self._scroll_state = ScrollState()
        # DON'T attach scroll state

    def _send_message(self, text: str):
        # Add user message
        self._messages.append(ChatMessageData(role="user", content=text))

        # Get response...
        response = get_response(text)

        # Set scroll BEFORE adding response (so re-render picks it up)
        self._scroll_state.y = 999999
        self._messages.append(ChatMessageData(role="assistant", content=response))
```

## Lazy State Attachment

For components created before App exists (like AgentHub):

```python
class MyComponent(Component):
    def __init__(self):
        super().__init__()
        self._state = State(0)
        self._states_attached = False
        # DON'T attach here - App may not exist yet

    def view(self):
        # Attach lazily when view() is called
        if not self._states_attached:
            self._state.attach(self)
            self._states_attached = True
        return Text(str(self._state()))
```

## Message Markdown Support

Messages support Markdown formatting:

```python
msg = ChatMessageData(
    role="assistant",
    content="""
# Weather Report

**Tokyo**: Sunny, 22°C

| Day | High | Low |
|-----|------|-----|
| Mon | 24°C | 18°C |
| Tue | 22°C | 17°C |
""",
)
```

## Best Practices

1. **Use ScrollState without attaching** for chat scroll
2. **Set scroll position before adding** new messages
3. **Use Markdown** for rich message content
4. **Handle loading states** for async responses
5. **Use ListState.append()** for new messages
6. **Use lazy state attachment** for hub-style components

## Reference

- `references/components.md` - Component API reference
- `references/data_classes.md` - ChatMessageData, ToolCallData types
- `scripts/` - Executable examples (simple_chat.py, multi_agent.py, agent_hub.py)
