"""Transport layer for A2UI streaming connections.

This module provides utilities for connecting to A2UI servers using
various streaming transports (SSE, WebSocket, raw HTTP).

These are optional features that require additional dependencies:
- SSE: requires `httpx`
- WebSocket: requires `websockets`

Example:
    from castella.a2ui import A2UIRenderer
    from castella.a2ui.transports import sse_stream, websocket_stream

    renderer = A2UIRenderer()

    # SSE streaming
    async for surface in renderer.handle_stream_async(
        await sse_stream("http://agent.example.com/ui")
    ):
        app.redraw()

    # WebSocket streaming
    async for surface in renderer.handle_stream_async(
        await websocket_stream("ws://agent.example.com/ui")
    ):
        app.redraw()
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterator
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    pass


class TransportError(Exception):
    """Base exception for transport errors."""

    pass


class SSEConnectionError(TransportError):
    """Error connecting to SSE endpoint."""

    pass


class WebSocketConnectionError(TransportError):
    """Error connecting to WebSocket endpoint."""

    pass


async def sse_stream(
    url: str,
    headers: dict[str, str] | None = None,
    timeout: float = 30.0,
) -> AsyncIterator[str]:
    """Connect to an SSE (Server-Sent Events) endpoint and yield data lines.

    Args:
        url: The SSE endpoint URL
        headers: Optional HTTP headers
        timeout: Connection timeout in seconds

    Yields:
        Data strings from SSE "data:" events

    Raises:
        SSEConnectionError: If connection fails
        ImportError: If httpx is not installed

    Example:
        async for data in sse_stream("http://agent.example.com/events"):
            message = ServerMessage.model_validate_json(data)
            renderer.handle_message(message)
    """
    try:
        import httpx
    except ImportError as e:
        raise ImportError(
            "httpx is required for SSE support. Install with: pip install httpx"
        ) from e

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            async with client.stream(
                "GET",
                url,
                headers={
                    "Accept": "text/event-stream",
                    "Cache-Control": "no-cache",
                    **(headers or {}),
                },
            ) as response:
                response.raise_for_status()

                async for line in response.aiter_lines():
                    # SSE format: "data: <json>\n\n"
                    if line.startswith("data:"):
                        data = line[5:].strip()
                        if data:
                            yield data + "\n"  # Add newline for JSONL parser
                    elif line.startswith("event:"):
                        # Could handle different event types here
                        pass
                    elif line.strip() == "":
                        # Empty line signals end of event
                        pass

    except httpx.HTTPStatusError as e:
        raise SSEConnectionError(f"HTTP error {e.response.status_code}: {e}") from e
    except httpx.RequestError as e:
        raise SSEConnectionError(f"Connection error: {e}") from e


async def websocket_stream(
    url: str,
    extra_headers: dict[str, str] | None = None,
    ping_interval: float | None = 20.0,
    ping_timeout: float | None = 20.0,
) -> AsyncIterator[str]:
    """Connect to a WebSocket endpoint and yield messages.

    Args:
        url: The WebSocket URL (ws:// or wss://)
        extra_headers: Optional additional headers
        ping_interval: Interval between pings (None to disable)
        ping_timeout: Timeout waiting for pong response

    Yields:
        Message strings from the WebSocket

    Raises:
        WebSocketConnectionError: If connection fails
        ImportError: If websockets is not installed

    Example:
        async for data in websocket_stream("ws://agent.example.com/ui"):
            message = ServerMessage.model_validate_json(data)
            renderer.handle_message(message)
    """
    try:
        import websockets
    except ImportError as e:
        raise ImportError(
            "websockets is required for WebSocket support. Install with: pip install websockets"
        ) from e

    try:
        async with websockets.connect(
            url,
            extra_headers=extra_headers or {},
            ping_interval=ping_interval,
            ping_timeout=ping_timeout,
        ) as websocket:
            async for message in websocket:
                if isinstance(message, bytes):
                    message = message.decode("utf-8")
                yield message + "\n"  # Add newline for JSONL parser

    except websockets.exceptions.WebSocketException as e:
        raise WebSocketConnectionError(f"WebSocket error: {e}") from e
    except Exception as e:
        raise WebSocketConnectionError(f"Connection error: {e}") from e


def http_post_stream(
    url: str,
    data: dict[str, Any] | str,
    headers: dict[str, str] | None = None,
    timeout: float = 30.0,
) -> Iterator[str]:
    """Make an HTTP POST request with streaming response (synchronous).

    Useful for streaming responses from agent endpoints that use
    HTTP POST for requests but return streaming JSONL.

    Args:
        url: The endpoint URL
        data: Request body (dict will be JSON-encoded)
        headers: Optional HTTP headers
        timeout: Connection timeout in seconds

    Yields:
        Lines from the streaming response

    Raises:
        TransportError: If request fails
        ImportError: If httpx is not installed

    Example:
        for line in http_post_stream(
            "http://agent.example.com/chat",
            {"message": "Hello"}
        ):
            message = ServerMessage.model_validate_json(line)
            renderer.handle_message(message)
    """
    try:
        import httpx
    except ImportError as e:
        raise ImportError(
            "httpx is required for HTTP streaming. Install with: pip install httpx"
        ) from e

    import json as json_module

    request_headers = {
        "Content-Type": "application/json",
        "Accept": "application/x-ndjson",
        **(headers or {}),
    }

    if isinstance(data, dict):
        body = json_module.dumps(data)
    else:
        body = data

    try:
        with httpx.Client(timeout=timeout) as client:
            with client.stream(
                "POST",
                url,
                content=body,
                headers=request_headers,
            ) as response:
                response.raise_for_status()

                for line in response.iter_lines():
                    if line.strip():
                        yield line + "\n"

    except httpx.HTTPStatusError as e:
        raise TransportError(f"HTTP error {e.response.status_code}: {e}") from e
    except httpx.RequestError as e:
        raise TransportError(f"Request error: {e}") from e


async def http_post_stream_async(
    url: str,
    data: dict[str, Any] | str,
    headers: dict[str, str] | None = None,
    timeout: float = 30.0,
) -> AsyncIterator[str]:
    """Make an HTTP POST request with streaming response (asynchronous).

    Args:
        url: The endpoint URL
        data: Request body (dict will be JSON-encoded)
        headers: Optional HTTP headers
        timeout: Connection timeout in seconds

    Yields:
        Lines from the streaming response

    Raises:
        TransportError: If request fails
        ImportError: If httpx is not installed

    Example:
        async for line in http_post_stream_async(
            "http://agent.example.com/chat",
            {"message": "Hello"}
        ):
            message = ServerMessage.model_validate_json(line)
            renderer.handle_message(message)
    """
    try:
        import httpx
    except ImportError as e:
        raise ImportError(
            "httpx is required for HTTP streaming. Install with: pip install httpx"
        ) from e

    import json as json_module

    request_headers = {
        "Content-Type": "application/json",
        "Accept": "application/x-ndjson",
        **(headers or {}),
    }

    if isinstance(data, dict):
        body = json_module.dumps(data)
    else:
        body = data

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            async with client.stream(
                "POST",
                url,
                content=body,
                headers=request_headers,
            ) as response:
                response.raise_for_status()

                async for line in response.aiter_lines():
                    if line.strip():
                        yield line + "\n"

    except httpx.HTTPStatusError as e:
        raise TransportError(f"HTTP error {e.response.status_code}: {e}") from e
    except httpx.RequestError as e:
        raise TransportError(f"Request error: {e}") from e
