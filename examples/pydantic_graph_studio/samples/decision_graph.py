"""pydantic-graph example with branching decisions.

This example demonstrates conditional execution:
- StartNode: Sets initial value
- ValidateNode: Branches based on validation result
- SuccessNode: Handles valid input
- ErrorNode: Handles invalid input

Run with: uv run python examples/pydantic_graph_studio/samples/decision_graph.py
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
class StartNode(BaseNode[dict, None, str]):
    """Entry node that sets the initial value."""

    value: int = 0

    async def run(self, ctx: GraphRunContext) -> "ValidateNode":
        """Store value in state."""
        ctx.state["value"] = self.value
        ctx.state["steps"] = ["started"]
        return ValidateNode()


@dataclass
class ValidateNode(BaseNode[dict, None, str]):
    """Validate the value and branch accordingly."""

    async def run(self, ctx: GraphRunContext) -> "SuccessNode | ErrorNode":
        """Check if value is positive."""
        value = ctx.state.get("value", 0)
        ctx.state["steps"].append("validated")

        if value > 0:
            ctx.state["validation"] = "passed"
            return SuccessNode()
        else:
            ctx.state["validation"] = "failed"
            return ErrorNode()


@dataclass
class SuccessNode(BaseNode[dict, None, str]):
    """Handle successful validation."""

    async def run(self, ctx: GraphRunContext) -> End[str]:
        """Return success message."""
        value = ctx.state.get("value", 0)
        ctx.state["steps"].append("completed")
        return End(data=f"Success! Value {value} is valid.")


@dataclass
class ErrorNode(BaseNode[dict, None, str]):
    """Handle validation errors."""

    async def run(self, ctx: GraphRunContext) -> End[str]:
        """Return error message."""
        value = ctx.state.get("value", 0)
        ctx.state["steps"].append("error_handled")
        return End(data=f"Error: Value {value} is not positive.")


# Create the graph
graph = Graph(nodes=[StartNode, ValidateNode, SuccessNode, ErrorNode])


if __name__ == "__main__":
    import asyncio

    async def main():
        # Test with positive value
        print("Testing with value=5:")
        result = await graph.run(StartNode(value=5), state={})
        print(f"  Result: {result.output}")
        print(f"  Steps: {result.state.get('steps', [])}")

        # Test with negative value
        print("\nTesting with value=-3:")
        result = await graph.run(StartNode(value=-3), state={})
        print(f"  Result: {result.output}")
        print(f"  Steps: {result.state.get('steps', [])}")

    asyncio.run(main())
