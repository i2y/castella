"""MCP Protocol Client - Connect to Castella via MCP protocol.

This client uses the official MCP Python SDK to connect to a Castella
MCP server and control it using MCP resources and tools.

Usage:
    python examples/mcp_protocol_client.py

This will:
1. Spawn the Castella MCP server as a subprocess
2. Connect via MCP protocol (stdio transport)
3. List resources and tools
4. Read the UI tree
5. Call tools to interact with the UI
"""

import asyncio
import json
import sys
import os

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main():
    print("=" * 60)
    print("MCP Protocol Client - Controlling Castella via MCP")
    print("=" * 60)
    print()

    # Path to the MCP server script
    server_script = os.path.join(os.path.dirname(__file__), "mcp_stdio_server.py")

    # Server parameters - spawn the Castella app as MCP server
    server_params = StdioServerParameters(
        command=sys.executable,
        args=[server_script],
        env=None,
    )

    print("Connecting to Castella MCP server...")
    print()

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the MCP session
            result = await session.initialize()
            print(f"Connected! Server: {result.serverInfo.name}")
            print()

            # ─────────────────────────────────────────────
            # 1. List available resources
            # ─────────────────────────────────────────────
            print("1. Available MCP Resources:")
            print("-" * 40)
            resources = await session.list_resources()
            for res in resources.resources:
                print(f"   {res.uri}")
                print(f"      {res.description or res.name}")
            print()

            # ─────────────────────────────────────────────
            # 2. List available tools
            # ─────────────────────────────────────────────
            print("2. Available MCP Tools:")
            print("-" * 40)
            tools = await session.list_tools()
            for tool in tools.tools:
                desc = (tool.description or "")[:50]
                print(f"   {tool.name}")
                print(f"      {desc}...")
            print()

            # ─────────────────────────────────────────────
            # 3. Read UI tree resource
            # ─────────────────────────────────────────────
            print("3. Reading ui://tree resource:")
            print("-" * 40)
            try:
                tree_result = await session.read_resource("ui://tree")
                if tree_result.contents:
                    tree_data = json.loads(tree_result.contents[0].text)
                    print_tree(tree_data, indent=3)
            except Exception as e:
                print(f"   Error: {e}")
            print()

            # ─────────────────────────────────────────────
            # 4. Read elements resource
            # ─────────────────────────────────────────────
            print("4. Reading ui://elements resource:")
            print("-" * 40)
            try:
                elements_result = await session.read_resource("ui://elements")
                if elements_result.contents:
                    elements = json.loads(elements_result.contents[0].text)
                    for elem in elements:
                        print(f"   {elem['id']}: {elem['type']} - {elem.get('label', '')}")
            except Exception as e:
                print(f"   Error: {e}")
            print()

            # ─────────────────────────────────────────────
            # 5. Call list_actionable tool
            # ─────────────────────────────────────────────
            print("5. Calling 'list_actionable' tool:")
            print("-" * 40)
            try:
                result = await session.call_tool("list_actionable", {})
                if result.content:
                    elements = json.loads(result.content[0].text)
                    for elem in elements:
                        print(f"   {elem['id']}: {elem['type']}")
            except Exception as e:
                print(f"   Error: {e}")
            print()

            # ─────────────────────────────────────────────
            # 6. Type text into name input
            # ─────────────────────────────────────────────
            print("6. Calling 'type_text_tool' - typing 'Claude':")
            print("-" * 40)
            try:
                result = await session.call_tool("type_text_tool", {
                    "element_id": "name-input",
                    "text": "Claude",
                    "replace": True,
                })
                if result.content:
                    response = json.loads(result.content[0].text)
                    print(f"   Success: {response.get('success')}")
                    print(f"   Message: {response.get('message')}")
            except Exception as e:
                print(f"   Error: {e}")
            print()

            # ─────────────────────────────────────────────
            # 7. Click increment button
            # ─────────────────────────────────────────────
            print("7. Calling 'click' tool - clicking increment button 5 times:")
            print("-" * 40)
            for i in range(5):
                try:
                    result = await session.call_tool("click", {
                        "element_id": "increment-btn",
                    })
                    if result.content:
                        response = json.loads(result.content[0].text)
                        print(f"   Click {i+1}: {response.get('success')}")
                    await asyncio.sleep(0.3)
                except Exception as e:
                    print(f"   Error: {e}")
            print()

            # ─────────────────────────────────────────────
            # 8. Toggle checkbox
            # ─────────────────────────────────────────────
            print("8. Calling 'toggle' tool - toggling checkbox:")
            print("-" * 40)
            try:
                result = await session.call_tool("toggle", {
                    "element_id": "my-checkbox",
                })
                if result.content:
                    response = json.loads(result.content[0].text)
                    print(f"   Success: {response.get('success')}")
                    print(f"   New value: {response.get('new_value')}")
            except Exception as e:
                print(f"   Error: {e}")
            print()

            # ─────────────────────────────────────────────
            # 9. Read focus info
            # ─────────────────────────────────────────────
            print("9. Reading ui://focus resource:")
            print("-" * 40)
            try:
                focus_result = await session.read_resource("ui://focus")
                if focus_result.contents:
                    focus_data = json.loads(focus_result.contents[0].text)
                    print(f"   Focused element: {focus_data.get('element_id')}")
                    print(f"   Type: {focus_data.get('element_type')}")
            except Exception as e:
                print(f"   Error: {e}")
            print()

            print("=" * 60)
            print("Demo complete! The Castella window should show the changes.")
            print("Close the window to exit.")
            print("=" * 60)

            # Keep connection open so user can see the GUI
            try:
                await asyncio.sleep(30)
            except KeyboardInterrupt:
                pass


def print_tree(node, indent=0):
    """Pretty print a UI tree node."""
    prefix = " " * indent
    label = node.get('label', '')
    label_str = f" - '{label}'" if label else ""
    print(f"{prefix}{node['id']} ({node['type']}){label_str}")
    for child in node.get('children', []):
        print_tree(child, indent + 2)


if __name__ == "__main__":
    asyncio.run(main())
