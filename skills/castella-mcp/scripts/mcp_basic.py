"""
Basic MCP Server Example - Demonstrates MCP-enabled Castella app.

Run with: uv run python skills/castella-mcp/examples/mcp_basic.py

This creates a simple form UI with semantic IDs that can be controlled
via MCP protocol (stdio transport).
"""

from castella import App, Component, State, Column, Row, Text, Button, Input, CheckBox
from castella.frame import Frame
from castella.mcp import CastellaMCPServer


class FormComponent(Component):
    """Simple form with semantic IDs for MCP control."""

    def __init__(self):
        super().__init__()
        self._name = State("")
        self._email = State("")
        self._subscribe = State(False)
        self._result = State("")
        self._result.attach(self)

    def view(self):
        return Column(
            Text("MCP-Enabled Form").font_size(20).semantic_id("title"),
            # Name input
            Row(
                Text("Name:").fixed_width(80),
                Input(self._name())
                .on_change(lambda t: self._name.set(t))
                .semantic_id("name-input"),
            ).fixed_height(40),
            # Email input
            Row(
                Text("Email:").fixed_width(80),
                Input(self._email())
                .on_change(lambda t: self._email.set(t))
                .semantic_id("email-input"),
            ).fixed_height(40),
            # Subscribe checkbox
            Row(
                Text("Subscribe:").fixed_width(80),
                CheckBox(self._subscribe)
                .on_change(lambda v: self._subscribe.set(v))
                .semantic_id("subscribe-check"),
            ).fixed_height(40),
            # Submit button
            Button("Submit")
            .on_click(self._submit)
            .fixed_height(40)
            .semantic_id("submit-btn"),
            # Result display
            Text(self._result()).text_color("#00ff00").semantic_id("result-text"),
        ).padding(20)

    def _submit(self, _event):
        name = self._name()
        email = self._email()
        subscribe = "Yes" if self._subscribe() else "No"
        self._result.set(f"Submitted: {name}, {email}, Subscribe: {subscribe}")


def main():
    app = App(Frame("MCP Basic", 500, 350), FormComponent())

    # Create MCP server with stdio transport
    mcp = CastellaMCPServer(app, name="form-demo")

    # Run MCP in background (stdio transport)
    mcp.run_in_background()

    print("MCP server running on stdio transport")
    print("Use an MCP client to interact with the UI")

    # Run Castella app on main thread
    app.run()


if __name__ == "__main__":
    main()
