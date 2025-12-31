"""MCP A2UI Server - A2UI-generated UI controlled via MCP.

This example demonstrates bidirectional A2UI + MCP integration:
1. A2UI generates the UI from JSON
2. MCP provides resources/tools to introspect and control the UI
3. MCP can send A2UI messages to update the UI dynamically

Usage:
    1. Start the server:
       python examples/mcp_a2ui_server.py

    2. Connect with the SSE client:
       python examples/mcp_a2ui_client.py
"""

from castella import App
from castella.frame import Frame
from castella.a2ui import A2UIRenderer, A2UIComponent, UserAction
from castella.mcp import CastellaMCPServer


# A2UI JSON defining the UI
A2UI_JSON = {
    "components": [
        {
            "id": "root",
            "component": "Column",
            "children": {"explicitList": ["header", "form", "result", "actions"]},
        },
        {
            "id": "header",
            "component": "Text",
            "text": {"literalString": "A2UI + MCP Demo"},
            "usageHint": "h2",
        },
        {
            "id": "form",
            "component": "Column",
            "children": {"explicitList": ["name-row", "message-row"]},
        },
        {
            "id": "name-row",
            "component": "Row",
            "children": {"explicitList": ["name-label", "name-input"]},
        },
        {
            "id": "name-label",
            "component": "Text",
            "text": {"literalString": "Name:"},
        },
        {
            "id": "name-input",
            "component": "TextField",
            "text": {"path": "/name"},
            "placeholder": {"literalString": "Enter your name"},
        },
        {
            "id": "message-row",
            "component": "Row",
            "children": {"explicitList": ["message-label", "message-input"]},
        },
        {
            "id": "message-label",
            "component": "Text",
            "text": {"literalString": "Message:"},
        },
        {
            "id": "message-input",
            "component": "TextField",
            "text": {"path": "/message"},
            "placeholder": {"literalString": "Enter a message"},
        },
        {
            "id": "result",
            "component": "Text",
            "text": {"path": "/result"},
            "usageHint": "body",
        },
        {
            "id": "actions",
            "component": "Row",
            "children": {"explicitList": ["submit-btn", "clear-btn", "toggle-check"]},
        },
        {
            "id": "submit-btn",
            "component": "Button",
            "text": {"literalString": "Submit"},
            "action": {"name": "submit", "context": []},
        },
        {
            "id": "clear-btn",
            "component": "Button",
            "text": {"literalString": "Clear"},
            "action": {"name": "clear", "context": []},
        },
        {
            "id": "toggle-check",
            "component": "CheckBox",
            "checked": {"path": "/enabled"},
        },
    ],
    "rootId": "root",
}

# Initial data model
INITIAL_DATA = {
    "/name": "",
    "/message": "",
    "/result": "Enter your name and message, then click Submit.",
    "/enabled": False,
}


def main():
    # Create A2UI renderer with action handler
    def on_action(action: UserAction):
        print(f"[A2UI Action] {action.name} from {action.source_component_id}")

        if action.name == "submit":
            # Get current values from data model (stored in surface)
            surface = renderer.get_surface("default")
            name = surface.data_model.get("name", "") if surface else ""
            message = surface.data_model.get("message", "") if surface else ""
            result = f"Hello, {name or 'World'}! Your message: {message or '(empty)'}"

            # Update result via A2UI updateDataModel
            renderer.handle_message({
                "updateDataModel": {
                    "surfaceId": "default",
                    "data": {"/result": result},
                }
            })
        elif action.name == "clear":
            # Clear all fields
            renderer.handle_message({
                "updateDataModel": {
                    "surfaceId": "default",
                    "data": {
                        "/name": "",
                        "/message": "",
                        "/result": "Cleared!",
                    },
                }
            })

    renderer = A2UIRenderer(on_action=on_action)

    # Render A2UI JSON
    renderer.render_json(A2UI_JSON, initial_data=INITIAL_DATA)
    surface = renderer.get_surface("default")

    # Create Castella app with A2UI component
    frame = Frame("A2UI + MCP Demo", 400, 300)
    component = A2UIComponent(surface)
    app = App(frame, component)

    # Create MCP server with A2UI renderer for bidirectional integration
    mcp = CastellaMCPServer(
        app,
        name="castella-a2ui-mcp",
        a2ui_renderer=renderer,
    )

    # Refresh registry
    mcp.refresh_registry()

    # Run SSE server in background
    mcp.run_sse_in_background(host="localhost", port=8766)

    print("=" * 55)
    print("A2UI + MCP Server Started")
    print("=" * 55)
    print()
    print("SSE endpoint: http://localhost:8766/sse")
    print("Message endpoint: http://localhost:8766/message")
    print()
    print("A2UI component IDs are used as MCP semantic IDs:")
    print("  - name-input    : TextField for name")
    print("  - message-input : TextField for message")
    print("  - submit-btn    : Submit button")
    print("  - clear-btn     : Clear button")
    print("  - toggle-check  : CheckBox")
    print()
    print("Connect with: python examples/mcp_a2ui_client.py")
    print()

    # Run GUI on main thread
    app.run()


if __name__ == "__main__":
    main()
