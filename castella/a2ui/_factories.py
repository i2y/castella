"""Factory functions for creating Castella widgets from A2UI components.

Each factory function takes an A2UI component definition, a data model,
and an action handler, and returns a configured Castella widget.
"""

from __future__ import annotations

from typing import Any, Callable

from castella.a2ui.types import (
    ButtonComponent,
    CardComponent,
    CheckBoxComponent,
    ChoicePickerComponent,
    ColumnComponent,
    DataBinding,
    DateTimeInputComponent,
    DividerComponent,
    ExplicitChildren,
    IconComponent,
    ImageComponent,
    ListComponent,
    LiteralBoolean,
    LiteralNumber,
    LiteralString,
    MarkdownComponent,
    ModalComponent,
    RowComponent,
    SliderComponent,
    TabsComponent,
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
    import os
    from castella.text import Text

    text_value = resolve_value(component.text, data_model, "")
    if os.environ.get("A2UI_DEBUG"):
        print(
            f"[FACTORY] create_text: id={component.id}, text={component.text} -> '{text_value}'"
        )

    # Determine font size based on usage hint
    font_size = None
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

    # Create widget with font_size if specified
    widget = Text(str(text_value), font_size=font_size)

    # Apply fixed height for elements with usage_hint to ensure proper layout
    if font_size is not None:
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
    """Create an Input widget from an A2UI TextField component.

    Supports both A2UI 0.9 spec usageHint values (shortText, longText, obscured)
    and Castella's values (text, password, multiline).
    """
    from castella.a2ui.types import TextFieldUsageHint
    from castella.input import Input

    # Get current value
    text_value = resolve_value(component.text, data_model, "")
    hint = component.usage_hint

    # Select widget type based on usage hint
    # Support both A2UI 0.9 spec values and Castella values
    if hint in (TextFieldUsageHint.PASSWORD, TextFieldUsageHint.OBSCURED):
        widget = Input(str(text_value), password=True)
    elif hint in (TextFieldUsageHint.MULTILINE, TextFieldUsageHint.LONG_TEXT):
        from castella.multiline_input import MultilineInput

        widget = MultilineInput(str(text_value), font_size=14)
    else:
        # text, shortText, email, number, phone, url - use standard Input
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


def create_slider(
    component: SliderComponent,
    data_model: dict[str, Any],
    action_handler: ActionHandler,
) -> Widget:
    """Create a Slider widget from an A2UI Slider component."""
    from castella.box import Box
    from castella.slider import Slider
    from castella.theme import ThemeManager

    # Get current value
    value = resolve_value(component.value, data_model, 0.0)

    slider = Slider(
        value=float(value) if value is not None else 0.0,
        min_val=component.min,
        max_val=component.max,
    )

    # Set fixed height
    slider = slider.height(40).height_policy(SizePolicy.FIXED)

    # If value is a binding, set up two-way binding via on_change
    if isinstance(component.value, DataBinding):
        path = component.value.path

        def on_change(new_value: float) -> None:
            action_handler(
                "__data_update__",
                component.id,
                {"path": path, "value": new_value},
            )

        slider = slider.on_change(on_change)

    # Wrap in Box with background color to prevent afterimage rendering bug
    theme = ThemeManager().current
    widget = (
        Box(slider)
        .bg_color(theme.colors.bg_secondary)
        .height(50)
        .height_policy(SizePolicy.FIXED)
    )

    # Apply flex weight if specified
    if component.weight is not None:
        widget = widget.flex(int(component.weight))

    return widget


def create_datetime_input(
    component: DateTimeInputComponent,
    data_model: dict[str, Any],
    action_handler: ActionHandler,
) -> Widget:
    """Create a DateTimeInput widget from an A2UI DateTimeInput component."""
    from castella.datetime_input import DateTimeInput, DateTimeInputState

    # Get label
    label = resolve_value(component.label, data_model, None)

    # Get value
    value = resolve_value(component.value, data_model, None)

    state = DateTimeInputState(
        value=str(value) if value else None,
        enable_date=component.enable_date,
        enable_time=component.enable_time,
    )

    widget = DateTimeInput(
        state=state,
        label=str(label) if label else None,
    )

    # Set up data binding for value
    if isinstance(component.value, DataBinding):
        path = component.value.path

        def on_change(new_value: str | None) -> None:
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


def create_image(
    component: ImageComponent,
    data_model: dict[str, Any],
    action_handler: ActionHandler,
) -> Widget:
    """Create an Image widget from an A2UI Image component."""
    from castella.net_image import ImageFit, NetImage

    src = resolve_value(component.src, data_model, "")

    # Use NetImage with CONTAIN fit to maintain aspect ratio
    # Set EXPANDING policies so image fills available space
    widget = (
        NetImage(str(src), fit=ImageFit.CONTAIN)
        .width_policy(SizePolicy.EXPANDING)
        .height_policy(SizePolicy.EXPANDING)
    )

    # Apply flex weight if specified
    if component.weight is not None:
        widget = widget.flex(int(component.weight))

    return widget


def create_icon(
    component: IconComponent,
    data_model: dict[str, Any],
    action_handler: ActionHandler,
) -> Widget:
    """Create a Text widget as placeholder for A2UI Icon component.

    Material Icons are not directly supported in Castella, so we render
    the icon name as text (emoji) for now.
    """
    from castella.text import Text

    icon_name = resolve_value(component.name, data_model, "")

    # Map common material icons to Unicode emoji/symbols
    icon_map = {
        "calendar_today": "📅",
        "location_on": "📍",
        "mail": "✉️",
        "call": "📞",
        "check_circle": "✓",
        "person": "👤",
        "search": "🔍",
        "settings": "⚙️",
        "home": "🏠",
        "star": "⭐",
        "favorite": "❤️",
        "close": "✕",
        "add": "+",
        "remove": "-",
        "edit": "✎",
        "delete": "🗑",
        "info": "ℹ",
        "warning": "⚠",
        "error": "⚠",
    }

    display_text = icon_map.get(str(icon_name), f"[{icon_name}]")

    # Use specified size or default
    size = int(component.size) if component.size else 24

    widget = Text(display_text, font_size=size)

    # Apply fixed size for icons
    widget = widget.fixed_height(size + 8).fixed_width(size + 8)

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
    """Create a Column widget from an A2UI Card component.

    Card is a container that lays out children vertically.
    We use Column instead of Box because Box stacks children
    on top of each other (z-order), while Column lays them out.
    """
    from castella.column import Column
    from castella.theme import ThemeManager

    theme = ThemeManager().current

    # Note: Children will be added by the renderer after all components are created
    widget = Column().bg_color(theme.colors.bg_secondary)

    # Apply flex weight if specified
    if component.weight is not None:
        widget = widget.flex(int(component.weight))

    return widget


def create_tabs(
    component: TabsComponent,
    data_model: dict[str, Any],
    action_handler: ActionHandler,
) -> Widget:
    """Create a Tabs widget from an A2UI Tabs component.

    Note: Tab content widgets are referenced by content_id and will be
    connected by the renderer after all components are created.
    """
    from castella.tabs import Tabs, TabsState, TabItem as CastellaTabItem
    from castella.spacer import Spacer

    # Build tab items (content will be connected by renderer)
    tab_items = []
    for item in component.tab_items:
        label = resolve_value(item.label, data_model, item.id)
        # Create placeholder content - renderer will replace with actual widget
        tab_items.append(
            CastellaTabItem(
                id=item.id,
                label=str(label),
                content=Spacer(),  # Placeholder
            )
        )

    # Get selected tab
    selected_id = resolve_value(component.selected_tab, data_model, None)
    if selected_id is None and tab_items:
        selected_id = tab_items[0].id

    state = TabsState(tab_items, str(selected_id) if selected_id else None)
    widget = Tabs(state)

    # Set up data binding for selected tab
    if isinstance(component.selected_tab, DataBinding):
        path = component.selected_tab.path

        def on_change(new_tab_id: str) -> None:
            action_handler(
                "__data_update__",
                component.id,
                {"path": path, "value": new_tab_id},
            )

        widget = widget.on_change(on_change)

    return widget


def create_modal(
    component: ModalComponent,
    data_model: dict[str, Any],
    action_handler: ActionHandler,
) -> Widget:
    """Create a Modal widget from an A2UI Modal component.

    Note: Modal children (content) will be connected by the renderer
    after all components are created.
    """
    from castella.modal import Modal, ModalState
    from castella.spacer import Spacer

    # Get title
    title = resolve_value(component.title, data_model, None)

    # Get open state
    is_open = resolve_value(component.open, data_model, False)

    state = ModalState(bool(is_open))

    # Create modal with placeholder content (renderer will replace)
    widget = Modal(
        content=Spacer(),  # Placeholder
        state=state,
        title=str(title) if title else None,
    )

    # Set up data binding for open state
    if isinstance(component.open, DataBinding):
        path = component.open.path

        def on_close() -> None:
            action_handler(
                "__data_update__",
                component.id,
                {"path": path, "value": False},
            )

        widget = widget.on_close(on_close)

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


def create_choice_picker(
    component: ChoicePickerComponent,
    data_model: dict[str, Any],
    action_handler: ActionHandler,
) -> Widget:
    """Create a choice picker widget from an A2UI ChoicePicker component.

    Uses RadioButtons for single selection, or a Column of CheckBoxes for multiple.
    """
    from castella.column import Column
    from castella.radio_buttons import RadioButtons
    from castella.checkbox import CheckBox

    # Get choices
    choices = []
    for choice in component.choices:
        choice_value = resolve_value(choice, data_model, "")
        choices.append(str(choice_value))

    # Get selected value(s)
    selected = resolve_value(component.selected, data_model, None)

    if component.allow_multiple:
        # Multiple selection - use CheckBoxes
        checkboxes = []
        selected_set = set(selected) if isinstance(selected, list) else set()

        for choice in choices:
            is_checked = choice in selected_set
            cb = CheckBox(
                checked=is_checked,
                on_label=choice,
                off_label=choice,
            )

            # Set up data binding if selected is a binding
            if isinstance(component.selected, DataBinding):
                path = component.selected.path

                def make_handler(choice_val: str, current_selected: set) -> Callable:
                    def handler(event: Any) -> None:
                        # Toggle selection
                        if choice_val in current_selected:
                            current_selected.discard(choice_val)
                        else:
                            current_selected.add(choice_val)
                        action_handler(
                            "__data_update__",
                            component.id,
                            {"path": path, "value": list(current_selected)},
                        )

                    return handler

                cb = cb.on_click(make_handler(choice, selected_set))

            checkboxes.append(cb.fixed_height(30))

        widget = Column(*checkboxes)
    else:
        # Single selection - use RadioButtons
        from castella.radio_buttons import RadioButtonsState

        initial_idx = 0
        if selected and selected in choices:
            initial_idx = choices.index(selected)

        state = RadioButtonsState(labels=choices, selected_index=initial_idx)
        widget = RadioButtons(state)

        # Set up data binding if selected is a binding
        if isinstance(component.selected, DataBinding):
            path = component.selected.path

            def on_select(idx: int) -> None:
                action_handler(
                    "__data_update__",
                    component.id,
                    {
                        "path": path,
                        "value": choices[idx] if idx < len(choices) else None,
                    },
                )

            widget = widget.on_select(on_select)

    # Apply flex weight if specified
    if component.weight is not None:
        widget = widget.flex(int(component.weight))

    return widget


def create_list(
    component: ListComponent,
    data_model: dict[str, Any],
    action_handler: ActionHandler,
) -> Widget:
    """Create a scrollable Column widget from an A2UI List component.

    Note: List children are created dynamically based on TemplateChildren.
    The renderer will populate children after all components are created.
    """
    from castella.column import Column

    # Create a scrollable column for the list
    # Children will be added by the renderer based on TemplateChildren
    widget = Column(scrollable=True)

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
