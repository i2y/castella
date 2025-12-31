"""MCP SSE Client - Connect to running Castella app via SSE.

This client connects to an already-running Castella MCP server
via HTTP/SSE transport.

Usage:
    1. Start the server first:
       python examples/mcp_sse_server.py

    2. Run this client:
       python examples/mcp_sse_client.py
"""

import json
import time
import urllib.request
import urllib.error


BASE_URL = "http://localhost:8765"


def send_message(msg_type: str, params: dict = None) -> dict:
    """Send MCP message to server."""
    message = {"type": msg_type, "params": params or {}}
    data = json.dumps(message).encode("utf-8")

    req = urllib.request.Request(
        f"{BASE_URL}/message",
        data=data,
        headers={"Content-Type": "application/json"},
    )

    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError as e:
        return {"error": str(e)}


def list_resources() -> list:
    """List available MCP resources."""
    result = send_message("list_resources")
    return result.get("resources", [])


def list_tools() -> list:
    """List available MCP tools."""
    result = send_message("list_tools")
    return result.get("tools", [])


def read_resource(uri: str) -> dict:
    """Read an MCP resource."""
    result = send_message("read_resource", {"uri": uri})
    return result


def call_tool(name: str, **kwargs) -> dict:
    """Call an MCP tool."""
    result = send_message("call_tool", {"name": name, "arguments": kwargs})
    return result


def print_tree(node: dict, indent: int = 0) -> None:
    """Pretty print a UI tree node."""
    prefix = "  " * indent
    label = node.get("label", "")
    label_str = f" - '{label}'" if label else ""
    print(f"{prefix}{node['id']} ({node['type']}){label_str}")
    for child in node.get("children", []):
        print_tree(child, indent + 1)


def main():
    print("=" * 60)
    print("MCP SSE Client - Connecting to Castella")
    print("=" * 60)
    print()

    # Check health
    try:
        req = urllib.request.Request(f"{BASE_URL}/health")
        with urllib.request.urlopen(req, timeout=2) as response:
            health = json.loads(response.read())
            print(f"Server status: {health.get('status')}")
    except Exception as e:
        print(f"Error: Cannot connect to server - {e}")
        print("Make sure the server is running: python examples/mcp_sse_server.py")
        return

    print()

    # 1. List resources
    print("1. Available Resources:")
    print("-" * 40)
    resources = list_resources()
    for res in resources:
        print(f"   {res['uri']}: {res['name']}")
    print()

    # 2. List tools
    print("2. Available Tools:")
    print("-" * 40)
    tools = list_tools()
    for tool in tools:
        print(f"   {tool['name']}: {tool['description']}")
    print()

    # 3. Read UI tree
    print("3. Reading ui://tree:")
    print("-" * 40)
    tree = read_resource("ui://tree")
    if "contents" in tree and tree["contents"]:
        print_tree(tree["contents"][0], indent=3)
    print()

    # 4. Read elements
    print("4. Reading ui://elements:")
    print("-" * 40)
    elements = read_resource("ui://elements")
    if "contents" in elements:
        for elem in elements["contents"]:
            print(f"   {elem['id']}: {elem['type']}")
    print()

    # 5. List actionable elements
    print("5. Calling list_actionable:")
    print("-" * 40)
    result = call_tool("list_actionable")
    if "content" in result:
        for elem in result["content"]:
            print(f"   {elem['id']}: {elem['type']}")
    print()

    # 6. Type text
    print("6. Typing 'Hello SSE!' into name-input:")
    print("-" * 40)
    result = call_tool("type_text", element_id="name-input", text="Hello SSE!", replace=True)
    print(f"   Result: {result.get('content', {})}")
    print()

    # 7. Click increment button
    print("7. Clicking increment button 3 times:")
    print("-" * 40)
    for i in range(3):
        result = call_tool("click", element_id="increment-btn")
        content = result.get("content", {})
        print(f"   Click {i+1}: {content.get('success', False)}")
        time.sleep(0.2)
    print()

    # 8. Toggle checkbox
    print("8. Toggling checkbox:")
    print("-" * 40)
    result = call_tool("toggle", element_id="my-checkbox")
    content = result.get("content", {})
    print(f"   Success: {content.get('success')}, New value: {content.get('new_value')}")
    print()

    # 9. Read focus
    print("9. Reading ui://focus:")
    print("-" * 40)
    focus = read_resource("ui://focus")
    if "contents" in focus and focus["contents"]:
        focus_data = focus["contents"][0]
        print(f"   Focused: {focus_data.get('element_id')}")
    print()

    print("=" * 60)
    print("Demo complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
