"""MCP SSE Server - Castella app with SSE transport.

This example runs a Castella app that can be controlled by any HTTP client
via Server-Sent Events (SSE) transport.

Unlike the stdio transport, SSE allows connecting to an already-running app.

Usage:
    1. Start the server:
       python examples/mcp_sse_server.py

    2. Connect with the SSE client:
       python examples/mcp_sse_client.py

    The server listens on http://localhost:8765
"""

from castella import (
    App,
    Column,
    Row,
    Button,
    Text,
    Input,
    CheckBox,
    SizePolicy,
    Component,
    State,
)
from castella.frame import Frame
from castella.mcp import CastellaMCPServer


class DemoApp(Component):
    """Demo app to be controlled via MCP SSE."""

    def __init__(self):
        super().__init__()
        self._status = State("SSE Server Ready")
        self._name = State("")
        self._counter = State(0)
        self._checked = State(False)

        self._status.attach(self)
        self._name.attach(self)
        self._counter.attach(self)
        self._checked.attach(self)

    def view(self):
        return Column(
            Text(f"[{self._status()}]")
            .semantic_id("status")
            .height(30)
            .height_policy(SizePolicy.FIXED)
            .bg_color("#2c3e50"),

            Row(
                Text("Name:").width(60).width_policy(SizePolicy.FIXED),
                Input(self._name())
                .semantic_id("name-input")
                .on_change(lambda t: self._name.set(t)),
            ).height(40).height_policy(SizePolicy.FIXED),

            Text(f"Hello, {self._name() or 'World'}!")
            .semantic_id("greeting")
            .height(35)
            .height_policy(SizePolicy.FIXED),

            Row(
                Button("−")
                .semantic_id("decrement-btn")
                .on_click(lambda _: self._dec())
                .width(50)
                .width_policy(SizePolicy.FIXED),
                Text(f" {self._counter()} ")
                .semantic_id("counter")
                .width(80)
                .width_policy(SizePolicy.FIXED),
                Button("+")
                .semantic_id("increment-btn")
                .on_click(lambda _: self._inc())
                .width(50)
                .width_policy(SizePolicy.FIXED),
            ).height(45).height_policy(SizePolicy.FIXED),

            Row(
                CheckBox(self._checked)
                .semantic_id("my-checkbox")
                .on_change(lambda c: self._checked.set(c))
                .width(35)
                .width_policy(SizePolicy.FIXED),
                Text("ON" if self._checked() else "OFF"),
            ).height(35).height_policy(SizePolicy.FIXED),
        )

    def _inc(self):
        self._counter.set(self._counter() + 1)
        self._status.set(f"Counter: {self._counter()}")

    def _dec(self):
        self._counter.set(self._counter() - 1)
        self._status.set(f"Counter: {self._counter()}")


def main():
    # Create the Castella app
    frame = Frame("MCP SSE Demo", 350, 250)
    demo = DemoApp()
    app = App(frame, demo)

    # Create MCP server
    mcp = CastellaMCPServer(app, name="castella-sse-demo")

    # Build initial widget tree for MCP
    demo.view()
    mcp.refresh_registry()

    # Run SSE server in background thread
    mcp.run_sse_in_background(host="localhost", port=8765)

    print("=" * 50)
    print("MCP SSE Server Started")
    print("=" * 50)
    print()
    print("SSE endpoint: http://localhost:8765/sse")
    print("Message endpoint: http://localhost:8765/message")
    print()
    print("Connect with: python examples/mcp_sse_client.py")
    print()

    # Run GUI on main thread (required by GLFW/macOS)
    app.run()


if __name__ == "__main__":
    main()
