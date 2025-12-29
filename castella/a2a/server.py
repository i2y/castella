"""A2A Server for Castella.

This module provides a wrapper for creating A2A-compliant agent servers,
allowing Castella applications to expose themselves as A2A agents.
"""

from __future__ import annotations

import functools
from typing import TYPE_CHECKING, Any, Callable

from castella.a2a.types import AgentCard, AgentSkill, TaskState

if TYPE_CHECKING:
    pass


class SkillDefinition:
    """Definition of an agent skill."""

    def __init__(
        self,
        name: str,
        description: str = "",
        tags: list[str] | None = None,
        examples: list[str] | None = None,
    ):
        self.name = name
        self.description = description
        self.tags = tags or []
        self.examples = examples or []
        self.handler: Callable[..., Any] | None = None


def skill(
    name: str,
    description: str = "",
    tags: list[str] | None = None,
    examples: list[str] | None = None,
) -> Callable:
    """Decorator to mark a method as an A2A skill.

    Example:
        class MyAgent(A2AServer):
            @skill(name="greet", description="Greet the user")
            def greet(self, name: str) -> str:
                return f"Hello, {name}!"

    Args:
        name: The skill name
        description: Description of what the skill does
        tags: Tags for categorizing the skill
        examples: Example invocations

    Returns:
        Decorator function
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return func(*args, **kwargs)

        # Attach skill metadata to the function
        wrapper._skill_definition = SkillDefinition(  # type: ignore
            name=name,
            description=description,
            tags=tags,
            examples=examples,
        )
        return wrapper

    return decorator


class A2AServer:
    """Base class for A2A agent servers.

    This class provides the foundation for creating A2A-compliant agents
    that can be accessed by other A2A clients.

    Example:
        class WeatherAgent(A2AServer):
            @skill(name="get_weather", description="Get weather for a location")
            def get_weather(self, location: str) -> str:
                return f"Weather in {location}: Sunny, 25°C"

            @skill(name="forecast", description="Get weather forecast")
            def forecast(self, location: str, days: int = 3) -> str:
                return f"{days}-day forecast for {location}: ..."

        # Create and run the agent
        agent = WeatherAgent(
            name="Weather Agent",
            description="Provides weather information",
            version="1.0.0"
        )
        agent.run(port=8080)
    """

    def __init__(
        self,
        name: str,
        description: str = "",
        version: str = "1.0.0",
        streaming: bool = False,
    ):
        """Initialize the A2A server.

        Args:
            name: The agent name
            description: Description of the agent
            version: Agent version
            streaming: Whether to support streaming responses
        """
        self._name = name
        self._description = description
        self._version = version
        self._streaming = streaming
        self._skills: list[SkillDefinition] = []
        self._server: Any = None
        self._port: int = 8080

        # Discover skills from decorated methods
        self._discover_skills()

    def _discover_skills(self) -> None:
        """Discover skills from decorated methods."""
        for attr_name in dir(self):
            if attr_name.startswith("_"):
                continue
            attr = getattr(self, attr_name)
            if callable(attr) and hasattr(attr, "_skill_definition"):
                skill_def: SkillDefinition = attr._skill_definition
                skill_def.handler = attr
                self._skills.append(skill_def)

    @property
    def name(self) -> str:
        """Get the agent name."""
        return self._name

    @property
    def description(self) -> str:
        """Get the agent description."""
        return self._description

    @property
    def version(self) -> str:
        """Get the agent version."""
        return self._version

    @property
    def skills(self) -> list[AgentSkill]:
        """Get the agent's skills as AgentSkill objects."""
        return [
            AgentSkill(
                id=s.name,
                name=s.name,
                description=s.description,
                tags=s.tags,
                examples=s.examples,
            )
            for s in self._skills
        ]

    @property
    def agent_card(self) -> AgentCard:
        """Get the agent card."""
        return AgentCard(
            name=self._name,
            description=self._description,
            version=self._version,
            url=f"http://localhost:{self._port}",
            skills=self.skills,
        )

    def get_skill_handler(self, skill_name: str) -> Callable[..., Any] | None:
        """Get the handler function for a skill.

        Args:
            skill_name: The name of the skill

        Returns:
            The handler function, or None if not found
        """
        for s in self._skills:
            if s.name == skill_name and s.handler:
                return s.handler
        return None

    def handle_message(self, message: str) -> str:
        """Handle an incoming message.

        Override this method to implement custom message handling.
        The default implementation looks for skill keywords in the message.

        Args:
            message: The incoming message

        Returns:
            The response message
        """
        # Default: Try to match message to a skill
        message_lower = message.lower()
        for s in self._skills:
            if s.name.lower() in message_lower and s.handler:
                try:
                    return str(s.handler(message))
                except Exception as e:
                    return f"Error executing skill {s.name}: {e}"

        return f"I'm {self._name}. I have these skills: {[s.name for s in self._skills]}"

    def run(self, host: str = "0.0.0.0", port: int = 8080) -> None:
        """Run the A2A server.

        This starts an HTTP server that exposes the agent via the A2A protocol.

        Args:
            host: The host to bind to
            port: The port to listen on
        """
        self._port = port

        try:
            from python_a2a import A2AServer as BaseA2AServer
            from python_a2a import agent as agent_decorator
            from python_a2a import run_server
            from python_a2a import skill as skill_decorator

            # Create a dynamic subclass with python-a2a decorators
            @agent_decorator(
                name=self._name,
                description=self._description,
                version=self._version,
            )
            class DynamicAgent(BaseA2AServer):
                pass

            # Add skills dynamically
            dynamic_agent = DynamicAgent()

            # Override handle_task to use our handler
            original_handle = self.handle_message

            def handle_task(task: Any) -> Any:
                # Extract message from task
                if hasattr(task, "input") and hasattr(task.input, "parts"):
                    parts = task.input.parts
                    if parts and len(parts) > 0:
                        message = parts[0].text if hasattr(parts[0], "text") else str(parts[0])
                        response = original_handle(message)

                        # Update task with response
                        task.status = type(task.status)(
                            state=TaskState.COMPLETED.value,
                        )
                        task.artifacts = [{"parts": [{"type": "text", "text": response}]}]
                return task

            dynamic_agent.handle_task = handle_task

            print(f"Starting A2A server: {self._name}")
            print(f"Agent Card: http://{host}:{port}/.well-known/agent.json")
            print(f"Skills: {[s.name for s in self._skills]}")

            run_server(dynamic_agent, host=host, port=port)

        except ImportError as e:
            raise ImportError(
                "python-a2a is not installed. "
                "Install it with: pip install python-a2a"
            ) from e

    def run_background(self, host: str = "0.0.0.0", port: int = 8080) -> None:
        """Run the A2A server in a background thread.

        Args:
            host: The host to bind to
            port: The port to listen on
        """
        import threading

        thread = threading.Thread(
            target=self.run,
            args=(host, port),
            daemon=True,
        )
        thread.start()

    def __repr__(self) -> str:
        return f"A2AServer(name={self._name!r}, skills={[s.name for s in self._skills]})"
