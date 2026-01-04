# Agent UI Data Classes

Data structures for chat messages and tool calls.

## ChatMessageData

Represents a chat message.

```python
from castella.agent import ChatMessageData

msg = ChatMessageData(
    role: str,                    # "user", "assistant", "system"
    content: str,                 # Message text (supports Markdown)
    tool_calls: list[ToolCallData] = None,  # Optional tool calls
    timestamp: datetime = None,   # Message time
    metadata: dict = None,        # Additional data
)
```

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `role` | str | Sender role |
| `content` | str | Message content |
| `tool_calls` | list | Tool call results |
| `timestamp` | datetime | When sent |
| `metadata` | dict | Extra data |

### Example

```python
# Simple message
msg = ChatMessageData(
    role="user",
    content="What's the weather in Tokyo?",
)

# Assistant with tool call
msg = ChatMessageData(
    role="assistant",
    content="Let me check that for you.",
    tool_calls=[
        ToolCallData(
            id="call_abc123",
            name="get_weather",
            arguments={"location": "Tokyo"},
            result="Sunny, 22°C",
        )
    ],
)

# System message
msg = ChatMessageData(
    role="system",
    content="Welcome! I'm your weather assistant.",
)
```

## ToolCallData

Represents a tool/function call.

```python
from castella.agent import ToolCallData

tool = ToolCallData(
    id: str,                      # Unique call ID
    name: str,                    # Tool/function name
    arguments: dict,              # Input arguments
    result: str = None,           # Output result
    is_error: bool = False,       # Error flag
    duration_ms: int = None,      # Execution time
)
```

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `id` | str | Unique identifier |
| `name` | str | Tool name |
| `arguments` | dict | Input parameters |
| `result` | str | Output or error |
| `is_error` | bool | Was error |
| `duration_ms` | int | Execution time |

### Example

```python
# Successful call
tool = ToolCallData(
    id="call_123",
    name="search_web",
    arguments={"query": "Python tutorials"},
    result="Found 10 results...",
    duration_ms=250,
)

# Failed call
tool = ToolCallData(
    id="call_456",
    name="send_email",
    arguments={"to": "invalid"},
    result="Invalid email address",
    is_error=True,
)
```

## Creating Messages from A2A

Convert A2A responses to ChatMessageData:

```python
from castella.agent import ChatMessageData
from castella.a2a import A2AClient

client = A2AClient("http://agent.example.com")
response = client.ask("Hello!")

msg = ChatMessageData(
    role="assistant",
    content=response,
)
```

## Creating Messages with Streaming

Build message incrementally:

```python
async def stream_message(client, query):
    chunks = []

    async for chunk in client.ask_stream(query):
        chunks.append(chunk)
        # Update message in place
        yield ChatMessageData(
            role="assistant",
            content="".join(chunks),
        )
```

## Message History Pattern

```python
from castella.core import ListState
from castella.agent import ChatMessageData

# Create message history
messages = ListState([
    ChatMessageData(role="system", content="Welcome!"),
])

# Add user message
messages.append(ChatMessageData(
    role="user",
    content="Hello!",
))

# Add assistant response
messages.append(ChatMessageData(
    role="assistant",
    content="Hi there! How can I help?",
))
```

## Serialization

Messages serialize to JSON:

```python
import json

msg = ChatMessageData(role="user", content="Hello")

# To dict
msg_dict = {
    "role": msg.role,
    "content": msg.content,
    "tool_calls": [
        {
            "id": tc.id,
            "name": tc.name,
            "arguments": tc.arguments,
            "result": tc.result,
        }
        for tc in (msg.tool_calls or [])
    ],
}

# To JSON
json_str = json.dumps(msg_dict)
```

## Rich Content

Messages support Markdown:

```python
msg = ChatMessageData(
    role="assistant",
    content="""
# Search Results

Found **3** relevant documents:

1. [Python Basics](https://example.com/1)
2. [Advanced Python](https://example.com/2)
3. [Python Best Practices](https://example.com/3)

```python
# Example code
print("Hello, World!")
```

| Feature | Status |
|---------|--------|
| Markdown | ✓ |
| Tables | ✓ |
| Code | ✓ |
""",
)
```
