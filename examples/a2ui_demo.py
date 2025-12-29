"""A2UI Renderer Demo

This example demonstrates how to use the A2UIRenderer to convert
A2UI JSON into Castella widgets.

Run with:
    uv run python examples/a2ui_demo.py
"""

from castella import App
from castella.a2ui import A2UIRenderer, UserAction
from castella.frame import Frame


def main():
    # Create renderer with action handler
    def on_action(action: UserAction):
        print(f"Action: {action.name}")
        print(f"  Source: {action.source_component_id}")
        print(f"  Context: {action.context}")

    renderer = A2UIRenderer(on_action=on_action)

    # A2UI JSON example - a simple form
    a2ui_json = {
        "components": [
            # Root column layout
            {
                "id": "root",
                "component": "Column",
                "children": {"explicitList": ["header", "content", "actions"]},
            },
            # Header section
            {
                "id": "header",
                "component": "Text",
                "text": {"literalString": "A2UI Demo"},
                "usageHint": "h1",
            },
            # Content section (card with form)
            {
                "id": "content",
                "component": "Card",
                "children": {"explicitList": ["form"]},
            },
            {
                "id": "form",
                "component": "Column",
                "children": {"explicitList": ["greeting", "name_row", "message"]},
            },
            # Greeting text
            {
                "id": "greeting",
                "component": "Text",
                "text": {"literalString": "Welcome to A2UI on Castella!"},
                "usageHint": "body",
            },
            # Name input row
            {
                "id": "name_row",
                "component": "Row",
                "children": {"explicitList": ["name_label", "name_input"]},
            },
            {
                "id": "name_label",
                "component": "Text",
                "text": {"literalString": "Name:"},
            },
            {
                "id": "name_input",
                "component": "TextField",
                "text": {"literalString": ""},
                "label": {"literalString": "Enter your name"},
            },
            # Message with markdown
            {
                "id": "message",
                "component": "Markdown",
                "content": {
                    "literalString": """
## Features

This demo shows A2UI components rendered as Castella widgets:

- **Text** - Display text with styling
- **Button** - Interactive buttons with actions
- **TextField** - Text input fields
- **Markdown** - Rich text with formatting
- **Row/Column** - Layout containers
- **Card** - Grouped content

All components render natively on **Desktop**, **Web**, and **Terminal**!
"""
                },
                "baseFontSize": 14,
            },
            # Action buttons
            {
                "id": "actions",
                "component": "Row",
                "children": {"explicitList": ["submit_btn", "cancel_btn"]},
            },
            {
                "id": "submit_btn",
                "component": "Button",
                "text": {"literalString": "Submit"},
                "action": {
                    "name": "submit",
                    "context": [],
                },
            },
            {
                "id": "cancel_btn",
                "component": "Button",
                "text": {"literalString": "Cancel"},
                "action": {
                    "name": "cancel",
                    "context": [],
                },
            },
        ],
        "rootId": "root",
    }

    # Render A2UI JSON to Castella widget
    widget = renderer.render_json(a2ui_json)

    # Run the app
    App(Frame("A2UI Demo", 800, 600), widget).run()


if __name__ == "__main__":
    main()
