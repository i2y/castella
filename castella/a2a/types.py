"""A2A type definitions for Castella.

This module defines data models for A2A protocol concepts,
providing a clean interface for working with A2A agents.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class TaskState(str, Enum):
    """Task execution states."""

    PENDING = "pending"
    WORKING = "working"
    INPUT_REQUIRED = "input_required"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AgentSkill(BaseModel):
    """Represents a skill that an agent can perform.

    Skills are advertised in the Agent Card and describe
    the capabilities of an agent.
    """

    id: str = ""
    name: str
    description: str = ""
    tags: list[str] = Field(default_factory=list)
    examples: list[str] = Field(default_factory=list)
    input_modes: list[str] = Field(default_factory=lambda: ["text/plain"])
    output_modes: list[str] = Field(default_factory=lambda: ["text/plain"])

    model_config = ConfigDict(populate_by_name=True)


class AgentCapabilities(BaseModel):
    """Agent capabilities configuration."""

    streaming: bool = False
    push_notifications: bool = Field(default=False, alias="pushNotifications")
    state_transition_history: bool = Field(
        default=False, alias="stateTransitionHistory"
    )

    model_config = ConfigDict(populate_by_name=True)


class AgentCard(BaseModel):
    """Represents an A2A Agent Card.

    The Agent Card is a JSON document that describes an agent's
    identity, capabilities, and how to connect to it.
    It is published at /.well-known/agent.json
    """

    name: str
    description: str = ""
    version: str = "1.0.0"
    url: str = ""
    capabilities: AgentCapabilities = Field(default_factory=AgentCapabilities)
    default_input_modes: list[str] = Field(
        default_factory=lambda: ["text/plain"], alias="defaultInputModes"
    )
    default_output_modes: list[str] = Field(
        default_factory=lambda: ["text/plain"], alias="defaultOutputModes"
    )
    skills: list[AgentSkill] = Field(default_factory=list)

    model_config = ConfigDict(populate_by_name=True)

    @classmethod
    def from_python_a2a(cls, card: Any) -> "AgentCard":
        """Create an AgentCard from a python-a2a AgentCard object."""
        skills = []
        if hasattr(card, "skills") and card.skills:
            for s in card.skills:
                skill = AgentSkill(
                    id=getattr(s, "id", "") or "",
                    name=getattr(s, "name", "") or "",
                    description=getattr(s, "description", "") or "",
                    tags=getattr(s, "tags", []) or [],
                    examples=getattr(s, "examples", []) or [],
                )
                skills.append(skill)

        capabilities = AgentCapabilities()
        if hasattr(card, "capabilities") and card.capabilities:
            cap = card.capabilities
            capabilities = AgentCapabilities(
                streaming=getattr(cap, "streaming", False) or False,
                pushNotifications=getattr(cap, "push_notifications", False) or False,
                stateTransitionHistory=getattr(cap, "state_transition_history", False)
                or False,
            )

        return cls(
            name=getattr(card, "name", "") or "",
            description=getattr(card, "description", "") or "",
            version=getattr(card, "version", "1.0.0") or "1.0.0",
            url=getattr(card, "url", "") or "",
            capabilities=capabilities,
            skills=skills,
        )


class MessageRole(str, Enum):
    """Message role in a conversation."""

    USER = "user"
    AGENT = "agent"
    SYSTEM = "system"


class Message(BaseModel):
    """A message in an A2A conversation."""

    role: MessageRole = MessageRole.USER
    content: str = ""
    timestamp: str | None = None

    model_config = ConfigDict(populate_by_name=True)


class TaskStatus(BaseModel):
    """Status of a task execution."""

    state: TaskState = TaskState.PENDING
    message: Message | None = None
    progress: float | None = None  # 0.0 to 1.0

    model_config = ConfigDict(populate_by_name=True)


class TaskResult(BaseModel):
    """Result of a completed task."""

    success: bool = True
    content: str = ""
    artifacts: list[dict[str, Any]] = Field(default_factory=list)
    error: str | None = None

    model_config = ConfigDict(populate_by_name=True)
