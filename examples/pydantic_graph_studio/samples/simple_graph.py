"""Simple pydantic-graph example using BaseNode API.

This example demonstrates a basic workflow with:
- InputNode: Receives initial input
- ProcessNode: Processes the input
- OutputNode: Returns the final result

Run with: uv run python examples/pydantic_graph_studio/samples/simple_graph.py
"""

from __future__ import annotations

from dataclasses import dataclass

try:
    from pydantic_graph import BaseNode, End, Graph, GraphRunContext
except ImportError:
    raise ImportError(
        "pydantic-graph is not installed. "
        "Install it with: pip install pydantic-graph"
    )


@dataclass
class InputNode(BaseNode[dict, None, str]):
    """Entry node that receives input text."""

    text: str = ""

    async def run(self, ctx: GraphRunContext) -> "ProcessNode":
        """Store input in state and move to processing."""
        ctx.state["input"] = self.text
        ctx.state["history"] = ["input received"]
        return ProcessNode()


@dataclass
class ProcessNode(BaseNode[dict, None, str]):
    """Process the input data."""

    async def run(self, ctx: GraphRunContext) -> "OutputNode | End[str]":
        """Process the input - uppercase the text."""
        text = ctx.state.get("input", "")
        if not text:
            return End(data="No input provided")

        ctx.state["processed"] = text.upper()
        ctx.state["history"].append("processed")
        return OutputNode()


@dataclass
class OutputNode(BaseNode[dict, None, str]):
    """Output the final result."""

    async def run(self, ctx: GraphRunContext) -> End[str]:
        """Return the processed result."""
        result = ctx.state.get("processed", "")
        ctx.state["history"].append("completed")
        return End(data=result)


# Create the graph - this is what the studio will find
graph = Graph(nodes=[InputNode, ProcessNode, OutputNode])


# Example of running the graph directly
if __name__ == "__main__":
    import asyncio

    async def main():
        result = await graph.run(
            InputNode(text="Hello, pydantic-graph!"),
            state={},
        )
        print(f"Result: {result.output}")
        print(f"Final state: {result.state}")

    asyncio.run(main())
