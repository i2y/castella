"""A2UI Renderer - Converts A2UI JSON to Castella widgets.

The renderer takes A2UI messages (createSurface, updateComponents, etc.)
and produces a tree of Castella widgets that can be displayed on any
Castella-supported platform (Desktop, Web, Terminal).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable

from castella.a2ui._factories import get_child_ids, resolve_value
from castella.a2ui.catalog import ComponentCatalog, get_default_catalog
from castella.a2ui.types import (
    CardComponent,
    ColumnComponent,
    Component,
    CreateSurface,
    ExplicitChildren,
    RowComponent,
    ServerMessage,
    TemplateChildren,
    UpdateComponents,
    UpdateDataModel,
    UserAction,
)
from castella.core import Widget

if TYPE_CHECKING:
    from castella.box import Box
    from castella.column import Column
    from castella.row import Row


class A2UISurface:
    """Represents a rendered A2UI surface.

    A surface contains a tree of widgets, a data model, and manages
    the relationship between A2UI component IDs and Castella widgets.
    """

    def __init__(self, surface_id: str, root_widget: Widget):
        self.surface_id = surface_id
        self.root_widget = root_widget
        self._widgets: dict[str, Widget] = {}
        self._data_model: dict[str, Any] = {}

    def get_widget(self, component_id: str) -> Widget | None:
        """Get the widget for a component ID."""
        return self._widgets.get(component_id)

    def register_widget(self, component_id: str, widget: Widget) -> None:
        """Register a widget with its component ID."""
        self._widgets[component_id] = widget

    @property
    def data_model(self) -> dict[str, Any]:
        """Get the current data model."""
        return self._data_model

    def update_data(self, path: str, value: Any) -> None:
        """Update a value in the data model.

        Args:
            path: JSON Pointer path (e.g., "/user/name")
            value: The new value
        """
        if path.startswith("/"):
            path = path[1:]
        parts = path.split("/")

        current = self._data_model
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]

        if parts:
            current[parts[-1]] = value


class A2UIRenderer:
    """Renders A2UI JSON into Castella widget trees.

    The renderer maintains surfaces (UI areas) and handles:
    - Creating new surfaces from A2UI JSON
    - Updating components and data models
    - Routing user actions back to the agent

    Example:
        renderer = A2UIRenderer()

        # Create surface from A2UI message
        surface = renderer.handle_message({
            "createSurface": {
                "surfaceId": "main",
                "components": [
                    {"id": "root", "component": "Column", "children": {"explicitList": ["text1"]}},
                    {"id": "text1", "component": "Text", "text": {"literalString": "Hello"}}
                ],
                "rootId": "root"
            }
        })

        # Get the root widget to display
        widget = surface.root_widget
    """

    def __init__(
        self,
        catalog: ComponentCatalog | None = None,
        on_action: Callable[[UserAction], None] | None = None,
    ):
        """Initialize the renderer.

        Args:
            catalog: Component catalog for creating widgets. Uses default if None.
            on_action: Callback for user actions. Called when user interacts with UI.
        """
        self._catalog = catalog or get_default_catalog()
        self._surfaces: dict[str, A2UISurface] = {}
        self._on_action = on_action

    def _action_handler(
        self, action_name: str, source_component_id: str, context: dict[str, Any]
    ) -> None:
        """Internal action handler that routes to the on_action callback."""
        # Handle special data update action
        if action_name == "__data_update__":
            # Find the surface containing this component
            for surface in self._surfaces.values():
                if surface.get_widget(source_component_id) is not None:
                    path = context.get("path", "")
                    value = context.get("value")
                    surface.update_data(path, value)
                    break
            return

        # Create UserAction and send to callback
        if self._on_action:
            # Find surface ID
            surface_id = ""
            for sid, surface in self._surfaces.items():
                if surface.get_widget(source_component_id) is not None:
                    surface_id = sid
                    break

            user_action = UserAction(
                name=action_name,
                surfaceId=surface_id,
                sourceComponentId=source_component_id,
                context=context,
            )
            self._on_action(user_action)

    def handle_message(self, message: dict[str, Any] | ServerMessage) -> A2UISurface | None:
        """Handle an A2UI server message.

        Args:
            message: The A2UI message (dict or ServerMessage)

        Returns:
            The affected surface, or None if no surface was created/updated
        """
        if isinstance(message, dict):
            message = ServerMessage.model_validate(message)

        if message.create_surface:
            return self._handle_create_surface(message.create_surface)
        elif message.update_components:
            return self._handle_update_components(message.update_components)
        elif message.update_data_model:
            return self._handle_update_data_model(message.update_data_model)
        elif message.delete_surface:
            self._surfaces.pop(message.delete_surface.surface_id, None)
            return None

        return None

    def _handle_create_surface(self, msg: CreateSurface) -> A2UISurface:
        """Create a new surface from a createSurface message."""
        surface_id = msg.surface_id
        components = msg.components

        # Build component lookup
        component_map: dict[str, Component] = {c.id: c for c in components}

        # Determine root component
        root_id = msg.root_id
        if not root_id and components:
            root_id = components[0].id

        if not root_id or root_id not in component_map:
            raise ValueError(f"Invalid root component ID: {root_id}")

        # Create a temporary surface to hold data model
        temp_surface = A2UISurface(surface_id, None)  # type: ignore

        # Create all widgets first
        widgets: dict[str, Widget] = {}
        for component in components:
            widget = self._catalog.create(
                component,
                temp_surface.data_model,
                self._action_handler,
            )
            widgets[component.id] = widget
            temp_surface.register_widget(component.id, widget)

        # Connect children for layout components
        for component in components:
            self._connect_children(component, widgets, component_map)

        # Create the final surface
        root_widget = widgets[root_id]
        surface = A2UISurface(surface_id, root_widget)
        surface._widgets = widgets
        surface._data_model = temp_surface._data_model

        self._surfaces[surface_id] = surface
        return surface

    def _connect_children(
        self,
        component: Component,
        widgets: dict[str, Widget],
        component_map: dict[str, Component],
    ) -> None:
        """Connect child widgets to parent layout widgets."""
        children_spec = None

        if isinstance(component, (RowComponent, ColumnComponent, CardComponent)):
            children_spec = component.children

        if children_spec is None:
            return

        parent_widget = widgets.get(component.id)
        if parent_widget is None:
            return

        if isinstance(children_spec, ExplicitChildren):
            child_ids = children_spec.explicit_list
            for child_id in child_ids:
                child_widget = widgets.get(child_id)
                if child_widget is not None:
                    self._add_child_to_parent(parent_widget, child_widget)

        elif isinstance(children_spec, TemplateChildren):
            # TODO: Handle template children with data binding
            pass

    def _add_child_to_parent(self, parent: Widget, child: Widget) -> None:
        """Add a child widget to a parent layout widget."""
        # Import here to avoid circular imports
        from castella.box import Box
        from castella.column import Column
        from castella.row import Row

        if isinstance(parent, (Column, Row, Box)):
            parent.add(child)

    def _handle_update_components(self, msg: UpdateComponents) -> A2UISurface | None:
        """Update components in an existing surface."""
        surface = self._surfaces.get(msg.surface_id)
        if surface is None:
            return None

        # TODO: Implement incremental updates
        # For now, this is a placeholder
        return surface

    def _handle_update_data_model(self, msg: UpdateDataModel) -> A2UISurface | None:
        """Update the data model for a surface."""
        surface = self._surfaces.get(msg.surface_id)
        if surface is None:
            return None

        # Update data model values
        for path, value in msg.data.items():
            surface.update_data(path, value)

        # TODO: Trigger widget updates for bound values
        return surface

    def get_surface(self, surface_id: str) -> A2UISurface | None:
        """Get a surface by ID.

        Args:
            surface_id: The surface ID

        Returns:
            The surface, or None if not found
        """
        return self._surfaces.get(surface_id)

    def render_components(
        self,
        components: list[Component],
        root_id: str | None = None,
        surface_id: str = "default",
    ) -> Widget:
        """Convenience method to render a list of components.

        Args:
            components: List of A2UI components
            root_id: ID of the root component (defaults to first component)
            surface_id: Surface ID to use

        Returns:
            The root widget
        """
        message = ServerMessage(
            createSurface=CreateSurface(
                surfaceId=surface_id,
                components=components,
                rootId=root_id,
            )
        )
        surface = self.handle_message(message)
        if surface is None:
            raise ValueError("Failed to create surface")
        return surface.root_widget

    def render_json(
        self,
        json_data: dict[str, Any],
        surface_id: str = "default",
    ) -> Widget:
        """Render A2UI JSON directly.

        Args:
            json_data: A2UI JSON with "components" and optional "rootId"
            surface_id: Surface ID to use

        Returns:
            The root widget
        """
        components_data = json_data.get("components", [])
        root_id = json_data.get("rootId")

        # Parse components
        from castella.a2ui.types import (
            ButtonComponent,
            CardComponent,
            CheckBoxComponent,
            ColumnComponent,
            DividerComponent,
            ImageComponent,
            MarkdownComponent,
            RowComponent,
            TextComponent,
            TextFieldComponent,
        )

        component_types = {
            "Text": TextComponent,
            "Button": ButtonComponent,
            "TextField": TextFieldComponent,
            "CheckBox": CheckBoxComponent,
            "Image": ImageComponent,
            "Divider": DividerComponent,
            "Row": RowComponent,
            "Column": ColumnComponent,
            "Card": CardComponent,
            "Markdown": MarkdownComponent,
        }

        components: list[Component] = []
        for comp_data in components_data:
            comp_type = comp_data.get("component")
            if comp_type in component_types:
                component_class = component_types[comp_type]
                component = component_class.model_validate(comp_data)
                components.append(component)

        return self.render_components(components, root_id, surface_id)
