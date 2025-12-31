"""Castella MCP (Model Context Protocol) support.

This module provides MCP server functionality for Castella applications,
enabling AI agents to introspect and control UIs programmatically.

Installation:
    pip install castella[mcp]

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
"""

from __future__ import annotations

# Check for MCP dependency
try:
    from mcp.server.fastmcp import FastMCP  # noqa: F401
except ImportError as e:
    raise ImportError(
        "MCP support requires the 'mcp' package. "
        "Install with: pip install castella[mcp] "
        "or: pip install mcp"
    ) from e

# Public API
from .server import CastellaMCPServer
from .registry import SemanticWidgetRegistry
from .introspection import WidgetIntrospector
from .watcher import CommandWatcher, CommandQueue
from .types import (
    ElementInfo,
    UITreeNode,
    FocusInfo,
    ActionResult,
    WidgetMetadata,
)

__all__ = [
    # Main server class
    "CastellaMCPServer",
    # Command control
    "CommandWatcher",
    "CommandQueue",
    # Registry and introspection
    "SemanticWidgetRegistry",
    "WidgetIntrospector",
    # Data types
    "ElementInfo",
    "UITreeNode",
    "FocusInfo",
    "ActionResult",
    "WidgetMetadata",
]
