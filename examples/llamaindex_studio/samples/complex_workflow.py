"""Complex LlamaIndex Workflow example.

A multi-step workflow demonstrating branching, parallel processing,
and aggregation patterns.
"""

from llama_index.core.workflow import (
    Workflow,
    Event,
    StartEvent,
    StopEvent,
    step,
)


# ========== Custom Events ==========

class ParsedEvent(Event):
    """Event emitted after parsing input."""
    text: str
    word_count: int


class AnalyzedEvent(Event):
    """Event emitted after text analysis."""
    text: str
    sentiment: str
    keywords: list[str]


class EnrichedEvent(Event):
    """Event emitted after enrichment."""
    text: str
    enriched_data: dict


class SummarizedEvent(Event):
    """Event emitted after summarization."""
    text: str
    summary: str


class FinalResultEvent(Event):
    """Event emitted with aggregated results."""
    original_text: str
    analysis: dict
    summary: str


# ========== Workflow Definition ==========

class ComplexWorkflow(Workflow):
    """A complex workflow with multiple processing steps.

    Flow:
        StartEvent
            │
            ▼
        ┌──────────┐
        │  parse   │
        └──────────┘
            │
            ▼
        ParsedEvent
           ╱   ╲
          ▼     ▼
    ┌─────────┐ ┌─────────┐
    │ analyze │ │ enrich  │
    └─────────┘ └─────────┘
          │           │
          ▼           ▼
    AnalyzedEvent  EnrichedEvent
           ╲       ╱
            ▼     ▼
         ┌───────────┐
         │ summarize │
         └───────────┘
               │
               ▼
         SummarizedEvent
               │
               ▼
         ┌───────────┐
         │ aggregate │
         └───────────┘
               │
               ▼
           StopEvent
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Store intermediate results for aggregation
        self._analysis_result: dict | None = None
        self._enriched_result: dict | None = None

    @step
    async def parse(self, ev: StartEvent) -> ParsedEvent:
        """Parse and validate input text.

        Takes raw input and performs initial parsing.
        """
        text = ev.get("text", "Hello, this is a sample text for workflow testing.")
        words = text.split()
        return ParsedEvent(text=text, word_count=len(words))

    @step
    async def analyze(self, ev: ParsedEvent) -> AnalyzedEvent:
        """Analyze text for sentiment and keywords.

        Performs NLP-style analysis on the text.
        """
        text = ev.text

        # Simple mock sentiment analysis
        positive_words = {"good", "great", "excellent", "happy", "love"}
        negative_words = {"bad", "terrible", "sad", "hate", "awful"}

        words_lower = set(text.lower().split())
        pos_count = len(words_lower & positive_words)
        neg_count = len(words_lower & negative_words)

        if pos_count > neg_count:
            sentiment = "positive"
        elif neg_count > pos_count:
            sentiment = "negative"
        else:
            sentiment = "neutral"

        # Extract "keywords" (just longer words for demo)
        keywords = [w for w in text.split() if len(w) > 5][:5]

        return AnalyzedEvent(text=text, sentiment=sentiment, keywords=keywords)

    @step
    async def enrich(self, ev: ParsedEvent) -> EnrichedEvent:
        """Enrich text with additional metadata.

        Adds computed metadata to the text.
        """
        text = ev.text
        enriched_data = {
            "word_count": ev.word_count,
            "char_count": len(text),
            "avg_word_length": len(text.replace(" ", "")) / max(1, ev.word_count),
            "has_punctuation": any(c in text for c in ".,!?;:"),
        }
        return EnrichedEvent(text=text, enriched_data=enriched_data)

    @step
    async def summarize(
        self, ev: AnalyzedEvent | EnrichedEvent
    ) -> SummarizedEvent | None:
        """Create a summary combining analysis and enrichment.

        Waits for both analyze and enrich results.
        """
        # Collect results
        if isinstance(ev, AnalyzedEvent):
            self._analysis_result = {
                "sentiment": ev.sentiment,
                "keywords": ev.keywords,
            }
        elif isinstance(ev, EnrichedEvent):
            self._enriched_result = ev.enriched_data

        # Wait for both results
        if self._analysis_result is None or self._enriched_result is None:
            return None

        # Create summary
        analysis = self._analysis_result
        enriched = self._enriched_result

        summary = (
            f"Text has {enriched['word_count']} words, "
            f"{enriched['char_count']} chars. "
            f"Sentiment: {analysis['sentiment']}. "
            f"Key terms: {', '.join(analysis['keywords'][:3]) or 'none'}."
        )

        return SummarizedEvent(text=ev.text, summary=summary)

    @step
    async def aggregate(self, ev: SummarizedEvent) -> StopEvent:
        """Aggregate all results into final output.

        Combines all processing results.
        """
        result = {
            "original_text": ev.text,
            "summary": ev.summary,
            "analysis": self._analysis_result,
            "enrichment": self._enriched_result,
            "status": "completed",
        }
        return StopEvent(result=result)
