"""A2UI Client for connecting to A2A agents with A2UI extension.

This module provides a client for communicating with A2A (Agent-to-Agent)
protocol agents that support the A2UI extension. The client handles:
- A2A protocol communication via HTTP/JSON-RPC
- A2UI extension negotiation
- Extracting A2UI messages from responses
- Integrating with A2UIRenderer

Example:
    from castella import App
    from castella.a2ui import A2UIClient, A2UIComponent
    from castella.frame import Frame

    # Connect to agent
    client = A2UIClient("http://localhost:10002")

    # Send message and get UI surface
    surface = client.send("Find me restaurants in Tokyo")

    if surface:
        App(Frame("Demo", 800, 600), A2UIComponent(surface)).run()

Async example:
    async def main():
        client = A2UIClient("http://localhost:10002")
        surface = await client.send_async("Hello!")
        if surface:
            print("Got surface:", surface.surface_id)
"""

from __future__ import annotations

import asyncio
import uuid
from typing import TYPE_CHECKING, Any, Callable

from castella.a2ui.renderer import A2UIRenderer, A2UISurface
from castella.a2ui.types import UserAction

if TYPE_CHECKING:
    pass


# A2UI Extension constants
A2UI_EXTENSION_URI = "https://a2ui.org/a2a-extension/a2ui/v0.8"
A2UI_MIME_TYPE = "application/json+a2ui"
A2UI_CATALOG_URL = "https://raw.githubusercontent.com/google/A2UI/refs/heads/main/specification/0.9/json/standard_catalog_definition.json"


class A2UIClientError(Exception):
    """Base exception for A2UI client errors."""

    pass


class A2UIConnectionError(A2UIClientError):
    """Failed to connect to A2A agent."""

    pass


class A2UIResponseError(A2UIClientError):
    """Error in A2A agent response."""

    pass


def _is_a2ui_part(part: dict[str, Any]) -> bool:
    """Check if a message part contains A2UI data."""
    if part.get("kind") == "data" and "data" in part:
        data = part["data"]
        a2ui_keys = [
            "beginRendering",
            "surfaceUpdate",
            "dataModelUpdate",
            "createSurface",
            "updateComponents",
            "updateDataModel",
            "deleteSurface",
        ]
        return any(key in data for key in a2ui_keys)
    if "data" in part:
        metadata = part.get("metadata", {})
        return metadata.get("mimeType") == A2UI_MIME_TYPE
    return False


def _extract_a2ui_data(
    response: dict[str, Any], debug: bool = False
) -> list[dict[str, Any]]:
    """Extract A2UI messages from an A2A response.

    Args:
        response: The A2A JSON-RPC response
        debug: If True, print debug information

    Returns:
        List of A2UI message dicts
    """
    a2ui_messages: list[dict[str, Any]] = []
    result = response.get("result", response)

    if debug:
        print(f"[DEBUG] Response result keys: {list(result.keys())}")

    # Check status.message.parts
    status = result.get("status", {})
    status_message = status.get("message", {})
    parts = status_message.get("parts", [])
    if debug:
        print(f"[DEBUG] status.message.parts count: {len(parts)}")
    for i, part in enumerate(parts):
        if debug:
            print(
                f"[DEBUG]   Part {i}: keys={list(part.keys())}, is_a2ui={_is_a2ui_part(part)}"
            )
        if _is_a2ui_part(part):
            a2ui_data = part.get("data", {})
            if a2ui_data:
                a2ui_messages.append(a2ui_data)

    # Check artifacts
    artifacts = result.get("artifacts", [])
    if debug and artifacts:
        print(f"[DEBUG] artifacts count: {len(artifacts)}")
    for artifact in artifacts:
        for part in artifact.get("parts", []):
            if _is_a2ui_part(part):
                a2ui_data = part.get("data", {})
                if a2ui_data:
                    a2ui_messages.append(a2ui_data)

    # Check history messages
    history = result.get("history", [])
    if debug and history:
        print(f"[DEBUG] history count: {len(history)}")
    for msg in history:
        for part in msg.get("parts", []):
            if _is_a2ui_part(part):
                a2ui_data = part.get("data", {})
                if a2ui_data:
                    a2ui_messages.append(a2ui_data)

    return a2ui_messages


class A2UIClient:
    """Client for A2A agents that support A2UI extension.

    This client communicates with A2A (Agent-to-Agent) protocol agents
    and handles the A2UI extension for generating UI surfaces.

    Example:
        # Basic usage
        client = A2UIClient("http://localhost:10002")
        surface = client.send("Find me restaurants in Tokyo")
        if surface:
            widget = surface.root_widget

        # With action handler
        def on_action(action):
            print(f"User clicked: {action.name}")

        client = A2UIClient(
            "http://localhost:10002",
            on_action=on_action
        )

        # Async usage
        async def main():
            client = A2UIClient("http://localhost:10002")
            surface = await client.send_async("Hello!")
    """

    def __init__(
        self,
        agent_url: str,
        renderer: A2UIRenderer | None = None,
        on_action: Callable[[UserAction], None] | None = None,
        timeout: float = 60.0,
    ):
        """Initialize the A2UI client.

        Args:
            agent_url: URL of the A2A agent (e.g., "http://localhost:10002")
            renderer: Optional A2UIRenderer instance. Creates one if not provided.
            on_action: Callback for user actions from the UI
            timeout: Request timeout in seconds
        """
        self._agent_url = agent_url.rstrip("/")
        self._timeout = timeout
        self._context_id: str | None = None
        self._current_surface: A2UISurface | None = None
        self._request_id = 0

        # Create or use provided renderer
        if renderer is not None:
            self._renderer = renderer
            if on_action is not None:
                self._renderer._on_action = on_action
        else:
            self._renderer = A2UIRenderer(on_action=on_action)

        self._on_action = on_action

    @property
    def agent_url(self) -> str:
        """Get the agent URL."""
        return self._agent_url

    @property
    def context_id(self) -> str | None:
        """Get the current conversation context ID."""
        return self._context_id

    @property
    def current_surface(self) -> A2UISurface | None:
        """Get the most recently created surface."""
        return self._current_surface

    @property
    def renderer(self) -> A2UIRenderer:
        """Get the A2UI renderer instance."""
        return self._renderer

    def _build_request(
        self,
        message: str | None = None,
        action: UserAction | None = None,
    ) -> dict[str, Any]:
        """Build an A2A JSON-RPC request.

        Args:
            message: Text message to send
            action: User action to send

        Returns:
            JSON-RPC request dict
        """
        self._request_id += 1
        message_id = str(uuid.uuid4())

        # Build message parts
        parts: list[dict[str, Any]] = []
        if message:
            parts.append({"text": message})
        if action:
            parts.append(
                {
                    "kind": "data",
                    "data": {
                        "action": action.name,
                        "sourceComponentId": action.source_component_id,
                        "context": action.context,
                    },
                }
            )

        request: dict[str, Any] = {
            "jsonrpc": "2.0",
            "id": self._request_id,
            "method": "message/send",
            "params": {
                "message": {
                    "messageId": message_id,
                    "parts": parts,
                    "role": "user",
                },
                "configuration": {
                    "acceptedOutputModes": ["text", A2UI_MIME_TYPE],
                    "extensions": [
                        {
                            "uri": A2UI_EXTENSION_URI,
                            "params": {
                                "a2uiClientCapabilities": {
                                    "supportedCatalogIds": [A2UI_CATALOG_URL]
                                }
                            },
                        }
                    ],
                },
            },
        }

        if self._context_id:
            request["params"]["contextId"] = self._context_id

        return request

    def _process_response(
        self, response: dict[str, Any], debug: bool = False
    ) -> A2UISurface | None:
        """Process an A2A response and extract A2UI surface.

        Args:
            response: The A2A JSON-RPC response
            debug: If True, print debug information

        Returns:
            The rendered A2UI surface, or None if no A2UI data found
        """
        # Check for errors
        if "error" in response:
            error = response["error"]
            raise A2UIResponseError(
                f"Agent error {error.get('code', 'unknown')}: {error.get('message', 'Unknown error')}"
            )

        # Extract context ID for conversation continuity
        result = response.get("result", {})
        if "contextId" in result:
            self._context_id = result["contextId"]

        # Extract A2UI messages
        a2ui_messages = _extract_a2ui_data(response, debug=debug)
        if debug:
            import json

            print(f"[DEBUG] Extracted {len(a2ui_messages)} A2UI messages:")
            for i, msg in enumerate(a2ui_messages):
                print(f"  [{i}] keys: {list(msg.keys())}")
                print(f"      {json.dumps(msg, indent=2)[:500]}...")

        if not a2ui_messages:
            return None

        # Process each A2UI message through the renderer
        surface: A2UISurface | None = None
        for msg in a2ui_messages:
            if debug:
                print(f"[DEBUG] Processing message: {list(msg.keys())}")
            result_surface = self._renderer.handle_message(msg)
            if debug:
                print(f"[DEBUG]   -> surface: {result_surface}")
            if result_surface is not None:
                surface = result_surface

        # Try to get the default surface if none was returned
        if surface is None:
            surface = self._renderer.get_surface("default")
            if debug:
                print(f"[DEBUG] Fallback to default surface: {surface}")

        self._current_surface = surface
        return surface

    async def send_async(
        self, message: str, *, debug: bool = False
    ) -> A2UISurface | None:
        """Send a message to the agent asynchronously.

        Args:
            message: The message to send
            debug: If True, print debug information

        Returns:
            The A2UI surface from the response, or None if no UI generated

        Raises:
            A2UIConnectionError: If connection fails
            A2UIResponseError: If agent returns an error
        """
        try:
            import httpx
        except ImportError as e:
            raise ImportError(
                "httpx is required for A2UIClient. Install with: pip install httpx"
            ) from e

        request = self._build_request(message=message)

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(
                    f"{self._agent_url}/",
                    json=request,
                    headers={
                        "Content-Type": "application/json",
                        "X-A2A-Extensions": A2UI_EXTENSION_URI,
                    },
                )
                response.raise_for_status()
                return self._process_response(response.json(), debug=debug)

        except httpx.ConnectError as e:
            raise A2UIConnectionError(
                f"Cannot connect to {self._agent_url}: {e}"
            ) from e
        except httpx.HTTPStatusError as e:
            raise A2UIConnectionError(
                f"HTTP error {e.response.status_code}: {e}"
            ) from e
        except httpx.RequestError as e:
            raise A2UIConnectionError(f"Request error: {e}") from e

    def send(self, message: str, *, debug: bool = False) -> A2UISurface | None:
        """Send a message to the agent synchronously.

        Args:
            message: The message to send
            debug: If True, print debug information

        Returns:
            The A2UI surface from the response, or None if no UI generated

        Raises:
            A2UIConnectionError: If connection fails
            A2UIResponseError: If agent returns an error
        """
        return asyncio.run(self.send_async(message, debug=debug))

    async def send_action_async(self, action: UserAction) -> A2UISurface | None:
        """Send a user action to the agent asynchronously.

        Use this to send button clicks, form submissions, etc. back to the agent.

        Args:
            action: The user action to send

        Returns:
            The updated A2UI surface, or None if no UI update

        Raises:
            A2UIConnectionError: If connection fails
            A2UIResponseError: If agent returns an error
        """
        try:
            import httpx
        except ImportError as e:
            raise ImportError(
                "httpx is required for A2UIClient. Install with: pip install httpx"
            ) from e

        request = self._build_request(action=action)

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(
                    f"{self._agent_url}/",
                    json=request,
                    headers={
                        "Content-Type": "application/json",
                        "X-A2A-Extensions": A2UI_EXTENSION_URI,
                    },
                )
                response.raise_for_status()
                return self._process_response(response.json())

        except httpx.ConnectError as e:
            raise A2UIConnectionError(
                f"Cannot connect to {self._agent_url}: {e}"
            ) from e
        except httpx.HTTPStatusError as e:
            raise A2UIConnectionError(
                f"HTTP error {e.response.status_code}: {e}"
            ) from e
        except httpx.RequestError as e:
            raise A2UIConnectionError(f"Request error: {e}") from e

    def send_action(self, action: UserAction) -> A2UISurface | None:
        """Send a user action to the agent synchronously.

        Args:
            action: The user action to send

        Returns:
            The updated A2UI surface, or None if no UI update
        """
        return asyncio.run(self.send_action_async(action))

    def reset_context(self) -> None:
        """Reset the conversation context.

        Call this to start a new conversation with the agent.
        """
        self._context_id = None
        self._current_surface = None

    def __repr__(self) -> str:
        return f"A2UIClient({self._agent_url!r})"
