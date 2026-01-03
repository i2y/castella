"""Step models for LlamaIndex Workflow Studio.

These models represent steps (event handlers) in the workflow.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field
from castella.models.geometry import Point, Size


class InputMode(str, Enum):
    """How the step receives input events."""

    SINGLE = "single"      # Single event type: ev: TypeA
    UNION = "union"        # Any of multiple event types (OR): ev: TypeA | TypeB
    COLLECT = "collect"    # All of multiple event types (AND): ev1: TypeA, ev2: TypeB


class OutputMode(str, Enum):
    """How the step emits output events."""

    SINGLE = "single"      # Single event type: -> TypeA
    UNION = "union"        # One of multiple event types (branching): -> TypeA | TypeB


class StepModel(BaseModel):
    """A step (event handler) in the workflow.

    Attributes:
        id: Step name/identifier.
        label: Display label.
        input_events: List of input event type names.
        input_mode: How input events are handled (SINGLE, UNION, COLLECT).
        output_events: List of output event type names.
        output_mode: How output events are handled (SINGLE, UNION).
        position: Layout position (x, y).
        size: Display size (width, height).
        docstring: Step method docstring.
        source_code: Source code of the step method.
        is_active: Whether the step is currently executing.
        execution_count: Number of times the step has been executed.
    """

    id: str
    label: str

    # Input event specification
    input_events: list[str] = Field(default_factory=list)
    input_mode: InputMode = InputMode.SINGLE

    # Output event specification
    output_events: list[str] = Field(default_factory=list)
    output_mode: OutputMode = OutputMode.SINGLE

    # Layout
    position: Point = Field(default_factory=lambda: Point(x=0, y=0))
    size: Size = Field(default_factory=lambda: Size(width=180, height=80))

    # Metadata
    docstring: str | None = None
    source_code: str | None = None

    # Runtime state (updated during execution)
    is_active: bool = False
    execution_count: int = 0

    def get_input_signature(self) -> str:
        """Get the input event signature as a string."""
        if not self.input_events:
            return ""

        if self.input_mode == InputMode.COLLECT:
            # (ev1: TypeA, ev2: TypeB)
            parts = [f"ev{i+1}: {evt}" for i, evt in enumerate(self.input_events)]
            return f"({', '.join(parts)})"
        elif self.input_mode == InputMode.UNION:
            # (ev: TypeA | TypeB)
            return f"(ev: {' | '.join(self.input_events)})"
        else:
            # (ev: TypeA)
            return f"(ev: {self.input_events[0]})" if self.input_events else ""

    def get_output_signature(self) -> str:
        """Get the output event signature as a string."""
        if not self.output_events:
            return "-> None"

        if self.output_mode == OutputMode.UNION:
            # -> TypeA | TypeB
            return f"-> {' | '.join(self.output_events)}"
        else:
            # -> TypeA
            return f"-> {self.output_events[0]}" if self.output_events else "-> None"
