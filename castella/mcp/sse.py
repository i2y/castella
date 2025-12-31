"""SSE (Server-Sent Events) transport for MCP server.

This module provides an SSE transport layer for the Castella MCP server,
allowing clients to connect to an already-running Castella app via HTTP.

Usage:
    from castella.mcp import CastellaMCPServer

    mcp = CastellaMCPServer(app, name="my-app")
    mcp.run_sse(port=8765)  # Starts HTTP server with SSE endpoint
"""

from __future__ import annotations

import json
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import TYPE_CHECKING, Any, Callable
from urllib.parse import urlparse
import queue

if TYPE_CHECKING:
    from .server import CastellaMCPServer


class SSEHandler(BaseHTTPRequestHandler):
    """HTTP request handler for SSE transport."""

    server: "SSEServer"

    def log_message(self, format: str, *args: Any) -> None:
        """Suppress default logging."""
        pass

    def do_GET(self) -> None:
        """Handle GET requests (SSE stream)."""
        parsed = urlparse(self.path)

        if parsed.path == "/sse":
            self._handle_sse()
        elif parsed.path == "/health":
            self._send_json({"status": "ok"})
        else:
            self.send_error(404)

    def do_POST(self) -> None:
        """Handle POST requests (MCP commands)."""
        parsed = urlparse(self.path)

        if parsed.path == "/message":
            self._handle_message()
        else:
            self.send_error(404)

    def _handle_sse(self) -> None:
        """Handle SSE connection for event streaming."""
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

        # Register this connection
        client_id = id(self)
        self.server.register_client(client_id, self)

        try:
            # Send initial connection event
            self._send_event("connected", {"client_id": str(client_id)})

            # Keep connection open and send events
            while not self.server.shutdown_flag.is_set():
                try:
                    # Check for events to send
                    event = self.server.get_event_for_client(client_id, timeout=1.0)
                    if event:
                        self._send_event(event["type"], event["data"])
                except queue.Empty:
                    # Send heartbeat
                    self._send_event("heartbeat", {})
                except Exception:
                    break
        finally:
            self.server.unregister_client(client_id)

    def _handle_message(self) -> None:
        """Handle incoming MCP message."""
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode("utf-8")
            message = json.loads(body)

            # Process the message
            response = self.server.process_message(message)
            self._send_json(response)
        except Exception as e:
            self._send_json({"error": str(e)}, status=400)

    def _send_json(self, data: dict[str, Any], status: int = 200) -> None:
        """Send JSON response."""
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _send_event(self, event_type: str, data: dict[str, Any]) -> None:
        """Send SSE event."""
        try:
            event = f"event: {event_type}\ndata: {json.dumps(data)}\n\n"
            self.wfile.write(event.encode("utf-8"))
            self.wfile.flush()
        except Exception:
            pass


class SSEServer(HTTPServer):
    """HTTP server with SSE support for MCP."""

    def __init__(
        self,
        address: tuple[str, int],
        mcp_server: "CastellaMCPServer",
    ) -> None:
        super().__init__(address, SSEHandler)
        self.mcp_server = mcp_server
        self.shutdown_flag = threading.Event()
        self._clients: dict[int, SSEHandler] = {}
        self._client_queues: dict[int, queue.Queue] = {}
        self._lock = threading.Lock()

    def register_client(self, client_id: int, handler: SSEHandler) -> None:
        """Register a new SSE client."""
        with self._lock:
            self._clients[client_id] = handler
            self._client_queues[client_id] = queue.Queue()

    def unregister_client(self, client_id: int) -> None:
        """Unregister an SSE client."""
        with self._lock:
            self._clients.pop(client_id, None)
            self._client_queues.pop(client_id, None)

    def get_event_for_client(
        self, client_id: int, timeout: float = 1.0
    ) -> dict[str, Any] | None:
        """Get next event for a client (blocking with timeout)."""
        q = self._client_queues.get(client_id)
        if q:
            return q.get(timeout=timeout)
        return None

    def broadcast_event(self, event_type: str, data: dict[str, Any]) -> None:
        """Broadcast event to all connected clients."""
        with self._lock:
            for q in self._client_queues.values():
                q.put({"type": event_type, "data": data})

    def process_message(self, message: dict[str, Any]) -> dict[str, Any]:
        """Process an MCP message and return response."""
        msg_type = message.get("type", "")
        params = message.get("params", {})

        try:
            if msg_type == "list_resources":
                return self._list_resources()
            elif msg_type == "list_tools":
                return self._list_tools()
            elif msg_type == "read_resource":
                return self._read_resource(params.get("uri", ""))
            elif msg_type == "call_tool":
                return self._call_tool(
                    params.get("name", ""),
                    params.get("arguments", {}),
                )
            else:
                return {"error": f"Unknown message type: {msg_type}"}
        except Exception as e:
            return {"error": str(e)}

    def _list_resources(self) -> dict[str, Any]:
        """List available resources."""
        return {
            "resources": [
                {"uri": "ui://tree", "name": "UI Tree"},
                {"uri": "ui://focus", "name": "Focus Info"},
                {"uri": "ui://elements", "name": "Interactive Elements"},
                {"uri": "a2ui://surfaces", "name": "A2UI Surfaces"},
            ]
        }

    def _list_tools(self) -> dict[str, Any]:
        """List available tools."""
        return {
            "tools": [
                {"name": "click", "description": "Click an element"},
                {"name": "type_text", "description": "Type text into input"},
                {"name": "focus", "description": "Focus an element"},
                {"name": "scroll", "description": "Scroll a container"},
                {"name": "toggle", "description": "Toggle checkbox/switch"},
                {"name": "select", "description": "Select a value"},
                {"name": "list_actionable", "description": "List interactive elements"},
            ]
        }

    def _read_resource(self, uri: str) -> dict[str, Any]:
        """Read a resource."""
        from .resources import (
            get_ui_tree,
            get_focus_info,
            list_elements,
            list_a2ui_surfaces,
        )

        mcp = self.mcp_server
        app = mcp._app
        registry = mcp._registry
        introspector = mcp._introspector

        if uri == "ui://tree":
            return {"contents": [get_ui_tree(app, registry, introspector)]}
        elif uri == "ui://focus":
            return {"contents": [get_focus_info(app, registry, introspector)]}
        elif uri == "ui://elements":
            return {"contents": list_elements(app, registry, introspector)}
        elif uri == "a2ui://surfaces":
            return {"contents": list_a2ui_surfaces(registry)}
        else:
            return {"error": f"Unknown resource: {uri}"}

    def _call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Call a tool."""
        from .tools import (
            click_element,
            type_text,
            focus_element,
            scroll_element,
            toggle_element,
            select_value,
            list_actionable_elements,
        )

        mcp = self.mcp_server
        app = mcp._app
        registry = mcp._registry
        introspector = mcp._introspector

        # Refresh registry before tool call
        root = app._root_widget
        if root is not None:
            registry.rebuild_from_tree(root)

        if name == "click":
            result = click_element(
                arguments.get("element_id", ""),
                registry,
                app,
            )
        elif name == "type_text":
            result = type_text(
                arguments.get("element_id", ""),
                arguments.get("text", ""),
                arguments.get("replace", False),
                registry,
                app,
            )
        elif name == "focus":
            result = focus_element(
                arguments.get("element_id", ""),
                registry,
                app,
            )
        elif name == "scroll":
            result = scroll_element(
                arguments.get("element_id", ""),
                arguments.get("direction", "down"),
                arguments.get("amount", 100),
                registry,
                app,
            )
        elif name == "toggle":
            result = toggle_element(
                arguments.get("element_id", ""),
                registry,
                app,
            )
        elif name == "select":
            result = select_value(
                arguments.get("element_id", ""),
                arguments.get("value", ""),
                registry,
                app,
            )
        elif name == "list_actionable":
            elements = list_actionable_elements(app, registry, introspector)
            return {"content": [e.model_dump() for e in elements]}
        else:
            return {"error": f"Unknown tool: {name}"}

        # Serialize ActionResult to dict
        return {"content": result.model_dump()}


def run_sse_server(
    mcp_server: "CastellaMCPServer",
    host: str = "localhost",
    port: int = 8765,
    on_start: Callable[[], None] | None = None,
) -> SSEServer:
    """Run SSE server in the current thread (blocking).

    Args:
        mcp_server: The CastellaMCPServer instance
        host: Host to bind to
        port: Port to listen on
        on_start: Callback when server starts

    Returns:
        The SSEServer instance
    """
    server = SSEServer((host, port), mcp_server)

    if on_start:
        on_start()

    server.serve_forever()
    return server


def run_sse_server_in_background(
    mcp_server: "CastellaMCPServer",
    host: str = "localhost",
    port: int = 8765,
) -> tuple[SSEServer, threading.Thread]:
    """Run SSE server in a background thread.

    Args:
        mcp_server: The CastellaMCPServer instance
        host: Host to bind to
        port: Port to listen on

    Returns:
        Tuple of (SSEServer, Thread)
    """
    server = SSEServer((host, port), mcp_server)

    thread = threading.Thread(
        target=server.serve_forever,
        daemon=True,
        name="castella-mcp-sse",
    )
    thread.start()

    return server, thread
