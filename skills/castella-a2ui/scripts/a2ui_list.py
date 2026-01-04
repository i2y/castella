"""
A2UI List Example - Demonstrates TemplateChildren for dynamic lists.

Run with: uv run python skills/castella-a2ui/examples/a2ui_list.py
"""

from castella import App
from castella.a2ui import A2UIRenderer, A2UIComponent, UserAction
from castella.frame import Frame


# A2UI with List component using TemplateChildren
a2ui_json = {
    "components": [
        {
            "id": "root",
            "component": "Column",
            "children": {"explicitList": ["header", "user_list", "add_btn"]},
        },
        {
            "id": "header",
            "component": "Text",
            "text": {"literalString": "User List"},
            "usageHint": "h2",
        },
        {
            "id": "user_list",
            "component": "List",
            "children": {
                "path": "/users",  # Data array path
                "componentId": "user_card",  # Template component
            },
        },
        # Template component for each user
        {
            "id": "user_card",
            "component": "Card",
            "children": {"explicitList": ["user_row"]},
        },
        {
            "id": "user_row",
            "component": "Row",
            "children": {"explicitList": ["user_icon", "user_info"]},
        },
        {
            "id": "user_icon",
            "component": "Icon",
            "name": {"literalString": "person"},
        },
        {
            "id": "user_info",
            "component": "Column",
            "children": {"explicitList": ["user_name", "user_email"]},
        },
        {
            "id": "user_name",
            "component": "Text",
            "text": {"path": "name"},  # Relative path within item
            "usageHint": "h4",
        },
        {
            "id": "user_email",
            "component": "Text",
            "text": {"path": "email"},  # Relative path within item
            "usageHint": "caption",
        },
        {
            "id": "add_btn",
            "component": "Button",
            "text": {"literalString": "Add User"},
            "action": {"name": "add_user", "context": []},
        },
    ],
    "rootId": "root",
}

# Initial data with user list
initial_data = {
    "/users": [
        {"name": "Alice", "email": "alice@example.com"},
        {"name": "Bob", "email": "bob@example.com"},
        {"name": "Charlie", "email": "charlie@example.com"},
    ]
}

# Counter for new users
user_counter = [4]  # Use list for mutable closure


def main():
    renderer = A2UIRenderer()

    def on_action(action: UserAction):
        if action.name == "add_user":
            # Get current users
            surface = renderer.get_surface("default")
            users = surface.data_model.get("/users", [])

            # Add new user
            new_user = {
                "name": f"User {user_counter[0]}",
                "email": f"user{user_counter[0]}@example.com",
            }
            user_counter[0] += 1
            users.append(new_user)

            # Update data model
            renderer.handle_message(
                {
                    "updateDataModel": {
                        "surfaceId": "default",
                        "data": {"/users": users},
                    }
                }
            )

    renderer._on_action = on_action

    # Render with initial data
    renderer.render_json(a2ui_json, initial_data=initial_data)
    surface = renderer.get_surface("default")

    App(Frame("A2UI List", 400, 500), A2UIComponent(surface)).run()


if __name__ == "__main__":
    main()
