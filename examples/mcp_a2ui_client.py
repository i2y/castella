"""MCP A2UI Client - Control A2UI-generated UI via MCP.

This client demonstrates:
1. Reading A2UI surfaces via MCP resources
2. Controlling A2UI widgets via MCP tools
3. Sending A2UI updateDataModel messages via MCP

Usage:
    1. Start the server first:
       python examples/mcp_a2ui_server.py

    2. Run this client:
       python examples/mcp_a2ui_client.py
"""

import json
import time
import urllib.request
import urllib.error


BASE_URL = "http://localhost:8766"


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


def read_resource(uri: str) -> dict:
    """Read an MCP resource."""
    return send_message("read_resource", {"uri": uri})


def call_tool(name: str, **kwargs) -> dict:
    """Call an MCP tool."""
    return send_message("call_tool", {"name": name, "arguments": kwargs})


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
    print("MCP A2UI Client - Controlling A2UI via MCP")
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
        print("Make sure the server is running: python examples/mcp_a2ui_server.py")
        return

    print()

    # 1. Read A2UI surfaces
    print("1. Reading a2ui://surfaces:")
    print("-" * 40)
    surfaces = read_resource("a2ui://surfaces")
    if "contents" in surfaces:
        for surf in surfaces["contents"]:
            print(f"   Surface: {surf.get('surface_id')}")
            print(f"   Root type: {surf.get('root_widget_type')}")
            print(f"   Widget count: {surf.get('widget_count')}")
    print()

    # 2. Read UI tree (shows A2UI component IDs)
    print("2. Reading ui://tree (A2UI component IDs):")
    print("-" * 40)
    tree = read_resource("ui://tree")
    if "contents" in tree and tree["contents"]:
        print_tree(tree["contents"][0], indent=3)
    print()

    # 3. List actionable elements
    print("3. Calling list_actionable:")
    print("-" * 40)
    result = call_tool("list_actionable")
    if "content" in result:
        for elem in result["content"]:
            elem_type = elem.get("type", "?")
            print(f"   {elem['id']}: {elem_type}")
    print()

    # 4. Type into name-input (A2UI TextField)
    print("4. Typing 'Claude' into name-input:")
    print("-" * 40)
    result = call_tool("type_text", element_id="name-input", text="Claude", replace=True)
    content = result.get("content", {})
    print(f"   Success: {content.get('success')}")
    print(f"   Message: {content.get('message')}")
    time.sleep(0.3)
    print()

    # 5. Type into message-input
    print("5. Typing 'Hello from MCP!' into message-input:")
    print("-" * 40)
    result = call_tool("type_text", element_id="message-input", text="Hello from MCP!", replace=True)
    content = result.get("content", {})
    print(f"   Success: {content.get('success')}")
    time.sleep(0.3)
    print()

    # 6. Click submit button (triggers A2UI action)
    print("6. Clicking submit-btn (triggers A2UI action):")
    print("-" * 40)
    result = call_tool("click", element_id="submit-btn")
    content = result.get("content", {})
    print(f"   Success: {content.get('success')}")
    print("   (Check the GUI - result text should update!)")
    time.sleep(0.5)
    print()

    # 7. Toggle the checkbox
    print("7. Toggling toggle-check:")
    print("-" * 40)
    result = call_tool("toggle", element_id="toggle-check")
    content = result.get("content", {})
    print(f"   Success: {content.get('success')}")
    print(f"   New value: {content.get('new_value')}")
    print()

    print("=" * 60)
    print("A2UI + MCP Demo Complete!")
    print()
    print("This demonstrated:")
    print("  - A2UI component IDs as MCP semantic IDs")
    print("  - MCP tools controlling A2UI widgets")
    print("  - A2UI actions triggered via MCP clicks")
    print("  - Bidirectional data flow")
    print("=" * 60)


if __name__ == "__main__":
    main()
