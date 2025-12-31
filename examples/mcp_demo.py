"""MCP (Model Context Protocol) Demo for Castella.

This example demonstrates how to expose a Castella UI to AI agents
via the Model Context Protocol (MCP).

To run this demo:
1. Install the mcp dependency: pip install castella[mcp]
2. Run this script: python examples/mcp_demo.py

The MCP server runs in the background on stdio, allowing AI agents
(like Claude Desktop) to connect and interact with the UI.

MCP Resources available:
- ui://tree - Get the complete UI tree
- ui://focus - Get the currently focused element
- ui://elements - Get all interactive elements
- ui://element/{id} - Get details of a specific element

MCP Tools available:
- click(element_id) - Click an element
- type_text(element_id, text, replace) - Type into an input
- focus(element_id) - Focus an element
- toggle(element_id) - Toggle a checkbox
- select(element_id, value) - Select in tabs/radio
- list_actionable() - List all interactive elements
"""

from castella import (
    App,
    Column,
    Row,
    Button,
    Text,
    Input,
    CheckBox,
    Slider,
    SliderState,
    Tabs,
    TabsState,
    TabItem,
    Component,
    State,
)
from castella.frame import Frame
from castella.mcp import CastellaMCPServer


class MCPDemoApp(Component):
    """Demo application with various interactive widgets."""

    def __init__(self):
        super().__init__()
        self._name = State("")
        self._counter = State(0)
        self._is_checked = State(False)
        self._slider = SliderState(value=50, min_val=0, max_val=100)
        self._tabs = TabsState([
            TabItem(id="home", label="Home", content=Text("Home tab content")),
            TabItem(id="settings", label="Settings", content=Text("Settings tab content")),
            TabItem(id="about", label="About", content=Text("About tab content")),
        ], selected_id="home")
        self._status = State("Ready")

        # Attach states for reactive updates
        self._name.attach(self)
        self._counter.attach(self)
        self._is_checked.attach(self)
        self._slider.attach(self)
        self._status.attach(self)

    def view(self):
        return Column(
            # Header
            Text("MCP Demo Application")
            .semantic_id("title")
            .fixed_height(40),

            # Name input
            Row(
                Text("Name:")
                .fixed_width(80)
                .fixed_height(30),
                Input(self._name())
                .semantic_id("name-input")
                .on_change(lambda t: self._name.set(t))
                .fixed_height(30),
            ).fixed_height(40),

            # Greeting text
            Text(f"Hello, {self._name() or 'World'}!")
            .semantic_id("greeting")
            .fixed_height(30),

            # Counter section
            Row(
                Button("Decrement")
                .semantic_id("decrement-btn")
                .on_click(lambda _: self._decrement())
                .fixed_width(100),
                Text(f"Count: {self._counter()}")
                .semantic_id("counter-display"),
                Button("Increment")
                .semantic_id("increment-btn")
                .on_click(lambda _: self._increment())
                .fixed_width(100),
            ).fixed_height(40),

            # Checkbox
            Row(
                CheckBox(self._is_checked)
                .semantic_id("feature-checkbox")
                .on_change(lambda c: self._on_checkbox_change(c)),
                Text("Enable feature" if not self._is_checked() else "Feature enabled!")
                .semantic_id("checkbox-label"),
            ).fixed_height(40),

            # Slider
            Row(
                Text("Volume:")
                .fixed_width(80),
                Slider(self._slider)
                .semantic_id("volume-slider")
                .on_change(lambda v: self._on_slider_change(v)),
                Text(f"{int(self._slider.value())}")
                .semantic_id("slider-value")
                .fixed_width(50),
            ).fixed_height(40),

            # Tabs
            Tabs(self._tabs)
            .semantic_id("main-tabs")
            .on_change(lambda tab_id: self._status.set(f"Tab: {tab_id}"))
            .fixed_height(150),

            # Status bar
            Text(f"Status: {self._status()}")
            .semantic_id("status-bar")
            .fixed_height(30),
        )

    def _increment(self):
        self._counter += 1
        self._status.set(f"Counter: {self._counter()}")

    def _decrement(self):
        self._counter -= 1
        self._status.set(f"Counter: {self._counter()}")

    def _on_checkbox_change(self, checked: bool):
        self._is_checked.set(checked)
        self._status.set(f"Checkbox: {'checked' if checked else 'unchecked'}")

    def _on_slider_change(self, value: float):
        self._status.set(f"Volume: {int(value)}")


def main():
    # Create the frame and app
    frame = Frame("MCP Demo", 600, 500)
    app = App(frame, MCPDemoApp())

    # Create MCP server
    mcp = CastellaMCPServer(app, name="castella-mcp-demo")

    # Start MCP server in background
    print("Starting MCP server...")
    mcp.run_in_background()
    print("MCP server running on stdio")
    print("Connect with an MCP client to interact with the UI")
    print()

    # Run the Castella app
    app.run()


if __name__ == "__main__":
    main()
