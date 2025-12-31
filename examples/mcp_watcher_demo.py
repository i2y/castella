"""MCP CommandWatcher Demo - Simple external control of Castella apps.

This demo shows how to use the CommandWatcher API to allow external
processes to control a Castella application via a command file.

Usage:
    1. Run this demo: python examples/mcp_watcher_demo.py
    2. Write commands to .castella_commands file:
       echo "click:increment-btn" >> .castella_commands

Command format:
    click:<element_id>
    type:<element_id>:<text>
    append:<element_id>:<text>
    toggle:<element_id>
    focus:<element_id>
    wait:<seconds>
"""

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
from castella.mcp import CastellaMCPServer, CommandWatcher


class SimpleApp(Component):
    def __init__(self):
        super().__init__()
        self._name = State("")
        self._counter = State(0)
        self._checked = State(False)

        self._name.attach(self)
        self._counter.attach(self)
        self._checked.attach(self)

    def view(self):
        return Column(
            Text("CommandWatcher Demo").semantic_id("title")
                .fixed_height(40),

            Row(
                Text("Name:").fixed_width(60),
                Input(self._name()).semantic_id("name-input")
                    .on_change(lambda t: self._name.set(t)),
            ).fixed_height(40),

            Text(f"Hello, {self._name() or 'World'}!")
                .semantic_id("greeting")
                .fixed_height(35),

            Row(
                Button("-").semantic_id("decrement-btn")
                    .on_click(lambda _: self._counter.set(self._counter() - 1))
                    .fixed_width(50),
                Text(f" {self._counter()} ").semantic_id("counter")
                    .fixed_width(80),
                Button("+").semantic_id("increment-btn")
                    .on_click(lambda _: self._counter.set(self._counter() + 1))
                    .fixed_width(50),
            ).fixed_height(40),

            Row(
                CheckBox(self._checked).semantic_id("my-checkbox")
                    .on_change(lambda c: self._checked.set(c)),
                Text("Enabled" if self._checked() else "Disabled"),
            ).fixed_height(35),
        )


def main():
    # Create app
    frame = Frame("CommandWatcher Demo", 350, 250)
    app = App(frame, SimpleApp())

    # Create MCP server
    mcp = CastellaMCPServer(app)

    # Create and start command watcher
    watcher = CommandWatcher(
        mcp,
        command_file=".castella_commands",
        on_command=lambda cmd, _: print(f"Executing: {cmd}"),
    )
    watcher.start()

    print("CommandWatcher Demo started!")
    print(f"Write commands to: {watcher.command_file.absolute()}")
    print()
    print("Example commands:")
    print('  echo "click:increment-btn" >> .castella_commands')
    print('  echo "type:name-input:Claude" >> .castella_commands')
    print('  echo "toggle:my-checkbox" >> .castella_commands')
    print()

    app.run()


if __name__ == "__main__":
    main()
