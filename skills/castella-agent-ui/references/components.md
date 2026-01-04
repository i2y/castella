# Agent UI Components Reference

Complete API reference for Castella agent UI components.

## AgentChat

High-level chat component.

### Constructor

```python
from castella.agent import AgentChat

chat = AgentChat(
    a2a_client: A2AClient = None,     # A2A client
    handler: Callable[[str], str] = None,  # Custom handler
    title: str = "Agent Chat",        # Window title
    placeholder: str = "Type a message...",
    system_message: str = None,       # Initial message
    show_agent_card: bool = True,     # Show agent info
    width: int = 700,
    height: int = 550,
)
```

### Factory Methods

```python
# From URL
AgentChat.from_a2a(url: str) -> AgentChat

# From client
AgentChat.from_a2a(client: A2AClient) -> AgentChat
```

### Methods

```python
chat.run()  # Run the chat app (blocking)
```

## ChatContainer

Embeddable chat container.

### Constructor

```python
from castella.agent import ChatContainer
from castella.core import ListState

messages = ListState([ChatMessageData(...)])

container = ChatContainer(
    messages: ListState[ChatMessageData],
    on_send: Callable[[str], None],
    title: str = "Chat",
    placeholder: str = "Type a message...",
    show_header: bool = True,
)
```

### Properties

```python
container.messages   # ListState of messages
container.on_send    # Send callback
```

## ChatView

Scrollable message list.

### Constructor

```python
from castella.agent import ChatView

view = ChatView(
    messages: ListState[ChatMessageData],
    scroll_state: ScrollState = None,
)
```

## ChatMessage

Single message display.

### Constructor

```python
from castella.agent import ChatMessage

message = ChatMessage(
    data: ChatMessageData,
    compact: bool = False,
)
```

## ChatInput

Input field with send button.

### Constructor

```python
from castella.agent import ChatInput

input_widget = ChatInput(
    placeholder: str = "Type a message...",
    on_send: Callable[[str], None] = None,
)
```

## ToolCallView

Tool call display.

### Constructor

```python
from castella.agent import ToolCallView

tool = ToolCallView(
    name: str,
    arguments: dict,
    result: str = None,
    is_error: bool = False,
    compact: bool = False,
)
```

## ToolHistoryPanel

Tool call history.

### Constructor

```python
from castella.agent import ToolHistoryPanel

panel = ToolHistoryPanel(
    tool_calls: ListState[ToolCallData],
    title: str = "Tool Calls",
)
```

## AgentCardView

Agent information display.

### Constructor

```python
from castella.agent import AgentCardView

card_view = AgentCardView(
    agent_card: AgentCard,
    show_skills: bool = True,
    compact: bool = False,
    on_click: Callable[[AgentCard], None] = None,
)
```

## AgentListView

List of agents.

### Constructor

```python
from castella.agent import AgentListView

agent_list = AgentListView(
    agents: list[AgentCard],
    on_select: Callable[[AgentCard], None] = None,
    selected_index: int = -1,
)
```

### Methods

```python
agent_list.set_agents(agents: list[AgentCard])
agent_list.select(index: int)
```

## MultiAgentChat

Multi-agent tabbed chat.

### Constructor

```python
from castella.agent import MultiAgentChat

chat = MultiAgentChat(
    agents: dict[str, A2AClient],
    title: str = "Multi-Agent Chat",
    width: int = 800,
    height: int = 600,
)
```

### Methods

```python
chat.run()  # Run the app (blocking)
```

## AgentHub

Agent discovery dashboard.

### Constructor

```python
from castella.agent import AgentHub

hub = AgentHub(
    title: str = "Agent Hub",
    agents: list[A2AClient] = None,
    width: int = 1000,
    height: int = 700,
)
```

### Methods

```python
hub.add_agent(url_or_client: str | A2AClient)
hub.remove_agent(index: int)
hub.run()  # Run the app (blocking)
```

## Styling

### Message Colors

```python
# Default colors by role
"user": "#1e40af"      # Blue
"assistant": "#1a1b26" # Dark
"system": "#374151"    # Gray
```

### Custom Styling

```python
# Access underlying widgets for styling
message_widget = ChatMessage(data)
styled = message_widget.bg_color("#custom").padding(10)
```

## Event Callbacks

### on_send

Called when user sends a message:

```python
def on_send(text: str):
    print(f"User sent: {text}")
    # Return response or update messages
```

### on_select

Called when agent is selected (AgentListView):

```python
def on_select(card: AgentCard):
    print(f"Selected: {card.name}")
```

### on_click

Called when agent card is clicked:

```python
def on_click(card: AgentCard):
    open_chat_with(card)
```
