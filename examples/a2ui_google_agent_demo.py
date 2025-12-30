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

import asyncio
import json
import sys
from typing import Any

try:
    import httpx
except ImportError:
    print("This example requires httpx. Install with: pip install httpx")
    sys.exit(1)

from castella import App
from castella.a2ui import A2UIComponent, A2UIRenderer, UserAction
from castella.frame import Frame


# A2UI Extension constants (from Google's A2UI SDK)
A2UI_EXTENSION_URI = "https://a2ui.org/a2a-extension/a2ui/v0.8"
A2UI_MIME_TYPE = "application/json+a2ui"


def is_a2ui_part(part: dict[str, Any]) -> bool:
    """Check if a message part contains A2UI data."""
    # Check if it's a data part with A2UI content
    if part.get("kind") == "data" and "data" in part:
        data = part["data"]
        # Check for A2UI message keys
        a2ui_keys = ["beginRendering", "surfaceUpdate", "dataModelUpdate",
                     "createSurface", "updateComponents", "updateDataModel", "deleteSurface"]
        return any(key in data for key in a2ui_keys)
    # Alternative: check metadata mimeType
    if "data" in part:
        metadata = part.get("metadata", {})
        return metadata.get("mimeType") == A2UI_MIME_TYPE
    return False


def extract_a2ui_data(response: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract A2UI messages from an A2A response.

    Returns a list of A2UI message dicts (createSurface, updateComponents, etc.)
    """
    a2ui_messages = []

    # Navigate to the message parts
    # Response structure: {result: {status: {message: {parts: [...]}}, history: [...]}}
    result = response.get("result", response)

    # Check status.message.parts (main response)
    status = result.get("status", {})
    status_message = status.get("message", {})
    status_parts = status_message.get("parts", [])
    for part in status_parts:
        if is_a2ui_part(part):
            a2ui_data = part.get("data", {})
            if a2ui_data:
                a2ui_messages.append(a2ui_data)

    # Check artifacts
    artifacts = result.get("artifacts", [])
    for artifact in artifacts:
        parts = artifact.get("parts", [])
        for part in parts:
            if is_a2ui_part(part):
                a2ui_data = part.get("data", {})
                if a2ui_data:
                    a2ui_messages.append(a2ui_data)

    # Check history messages
    history = result.get("history", [])
    for msg in history:
        parts = msg.get("parts", [])
        for part in parts:
            if is_a2ui_part(part):
                a2ui_data = part.get("data", {})
                if a2ui_data:
                    a2ui_messages.append(a2ui_data)

    return a2ui_messages


async def send_message(
    base_url: str,
    message: str,
    context_id: str | None = None,
) -> dict[str, Any]:
    """Send a message to an A2A agent and get the response.

    Args:
        base_url: The agent's base URL (e.g., "http://localhost:10002")
        message: The user message to send
        context_id: Optional conversation context ID

    Returns:
        The A2A response dict
    """
    import uuid

    async with httpx.AsyncClient(timeout=60.0) as client:
        # Construct A2A message with required fields
        message_id = str(uuid.uuid4())
        request_body = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "message/send",
            "params": {
                "message": {
                    "messageId": message_id,
                    "parts": [{"text": message}],
                    "role": "user",
                },
                "configuration": {
                    "acceptedOutputModes": ["text", "application/json+a2ui"],
                    "extensions": [
                        {
                            "uri": A2UI_EXTENSION_URI,
                            "params": {
                                "a2uiClientCapabilities": {
                                    "supportedCatalogIds": [
                                        "https://raw.githubusercontent.com/google/A2UI/refs/heads/main/specification/0.9/json/standard_catalog_definition.json"
                                    ]
                                }
                            }
                        }
                    ]
                }
            }
        }

        if context_id:
            request_body["params"]["contextId"] = context_id

        response = await client.post(
            f"{base_url}/",
            json=request_body,
            headers={
                "Content-Type": "application/json",
                "X-A2A-Extensions": A2UI_EXTENSION_URI,
            },
        )
        response.raise_for_status()
        return response.json()


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

    # Create renderer with action handler
    renderer = A2UIRenderer()
    context_id = None

    def on_action(action: UserAction):
        """Handle user actions from the UI."""
        nonlocal context_id
        print(f"Action: {action.name}")
        print(f"  Source: {action.source_component_id}")
        print(f"  Context: {action.context}")

        # For now, just print the action
        # In a real app, you would send this back to the agent

    renderer._on_action = on_action

    async def fetch_and_render():
        nonlocal context_id

        # Send message to agent
        response = await send_message(agent_url, query)

        # Debug: print raw response
        print("Response received:")
        print(json.dumps(response, indent=2)[:2000])
        print()

        # Extract A2UI messages
        a2ui_messages = extract_a2ui_data(response)

        if not a2ui_messages:
            print("No A2UI data found in response.")
            print("The agent may not have returned UI components.")
            return None

        print(f"Found {len(a2ui_messages)} A2UI message(s)")

        # Process each A2UI message
        surface = None
        for msg in a2ui_messages:
            print(f"Processing: {list(msg.keys())}")
            surface = renderer.handle_message(msg)

        return surface or renderer.get_surface("default")

    # Run async fetch
    surface = asyncio.run(fetch_and_render())

    if surface is None:
        print("Failed to create surface. Check the agent response.")
        return

    print("Surface created successfully!")
    print("Launching Castella UI...")

    # Create component and run app
    component = A2UIComponent(surface)
    App(Frame("A2UI Demo - Restaurant Finder", 900, 700), component).run()


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
