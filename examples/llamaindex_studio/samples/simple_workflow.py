"""Simple LlamaIndex Workflow example.

A basic workflow demonstrating the event-driven pattern.
"""

from llama_index.core.workflow import (
    Workflow,
    Event,
    StartEvent,
    StopEvent,
    step,
)


class ProcessedEvent(Event):
    """Event emitted after processing."""

    text: str


class ValidatedEvent(Event):
    """Event emitted after validation."""

    text: str
    is_valid: bool


class SimpleWorkflow(Workflow):
    """A simple workflow with two steps.

    Flow: StartEvent -> process -> ProcessedEvent -> validate -> StopEvent
    """

    @step
    async def process(self, ev: StartEvent) -> ProcessedEvent:
        """Process the input text.

        Takes the input and transforms it.
        """
        text = ev.get("text", "Hello World")
        processed = text.upper()
        return ProcessedEvent(text=processed)

    @step
    async def validate(self, ev: ProcessedEvent) -> StopEvent:
        """Validate the processed text.

        Checks if the text meets validation criteria.
        """
        is_valid = len(ev.text) > 0
        return StopEvent(result={"text": ev.text, "valid": is_valid})
