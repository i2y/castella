"""Simple agent workflow for testing LangGraph Studio.

This is a minimal LangGraph example with:
- A start node
- An agent node that processes input
- A tool node that performs actions
- An end node

Run with:
    python -m examples.langgraph_studio.samples.simple_agent
"""

from typing import TypedDict, Annotated
from operator import add


# Define the state
class AgentState(TypedDict):
    """State for the simple agent."""
    messages: Annotated[list[str], add]
    current_step: str


def agent_node(state: AgentState) -> dict:
    """Agent node that processes messages."""
    _ = state.get("messages", [])  # Access state for demo
    return {
        "messages": ["Agent processed the input"],
        "current_step": "agent",
    }


def tool_node(state: AgentState) -> dict:
    """Tool node that performs actions."""
    return {
        "messages": ["Tool executed successfully"],
        "current_step": "tool",
    }


def should_use_tool(state: AgentState) -> str:
    """Decide whether to use a tool or end."""
    # Simple logic: if we've processed, go to tool
    if state.get("current_step") == "agent":
        return "tool"
    return "end"


# Build the graph
try:
    from langgraph.graph import StateGraph, START, END

    # Create the graph
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("agent", agent_node)
    workflow.add_node("tool", tool_node)

    # Add edges
    workflow.add_edge(START, "agent")
    workflow.add_conditional_edges(
        "agent",
        should_use_tool,
        {
            "tool": "tool",
            "end": END,
        }
    )
    workflow.add_edge("tool", END)

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
            yield {"agent": {"messages": ["Agent processing..."], "current_step": "agent"}}
            yield {"tool": {"messages": ["Tool executing..."], "current_step": "tool"}}

        def invoke(self, initial_state):
            """Mock invocation."""
            return {"messages": ["Done"], "current_step": "end"}

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

        def __repr__(self):
            return f"Edge(source={self.source!r}, target={self.target!r}, data={self.data!r}, conditional={self.conditional})"

    class MockDrawableGraph:
        """Mock drawable graph structure."""

        @property
        def nodes(self):
            return {
                "__start__": None,
                "agent": agent_node,
                "tool": tool_node,
                "__end__": None,
            }

        @property
        def edges(self):
            return [
                MockEdge("__start__", "agent"),
                MockEdge("agent", "tool", conditional=True),
                MockEdge("agent", "__end__", data="end", conditional=True),
                MockEdge("tool", "__end__"),
            ]

    graph = MockGraph()


if __name__ == "__main__":
    # Test the graph
    result = graph.invoke({"messages": [], "current_step": ""})
    print("Result:", result)
