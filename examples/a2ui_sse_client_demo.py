"""A2UI SSE Client Demo - Connect to Mock A2UI Server

This demo connects to a mock A2UI server via Server-Sent Events (SSE)
and renders the streamed UI components in real-time.

Requirements:
    pip install httpx

Setup:
    1. Start the mock server:
       uvicorn examples.a2ui_mock_server:app --port 8080

    2. Run this client:
       uv run python examples/a2ui_sse_client_demo.py

The client will connect to the server and progressively render
the weather UI as components stream in.
"""

import asyncio
import threading

from castella import App, Box, Button, Column, Row, Text
from castella.a2ui import A2UIRenderer, UserAction
from castella.core import Component, State
from castella.frame import Frame


class A2UISSEClient(Component):
    """A2UI client that connects to an SSE endpoint and renders the UI."""

    def __init__(
        self,
        base_url: str = "http://localhost:8080",
        initial_endpoint: str = "/ui/weather?city=Tokyo",
    ):
        super().__init__()
        self._base_url = base_url
        self._endpoint = initial_endpoint

        # State - can now attach in __init__ (App.get() returns None safely)
        self._status = State("Connecting...")
        self._widget_content = State[any](None)
        self._error = State("")
        self._status.attach(self)
        self._widget_content.attach(self)
        self._error.attach(self)

        # Renderer
        def on_action(action: UserAction):
            print(f"Action: {action.name}")
            if action.name == "refresh":
                self._fetch_ui(self._endpoint)
            elif action.name == "close":
                print("Close requested")

        self._renderer = A2UIRenderer(on_action=on_action)

        # Start initial fetch
        self._fetch_ui(self._endpoint)

    def _fetch_ui(self, endpoint: str):
        """Fetch UI from the SSE endpoint in a background thread."""
        self._status.set("Connecting...")
        self._error.set("")
        self._widget_content.set(None)

        def run_async():
            asyncio.run(self._fetch_async(endpoint))

        thread = threading.Thread(target=run_async, daemon=True)
        thread.start()

    async def _fetch_async(self, endpoint: str):
        """Async SSE fetch."""
        try:
            import httpx
        except ImportError:
            self._error.set("httpx not installed. Run: pip install httpx")
            self._status.set("Error")
            return

        url = f"{self._base_url}{endpoint}"
        self._status.set(f"Fetching: {url}")

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                async with client.stream(
                    "GET",
                    url,
                    headers={"Accept": "text/event-stream"},
                ) as response:
                    response.raise_for_status()
                    self._status.set("Streaming...")

                    buffer = ""
                    async for line in response.aiter_lines():
                        if line.startswith("data:"):
                            data = line[5:].strip()
                            if data:
                                buffer += data + "\n"

                    # Process all messages
                    if buffer:
                        surface = self._renderer.handle_jsonl(buffer)
                        if surface:
                            self._widget_content.set(surface.root_widget)
                            self._status.set("Complete")
                        else:
                            self._error.set("Failed to render surface")
                            self._status.set("Error")

        except httpx.ConnectError:
            self._error.set(f"Cannot connect to {self._base_url}\nMake sure the server is running.")
            self._status.set("Connection Failed")
        except Exception as e:
            self._error.set(str(e))
            self._status.set("Error")

    def _switch_endpoint(self, endpoint: str):
        """Switch to a different endpoint."""
        self._endpoint = endpoint
        self._fetch_ui(endpoint)

    def view(self):
        from castella.theme import ThemeManager

        theme = ThemeManager().current

        # Header with endpoint buttons
        header = Row(
            Button("Weather (Tokyo)").on_click(
                lambda _: self._switch_endpoint("/ui/weather?city=Tokyo")
            ),
            Button("Weather (NYC)").on_click(
                lambda _: self._switch_endpoint("/ui/weather?city=New York")
            ),
            Button("Form").on_click(
                lambda _: self._switch_endpoint("/ui/form")
            ),
        ).fixed_height(50)

        # Status bar
        status_bar = (
            Text(f"Status: {self._status()}")
            .text_color(theme.colors.text_info)
            .fixed_height(24)
        )

        # Main content
        content = self._widget_content()
        if content is not None:
            main_area = Box(content).bg_color(theme.colors.bg_secondary)
        elif self._error():
            main_area = Column(
                Text("Error").text_color(theme.colors.text_danger),
                Text(self._error()).text_color(theme.colors.text_warning),
            ).bg_color(theme.colors.bg_secondary)
        else:
            main_area = Column(
                Text("Loading...").text_color(theme.colors.text_info),
            ).bg_color(theme.colors.bg_secondary)

        return Column(
            header,
            status_bar,
            main_area,
        ).bg_color(theme.colors.bg_primary)


def main():
    """Run the A2UI SSE client demo."""
    print("A2UI SSE Client Demo")
    print("=" * 40)
    print()
    print("Make sure the mock server is running:")
    print("  uvicorn examples.a2ui_mock_server:app --port 8080")
    print()
    print("Or run it directly:")
    print("  uv run python examples/a2ui_mock_server.py")
    print()

    # Check if httpx is available
    try:
        import httpx

        print("httpx is installed - SSE streaming enabled")
    except ImportError:
        print("WARNING: httpx not installed")
        print("Install it with: pip install httpx")
        print()

    client = A2UISSEClient(
        base_url="http://localhost:8080",
        initial_endpoint="/ui/weather?city=Tokyo",
    )

    App(Frame("A2UI SSE Client", 800, 600), client).run()


if __name__ == "__main__":
    main()
