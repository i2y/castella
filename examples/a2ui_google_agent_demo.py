"""Castella client for Google A2UI sample agents.

This example demonstrates connecting to Google's A2UI sample agents
(Restaurant Finder, Contact Lookup, etc.) and rendering their UI
natively using Castella widgets.

Prerequisites:
1. Clone and run a sample agent:
   ```bash
   git clone https://github.com/google/A2UI.git /tmp/a2ui
   cd /tmp/a2ui/samples/agent/adk/restaurant_finder
   export GEMINI_API_KEY="your_key_here"
   uv run .
   ```

2. Run this client:
   ```bash
   uv run python examples/a2ui_google_agent_demo.py
   ```

The client connects to the A2A agent via HTTP, requests the A2UI extension,
and renders the returned UI components using Castella's A2UI renderer.
"""

import sys

try:
    import httpx  # noqa: F401
except ImportError:
    print("This example requires httpx. Install with: pip install httpx")
    sys.exit(1)

from castella import App
from castella.a2ui import A2UIClient, A2UIClientError, A2UIComponent, UserAction
from castella.frame import Frame


def run_demo(agent_url: str = "http://localhost:10002", query: str | None = None):
    """Run the A2UI demo.

    Args:
        agent_url: The A2A agent URL
        query: The query to send to the agent
    """
    if query is None:
        query = "Find me 2 Chinese restaurants in San Francisco"

    print(f"Connecting to agent at {agent_url}...")
    print(f"Query: {query}")
    print()

    # Create client with action handler
    def on_action(action: UserAction):
        """Handle user actions from the UI."""
        print(f"Action: {action.name}")
        print(f"  Source: {action.source_component_id}")
        print(f"  Context: {action.context}")

    client = A2UIClient(agent_url, on_action=on_action)

    try:
        # Send message and get A2UI surface
        print("Sending message...")
        surface = client.send(query)

        if surface is None:
            print("No A2UI data received from agent.")
            print("The agent may not have returned UI components.")
            return

        print(f"Surface created: {surface.surface_id}")
        print(f"Root widget: {surface.root_widget}")
        print(f"Components: {list(surface._components.keys())}")
        print(f"Data model: {surface._data_model}")
        print("Launching Castella UI...")

        # Create component and run app
        component = A2UIComponent(surface)
        App(Frame("A2UI Demo - Restaurant Finder", 900, 700), component).run()

    except A2UIClientError as e:
        print(f"Error: {e}")
        sys.exit(1)


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Connect to a Google A2UI sample agent and render its UI"
    )
    parser.add_argument(
        "--url",
        default="http://localhost:10002",
        help="Agent URL (default: http://localhost:10002 for Restaurant Finder)",
    )
    parser.add_argument(
        "--query",
        default=None,
        help="Query to send to the agent",
    )

    args = parser.parse_args()
    run_demo(args.url, args.query)


if __name__ == "__main__":
    main()
