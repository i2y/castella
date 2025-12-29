"""A2A Client for Castella.

This module provides a wrapper around python-a2a's A2AClient,
adding Castella-specific integrations and conveniences.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any, AsyncIterator, Callable

from castella.a2a.types import AgentCard, AgentSkill, Message, MessageRole

if TYPE_CHECKING:
    pass


class A2AClientError(Exception):
    """Base exception for A2A client errors."""

    pass


class A2AConnectionError(A2AClientError):
    """Failed to connect to A2A agent."""

    pass


class A2AResponseError(A2AClientError):
    """Error in A2A agent response."""

    pass


class A2AClient:
    """Client for communicating with A2A agents.

    This class wraps python-a2a's A2AClient and provides:
    - Clean access to agent metadata (name, skills, etc.)
    - Async/await support for non-blocking communication
    - Integration with Castella's state management
    - Streaming response support

    Example:
        # Basic usage
        client = A2AClient("http://agent.example.com")
        print(f"Connected to: {client.name}")
        print(f"Skills: {[s.name for s in client.skills]}")

        response = client.ask("What's the weather in Tokyo?")
        print(response)

        # Async usage
        async def main():
            client = A2AClient("http://agent.example.com")
            response = await client.ask_async("Hello!")
            print(response)

        # Streaming
        async for chunk in client.ask_stream("Tell me a story"):
            print(chunk, end="", flush=True)
    """

    def __init__(
        self,
        agent_url: str,
        timeout: float = 30.0,
        on_error: Callable[[Exception], None] | None = None,
    ):
        """Initialize the A2A client.

        Args:
            agent_url: URL of the A2A agent (base URL, not the agent.json path)
            timeout: Request timeout in seconds
            on_error: Optional callback for error handling
        """
        self._agent_url = agent_url.rstrip("/")
        self._timeout = timeout
        self._on_error = on_error
        self._client: Any = None
        self._agent_card: AgentCard | None = None
        self._connected = False

        # Try to connect immediately
        self._connect()

    def _connect(self) -> None:
        """Connect to the A2A agent and fetch the agent card."""
        try:
            from python_a2a import A2AClient as BaseA2AClient

            self._client = BaseA2AClient(self._agent_url)
            if hasattr(self._client, "agent_card") and self._client.agent_card:
                self._agent_card = AgentCard.from_python_a2a(self._client.agent_card)
            else:
                # Create minimal agent card
                self._agent_card = AgentCard(
                    name="Unknown Agent",
                    description="Agent card not available",
                    url=self._agent_url,
                )
            self._connected = True
        except ImportError as e:
            raise A2AClientError(
                "python-a2a is not installed. Install it with: pip install python-a2a"
            ) from e
        except Exception as e:
            self._connected = False
            if self._on_error:
                self._on_error(e)
            raise A2AConnectionError(
                f"Failed to connect to {self._agent_url}: {e}"
            ) from e

    @property
    def is_connected(self) -> bool:
        """Check if connected to the agent."""
        return self._connected

    @property
    def agent_url(self) -> str:
        """Get the agent URL."""
        return self._agent_url

    @property
    def agent_card(self) -> AgentCard:
        """Get the agent card."""
        if self._agent_card is None:
            raise A2AClientError("Not connected to agent")
        return self._agent_card

    @property
    def name(self) -> str:
        """Get the agent name."""
        return self.agent_card.name

    @property
    def description(self) -> str:
        """Get the agent description."""
        return self.agent_card.description

    @property
    def version(self) -> str:
        """Get the agent version."""
        return self.agent_card.version

    @property
    def skills(self) -> list[AgentSkill]:
        """Get the agent's skills."""
        return self.agent_card.skills

    @property
    def supports_streaming(self) -> bool:
        """Check if the agent supports streaming responses."""
        return self.agent_card.capabilities.streaming

    def ask(self, message: str) -> str:
        """Send a message to the agent and get a response.

        Args:
            message: The message to send

        Returns:
            The agent's response as a string

        Raises:
            A2AClientError: If not connected
            A2AResponseError: If the agent returns an error
        """
        if not self._connected or self._client is None:
            raise A2AClientError("Not connected to agent")

        try:
            response = self._client.ask(message)
            return str(response) if response else ""
        except Exception as e:
            if self._on_error:
                self._on_error(e)
            raise A2AResponseError(f"Error from agent: {e}") from e

    async def ask_async(self, message: str) -> str:
        """Send a message asynchronously.

        Args:
            message: The message to send

        Returns:
            The agent's response as a string
        """
        # Run sync ask in thread pool
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.ask, message)

    async def ask_stream(self, message: str) -> AsyncIterator[str]:
        """Send a message and stream the response.

        Args:
            message: The message to send

        Yields:
            Response chunks as they arrive

        Note:
            Falls back to non-streaming if agent doesn't support it.
        """
        if not self.supports_streaming:
            # Fall back to regular ask
            response = await self.ask_async(message)
            yield response
            return

        # TODO: Implement proper streaming when python-a2a supports it
        response = await self.ask_async(message)
        yield response

    def send_message(self, message: Message) -> Message:
        """Send a structured message to the agent.

        Args:
            message: The Message object to send

        Returns:
            The agent's response as a Message
        """
        response_text = self.ask(message.content)
        return Message(
            role=MessageRole.AGENT,
            content=response_text,
        )

    def get_skill(self, skill_name: str) -> AgentSkill | None:
        """Get a skill by name.

        Args:
            skill_name: The name of the skill

        Returns:
            The skill if found, None otherwise
        """
        for skill in self.skills:
            if skill.name == skill_name:
                return skill
        return None

    def has_skill(self, skill_name: str) -> bool:
        """Check if the agent has a specific skill.

        Args:
            skill_name: The name of the skill

        Returns:
            True if the skill exists
        """
        return self.get_skill(skill_name) is not None

    def __repr__(self) -> str:
        status = "connected" if self._connected else "disconnected"
        return f"A2AClient({self._agent_url!r}, status={status})"
