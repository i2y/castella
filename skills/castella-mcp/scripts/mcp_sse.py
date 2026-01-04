"""
MCP SSE Server Example - Demonstrates HTTP-based MCP server.

Run with: uv run python skills/castella-mcp/examples/mcp_sse.py

This creates an MCP server accessible via HTTP SSE transport.
Control the UI using HTTP requests to localhost:8765.

Example client commands (in another terminal):
  curl http://localhost:8765/health
  curl -X POST http://localhost:8765/message -H "Content-Type: application/json" \
    -d '{"type":"call_tool","params":{"name":"list_actionable","arguments":{}}}'
"""

from castella import App, Component, State, Column, Row, Text, Button, Slider, SliderState
from castella.frame import Frame
from castella.mcp import CastellaMCPServer


class SliderDemo(Component):
    """Interactive slider demo with MCP control."""

    def __init__(self):
        super().__init__()
        self._slider_state = SliderState(value=50, min_val=0, max_val=100)
        self._value_display = State("50")
        self._value_display.attach(self)

    def view(self):
        return Column(
            Text("MCP SSE Demo").font_size(20).semantic_id("title"),
            Text(f"Value: {self._value_display()}").semantic_id("value-display"),
            Slider(self._slider_state)
            .on_change(self._on_slider_change)
            .fixed_height(40)
            .semantic_id("main-slider"),
            Row(
                Button("Min").on_click(self._set_min).semantic_id("min-btn"),
                Button("Mid").on_click(self._set_mid).semantic_id("mid-btn"),
                Button("Max").on_click(self._set_max).semantic_id("max-btn"),
            ).fixed_height(40),
            Text("Connect via: http://localhost:8765").semantic_id("info"),
        ).padding(20)

    def _on_slider_change(self, value):
        self._value_display.set(str(int(value)))

    def _set_min(self, _event):
        self._slider_state.set(0)
        self._value_display.set("0")

    def _set_mid(self, _event):
        self._slider_state.set(50)
        self._value_display.set("50")

    def _set_max(self, _event):
        self._slider_state.set(100)
        self._value_display.set("100")


def main():
    app = App(Frame("MCP SSE Demo", 400, 300), SliderDemo())

    # Create MCP server
    mcp = CastellaMCPServer(app, name="slider-demo")

    # Run SSE transport in background
    host = "localhost"
    port = 8765
    mcp.run_sse_in_background(host=host, port=port)

    print(f"MCP SSE server running at http://{host}:{port}")
    print(f"  Health check: http://{host}:{port}/health")
    print(f"  SSE stream:   http://{host}:{port}/sse")
    print(f"  Messages:     POST http://{host}:{port}/message")
    print()
    print("Example: List interactive elements:")
    print(f'  curl -X POST http://{host}:{port}/message \\')
    print('    -H "Content-Type: application/json" \\')
    print("    -d '{\"type\":\"call_tool\",\"params\":{\"name\":\"list_actionable\",\"arguments\":{}}}'")

    # Run Castella app on main thread
    app.run()


if __name__ == "__main__":
    main()
