"""
Basic A2UI Rendering Example - Demonstrates rendering A2UI JSON.

Run with: uv run python skills/castella-a2ui/examples/basic_a2ui.py
"""

from castella import App
from castella.a2ui import A2UIRenderer, A2UIComponent, UserAction
from castella.frame import Frame


def on_action(action: UserAction):
    """Handle A2UI actions from user interactions."""
    print(f"Action: {action.name}")
    print(f"Source: {action.source_component_id}")
    print(f"Context: {action.context}")


# A2UI JSON defining the UI
a2ui_json = {
    "components": [
        {
            "id": "root",
            "component": "Column",
            "children": {"explicitList": ["title", "description", "button"]},
        },
        {
            "id": "title",
            "component": "Text",
            "text": {"literalString": "Welcome to A2UI"},
            "usageHint": "h1",
        },
        {
            "id": "description",
            "component": "Text",
            "text": {"literalString": "This UI was generated from JSON."},
        },
        {
            "id": "button",
            "component": "Button",
            "text": {"literalString": "Click Me"},
            "action": {"name": "clicked", "context": []},
        },
    ],
    "rootId": "root",
}


def main():
    # Create renderer with action handler
    renderer = A2UIRenderer(on_action=on_action)

    # Render A2UI JSON to widget
    widget = renderer.render_json(a2ui_json)

    # Run app
    App(Frame("Basic A2UI", 400, 200), widget).run()


if __name__ == "__main__":
    main()
