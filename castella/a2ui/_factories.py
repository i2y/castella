"""Factory functions for creating Castella widgets from A2UI components.

Each factory function takes an A2UI component definition, a data model,
and an action handler, and returns a configured Castella widget.
"""

from __future__ import annotations

from typing import Any, Callable

from castella.a2ui.types import (
    Alignment,
    ButtonComponent,
    CardComponent,
    CheckBoxComponent,
    ColumnComponent,
    DataBinding,
    DividerComponent,
    Distribution,
    ExplicitChildren,
    ImageComponent,
    LiteralBoolean,
    LiteralNumber,
    LiteralString,
    MarkdownComponent,
    RowComponent,
    TextComponent,
    TextFieldComponent,
    TextUsageHint,
)
from castella.core import SizePolicy, Widget


# Type alias for action handler
ActionHandler = Callable[[str, str, dict[str, Any]], None]


def resolve_value(
    value: LiteralString | LiteralNumber | LiteralBoolean | DataBinding | None,
    data_model: dict[str, Any],
    default: Any = None,
) -> Any:
    """Resolve a value from either a literal or data binding.

    Args:
        value: The value to resolve (literal or binding)
        data_model: The data model for resolving bindings
        default: Default value if value is None

    Returns:
        The resolved value
    """
    if value is None:
        return default

    if isinstance(value, LiteralString):
        return value.literal_string
    elif isinstance(value, LiteralNumber):
        return value.literal_number
    elif isinstance(value, LiteralBoolean):
        return value.literal_boolean
    elif isinstance(value, DataBinding):
        # Resolve JSON Pointer path
        path = value.path
        if path.startswith("/"):
            path = path[1:]  # Remove leading slash
        parts = path.split("/")

        current = data_model
        for part in parts:
            if isinstance(current, dict):
                current = current.get(part, default)
            elif isinstance(current, list):
                try:
                    idx = int(part)
                    current = current[idx] if 0 <= idx < len(current) else default
                except (ValueError, IndexError):
                    return default
            else:
                return default
        return current

    return default


def create_text(
    component: TextComponent,
    data_model: dict[str, Any],
    action_handler: ActionHandler,
) -> Widget:
    """Create a Text widget from an A2UI Text component."""
    from castella.text import Text

    text_value = resolve_value(component.text, data_model, "")

    widget = Text(str(text_value))

    # Apply usage hint styling
    if component.usage_hint:
        # Map A2UI usage hints to font sizes
        size_map = {
            TextUsageHint.H1: 32,
            TextUsageHint.H2: 28,
            TextUsageHint.H3: 24,
            TextUsageHint.H4: 20,
            TextUsageHint.H5: 18,
            TextUsageHint.BODY: 14,
            TextUsageHint.CAPTION: 12,
        }
        font_size = size_map.get(component.usage_hint, 14)
        widget = widget.fixed_height(font_size + 16)  # Add padding

    # Apply flex weight if specified
    if component.weight is not None:
        widget = widget.flex(int(component.weight))

    return widget


def create_button(
    component: ButtonComponent,
    data_model: dict[str, Any],
    action_handler: ActionHandler,
) -> Widget:
    """Create a Button widget from an A2UI Button component."""
    from castella.button import Button

    # Get button text
    text_value = resolve_value(component.text, data_model, "Button")

    widget = Button(str(text_value))

    # Set up action handler
    if component.action:
        action_name = component.action.name

        # Resolve action context
        def make_handler(act_name: str, comp_id: str, ctx_items: list) -> Callable:
            def handler(event: Any) -> None:
                context = {}
                for item in ctx_items:
                    resolved = resolve_value(item.value, data_model)
                    context[item.key] = resolved
                action_handler(act_name, comp_id, context)

            return handler

        widget = widget.on_click(
            make_handler(action_name, component.id, component.action.context)
        )

    # Apply flex weight if specified
    if component.weight is not None:
        widget = widget.flex(int(component.weight))

    return widget


def create_textfield(
    component: TextFieldComponent,
    data_model: dict[str, Any],
    action_handler: ActionHandler,
) -> Widget:
    """Create an Input widget from an A2UI TextField component."""
    from castella.input import Input

    # Get current value
    text_value = resolve_value(component.text, data_model, "")

    widget = Input(str(text_value))

    # If the text is a binding, set up two-way binding via on_change
    if isinstance(component.text, DataBinding):
        path = component.text.path

        def on_change(new_value: str) -> None:
            # Notify action handler of value change
            action_handler(
                "__data_update__",
                component.id,
                {"path": path, "value": new_value},
            )

        widget = widget.on_change(on_change)

    # Apply flex weight if specified
    if component.weight is not None:
        widget = widget.flex(int(component.weight))

    return widget


def create_checkbox(
    component: CheckBoxComponent,
    data_model: dict[str, Any],
    action_handler: ActionHandler,
) -> Widget:
    """Create a CheckBox widget from an A2UI CheckBox component."""
    from castella.checkbox import CheckBox

    # Get label
    label = resolve_value(component.label, data_model, "")

    # Get checked state
    checked = resolve_value(component.checked, data_model, False)

    widget = CheckBox(checked=bool(checked), on_label=str(label), off_label=str(label))

    # If checked is a binding, set up two-way binding
    if isinstance(component.checked, DataBinding):
        path = component.checked.path

        def on_click(event: Any) -> None:
            # Toggle and notify
            action_handler(
                "__data_update__",
                component.id,
                {"path": path, "value": not checked},
            )

        widget = widget.on_click(on_click)

    return widget


def create_image(
    component: ImageComponent,
    data_model: dict[str, Any],
    action_handler: ActionHandler,
) -> Widget:
    """Create an Image widget from an A2UI Image component."""
    from castella.net_image import NetImage

    src = resolve_value(component.src, data_model, "")

    # Use NetImage for URLs
    widget = NetImage(str(src))

    # Apply flex weight if specified
    if component.weight is not None:
        widget = widget.flex(int(component.weight))

    return widget


def create_divider(
    component: DividerComponent,
    data_model: dict[str, Any],
    action_handler: ActionHandler,
) -> Widget:
    """Create a Spacer widget from an A2UI Divider component."""
    from castella.spacer import Spacer

    # Create a thin spacer as divider
    widget = Spacer()

    # Apply orientation
    if component.orientation.value == "horizontal":
        widget = widget.fixed_height(1).width_policy(SizePolicy.EXPANDING)
    else:
        widget = widget.fixed_width(1).height_policy(SizePolicy.EXPANDING)

    return widget


def create_row(
    component: RowComponent,
    data_model: dict[str, Any],
    action_handler: ActionHandler,
) -> Widget:
    """Create a Row widget from an A2UI Row component."""
    from castella.row import Row

    # Note: Children will be added by the renderer after all components are created
    widget = Row()

    # Apply flex weight if specified
    if component.weight is not None:
        widget = widget.flex(int(component.weight))

    return widget


def create_column(
    component: ColumnComponent,
    data_model: dict[str, Any],
    action_handler: ActionHandler,
) -> Widget:
    """Create a Column widget from an A2UI Column component."""
    from castella.column import Column

    # Note: Children will be added by the renderer after all components are created
    widget = Column()

    # Apply flex weight if specified
    if component.weight is not None:
        widget = widget.flex(int(component.weight))

    return widget


def create_card(
    component: CardComponent,
    data_model: dict[str, Any],
    action_handler: ActionHandler,
) -> Widget:
    """Create a Box widget from an A2UI Card component."""
    from castella.box import Box

    # Note: Children will be added by the renderer after all components are created
    widget = Box()

    # Apply flex weight if specified
    if component.weight is not None:
        widget = widget.flex(int(component.weight))

    return widget


def create_markdown(
    component: MarkdownComponent,
    data_model: dict[str, Any],
    action_handler: ActionHandler,
) -> Widget:
    """Create a Markdown widget from an A2UI Markdown component."""
    from castella.markdown import Markdown

    content = resolve_value(component.content, data_model, "")

    widget = Markdown(
        str(content),
        base_font_size=component.base_font_size,
    )

    # Apply flex weight if specified
    if component.weight is not None:
        widget = widget.flex(int(component.weight))

    return widget


def get_child_ids(children: ExplicitChildren | None) -> list[str]:
    """Extract child IDs from a Children specification.

    Args:
        children: The children specification

    Returns:
        List of child component IDs
    """
    if children is None:
        return []
    if isinstance(children, ExplicitChildren):
        return children.explicit_list
    # TemplateChildren requires special handling in the renderer
    return []
