"""
A2UI Form Example - Demonstrates data binding and actions.

Run with: uv run python skills/castella-a2ui/examples/a2ui_form.py
"""

from castella import App
from castella.a2ui import A2UIRenderer, A2UIComponent, UserAction
from castella.frame import Frame


# A2UI form definition with data binding
a2ui_json = {
    "components": [
        {
            "id": "root",
            "component": "Column",
            "children": {
                "explicitList": [
                    "title",
                    "name_row",
                    "email_row",
                    "subscribe_row",
                    "submit_btn",
                    "result",
                ]
            },
        },
        {
            "id": "title",
            "component": "Text",
            "text": {"literalString": "Registration Form"},
            "usageHint": "h2",
        },
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
            "text": {"path": "/name"},
        },
        {
            "id": "email_row",
            "component": "Row",
            "children": {"explicitList": ["email_label", "email_input"]},
        },
        {
            "id": "email_label",
            "component": "Text",
            "text": {"literalString": "Email:"},
        },
        {
            "id": "email_input",
            "component": "TextField",
            "text": {"path": "/email"},
        },
        {
            "id": "subscribe_row",
            "component": "Row",
            "children": {"explicitList": ["subscribe_label", "subscribe_check"]},
        },
        {
            "id": "subscribe_label",
            "component": "Text",
            "text": {"literalString": "Subscribe:"},
        },
        {
            "id": "subscribe_check",
            "component": "CheckBox",
            "checked": {"path": "/subscribe"},
        },
        {
            "id": "submit_btn",
            "component": "Button",
            "text": {"literalString": "Submit"},
            "action": {"name": "submit", "context": ["/name", "/email", "/subscribe"]},
        },
        {
            "id": "result",
            "component": "Text",
            "text": {"path": "/result"},
        },
    ],
    "rootId": "root",
}

# Initial data for bindings
initial_data = {
    "/name": "",
    "/email": "",
    "/subscribe": False,
    "/result": "",
}


def main():
    renderer = A2UIRenderer()

    def on_action(action: UserAction):
        if action.name == "submit":
            # Get current data from surface
            surface = renderer.get_surface("default")
            name = surface.data_model.get("/name", "")
            email = surface.data_model.get("/email", "")
            subscribe = surface.data_model.get("/subscribe", False)

            # Update result via data model
            result = f"Submitted: {name}, {email}, Subscribe: {subscribe}"
            renderer.handle_message(
                {
                    "updateDataModel": {
                        "surfaceId": "default",
                        "data": {"/result": result},
                    }
                }
            )

    renderer._on_action = on_action

    # Render with initial data
    renderer.render_json(a2ui_json, initial_data=initial_data)
    surface = renderer.get_surface("default")

    # Use A2UIComponent for reactive updates
    App(Frame("A2UI Form", 500, 350), A2UIComponent(surface)).run()


if __name__ == "__main__":
    main()
