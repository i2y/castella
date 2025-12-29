"""Agent UI components for Castella.

This module provides UI components for building agent-based applications,
including chat interfaces, tool visualization, and agent management.

Example:
    from castella.agent import AgentCardView
    from castella.a2a import A2AClient

    client = A2AClient("http://agent.example.com")
    card_view = AgentCardView(client.agent_card)
    run_app(card_view)
"""

from castella.agent.card_view import AgentCardView, AgentListView

__all__ = [
    "AgentCardView",
    "AgentListView",
]
