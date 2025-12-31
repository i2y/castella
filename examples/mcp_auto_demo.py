"""MCP Auto Demo - Watch AI manipulate the GUI automatically!

This demo starts a Castella GUI and then automatically performs
operations via MCP tools, so you can watch the UI being controlled.
"""

import threading
import time

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
    Component,
    State,
)
from castella.frame import Frame
from castella.mcp import CastellaMCPServer
from castella.mcp.tools import (
    click_element,
    type_text,
    toggle_element,
    focus_element,
)


class MCPAutoDemo(Component):
    """Demo application that will be manipulated by MCP."""

    def __init__(self):
        super().__init__()
        self._name = State("")
        self._counter = State(0)
        self._is_checked = State(False)
        self._slider = SliderState(value=50, min_val=0, max_val=100)
        self._status = State("Waiting for MCP actions...")

        self._name.attach(self)
        self._counter.attach(self)
        self._is_checked.attach(self)
        self._slider.attach(self)
        self._status.attach(self)

    def view(self):
        return Column(
            # Title
            Text("MCP Auto Demo - Watch the AI control this UI!")
            .semantic_id("title")
            .fixed_height(50),

            # Status display
            Text(f"Status: {self._status()}")
            .semantic_id("status")
            .fixed_height(30)
            .bg_color("#2d2d2d"),

            # Name input section
            Row(
                Text("Name:")
                .fixed_width(80)
                .fixed_height(35),
                Input(self._name())
                .semantic_id("name-input")
                .on_change(lambda t: self._name.set(t))
                .fixed_height(35),
            ).fixed_height(50),

            # Greeting
            Text(f"Hello, {self._name() or '...'}!")
            .semantic_id("greeting")
            .fixed_height(40),

            # Counter section
            Row(
                Button("−")
                .semantic_id("decrement-btn")
                .on_click(lambda _: self._decrement())
                .fixed_width(60),
                Text(f"  Count: {self._counter()}  ")
                .semantic_id("counter-display")
                .fixed_width(120),
                Button("+")
                .semantic_id("increment-btn")
                .on_click(lambda _: self._increment())
                .fixed_width(60),
            ).fixed_height(50),

            # Checkbox
            Row(
                CheckBox(self._is_checked)
                .semantic_id("feature-checkbox")
                .on_change(lambda c: self._on_checkbox(c))
                .fixed_width(40),
                Text("Enable special feature" if not self._is_checked() else "Feature ENABLED!")
                .semantic_id("checkbox-label"),
            ).fixed_height(50),

            # Slider
            Row(
                Text("Volume:")
                .fixed_width(80),
                Slider(self._slider)
                .semantic_id("volume-slider")
                .on_change(lambda v: self._on_slider(v)),
                Text(f" {int(self._slider.value())}%")
                .semantic_id("slider-value")
                .fixed_width(60),
            ).fixed_height(50),
        )

    def _increment(self):
        self._counter += 1

    def _decrement(self):
        self._counter -= 1

    def _on_checkbox(self, checked: bool):
        self._is_checked.set(checked)

    def _on_slider(self, value: float):
        pass  # SliderState handles this

    def set_status(self, status: str):
        self._status.set(status)


def run_mcp_actions(app, mcp, demo_component):
    """Run MCP actions in a background thread."""
    time.sleep(2)  # Wait for GUI to fully load

    registry = mcp.registry

    # Rebuild registry to get all widgets
    demo_component.view()  # Ensure view is built
    # We need to rebuild from the actual rendered tree
    # For now, let's manually register by calling view again
    root = demo_component.view()
    registry.rebuild_from_tree(root)

    actions = [
        ("Focusing on name input...", lambda: focus_element("name-input", registry, app)),
        ("Typing 'C'...", lambda: type_text("name-input", "C", False, registry, app)),
        ("Typing 'l'...", lambda: type_text("name-input", "l", False, registry, app)),
        ("Typing 'a'...", lambda: type_text("name-input", "a", False, registry, app)),
        ("Typing 'u'...", lambda: type_text("name-input", "u", False, registry, app)),
        ("Typing 'd'...", lambda: type_text("name-input", "d", False, registry, app)),
        ("Typing 'e'...", lambda: type_text("name-input", "e", False, registry, app)),
        ("Clicking increment button...", lambda: click_element("increment-btn", registry, app)),
        ("Clicking increment button...", lambda: click_element("increment-btn", registry, app)),
        ("Clicking increment button...", lambda: click_element("increment-btn", registry, app)),
        ("Clicking decrement button...", lambda: click_element("decrement-btn", registry, app)),
        ("Toggling checkbox ON...", lambda: toggle_element("feature-checkbox", registry, app)),
        ("Waiting...", lambda: None),
        ("Toggling checkbox OFF...", lambda: toggle_element("feature-checkbox", registry, app)),
        ("Clicking increment 5 times...", lambda: [click_element("increment-btn", registry, app) for _ in range(5)]),
        ("Done! AI has finished controlling the UI.", lambda: None),
    ]

    for status, action in actions:
        demo_component.set_status(status)
        if action:
            action()
        time.sleep(0.8)

    demo_component.set_status("Demo complete! You can now interact manually.")


def main():
    # Create the frame and app
    frame = Frame("MCP Auto Demo", 500, 450)
    demo = MCPAutoDemo()
    app = App(frame, demo)

    # Create MCP server
    mcp = CastellaMCPServer(app, name="mcp-auto-demo")

    # Start background thread for MCP actions
    action_thread = threading.Thread(
        target=run_mcp_actions,
        args=(app, mcp, demo),
        daemon=True,
    )
    action_thread.start()

    # Run the Castella app (blocks until window is closed)
    app.run()


if __name__ == "__main__":
    main()
