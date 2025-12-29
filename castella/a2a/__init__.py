"""A2A (Agent-to-Agent) protocol support for Castella.

This module provides integration with the A2A protocol, enabling Castella
applications to connect to and display information from AI agents.

A2A is an open protocol by Google that enables communication between
AI agents from different vendors and frameworks.

Castella focuses on the UI layer:
- A2AClient: Connect to A2A agents and get typed AgentCard
- AgentCardView: Display agent information in Castella UI
- A2UIRenderer: Render A2UI JSON responses as Castella widgets

For creating A2A servers, use python-a2a directly:
    from python_a2a import A2AServer, skill, run_server

Example:
    # Connect to an A2A agent
    from castella.a2a import A2AClient

    client = A2AClient("http://agent.example.com")
    print(f"Connected to: {client.name}")
    response = client.ask("What's the weather?")

    # Display agent card in UI
    from castella.agent import AgentCardView
    card_view = AgentCardView(client.agent_card)

Reference:
    - A2A Protocol: https://a2a-protocol.org/
    - python-a2a: https://github.com/themanojdesai/python-a2a
"""

from castella.a2a.client import A2AClient
from castella.a2a.types import AgentCard, AgentSkill, Message, TaskState, TaskStatus

__all__ = [
    # Client
    "A2AClient",
    # Types
    "AgentCard",
    "AgentSkill",
    "Message",
    "TaskStatus",
    "TaskState",
]
