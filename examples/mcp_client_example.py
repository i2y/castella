"""MCP Client Example - Connect to a Castella MCP server.

This example demonstrates how to use the MCP Python SDK to connect
to a Castella application and control it programmatically.

The client spawns the Castella app as a subprocess and communicates
via the MCP protocol over stdio.

Usage:
    python examples/mcp_client_example.py
"""

import asyncio
import json
import sys
from contextlib import asynccontextmanager

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


# The Castella app to control (as a separate script)
CASTELLA_APP_CODE = '''
from castella import App, Column, Row, Button, Text, Input, CheckBox, Component, State
from castella.frame import Frame
from castella.mcp import CastellaMCPServer

class DemoApp(Component):
    def __init__(self):
        super().__init__()
        self._name = State("")
        self._counter = State(0)
        self._checked = State(False)
        self._name.attach(self)
        self._counter.attach(self)
        self._checked.attach(self)

    def view(self):
        return Column(
            Text("MCP Client Demo").semantic_id("title").fixed_height(40),
            Row(
                Text("Name:").fixed_width(60),
                Input(self._name()).semantic_id("name-input").on_change(lambda t: self._name.set(t)),
            ).fixed_height(40),
            Text(f"Hello, {self._name() or 'World'}!").semantic_id("greeting").fixed_height(35),
            Row(
                Button("-").semantic_id("decrement-btn").on_click(lambda _: self._counter.set(self._counter() - 1)).fixed_width(50),
                Text(f" {self._counter()} ").semantic_id("counter").fixed_width(80),
                Button("+").semantic_id("increment-btn").on_click(lambda _: self._counter.set(self._counter() + 1)).fixed_width(50),
            ).fixed_height(40),
            Row(
                CheckBox(self._checked).semantic_id("feature-checkbox").on_change(lambda c: self._checked.set(c)),
                Text("ON" if self._checked() else "OFF").semantic_id("checkbox-label"),
            ).fixed_height(35),
        )

frame = Frame("MCP Client Demo", 350, 250)
app = App(frame, DemoApp())
mcp = CastellaMCPServer(app, name="castella-demo")
mcp.run()  # This runs the MCP server on stdio (blocks for client connection)
'''


@asynccontextmanager
async def create_castella_client():
    """Create an MCP client connected to a Castella app."""
    # Write the Castella app to a temp file
    import tempfile
    import os

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(CASTELLA_APP_CODE)
        app_path = f.name

    try:
        server_params = StdioServerParameters(
            command=sys.executable,
            args=[app_path],
        )

        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # Initialize the connection
                await session.initialize()
                yield session
    finally:
        os.unlink(app_path)


async def demo_mcp_client():
    """Demonstrate MCP client operations."""
    print("=" * 60)
    print("MCP Client Example")
    print("=" * 60)
    print()
    print("Connecting to Castella MCP server...")
    print()

    async with create_castella_client() as client:
        # 1. List available tools
        print("1. Available Tools:")
        print("-" * 40)
        tools = await client.list_tools()
        for tool in tools.tools:
            print(f"   - {tool.name}: {tool.description[:50]}...")
        print()

        # 2. List available resources
        print("2. Available Resources:")
        print("-" * 40)
        resources = await client.list_resources()
        for res in resources.resources:
            print(f"   - {res.uri}: {res.name}")
        print()

        # 3. Read the UI tree
        print("3. Reading UI Tree (ui://tree):")
        print("-" * 40)
        tree_response = await client.read_resource("ui://tree")
        if tree_response.contents:
            tree_data = json.loads(tree_response.contents[0].text)
            print_tree(tree_data)
        print()

        # 4. List actionable elements
        print("4. Calling list_actionable() tool:")
        print("-" * 40)
        result = await client.call_tool("list_actionable", {})
        if result.content:
            elements = json.loads(result.content[0].text)
            for elem in elements:
                print(f"   - {elem['id']}: {elem['type']} ({elem.get('label', 'no label')})")
        print()

        # 5. Interact with the UI
        print("5. Interacting with the UI:")
        print("-" * 40)

        # Type a name
        print("   Typing 'Claude' into name-input...")
        result = await client.call_tool("type_text_tool", {
            "element_id": "name-input",
            "text": "Claude",
            "replace": True,
        })
        print(f"   Result: {json.loads(result.content[0].text)}")

        # Click increment button 3 times
        for i in range(3):
            print(f"   Clicking increment-btn ({i+1}/3)...")
            result = await client.call_tool("click", {"element_id": "increment-btn"})

        # Toggle checkbox
        print("   Toggling feature-checkbox...")
        result = await client.call_tool("toggle", {"element_id": "feature-checkbox"})
        print(f"   Result: {json.loads(result.content[0].text)}")

        print()

        # 6. Read UI elements again to see changes
        print("6. Reading elements after changes:")
        print("-" * 40)
        result = await client.call_tool("list_actionable", {})
        if result.content:
            elements = json.loads(result.content[0].text)
            for elem in elements:
                if isinstance(elem, dict):
                    value_str = ""
                    if elem.get('value') is not None:
                        value_str = f", value={elem['value']}"
                    print(f"   - {elem['id']}: {elem['type']}{value_str}")
                else:
                    print(f"   - {elem}")
        print()

        print("=" * 60)
        print("Demo complete!")
        print("=" * 60)


def print_tree(node, indent=0):
    """Pretty print a UI tree node."""
    prefix = "   " + "  " * indent
    print(f"{prefix}{node['id']} ({node['type']})")
    for child in node.get('children', []):
        print_tree(child, indent + 1)


if __name__ == "__main__":
    asyncio.run(demo_mcp_client())
