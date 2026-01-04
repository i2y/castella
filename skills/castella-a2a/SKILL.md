---
name: castella-a2a
description: Connect to A2A protocol agents from Castella. Communicate with agents, display agent cards, send messages, handle responses, and stream results.
---

# Castella A2A Protocol Integration

A2A (Agent-to-Agent) is an open protocol for AI agent communication and discovery. Castella provides a client for connecting to A2A agents and displaying their information.

**When to use**: "connect to A2A agent", "A2AClient", "agent card", "send message to agent", "list agent skills", "A2A protocol", "stream agent response"

## Quick Start

Connect to an A2A agent:

```python
from castella.a2a import A2AClient

client = A2AClient("http://agent.example.com")
print(f"Connected to: {client.name}")
print(f"Skills: {[s.name for s in client.skills]}")

response = client.ask("What's the weather in Tokyo?")
print(response)
```

## Installation

```bash
uv sync --extra agent   # A2A + A2UI support
```

## A2AClient

The main class for A2A communication:

```python
from castella.a2a import A2AClient

client = A2AClient(
    agent_url="http://localhost:8080",
    timeout=30.0,
)
```

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `name` | str | Agent name |
| `description` | str | Agent description |
| `version` | str | Agent version |
| `skills` | list[AgentSkill] | Available skills |
| `is_connected` | bool | Connection status |
| `supports_streaming` | bool | Streaming capability |
| `agent_card` | AgentCard | Full agent metadata |

### Methods

```python
# Synchronous ask
response = client.ask("Hello!")

# Asynchronous ask
response = await client.ask_async("Hello!")

# Streaming (async)
async for chunk in client.ask_stream("Tell me a story"):
    print(chunk, end="", flush=True)

# Send structured message
from castella.a2a import Message
response = client.send_message(Message(role="user", content="Hello"))

# Check skills
if client.has_skill("get_weather"):
    skill = client.get_skill("get_weather")
    print(f"Skill: {skill.name} - {skill.description}")
```

## Agent Card

Access agent metadata via the agent card:

```python
from castella.a2a import A2AClient

client = A2AClient("http://agent.example.com")
card = client.agent_card

print(f"Name: {card.name}")
print(f"Description: {card.description}")
print(f"Version: {card.version}")
print(f"URL: {card.url}")

# List skills
for skill in card.skills:
    print(f"  - {skill.name}: {skill.description}")
    print(f"    Tags: {skill.tags}")
```

## AgentSkill

Skills define agent capabilities:

```python
skill = client.get_skill("get_weather")

print(skill.name)          # "get_weather"
print(skill.description)   # "Get current weather"
print(skill.tags)          # ["weather", "api"]
print(skill.examples)      # ["What's the weather in Tokyo?"]
```

## Error Handling

```python
from castella.a2a import A2AClient, A2AConnectionError, A2AResponseError

try:
    client = A2AClient("http://agent.example.com")
    response = client.ask("Hello")
except A2AConnectionError as e:
    print(f"Connection failed: {e}")
except A2AResponseError as e:
    print(f"Agent error: {e}")
```

## Streaming Responses

For long-running responses:

```python
async def stream_story():
    client = A2AClient("http://agent.example.com")

    if client.supports_streaming:
        async for chunk in client.ask_stream("Tell me a story"):
            print(chunk, end="", flush=True)
    else:
        # Fallback to non-streaming
        response = await client.ask_async("Tell me a story")
        print(response)
```

## AgentCardView Widget

Display agent card in Castella UI:

```python
from castella import App, Column
from castella.agent import AgentCardView
from castella.a2a import A2AClient
from castella.frame import Frame

client = A2AClient("http://agent.example.com")

card_view = AgentCardView(
    client.agent_card,
    show_skills=True,
    compact=False,
)

App(Frame("Agent Info", 400, 300), card_view).run()
```

## Integration with AgentChat

Use A2AClient with high-level chat components:

```python
from castella.agent import AgentChat

# Automatic connection and chat UI
chat = AgentChat.from_a2a("http://localhost:8080")
chat.run()
```

See the `castella-agent-ui` skill for more chat options.

## Creating A2A Servers

For creating A2A servers, use python-a2a directly:

```python
from python_a2a import A2AServer, skill, run_server

class WeatherAgent(A2AServer):
    @skill(name="get_weather", description="Get current weather")
    def get_weather(self, location: str) -> str:
        return f"Weather in {location}: Sunny, 22°C"

agent = WeatherAgent(
    name="Weather Agent",
    description="Provides weather information",
    version="1.0.0",
    url="http://localhost:8080",
)

run_server(agent, port=8080)
```

## Best Practices

1. **Check capabilities** before using features:
   ```python
   if client.supports_streaming:
       async for chunk in client.ask_stream(msg):
           ...
   ```

2. **Handle errors gracefully**:
   ```python
   try:
       response = client.ask(msg)
   except A2AConnectionError:
       # Retry or show offline message
   ```

3. **Use async for UI responsiveness**:
   ```python
   response = await client.ask_async(msg)
   ```

4. **Inspect skills for routing**:
   ```python
   if client.has_skill("search"):
       # Route search queries to this agent
   ```

## Reference

- `references/types.md` - AgentCard, AgentSkill, Message types
- `references/streaming.md` - Streaming response handling
- `scripts/` - Executable examples (a2a_connect.py, a2a_async.py)
- A2A Protocol: https://a2a-protocol.org/
- python-a2a: https://github.com/themanojdesai/python-a2a
