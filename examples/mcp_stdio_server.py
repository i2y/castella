"""MCP Stdio Server - Castella app as a proper MCP server.

This example runs a Castella app that can be controlled by any MCP client
(including Claude Desktop) via the standard MCP protocol over stdio.

The MCP server runs in a background thread while GUI runs on main thread
(required by GLFW on macOS and most platforms).

Usage with Claude Desktop:
    Add to your Claude Desktop config (claude_desktop_config.json):
    {
        "mcpServers": {
            "castella-demo": {
                "command": "python",
                "args": ["/path/to/examples/mcp_stdio_server.py"]
            }
        }
    }

Usage with MCP client:
    python examples/mcp_protocol_client.py
"""

import sys
import time

from castella import (
    App,
    Column,
    Row,
    Button,
    Text,
    Input,
    CheckBox,
    Component,
    State,
)
from castella.frame import Frame
from castella.mcp import CastellaMCPServer


class DemoApp(Component):
    """Demo app to be controlled via MCP."""

    def __init__(self):
        super().__init__()
        self._status = State("MCP Server Ready")
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
            .fixed_height(30)
            .bg_color("#2c3e50"),

            Row(
                Text("Name:").fixed_width(60),
                Input(self._name())
                .semantic_id("name-input")
                .on_change(lambda t: self._name.set(t)),
            ).fixed_height(40),

            Text(f"Hello, {self._name() or 'World'}!")
            .semantic_id("greeting")
            .fixed_height(35),

            Row(
                Button("−")
                .semantic_id("decrement-btn")
                .on_click(lambda _: self._dec())
                .fixed_width(50),
                Text(f" {self._counter()} ")
                .semantic_id("counter")
                .fixed_width(80),
                Button("+")
                .semantic_id("increment-btn")
                .on_click(lambda _: self._inc())
                .fixed_width(50),
            ).fixed_height(45),

            Row(
                CheckBox(self._checked)
                .semantic_id("my-checkbox")
                .on_change(lambda c: self._checked.set(c))
                .fixed_width(35),
                Text("ON" if self._checked() else "OFF"),
            ).fixed_height(35),
        )

    def _inc(self):
        self._counter.set(self._counter() + 1)
        self._status.set(f"Counter: {self._counter()}")

    def _dec(self):
        self._counter.set(self._counter() - 1)
        self._status.set(f"Counter: {self._counter()}")


def main():
    # Create the Castella app
    frame = Frame("MCP Demo", 350, 250)
    demo = DemoApp()
    app = App(frame, demo)

    # Create MCP server
    mcp = CastellaMCPServer(app, name="castella-demo")

    # Build initial widget tree for MCP
    demo.view()
    mcp.refresh_registry()

    # Run MCP server in background thread (handles stdio protocol)
    mcp.run_in_background(transport="stdio")

    # Give MCP server time to start
    time.sleep(0.2)

    print("MCP server started in background", file=sys.stderr)

    # Run GUI on main thread (required by GLFW/macOS)
    # When window closes, daemon thread will be terminated
    app.run()


if __name__ == "__main__":
    main()
