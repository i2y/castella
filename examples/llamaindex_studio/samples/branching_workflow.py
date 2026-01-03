"""Branching LlamaIndex Workflow example.

Demonstrates Union output pattern (one of multiple possible events).
"""

from llama_index.core.workflow import (
    Workflow,
    Event,
    StartEvent,
    StopEvent,
    step,
)


class AnalyzedEvent(Event):
    """Event after text analysis."""

    text: str
    sentiment: str


class PositiveEvent(Event):
    """Event for positive sentiment."""

    text: str


class NegativeEvent(Event):
    """Event for negative sentiment."""

    text: str


class BranchingWorkflow(Workflow):
    """A workflow with branching based on sentiment.

    Demonstrates the Union output pattern.
    """

    @step
    async def analyze(self, ev: StartEvent) -> AnalyzedEvent:
        """Analyze the input text sentiment."""
        text = ev.get("text", "I love this!")

        # Simple sentiment detection
        positive_words = ["love", "great", "awesome", "happy", "good"]
        negative_words = ["hate", "bad", "terrible", "sad", "awful"]

        text_lower = text.lower()
        sentiment = "neutral"

        if any(word in text_lower for word in positive_words):
            sentiment = "positive"
        elif any(word in text_lower for word in negative_words):
            sentiment = "negative"

        return AnalyzedEvent(text=text, sentiment=sentiment)

    @step
    async def route(self, ev: AnalyzedEvent) -> PositiveEvent | NegativeEvent:
        """Route based on sentiment (Union output pattern)."""
        if ev.sentiment == "positive":
            return PositiveEvent(text=ev.text)
        else:
            return NegativeEvent(text=ev.text)

    @step
    async def handle_positive(self, ev: PositiveEvent) -> StopEvent:
        """Handle positive sentiment."""
        return StopEvent(result={"text": ev.text, "response": "Glad to hear!"})

    @step
    async def handle_negative(self, ev: NegativeEvent) -> StopEvent:
        """Handle negative sentiment."""
        return StopEvent(result={"text": ev.text, "response": "Sorry to hear that."})
