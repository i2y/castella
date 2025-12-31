"""CastellaMCPServer - Main MCP server for Castella UI."""

from __future__ import annotations

import asyncio
import threading
from typing import TYPE_CHECKING, Any

from .registry import SemanticWidgetRegistry
from .introspection import WidgetIntrospector
from .resources import register_resources
from .tools import register_tools

if TYPE_CHECKING:
    from castella.core import App


class CastellaMCPServer:
    """MCP server that exposes Castella UI for AI agents.

    This server allows AI agents to introspect and control Castella UIs
    via the Model Context Protocol (MCP). It provides:

    Resources (read-only data):
    - ui://tree - Complete UI tree structure
    - ui://focus - Currently focused element
    - ui://elements - All interactive elements
    - ui://element/{id} - Specific element details
    - a2ui://surfaces - All A2UI surfaces (if A2UI enabled)

    Tools (actions):
    - click(element_id) - Click/tap an element
    - type_text(element_id, text, replace) - Type into input
    - focus(element_id) - Set focus
    - scroll(element_id, direction, amount) - Scroll container
    - toggle(element_id) - Toggle checkbox/switch
    - select(element_id, value) - Select in picker/tabs
    - list_actionable() - Get interactive elements
    - send_a2ui(message) - Send A2UI message (if A2UI enabled)

    Example:
        ```python
        from castella import App, Frame, Column, Button, Text
        from castella.mcp import CastellaMCPServer

        app = App(
            Frame("Demo", 800, 600),
            Column(
                Text("Hello MCP!").semantic_id("greeting"),
                Button("Click me").semantic_id("btn"),
            )
        )

        # Create and start MCP server
        mcp = CastellaMCPServer(app, name="my-app")
        mcp.run_in_background()

        # Run the Castella app
        app.run()
        ```
    """

    def __init__(
        self,
        app: "App",
        name: str = "castella-ui",
        version: str = "1.0.0",
        a2ui_renderer: Any = None,
    ) -> None:
        """Initialize the MCP server.

        Args:
            app: The Castella App instance to expose
            name: MCP server name (default: "castella-ui")
            version: MCP server version (default: "1.0.0")
            a2ui_renderer: Optional A2UIRenderer for bidirectional A2UI support
        """
        self._app = app
        self._name = name
        self._version = version
        self._a2ui_renderer = a2ui_renderer

        # Create registry and introspector
        self._registry = SemanticWidgetRegistry()
        self._introspector = WidgetIntrospector(self._registry)

        # Create the MCP server
        self._mcp = self._create_mcp_server()

        # Register A2UI surfaces if renderer provided
        if a2ui_renderer is not None:
            self._setup_a2ui_integration()

        # Thread management
        self._thread: threading.Thread | None = None
        self._running = False

    def _create_mcp_server(self) -> Any:
        """Create and configure the FastMCP server."""
        from mcp.server.fastmcp import FastMCP

        mcp = FastMCP(self._name)

        # Register resources
        register_resources(
            mcp,
            self._app,
            self._registry,
            self._introspector,
        )

        # Register tools
        register_tools(
            mcp,
            self._app,
            self._registry,
            self._introspector,
            self._a2ui_renderer,
        )

        return mcp

    def _setup_a2ui_integration(self) -> None:
        """Set up A2UI integration hooks."""
        # Register existing surfaces
        if hasattr(self._a2ui_renderer, "_surfaces"):
            for surface in self._a2ui_renderer._surfaces.values():
                self._registry.register_a2ui_surface(surface)

        # Hook into renderer to register new surfaces
        original_handler = getattr(self._a2ui_renderer, "_on_surface_created", None)

        def on_surface_created(surface: Any) -> None:
            self._registry.register_a2ui_surface(surface)
            if original_handler is not None:
                original_handler(surface)

        self._a2ui_renderer._on_surface_created = on_surface_created

    @property
    def registry(self) -> SemanticWidgetRegistry:
        """Get the semantic widget registry."""
        return self._registry

    @property
    def introspector(self) -> WidgetIntrospector:
        """Get the widget introspector."""
        return self._introspector

    def run(self, transport: str = "stdio") -> None:
        """Run the MCP server (blocking).

        This method blocks until the server is stopped. For non-blocking
        operation, use `run_in_background()`.

        Args:
            transport: Transport mechanism ("stdio" supported)
        """
        if transport != "stdio":
            raise ValueError(
                f"Unsupported transport: {transport}. Only 'stdio' is supported."
            )

        self._running = True
        self._mcp.run(transport=transport)

    def run_in_background(self, transport: str = "stdio") -> threading.Thread:
        """Run the MCP server in a background thread.

        Returns the thread object for management.

        Args:
            transport: Transport mechanism ("stdio" supported)

        Returns:
            The background thread running the server
        """
        if self._thread is not None and self._thread.is_alive():
            raise RuntimeError("MCP server is already running")

        self._thread = threading.Thread(
            target=self._run_in_thread,
            args=(transport,),
            daemon=True,
            name="castella-mcp-server",
        )
        self._thread.start()
        return self._thread

    def _run_in_thread(self, transport: str) -> None:
        """Internal method to run the server in a thread."""
        # Create a new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            self.run(transport)
        finally:
            loop.close()

    def stop(self) -> None:
        """Stop the MCP server.

        Note: For stdio transport, this may not cleanly stop the server
        as it blocks on stdin.
        """
        self._running = False
        # Note: FastMCP doesn't have a clean shutdown mechanism for stdio
        # The thread is daemon, so it will stop when the main program exits

    def is_running(self) -> bool:
        """Check if the server is running."""
        return self._running and (self._thread is None or self._thread.is_alive())

    def refresh_registry(self) -> None:
        """Manually refresh the widget registry.

        Call this after major UI changes if widgets are not being
        detected correctly.
        """
        root = self._app._root_widget
        if root is not None:
            self._registry.rebuild_from_tree(root)

    def run_sse(
        self,
        host: str = "localhost",
        port: int = 8765,
    ) -> None:
        """Run the MCP server with SSE transport (blocking).

        This starts an HTTP server that accepts SSE connections and
        processes MCP messages via HTTP POST.

        Args:
            host: Host to bind to (default: localhost)
            port: Port to listen on (default: 8765)
        """
        from .sse import run_sse_server

        self._running = True
        run_sse_server(self, host, port)

    def run_sse_in_background(
        self,
        host: str = "localhost",
        port: int = 8765,
    ) -> threading.Thread:
        """Run the MCP SSE server in a background thread.

        Args:
            host: Host to bind to (default: localhost)
            port: Port to listen on (default: 8765)

        Returns:
            The background thread running the server
        """
        from .sse import run_sse_server_in_background

        self._running = True
        self._sse_server, thread = run_sse_server_in_background(self, host, port)
        return thread
