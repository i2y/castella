"""A2UI Component Catalog - Maps A2UI components to Castella widgets.

This module defines the mapping between A2UI component types and Castella
widget classes, enabling the A2UIRenderer to convert A2UI JSON into
native Castella UI elements.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable

from castella.core import Widget

if TYPE_CHECKING:
    from castella.a2ui.types import Component


# Type alias for widget factory functions
# Factory receives (component, data_model, action_handler) and returns Widget
WidgetFactory = Callable[["Component", dict[str, Any], Callable], Widget]


class ComponentCatalog:
    """Registry of A2UI component types to Castella widget factories.

    The catalog maps A2UI component type names (e.g., "Text", "Button") to
    factory functions that create the corresponding Castella widgets.

    Example:
        catalog = ComponentCatalog()
        catalog.register("CustomChart", my_chart_factory)
        widget = catalog.create("Text", text_component, data_model, action_handler)
    """

    def __init__(self, factories: dict[str, WidgetFactory] | None = None):
        """Initialize the catalog with optional custom factories.

        Args:
            factories: Optional dict of component type -> factory function.
                      If provided, these will override the default factories.
        """
        self._factories: dict[str, WidgetFactory] = {}
        self._register_defaults()

        if factories:
            self._factories.update(factories)

    def _register_defaults(self) -> None:
        """Register default A2UI component factories."""
        # Import here to avoid circular imports
        from castella.a2ui._factories import (
            create_button,
            create_card,
            create_checkbox,
            create_choice_picker,
            create_column,
            create_datetime_input,
            create_divider,
            create_icon,
            create_image,
            create_list,
            create_markdown,
            create_modal,
            create_row,
            create_slider,
            create_tabs,
            create_text,
            create_textfield,
        )

        self._factories = {
            # Display components
            "Text": create_text,
            "Image": create_image,
            "Icon": create_icon,
            "Divider": create_divider,
            "Markdown": create_markdown,
            # Interactive components
            "Button": create_button,
            "TextField": create_textfield,
            "CheckBox": create_checkbox,
            "Slider": create_slider,
            "DateTimeInput": create_datetime_input,
            "ChoicePicker": create_choice_picker,
            # Layout components
            "Row": create_row,
            "Column": create_column,
            "Card": create_card,
            "List": create_list,
            "Tabs": create_tabs,
            "Modal": create_modal,
        }

    def register(self, component_type: str, factory: WidgetFactory) -> None:
        """Register a custom component factory.

        Args:
            component_type: The A2UI component type name (e.g., "CustomChart")
            factory: A factory function that creates a Castella widget
        """
        self._factories[component_type] = factory

    def unregister(self, component_type: str) -> None:
        """Unregister a component factory.

        Args:
            component_type: The component type to unregister
        """
        self._factories.pop(component_type, None)

    def has(self, component_type: str) -> bool:
        """Check if a component type is registered.

        Args:
            component_type: The component type to check

        Returns:
            True if the component type is registered
        """
        return component_type in self._factories

    def create(
        self,
        component: "Component",
        data_model: dict[str, Any],
        action_handler: Callable[[str, str, dict[str, Any]], None],
    ) -> Widget:
        """Create a Castella widget from an A2UI component.

        Args:
            component: The A2UI component definition
            data_model: The current data model for resolving bindings
            action_handler: Callback for handling user actions
                           (action_name, source_component_id, context)

        Returns:
            A Castella Widget instance

        Raises:
            ValueError: If the component type is not registered
        """
        component_type = component.component
        if component_type not in self._factories:
            raise ValueError(f"Unknown component type: {component_type}")

        factory = self._factories[component_type]
        return factory(component, data_model, action_handler)

    def supported_types(self) -> list[str]:
        """Get list of supported component types.

        Returns:
            List of registered component type names
        """
        return list(self._factories.keys())


# Default catalog instance
_default_catalog: ComponentCatalog | None = None


def get_default_catalog() -> ComponentCatalog:
    """Get the default component catalog (singleton).

    Returns:
        The default ComponentCatalog instance
    """
    global _default_catalog
    if _default_catalog is None:
        _default_catalog = ComponentCatalog()
    return _default_catalog


def reset_default_catalog() -> None:
    """Reset the default catalog to its initial state."""
    global _default_catalog
    _default_catalog = None
