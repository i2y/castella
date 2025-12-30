"""A2UI Renderer Demo - Comprehensive Widget Showcase

This example demonstrates ALL supported A2UI components rendered as Castella widgets.

Supported Components:
- Text (with usageHint: h1-h5, body, caption)
- Button (with actions)
- TextField (text input)
- CheckBox
- Slider (range input)
- DateTimeInput (date/time picker)
- Image
- Divider
- Row/Column (layout)
- Card (container)
- Tabs (navigation)
- Modal (dialog)
- Markdown (rich text)

Run with:
    uv run python examples/a2ui_demo.py
"""

from castella import App
from castella.a2ui import A2UIComponent, A2UIRenderer, UserAction
from castella.frame import Frame


def main():
    # Counter state for updateDataModel demo
    counter_value = [0]  # Use list for mutability in closure

    # Create renderer (we'll set up action handler after renderer is created)
    renderer = A2UIRenderer()

    # Action handler that demonstrates updateDataModel
    def on_action(action: UserAction):
        print(f"Action: {action.name}")
        print(f"  Source: {action.source_component_id}")
        print(f"  Context: {action.context}")

        # Handle increment_counter action to demonstrate updateDataModel
        if action.name == "increment_counter":
            counter_value[0] += 1
            # Send updateDataModel message to update the UI
            renderer.handle_message({
                "updateDataModel": {
                    "surfaceId": "default",
                    "data": {
                        "/counter": f"Counter: {counter_value[0]}",
                    },
                }
            })
            print(f"  Counter updated to: {counter_value[0]}")

    # Set the action handler
    renderer._on_action = on_action

    # Comprehensive A2UI JSON with all supported components
    a2ui_json = {
        "components": [
            # Root layout
            {
                "id": "root",
                "component": "Column",
                "children": {"explicitList": [
                    "header",
                    "divider1",
                    "main_content",
                ]},
            },

            # ===== Header =====
            {
                "id": "header",
                "component": "Text",
                "text": {"literalString": "A2UI Component Showcase"},
                "usageHint": "h1",
            },
            {
                "id": "divider1",
                "component": "Divider",
                "orientation": "horizontal",
            },

            # ===== Main Content =====
            {
                "id": "main_content",
                "component": "Row",
                "children": {"explicitList": ["left_panel", "right_panel"]},
            },

            # ----- Left Panel: Form Components -----
            {
                "id": "left_panel",
                "component": "Card",
                "children": {"explicitList": ["form_section"]},
            },
            {
                "id": "form_section",
                "component": "Column",
                "children": {"explicitList": [
                    "form_title",
                    "text_field_row",
                    "password_field_row",
                    "multiline_section",
                    "checkbox_row",
                    "slider_section",
                    "datetime_section",
                    "button_row",
                ]},
            },

            # Form Title
            {
                "id": "form_title",
                "component": "Text",
                "text": {"literalString": "Interactive Form"},
                "usageHint": "h3",
            },

            # TextField
            {
                "id": "text_field_row",
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
                "usageHint": "text",
            },

            # Password Field (usageHint: password)
            {
                "id": "password_field_row",
                "component": "Row",
                "children": {"explicitList": ["password_label", "password_input"]},
            },
            {
                "id": "password_label",
                "component": "Text",
                "text": {"literalString": "Password:"},
            },
            {
                "id": "password_input",
                "component": "TextField",
                "text": {"literalString": ""},
                "usageHint": "password",
            },

            # Multiline Field (usageHint: multiline)
            {
                "id": "multiline_section",
                "component": "Column",
                "children": {"explicitList": ["multiline_label", "multiline_input"]},
            },
            {
                "id": "multiline_label",
                "component": "Text",
                "text": {"literalString": "Comments:"},
            },
            {
                "id": "multiline_input",
                "component": "TextField",
                "text": {"literalString": "Enter multiple lines here..."},
                "usageHint": "multiline",
            },

            # CheckBox
            {
                "id": "checkbox_row",
                "component": "Row",
                "children": {"explicitList": ["agree_checkbox"]},
            },
            {
                "id": "agree_checkbox",
                "component": "CheckBox",
                "label": {"literalString": "I agree to the terms"},
                "checked": {"literalBoolean": False},
            },

            # Slider
            {
                "id": "slider_section",
                "component": "Column",
                "children": {"explicitList": ["slider_label", "volume_slider"]},
            },
            {
                "id": "slider_label",
                "component": "Text",
                "text": {"literalString": "Volume: 50"},
                "usageHint": "caption",
            },
            {
                "id": "volume_slider",
                "component": "Slider",
                "value": {"literalNumber": 50},
                "min": 0,
                "max": 100,
            },

            # DateTimeInput
            {
                "id": "datetime_section",
                "component": "Column",
                "children": {"explicitList": ["datetime_label", "appointment_input"]},
            },
            {
                "id": "datetime_label",
                "component": "Text",
                "text": {"literalString": "Appointment:"},
                "usageHint": "caption",
            },
            {
                "id": "appointment_input",
                "component": "DateTimeInput",
                "label": {"literalString": "Select date/time"},
                "value": {"literalString": "2024-12-25T14:30:00"},
                "enableDate": True,
                "enableTime": True,
            },

            # Action Buttons
            {
                "id": "button_row",
                "component": "Row",
                "children": {"explicitList": ["submit_btn", "reset_btn"]},
            },
            {
                "id": "submit_btn",
                "component": "Button",
                "text": {"literalString": "Submit"},
                "action": {
                    "name": "submit_form",
                    "context": [],
                },
            },
            {
                "id": "reset_btn",
                "component": "Button",
                "text": {"literalString": "Reset"},
                "action": {
                    "name": "reset_form",
                    "context": [],
                },
            },

            # ----- Right Panel: Display Components -----
            {
                "id": "right_panel",
                "component": "Card",
                "children": {"explicitList": ["display_section"]},
            },
            {
                "id": "display_section",
                "component": "Column",
                "children": {"explicitList": [
                    "display_title",
                    "counter_section",
                    "list_section",
                    "markdown_content",
                ]},
            },

            # Display Title
            {
                "id": "display_title",
                "component": "Text",
                "text": {"literalString": "Display Components"},
                "usageHint": "h3",
            },

            # Data Binding Test (updateDataModel)
            {
                "id": "counter_section",
                "component": "Column",
                "children": {"explicitList": ["counter_title", "counter_text", "counter_btn"]},
            },
            {
                "id": "counter_title",
                "component": "Text",
                "text": {"literalString": "Data Binding Test:"},
                "usageHint": "caption",
            },
            {
                "id": "counter_text",
                "component": "Text",
                "text": {"path": "/counter"},
            },
            {
                "id": "counter_btn",
                "component": "Button",
                "text": {"literalString": "Increment Counter"},
                "action": {
                    "name": "increment_counter",
                    "context": [],
                },
            },

            # List with TemplateChildren
            {
                "id": "list_section",
                "component": "Column",
                "children": {"explicitList": ["list_title", "user_list"]},
            },
            {
                "id": "list_title",
                "component": "Text",
                "text": {"literalString": "Dynamic List (TemplateChildren):"},
                "usageHint": "caption",
            },
            {
                "id": "user_list",
                "component": "List",
                "children": {"path": "/users", "componentId": "user_item"},
            },
            # Template for list items
            {
                "id": "user_item",
                "component": "Text",
                "text": {"path": "name"},
            },

            # Markdown
            {
                "id": "markdown_content",
                "component": "Markdown",
                "content": {
                    "literalString": """## A2UI on Castella

This demo showcases **all supported A2UI components**:

### Form Components
- `TextField` - Text input
- `CheckBox` - Boolean toggle
- `Slider` - Range input
- `DateTimeInput` - Date/time picker
- `Button` - Actions

### Layout Components
- `Row` / `Column` - Flexbox-like layout
- `Card` - Grouped content
- `Divider` - Visual separator

### Display Components
- `Text` - With heading levels (h1-h5)
- `Markdown` - Rich formatted text
- `Image` - URL-based images

All render natively on **Desktop**, **Web**, and **Terminal**!
"""
                },
                "baseFontSize": 13,
            },

            # Text usage hint examples
            {
                "id": "text_examples",
                "component": "Column",
                "children": {"explicitList": [
                    "text_h2", "text_h4", "text_body", "text_caption"
                ]},
            },
            {
                "id": "text_h2",
                "component": "Text",
                "text": {"literalString": "Heading 2 (h2)"},
                "usageHint": "h2",
            },
            {
                "id": "text_h4",
                "component": "Text",
                "text": {"literalString": "Heading 4 (h4)"},
                "usageHint": "h4",
            },
            {
                "id": "text_body",
                "component": "Text",
                "text": {"literalString": "Body text - normal paragraph style"},
                "usageHint": "body",
            },
            {
                "id": "text_caption",
                "component": "Text",
                "text": {"literalString": "Caption - small helper text"},
                "usageHint": "caption",
            },
        ],
        "rootId": "root",
    }

    # Initial data for List component and counter
    initial_data = {
        "/users": [
            {"name": "Alice Johnson"},
            {"name": "Bob Smith"},
            {"name": "Charlie Brown"},
            {"name": "Diana Prince"},
        ],
        "/counter": "Counter: 0",
    }

    # Render A2UI JSON to create the surface
    renderer.render_json(a2ui_json, initial_data=initial_data)

    # Get the surface and wrap it in A2UIComponent for auto-update on data changes
    surface = renderer.get_surface("default")
    component = A2UIComponent(surface)

    # Run the app
    App(Frame("A2UI Component Showcase", 1000, 700), component).run()


if __name__ == "__main__":
    main()
