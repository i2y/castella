"""RAG (Retrieval-Augmented Generation) agent workflow for testing LangGraph Studio.

This is a more complex LangGraph example with:
- Multiple decision points
- Retrieval and reranking nodes
- Answer generation and verification
- A retry loop for re-retrieval

Run with:
    python -m examples.langgraph_studio.samples.rag_agent
"""

from typing import TypedDict, Annotated, Literal
from operator import add


# Define the state
class RAGState(TypedDict):
    """State for the RAG agent."""
    query: str
    documents: Annotated[list[str], add]
    answer: str
    confidence: float
    retries: int
    messages: Annotated[list[str], add]


def query_analyzer(state: RAGState) -> dict:
    """Analyze the query to determine retrieval strategy."""
    query = state.get("query", "")
    return {
        "messages": [f"Analyzed query: {query[:50]}..."],
    }


def retriever(state: RAGState) -> dict:
    """Retrieve relevant documents."""
    retries = state.get("retries", 0)
    return {
        "documents": [f"Document {i+1} (attempt {retries+1})" for i in range(3)],
        "messages": ["Retrieved 3 documents"],
    }


def reranker(state: RAGState) -> dict:
    """Rerank documents by relevance."""
    docs = state.get("documents", [])
    return {
        "documents": list(reversed(docs))[:2],  # Keep top 2
        "messages": [f"Reranked {len(docs)} documents, kept top 2"],
    }


def generator(state: RAGState) -> dict:
    """Generate answer from documents."""
    docs = state.get("documents", [])
    query = state.get("query", "")
    retries = state.get("retries", 0)

    # Simulate varying confidence based on retries
    confidence = 0.5 + (retries * 0.2)
    confidence = min(confidence, 0.95)

    return {
        "answer": f"Answer based on {len(docs)} documents for: {query[:30]}",
        "confidence": confidence,
        "messages": [f"Generated answer with confidence {confidence:.2f}"],
    }


def verifier(state: RAGState) -> dict:
    """Verify the answer quality."""
    _ = state.get("answer", "")  # Access for demo
    confidence = state.get("confidence", 0)
    return {
        "messages": [f"Verified answer (confidence: {confidence:.2f})"],
    }


def should_rerank(state: RAGState) -> Literal["rerank", "generate"]:
    """Decide whether to rerank or go directly to generation."""
    docs = state.get("documents", [])
    if len(docs) > 2:
        return "rerank"
    return "generate"


def is_answer_good(state: RAGState) -> Literal["accept", "retry", "fail"]:
    """Check if answer is good enough or needs retry."""
    confidence = state.get("confidence", 0)
    retries = state.get("retries", 0)

    if confidence >= 0.8:
        return "accept"
    elif retries < 2:
        return "retry"
    else:
        return "fail"


def retry_handler(state: RAGState) -> dict:
    """Handle retry by incrementing counter."""
    retries = state.get("retries", 0)
    return {
        "retries": retries + 1,
        "messages": [f"Retrying (attempt {retries + 2})..."],
        "documents": [],  # Clear for fresh retrieval
    }


def failure_handler(state: RAGState) -> dict:
    """Handle failure case."""
    return {
        "answer": "Unable to generate a confident answer after multiple attempts.",
        "messages": ["Failed to generate satisfactory answer"],
    }


# Build the graph
try:
    from langgraph.graph import StateGraph, START, END

    # Create the graph
    workflow = StateGraph(RAGState)

    # Add nodes
    workflow.add_node("analyze", query_analyzer)
    workflow.add_node("retrieve", retriever)
    workflow.add_node("rerank", reranker)
    workflow.add_node("generate", generator)
    workflow.add_node("verify", verifier)
    workflow.add_node("retry", retry_handler)
    workflow.add_node("fail", failure_handler)

    # Add edges
    workflow.add_edge(START, "analyze")
    workflow.add_edge("analyze", "retrieve")

    # Conditional: rerank or skip to generate
    workflow.add_conditional_edges(
        "retrieve",
        should_rerank,
        {
            "rerank": "rerank",
            "generate": "generate",
        }
    )
    workflow.add_edge("rerank", "generate")
    workflow.add_edge("generate", "verify")

    # Conditional: accept, retry, or fail
    workflow.add_conditional_edges(
        "verify",
        is_answer_good,
        {
            "accept": END,
            "retry": "retry",
            "fail": "fail",
        }
    )
    workflow.add_edge("retry", "retrieve")  # Loop back
    workflow.add_edge("fail", END)

    # Compile the graph
    graph = workflow.compile()

except ImportError:
    # LangGraph not installed - create a mock for testing
    print("Warning: LangGraph not installed. Using mock graph.")

    class MockGraph:
        """Mock graph for testing without LangGraph installed."""

        def get_graph(self):
            """Return a mock graph structure."""
            return MockDrawableGraph()

        def stream(self, initial_state):
            """Mock streaming execution."""
            # Simulate first pass: analyze -> retrieve -> rerank -> generate -> verify -> retry
            yield {"analyze": {"messages": ["Analyzed query"]}}
            yield {"retrieve": {"documents": ["Doc1", "Doc2", "Doc3"], "messages": ["Retrieved 3 documents"]}}
            yield {"rerank": {"documents": ["Doc3", "Doc1"], "messages": ["Reranked, kept top 2"]}}
            yield {"generate": {"answer": "Initial answer", "confidence": 0.5, "messages": ["Generated with 0.5 confidence"]}}
            yield {"verify": {"messages": ["Verified, needs retry"]}}
            yield {"retry": {"retries": 1, "messages": ["Retrying..."], "documents": []}}

            # Second pass: retrieve -> rerank -> generate -> verify -> accept
            yield {"retrieve": {"documents": ["Doc4", "Doc5", "Doc6"], "messages": ["Retrieved 3 documents"]}}
            yield {"rerank": {"documents": ["Doc5", "Doc4"], "messages": ["Reranked, kept top 2"]}}
            yield {"generate": {"answer": "Better answer", "confidence": 0.85, "messages": ["Generated with 0.85 confidence"]}}
            yield {"verify": {"messages": ["Verified, accepted"]}}

        def invoke(self, initial_state):
            """Mock invocation."""
            return {
                "query": initial_state.get("query", ""),
                "answer": "Final answer",
                "confidence": 0.85,
                "messages": ["Completed"],
            }

    class MockEdge:
        """Mock edge matching LangGraph Edge structure."""

        def __init__(
            self, source: str, target: str, data: str | None = None, conditional: bool = False
        ):
            self.source = source
            self.target = target
            self.data = data
            self.conditional = conditional

        def __len__(self):
            return 4

    class MockDrawableGraph:
        """Mock drawable graph structure."""

        @property
        def nodes(self):
            return {
                "__start__": None,
                "analyze": query_analyzer,
                "retrieve": retriever,
                "rerank": reranker,
                "generate": generator,
                "verify": verifier,
                "retry": retry_handler,
                "fail": failure_handler,
                "__end__": None,
            }

        @property
        def edges(self):
            return [
                MockEdge("__start__", "analyze"),
                MockEdge("analyze", "retrieve"),
                MockEdge("retrieve", "rerank", data="rerank", conditional=True),
                MockEdge("retrieve", "generate", data="generate", conditional=True),
                MockEdge("rerank", "generate"),
                MockEdge("generate", "verify"),
                MockEdge("verify", "__end__", data="accept", conditional=True),
                MockEdge("verify", "retry", data="retry", conditional=True),
                MockEdge("verify", "fail", data="fail", conditional=True),
                MockEdge("retry", "retrieve"),  # Loop back
                MockEdge("fail", "__end__"),
            ]

    graph = MockGraph()


if __name__ == "__main__":
    # Test the graph
    result = graph.invoke({
        "query": "What is the capital of France?",
        "documents": [],
        "answer": "",
        "confidence": 0.0,
        "retries": 0,
        "messages": [],
    })
    print("Result:", result)
