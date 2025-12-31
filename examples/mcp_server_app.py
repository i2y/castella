"""MCP Server App - A Castella app that can be controlled via MCP.

This app runs with GUI and accepts MCP commands via a Unix socket
or the CommandWatcher file-based approach.

For testing with an MCP client, you can use the CommandWatcher
which provides a simpler integration path.

Usage:
    python examples/mcp_server_app.py

Then control it with:
    python examples/mcp_simple_client.py
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
    Component,
    State,
)
from castella.frame import Frame
from castella.mcp import CastellaMCPServer, CommandWatcher


class ControlledApp(Component):
    """An app designed to be controlled externally via MCP."""

    def __init__(self):
        super().__init__()
        self._message = State("Waiting for commands...")
        self._name = State("")
        self._counter = State(0)
        self._enabled = State(False)
        self._volume = SliderState(value=50, min_val=0, max_val=100)

        self._message.attach(self)
        self._name.attach(self)
        self._counter.attach(self)
        self._enabled.attach(self)
        self._volume.attach(self)

    def view(self):
        return Column(
            # Status bar
            Text(f">> {self._message()}")
            .semantic_id("status")
            .fixed_height(30)
            .bg_color("#1e3a5f"),

            # Name input
            Row(
                Text("Name:").fixed_width(70),
                Input(self._name())
                .semantic_id("name-input")
                .on_change(self._on_name_change),
            ).fixed_height(40),

            # Greeting
            Text(f"Hello, {self._name() or '...'}!")
            .semantic_id("greeting")
            .fixed_height(35),

            # Counter
            Row(
                Button("−")
                .semantic_id("decrement-btn")
                .on_click(lambda _: self._update_counter(-1))
                .fixed_width(50),
                Text(f" {self._counter()} ")
                .semantic_id("counter-display")
                .fixed_width(100),
                Button("+")
                .semantic_id("increment-btn")
                .on_click(lambda _: self._update_counter(1))
                .fixed_width(50),
            ).fixed_height(45),

            # Checkbox
            Row(
                CheckBox(self._enabled)
                .semantic_id("enable-checkbox")
                .on_change(self._on_enable_change),
                Text("Enabled" if self._enabled() else "Disabled")
                .semantic_id("enable-label"),
            ).fixed_height(40),

            # Slider
            Row(
                Text("Volume:").fixed_width(70),
                Slider(self._volume)
                .semantic_id("volume-slider")
                .on_change(self._on_volume_change),
                Text(f"{int(self._volume.value())}%")
                .semantic_id("volume-display")
                .fixed_width(50),
            ).fixed_height(40),
        )

    def _on_name_change(self, name: str):
        self._name.set(name)
        self._message.set(f"Name changed to: {name}")

    def _update_counter(self, delta: int):
        self._counter.set(self._counter() + delta)
        self._message.set(f"Counter: {self._counter()}")

    def _on_enable_change(self, enabled: bool):
        self._enabled.set(enabled)
        self._message.set(f"Enabled: {enabled}")

    def _on_volume_change(self, volume: float):
        self._message.set(f"Volume: {int(volume)}%")


def main():
    # Create app
    frame = Frame("MCP Server App", 400, 320)
    app = App(frame, ControlledApp())

    # Create MCP server
    mcp = CastellaMCPServer(app, name="castella-server")

    # Start command watcher for external control
    watcher = CommandWatcher(
        mcp,
        command_file=".castella_commands",
        on_command=lambda cmd, _: print(f"[MCP] {cmd}"),
    )
    watcher.start()

    print("=" * 50)
    print("MCP Server App Started")
    print("=" * 50)
    print()
    print("Control this app by writing to .castella_commands")
    print("Or use: python examples/mcp_simple_client.py")
    print()
    print("Available elements:")
    print("  - name-input      : Text input")
    print("  - increment-btn   : + button")
    print("  - decrement-btn   : - button")
    print("  - enable-checkbox : Checkbox")
    print("  - volume-slider   : Slider (use scroll)")
    print()

    app.run()


if __name__ == "__main__":
    main()
