"""MCP Interactive Demo - Continuously accepts commands from a file.

This demo watches a command file and executes MCP operations in real-time.
Write commands to the file and watch the UI respond!
"""

import threading
import time
import os

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

COMMAND_FILE = "examples/mcp_commands.txt"


class MCPInteractiveDemo(Component):
    """Demo application controlled by MCP commands."""

    def __init__(self):
        super().__init__()
        self._name = State("")
        self._counter = State(0)
        self._is_checked = State(False)
        self._slider = SliderState(value=50, min_val=0, max_val=100)
        self._status = State("Watching for commands...")
        self._last_action = State("")

        self._name.attach(self)
        self._counter.attach(self)
        self._is_checked.attach(self)
        self._slider.attach(self)
        self._status.attach(self)
        self._last_action.attach(self)

    def view(self):
        return Column(
            # Title
            Text("MCP Interactive Demo")
            .semantic_id("title")
            .fixed_height(40),

            # Status
            Text(f"Status: {self._status()}")
            .semantic_id("status")
            .fixed_height(25)
            .bg_color("#1a1a2e"),

            # Last action
            Text(f"Last: {self._last_action()}")
            .semantic_id("last-action")
            .fixed_height(25)
            .bg_color("#16213e"),

            # Name input
            Row(
                Text("Name:")
                .fixed_width(70)
                .fixed_height(35),
                Input(self._name())
                .semantic_id("name-input")
                .on_change(lambda t: self._name.set(t))
                .fixed_height(35),
            ).fixed_height(45),

            # Greeting
            Text(f"Hello, {self._name() or '...'}!")
            .semantic_id("greeting")
            .fixed_height(35),

            # Counter
            Row(
                Button("−")
                .semantic_id("decrement-btn")
                .on_click(lambda _: self._decrement())
                .fixed_width(50),
                Text(f" {self._counter()} ")
                .semantic_id("counter-display")
                .fixed_width(80),
                Button("+")
                .semantic_id("increment-btn")
                .on_click(lambda _: self._increment())
                .fixed_width(50),
            ).fixed_height(45),

            # Checkbox
            Row(
                CheckBox(self._is_checked)
                .semantic_id("feature-checkbox")
                .on_change(lambda c: self._on_checkbox(c))
                .fixed_width(35),
                Text("Feature ON" if self._is_checked() else "Feature OFF")
                .semantic_id("checkbox-label"),
            ).fixed_height(40),

            # Slider
            Row(
                Text("Vol:")
                .fixed_width(50),
                Slider(self._slider)
                .semantic_id("volume-slider"),
                Text(f"{int(self._slider.value())}%")
                .semantic_id("slider-value")
                .fixed_width(50),
            ).fixed_height(40),
        )

    def _increment(self):
        self._counter += 1

    def _decrement(self):
        self._counter -= 1

    def _on_checkbox(self, checked: bool):
        self._is_checked.set(checked)

    def set_status(self, status: str):
        self._status.set(status)

    def set_last_action(self, action: str):
        self._last_action.set(action)


def watch_commands(app, mcp, demo):
    """Watch command file and execute MCP operations."""
    time.sleep(1.5)

    registry = mcp.registry
    root = demo.view()
    registry.rebuild_from_tree(root)

    last_mtime = 0

    demo.set_status("Ready! Watching for commands...")

    while True:
        try:
            if os.path.exists(COMMAND_FILE):
                mtime = os.path.getmtime(COMMAND_FILE)
                if mtime > last_mtime:
                    last_mtime = mtime
                    demo.set_status("Reading commands...")

                    with open(COMMAND_FILE, "r") as f:
                        commands = f.readlines()

                    # Clear the file
                    with open(COMMAND_FILE, "w") as f:
                        f.write("")

                    for cmd in commands:
                        cmd = cmd.strip()
                        if not cmd:
                            continue

                        parts = cmd.split(":", 2)
                        action = parts[0]

                        if action == "click" and len(parts) >= 2:
                            element_id = parts[1]
                            demo.set_last_action(f"click({element_id})")
                            click_element(element_id, registry, app)

                        elif action == "type" and len(parts) >= 3:
                            element_id = parts[1]
                            text = parts[2]
                            demo.set_last_action(f"type({element_id}, '{text}')")
                            type_text(element_id, text, True, registry, app)

                        elif action == "append" and len(parts) >= 3:
                            element_id = parts[1]
                            text = parts[2]
                            demo.set_last_action(f"append({element_id}, '{text}')")
                            type_text(element_id, text, False, registry, app)

                        elif action == "toggle" and len(parts) >= 2:
                            element_id = parts[1]
                            demo.set_last_action(f"toggle({element_id})")
                            toggle_element(element_id, registry, app)

                        elif action == "focus" and len(parts) >= 2:
                            element_id = parts[1]
                            demo.set_last_action(f"focus({element_id})")
                            focus_element(element_id, registry, app)

                        elif action == "wait":
                            secs = float(parts[1]) if len(parts) >= 2 else 1.0
                            demo.set_last_action(f"wait({secs}s)")
                            time.sleep(secs)

                        time.sleep(0.3)

                    demo.set_status("Done! Watching for more...")

        except Exception as e:
            demo.set_status(f"Error: {e}")

        time.sleep(0.2)


def main():
    # Clear command file
    with open(COMMAND_FILE, "w") as f:
        f.write("")

    frame = Frame("MCP Interactive Demo", 400, 380)
    demo = MCPInteractiveDemo()
    app = App(frame, demo)
    mcp = CastellaMCPServer(app, name="mcp-interactive")

    # Start command watcher
    watcher = threading.Thread(target=watch_commands, args=(app, mcp, demo), daemon=True)
    watcher.start()

    app.run()


if __name__ == "__main__":
    main()
