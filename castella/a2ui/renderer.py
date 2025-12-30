"""A2UI Renderer - Converts A2UI JSON to Castella widgets.

The renderer takes A2UI messages (createSurface, updateComponents, etc.)
and produces a tree of Castella widgets that can be displayed on any
Castella-supported platform (Desktop, Web, Terminal).

Supports both the official A2UI 0.9 specification format and Castella's
internal format. Messages are automatically normalized via the compat module.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterator
from typing import TYPE_CHECKING, Any, Callable

from castella.a2ui._factories import resolve_value
from castella.a2ui.catalog import ComponentCatalog, get_default_catalog
from castella.a2ui.compat import normalize_message
from castella.a2ui.types import (
    BeginRendering,
    CardComponent,
    ColumnComponent,
    Component,
    CreateSurface,
    ExplicitChildren,
    ListComponent,
    RowComponent,
    ServerMessage,
    TemplateChildren,
    UpdateComponents,
    UpdateDataModel,
    UserAction,
)
from castella.core import Component as CastellaComponent
from castella.core import ObservableBase, Widget

if TYPE_CHECKING:
    pass


class A2UISurface(ObservableBase):
    """Represents a rendered A2UI surface.

    A surface contains a tree of widgets, a data model, and manages
    the relationship between A2UI component IDs and Castella widgets.

    The surface is observable - when the data model is updated via
    updateDataModel message, observers (like A2UIComponent) are notified
    to trigger a UI rebuild.
    """

    def __init__(self, surface_id: str, root_widget: Widget):
        super().__init__()
        self.surface_id = surface_id
        self.root_widget = root_widget
        self._widgets: dict[str, Widget] = {}
        self._components: dict[str, Component] = {}  # Store component definitions
        self._data_model: dict[str, Any] = {}
        self._root_id: str | None = None  # For re-rendering on data model updates

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

    def notify_update(self) -> None:
        """Notify observers that the surface has been updated."""
        self.notify()


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
        self._pending_initial_data: dict[str, Any] | None = None
        # For progressive rendering: track pending surfaces and their root IDs
        self._pending_roots: dict[str, str] = {}  # surface_id -> root_id
        self._pending_components: dict[
            str, dict[str, Component]
        ] = {}  # surface_id -> {id: component}

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

    def handle_message(
        self, message: dict[str, Any] | ServerMessage
    ) -> A2UISurface | None:
        """Handle an A2UI server message.

        Supports both A2UI 0.9 specification format and Castella's internal format.
        Messages are automatically normalized to Castella's format.

        Args:
            message: The A2UI message (dict or ServerMessage)

        Returns:
            The affected surface, or None if no surface was created/updated
        """
        if isinstance(message, dict):
            # Normalize A2UI 0.9 spec format to Castella format
            message = normalize_message(message)
            message = ServerMessage.model_validate(message)

        if message.begin_rendering:
            return self._handle_begin_rendering(message.begin_rendering)
        elif message.create_surface:
            return self._handle_create_surface(message.create_surface)
        elif message.update_components:
            return self._handle_update_components(message.update_components)
        elif message.update_data_model:
            return self._handle_update_data_model(message.update_data_model)
        elif message.delete_surface:
            self._surfaces.pop(message.delete_surface.surface_id, None)
            # Clean up pending state
            self._pending_roots.pop(message.delete_surface.surface_id, None)
            self._pending_components.pop(message.delete_surface.surface_id, None)
            return None

        return None

    def _handle_begin_rendering(self, msg: BeginRendering) -> A2UISurface | None:
        """Handle a beginRendering message.

        This prepares for progressive rendering by storing the root ID
        and creating an empty pending component map.

        If a surface with the same ID already exists, it is deleted first
        to allow for a fresh render.
        """
        surface_id = msg.surface_id

        # Clear existing surface if any (allows re-rendering)
        if surface_id in self._surfaces:
            del self._surfaces[surface_id]

        self._pending_roots[surface_id] = msg.root
        self._pending_components[surface_id] = {}
        return None  # Surface not yet created

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

        # Apply initial data if provided (for TemplateChildren/List support)
        if self._pending_initial_data:
            for path, value in self._pending_initial_data.items():
                temp_surface.update_data(path, value)

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
            self._connect_children(component, widgets, component_map, temp_surface)

        # Create the final surface
        root_widget = widgets[root_id]
        surface = A2UISurface(surface_id, root_widget)
        surface._widgets = widgets
        surface._components = component_map  # Store component definitions
        surface._data_model = temp_surface._data_model
        surface._root_id = root_id  # Store for re-rendering on data model updates

        self._surfaces[surface_id] = surface
        return surface

    def _connect_children(
        self,
        component: Component,
        widgets: dict[str, Widget],
        component_map: dict[str, Component],
        surface: A2UISurface,
    ) -> None:
        """Connect child widgets to parent layout widgets."""
        children_spec = None

        if isinstance(component, (RowComponent, ColumnComponent, CardComponent)):
            children_spec = component.children
        elif isinstance(component, ListComponent):
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
            # Handle template children with data binding
            self._render_template_children(
                parent_widget,
                children_spec,
                component_map,
                surface,
            )

    def _add_child_to_parent(self, parent: Widget, child: Widget) -> None:
        """Add a child widget to a parent layout widget.

        Avoids adding duplicates if child is already a child of parent.
        """
        import os

        # Import here to avoid circular imports
        from castella.box import Box
        from castella.column import Column
        from castella.row import Row

        if isinstance(parent, (Column, Row, Box)):
            # Check if child is already added to avoid duplicates
            existing_children = getattr(parent, "_children", [])
            if child not in existing_children:
                parent.add(child)
                if os.environ.get("A2UI_DEBUG"):
                    print(f"[RENDERER] Added child {child} to parent {parent}")

    def _render_template_children(
        self,
        parent_widget: Widget,
        template_spec: TemplateChildren,
        component_map: dict[str, Component],
        surface: A2UISurface,
    ) -> None:
        """Render template children based on array data.

        For each item in the data array at `path`, creates a widget from
        the template component with that item as scoped data.

        Args:
            parent_widget: The parent widget to add children to
            template_spec: The TemplateChildren specification
            component_map: Map of component IDs to component definitions
            surface: The current surface (for data model access)
        """
        from castella.a2ui.types import DataBinding

        # Get array data from data model
        array_data = resolve_value(
            DataBinding(path=template_spec.path),
            surface.data_model,
            default=[],
        )

        # Handle both list and dict (legacy valueMap format)
        if isinstance(array_data, dict):
            # Convert dict values to list for iteration
            array_data = list(array_data.values())
        elif not isinstance(array_data, list):
            return

        # Get template component
        template_component = component_map.get(template_spec.component_id)
        if template_component is None:
            return

        # Render a widget for each item in the array
        for idx, item in enumerate(array_data):
            # Create scoped data model for this item
            # The item becomes the root of relative paths
            scoped_data = surface.data_model.copy()

            # Add the current item at a special scope path
            # This allows relative paths like "name" to resolve to item["name"]
            if isinstance(item, dict):
                # Merge item data at root level for relative path access
                scoped_data.update(item)
                # Also store at indexed path for absolute access
                item_path = template_spec.path.lstrip("/")
                if item_path:
                    parts = item_path.split("/")
                    current = scoped_data
                    for part in parts[:-1]:
                        if part not in current:
                            current[part] = {}
                        current = current[part]
                    if parts:
                        if parts[-1] not in current:
                            current[parts[-1]] = []
                        if isinstance(current[parts[-1]], list) and idx < len(
                            current[parts[-1]]
                        ):
                            pass  # Already there
            else:
                # Primitive value - store as "_item"
                scoped_data["_item"] = item

            # Create widget from template with scoped data
            # We need to create the template widget AND its children with scoped data
            widget = self._catalog.create(
                template_component,
                scoped_data,
                self._action_handler,
            )

            # Recursively create and connect child widgets with scoped data
            self._create_template_children(
                template_component,
                widget,
                component_map,
                scoped_data,
            )

            # For List items, ensure they have CONTENT or FIXED height
            # (scrollable containers can't have EXPANDING children)
            from castella.core import SizePolicy

            if hasattr(widget, "_height_policy"):
                current_policy = widget._height_policy
                if current_policy == SizePolicy.EXPANDING:
                    # Set fixed height for list items (default item height)
                    widget = widget.fixed_height(100)

            # Add to parent
            self._add_child_to_parent(parent_widget, widget)

    def _create_template_children(
        self,
        component: Component,
        parent_widget: Widget,
        component_map: dict[str, Component],
        scoped_data: dict[str, Any],
    ) -> None:
        """Recursively create child widgets for a template with scoped data.

        This ensures all nested children in a template are created with
        the item-specific data model.
        """
        children_spec = None

        if isinstance(component, (RowComponent, ColumnComponent, CardComponent)):
            children_spec = component.children
        elif isinstance(component, ListComponent):
            children_spec = component.children

        if children_spec is None:
            return

        if isinstance(children_spec, ExplicitChildren):
            for child_id in children_spec.explicit_list:
                child_component = component_map.get(child_id)
                if child_component is None:
                    continue

                # Create child widget with scoped data
                child_widget = self._catalog.create(
                    child_component,
                    scoped_data,
                    self._action_handler,
                )

                # Add to parent
                self._add_child_to_parent(parent_widget, child_widget)

                # Recursively process grandchildren
                self._create_template_children(
                    child_component,
                    child_widget,
                    component_map,
                    scoped_data,
                )

    def _handle_update_components(self, msg: UpdateComponents) -> A2UISurface | None:
        """Update components in an existing surface (progressive rendering).

        If the surface doesn't exist yet but beginRendering was called,
        this accumulates components until the root is available, then builds
        the surface.
        """
        surface_id = msg.surface_id
        surface = self._surfaces.get(surface_id)

        # Case 1: Surface exists - update incrementally
        if surface is not None:
            return self._update_existing_surface(surface, msg.components)

        # Case 2: No surface yet, but beginRendering was called - accumulate
        if surface_id in self._pending_roots:
            pending_map = self._pending_components.get(surface_id, {})
            for component in msg.components:
                pending_map[component.id] = component
            self._pending_components[surface_id] = pending_map

            # Check if we have the root component now
            root_id = self._pending_roots[surface_id]
            if root_id in pending_map:
                # Try to build the surface
                return self._try_build_pending_surface(surface_id)

        return None

    def _update_existing_surface(
        self,
        surface: A2UISurface,
        components: list[Component],
    ) -> A2UISurface:
        """Update an existing surface with new/updated components."""

        # Track newly added component IDs
        new_ids = set()

        # Create or update widgets and store component definitions
        for component in components:
            new_ids.add(component.id)
            surface._components[component.id] = component

            widget = self._catalog.create(
                component,
                surface.data_model,
                self._action_handler,
            )
            surface._widgets[component.id] = widget

        # Reconnect children for the new components
        for component in components:
            self._connect_children(
                component,
                surface._widgets,
                surface._components,
                surface,
            )

        # Also reconnect existing parent components that reference new children
        for comp_id, component in surface._components.items():
            if comp_id in new_ids:
                continue  # Already handled above

            # Check if this component references any of the new IDs as children
            child_ids = self._get_child_ids(component)
            if child_ids and any(cid in new_ids for cid in child_ids):
                self._connect_children(
                    component,
                    surface._widgets,
                    surface._components,
                    surface,
                )

        return surface

    def _get_child_ids(self, component: Component) -> list[str]:
        """Get child IDs from a component's children specification."""
        children_spec = None

        if isinstance(component, (RowComponent, ColumnComponent, CardComponent)):
            children_spec = component.children
        elif isinstance(component, ListComponent):
            children_spec = component.children

        if children_spec is None:
            return []

        if isinstance(children_spec, ExplicitChildren):
            return children_spec.explicit_list

        return []

    def _try_build_pending_surface(self, surface_id: str) -> A2UISurface | None:
        """Try to build a surface from accumulated pending components.

        Returns the surface if successful, None if more components are needed.
        """
        root_id = self._pending_roots.get(surface_id)
        pending_map = self._pending_components.get(surface_id, {})

        if not root_id or root_id not in pending_map:
            return None

        # Convert to list for CreateSurface
        components = list(pending_map.values())

        # Build using existing create_surface logic
        create_msg = CreateSurface(
            surfaceId=surface_id,
            components=components,
            rootId=root_id,
        )
        surface = self._handle_create_surface(create_msg)

        # Clean up pending state
        self._pending_roots.pop(surface_id, None)
        self._pending_components.pop(surface_id, None)

        return surface

    def _handle_update_data_model(self, msg: UpdateDataModel) -> A2UISurface | None:
        """Update the data model for a surface and re-render bound widgets."""
        import os

        debug = os.environ.get("A2UI_DEBUG")

        if debug:
            print(f"[RENDERER] _handle_update_data_model: surfaceId={msg.surface_id}")
            print(f"[RENDERER]   msg.data = {msg.data}")

        surface = self._surfaces.get(msg.surface_id)
        if surface is None:
            if debug:
                print("[RENDERER]   Surface not found!")
            return None

        # Update data model values
        for path, value in msg.data.items():
            surface.update_data(path, value)

        if debug:
            print(f"[RENDERER]   Updated data_model = {surface._data_model}")
            print(
                f"[RENDERER]   Components: {list(surface._components.keys()) if surface._components else 'None'}"
            )
            print(f"[RENDERER]   root_id: {surface._root_id}")

        # Re-render all components with updated data model
        if surface._components and surface._root_id:
            # Recreate all widgets with the new data model values
            for comp_id, component in surface._components.items():
                widget = self._catalog.create(
                    component,
                    surface._data_model,
                    self._action_handler,
                )
                surface._widgets[comp_id] = widget

            # Reconnect children for layout components
            for comp_id, component in surface._components.items():
                self._connect_children(
                    component,
                    surface._widgets,
                    surface._components,
                    surface,
                )

            # Update root_widget reference
            surface.root_widget = surface._widgets[surface._root_id]

            # Notify observers that the surface has been updated
            surface.notify_update()

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
        initial_data: dict[str, Any] | None = None,
    ) -> Widget:
        """Convenience method to render a list of components.

        Args:
            components: List of A2UI components
            root_id: ID of the root component (defaults to first component)
            surface_id: Surface ID to use
            initial_data: Initial data model values (for TemplateChildren/List)

        Returns:
            The root widget
        """
        # Store initial data temporarily for _handle_create_surface
        self._pending_initial_data = initial_data

        message = ServerMessage(
            createSurface=CreateSurface(
                surfaceId=surface_id,
                components=components,
                rootId=root_id,
            )
        )
        surface = self.handle_message(message)

        # Clear pending data
        self._pending_initial_data = None

        if surface is None:
            raise ValueError("Failed to create surface")
        return surface.root_widget

    def render_json(
        self,
        json_data: dict[str, Any],
        surface_id: str = "default",
        initial_data: dict[str, Any] | None = None,
    ) -> Widget:
        """Render A2UI JSON directly.

        Supports both A2UI 0.9 specification format and Castella's internal format.
        Components are automatically normalized to Castella's format.

        Args:
            json_data: A2UI JSON with "components" and optional "rootId"
            surface_id: Surface ID to use
            initial_data: Initial data model values (for TemplateChildren/List)

        Returns:
            The root widget
        """
        from castella.a2ui.compat import normalize_component

        components_data = json_data.get("components", [])
        # Normalize each component to Castella's format
        components_data = [normalize_component(c) for c in components_data]
        root_id = json_data.get("rootId")
        # Also check for data in json_data
        data_from_json = json_data.get("data", {})
        merged_data = {**data_from_json, **(initial_data or {})}

        # Parse components
        from castella.a2ui.types import (
            ButtonComponent,
            CardComponent,
            CheckBoxComponent,
            ChoicePickerComponent,
            ColumnComponent,
            DateTimeInputComponent,
            DividerComponent,
            IconComponent,
            ImageComponent,
            ListComponent as ListComp,
            MarkdownComponent,
            ModalComponent,
            RowComponent,
            SliderComponent,
            TabsComponent,
            TextComponent,
            TextFieldComponent,
        )

        component_types = {
            "Text": TextComponent,
            "Button": ButtonComponent,
            "TextField": TextFieldComponent,
            "CheckBox": CheckBoxComponent,
            "Slider": SliderComponent,
            "DateTimeInput": DateTimeInputComponent,
            "ChoicePicker": ChoicePickerComponent,
            "Image": ImageComponent,
            "Icon": IconComponent,
            "Divider": DividerComponent,
            "Row": RowComponent,
            "Column": ColumnComponent,
            "Card": CardComponent,
            "List": ListComp,
            "Tabs": TabsComponent,
            "Modal": ModalComponent,
            "Markdown": MarkdownComponent,
        }

        components: list[Component] = []
        for comp_data in components_data:
            comp_type = comp_data.get("component")
            if comp_type in component_types:
                component_class = component_types[comp_type]
                component = component_class.model_validate(comp_data)
                components.append(component)

        return self.render_components(components, root_id, surface_id, merged_data)

    # =========================================================================
    # Streaming API
    # =========================================================================

    def handle_stream(
        self,
        stream: Iterator[str],
        on_update: Callable[[A2UISurface], None] | None = None,
        surface_id: str | None = None,
    ) -> A2UISurface | None:
        """Handle a JSONL stream of A2UI messages (synchronous).

        Processes messages from a JSONL stream, progressively building or
        updating surfaces as messages arrive.

        Args:
            stream: An iterator yielding JSONL strings (e.g., file lines)
            on_update: Callback called whenever a surface is created/updated
            surface_id: If provided, returns only this surface at the end

        Returns:
            The surface (if surface_id provided), or the last updated surface

        Example:
            with open("ui.jsonl") as f:
                surface = renderer.handle_stream(f, on_update=lambda s: app.redraw())
                if surface:
                    widget = surface.root_widget
        """
        from castella.a2ui.stream import parse_sync_stream

        last_surface: A2UISurface | None = None

        for message in parse_sync_stream(stream):
            result = self.handle_message(message)
            if result is not None:
                last_surface = result
                if on_update:
                    on_update(result)

        if surface_id:
            return self.get_surface(surface_id)
        return last_surface

    async def handle_stream_async(
        self,
        stream: AsyncIterator[str],
        on_update: Callable[[A2UISurface], None] | None = None,
        surface_id: str | None = None,
    ) -> A2UISurface | None:
        """Handle a JSONL stream of A2UI messages (asynchronous).

        Processes messages from an async JSONL stream, progressively building
        or updating surfaces as messages arrive.

        Args:
            stream: An async iterator yielding JSONL strings (e.g., SSE events)
            on_update: Callback called whenever a surface is created/updated
            surface_id: If provided, returns only this surface at the end

        Returns:
            The surface (if surface_id provided), or the last updated surface

        Example:
            async for surface in renderer.handle_stream_async(sse_stream(url)):
                await on_update(surface)
        """
        from castella.a2ui.stream import parse_async_stream

        last_surface: A2UISurface | None = None

        async for message in parse_async_stream(stream):
            result = self.handle_message(message)
            if result is not None:
                last_surface = result
                if on_update:
                    on_update(result)

        if surface_id:
            return self.get_surface(surface_id)
        return last_surface

    def handle_jsonl(
        self,
        jsonl_content: str,
        on_update: Callable[[A2UISurface], None] | None = None,
        surface_id: str | None = None,
    ) -> A2UISurface | None:
        """Handle a complete JSONL string.

        Convenience method for processing a complete JSONL string.

        Args:
            jsonl_content: A string containing multiple JSON lines
            on_update: Callback called whenever a surface is created/updated
            surface_id: If provided, returns only this surface at the end

        Returns:
            The surface (if surface_id provided), or the last updated surface

        Example:
            jsonl = '''
            {"beginRendering": {"surfaceId": "main", "root": "root"}}
            {"updateComponents": {"surfaceId": "main", "components": [...]}}
            '''
            surface = renderer.handle_jsonl(jsonl)
        """
        from castella.a2ui.stream import parse_jsonl_string

        last_surface: A2UISurface | None = None

        for message in parse_jsonl_string(jsonl_content):
            result = self.handle_message(message)
            if result is not None:
                last_surface = result
                if on_update:
                    on_update(result)

        if surface_id:
            return self.get_surface(surface_id)
        return last_surface


class A2UIComponent(CastellaComponent):
    """A Castella Component that wraps an A2UI surface.

    This component automatically rebuilds its view when the underlying
    A2UI surface is updated (e.g., via updateDataModel message).

    Example:
        renderer = A2UIRenderer(on_action=on_action)
        surface = renderer.handle_message(create_surface_msg)

        # Create component that auto-updates on data changes
        component = A2UIComponent(surface)

        # Run the app
        App(Frame("A2UI App", 800, 600), component).run()
    """

    def __init__(self, surface: A2UISurface):
        super().__init__()
        self._surface = surface
        self._surface.attach(self)

    def view(self) -> Widget:
        """Return the current root widget from the surface."""
        return self._surface.root_widget
