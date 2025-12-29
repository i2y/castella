"""A2A (Agent-to-Agent) protocol support for Castella.

This module provides integration with the A2A protocol, enabling Castella
applications to communicate with AI agents and expose themselves as A2A
agents.

A2A is an open protocol by Google that enables communication between
AI agents from different vendors and frameworks.

Example:
    # Connect to an A2A agent
    from castella.a2a import A2AClient

    client = A2AClient("http://agent.example.com")
    print(f"Connected to: {client.name}")
    response = client.ask("What's the weather?")

    # Create an A2A server
    from castella.a2a import A2AServer, skill

    class MyAgent(A2AServer):
        @skill(name="greet", description="Greet the user")
        def greet(self, name: str) -> str:
            return f"Hello, {name}!"

    server = MyAgent(name="Greeter", description="A friendly greeter")
    server.run(port=8080)

Reference:
    - A2A Protocol: https://a2a-protocol.org/
    - python-a2a: https://github.com/themanojdesai/python-a2a
"""

from castella.a2a.client import A2AClient
from castella.a2a.server import A2AServer, skill
from castella.a2a.types import AgentCard, AgentSkill, Message, TaskStatus, TaskState

__all__ = [
    # Client
    "A2AClient",
    # Server
    "A2AServer",
    "skill",
    # Types
    "AgentCard",
    "AgentSkill",
    "Message",
    "TaskStatus",
    "TaskState",
]
