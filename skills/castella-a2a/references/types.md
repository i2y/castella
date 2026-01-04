# A2A Type Reference

Data types used in Castella A2A integration.

## AgentCard

Metadata describing an A2A agent.

```python
from castella.a2a import AgentCard

card = client.agent_card

# Properties
card.name           # str - Agent name
card.description    # str - Description
card.version        # str - Version string
card.url            # str - Agent URL
card.skills         # list[AgentSkill] - Available skills
card.capabilities   # dict - Agent capabilities
```

## AgentSkill

Describes a specific capability of an agent.

```python
from castella.a2a import AgentSkill

skill = client.get_skill("get_weather")

# Properties
skill.name          # str - Skill identifier
skill.description   # str - Human-readable description
skill.tags          # list[str] - Categorization tags
skill.examples      # list[str] - Example prompts
skill.input_modes   # list[str] - Supported input modes
skill.output_modes  # list[str] - Supported output modes
```

## TaskState

Enum representing task execution states.

```python
from castella.a2a import TaskState

TaskState.PENDING        # Task created, not started
TaskState.WORKING        # Task in progress
TaskState.INPUT_REQUIRED # Waiting for user input
TaskState.COMPLETED      # Task finished successfully
TaskState.FAILED         # Task failed with error
TaskState.CANCELLED      # Task was cancelled
```

## Message

Structured message for agent communication.

```python
from castella.a2a import Message

# Create message
msg = Message(
    role="user",      # "user", "agent", or "system"
    content="Hello!",
)

# Properties
msg.role      # str - Message sender role
msg.content   # str - Message text content
msg.metadata  # dict - Optional metadata
```

## A2AClient Types

### Constructor

```python
from castella.a2a import A2AClient

client = A2AClient(
    agent_url: str,           # Agent base URL
    timeout: float = 30.0,    # Request timeout in seconds
)
```

### Properties

```python
client.name: str              # Agent name
client.description: str       # Agent description
client.version: str           # Agent version
client.skills: list[AgentSkill]  # Available skills
client.is_connected: bool     # Connection status
client.supports_streaming: bool  # Streaming capability
client.agent_card: AgentCard  # Full metadata
```

### Methods

```python
# Synchronous
def ask(self, message: str) -> str: ...
def send_message(self, message: Message) -> str: ...
def has_skill(self, name: str) -> bool: ...
def get_skill(self, name: str) -> AgentSkill | None: ...

# Asynchronous
async def ask_async(self, message: str) -> str: ...
async def ask_stream(self, message: str) -> AsyncIterator[str]: ...
```

## Exceptions

```python
from castella.a2a import A2AConnectionError, A2AResponseError

# A2AConnectionError
# Raised when connection to agent fails
# - Network unreachable
# - Agent offline
# - Timeout

# A2AResponseError
# Raised when agent returns error
# - Invalid request
# - Internal agent error
# - Task failed
```

## Example: Type Usage

```python
from castella.a2a import A2AClient, AgentCard, AgentSkill, Message, TaskState
from castella.a2a import A2AConnectionError, A2AResponseError

def connect_and_query(url: str, query: str) -> str:
    try:
        client = A2AClient(url)

        # Access card
        card: AgentCard = client.agent_card
        print(f"Agent: {card.name} v{card.version}")

        # Check skill
        skills: list[AgentSkill] = client.skills
        for skill in skills:
            print(f"  Skill: {skill.name}")

        # Send query
        response = client.ask(query)
        return response

    except A2AConnectionError as e:
        return f"Connection error: {e}"
    except A2AResponseError as e:
        return f"Agent error: {e}"
```
