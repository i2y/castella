"""Semantic widget registry for stable ID management."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from weakref import WeakValueDictionary

from .types import WidgetMetadata

if TYPE_CHECKING:
    from castella.core import Widget


class SemanticWidgetRegistry:
    """Assigns and tracks stable semantic IDs for widgets.

    This registry maintains a mapping between stable semantic IDs and widgets,
    allowing MCP tools to reference widgets even after view rebuilds.

    For A2UI widgets, the component ID is used directly as the semantic ID.
    For native Castella widgets, IDs are generated from widget type and hints.
    """

    def __init__(self) -> None:
        # Weak references to widgets - garbage collected when widget is destroyed
        self._widgets: WeakValueDictionary[str, Widget] = WeakValueDictionary()
        # Metadata for each registered widget
        self._metadata: dict[str, WidgetMetadata] = {}
        # Memory address to semantic ID mapping for reverse lookup
        self._memory_to_semantic: dict[int, str] = {}
        # Counter for generating unique IDs
        self._counter: int = 0
        # A2UI surfaces for integration
        self._a2ui_surfaces: dict[str, Any] = {}

    def register(
        self,
        widget: "Widget",
        hint: str | None = None,
        a2ui_id: str | None = None,
        parent_id: str | None = None,
    ) -> str:
        """Register a widget and return its stable semantic ID.

        Args:
            widget: The widget to register
            hint: Optional semantic ID hint (e.g., from widget.semantic_id())
            a2ui_id: A2UI component ID if this widget came from A2UI
            parent_id: Semantic ID of the parent widget

        Returns:
            The stable semantic ID for the widget
        """
        # Check if widget already registered
        mem_id = id(widget)
        if mem_id in self._memory_to_semantic:
            return self._memory_to_semantic[mem_id]

        # Determine semantic ID
        if a2ui_id is not None:
            # A2UI widgets use their component ID directly
            semantic_id = a2ui_id
        elif hint is not None:
            # Use provided hint
            semantic_id = hint
        else:
            # Generate from widget type
            widget_type = type(widget).__name__.lower()
            semantic_id = f"{widget_type}_{self._counter}"
            self._counter += 1

        # Handle duplicates by appending counter
        original_id = semantic_id
        suffix = 1
        while semantic_id in self._widgets:
            semantic_id = f"{original_id}_{suffix}"
            suffix += 1

        # Register the widget
        self._widgets[semantic_id] = widget
        self._memory_to_semantic[mem_id] = semantic_id
        self._metadata[semantic_id] = WidgetMetadata(
            semantic_id=semantic_id,
            widget_type=type(widget).__name__,
            label=self._extract_label(widget),
            is_interactive=self._is_interactive(widget),
            can_focus=self._can_focus(widget),
            parent_id=parent_id,
            a2ui_component_id=a2ui_id,
        )

        return semantic_id

    def unregister(self, semantic_id: str) -> None:
        """Unregister a widget by its semantic ID."""
        if semantic_id in self._widgets:
            widget = self._widgets.get(semantic_id)
            if widget is not None:
                mem_id = id(widget)
                self._memory_to_semantic.pop(mem_id, None)
            del self._widgets[semantic_id]
            self._metadata.pop(semantic_id, None)

    def get_widget(self, semantic_id: str) -> "Widget | None":
        """Get widget by semantic ID."""
        return self._widgets.get(semantic_id)

    def get_semantic_id(self, widget: "Widget") -> str | None:
        """Get the semantic ID for a widget."""
        return self._memory_to_semantic.get(id(widget))

    def get_metadata(self, semantic_id: str) -> WidgetMetadata | None:
        """Get widget metadata by semantic ID."""
        return self._metadata.get(semantic_id)

    def get_all_widgets(self) -> dict[str, "Widget"]:
        """Get all registered widgets."""
        return dict(self._widgets)

    def get_all_metadata(self) -> dict[str, WidgetMetadata]:
        """Get all widget metadata."""
        return dict(self._metadata)

    def clear(self) -> None:
        """Clear all registrations."""
        self._widgets.clear()
        self._metadata.clear()
        self._memory_to_semantic.clear()
        self._counter = 0

    def rebuild_from_tree(self, root: "Widget") -> None:
        """Rebuild registry by traversing the current widget tree.

        This method walks the widget tree and registers all widgets,
        preserving semantic IDs for widgets that have hints or A2UI IDs.
        A2UI surface registrations are preserved across rebuilds.
        """
        # Preserve A2UI surfaces
        preserved_surfaces = dict(self._a2ui_surfaces)

        self.clear()

        # Restore A2UI surfaces and re-register their widgets
        self._a2ui_surfaces = preserved_surfaces
        for surface in preserved_surfaces.values():
            widgets = getattr(surface, "_widgets", {})
            for comp_id, widget in widgets.items():
                self.register(widget, a2ui_id=comp_id)

        self._traverse_and_register(root, parent_id=None)

    def _traverse_and_register(self, widget: "Widget", parent_id: str | None) -> str:
        """Recursively traverse and register widgets."""
        # Check if already registered (e.g., from A2UI)
        existing_id = self.get_semantic_id(widget)
        if existing_id is not None:
            semantic_id = existing_id
        else:
            # Get hint from widget if available
            hint = getattr(widget, "_semantic_id_hint", None)

            # Register this widget
            semantic_id = self.register(widget, hint=hint, parent_id=parent_id)

        # Traverse children if this is a layout (even if already registered)
        from castella.core import Layout, Component

        if isinstance(widget, Layout):
            children = getattr(widget, "_children", [])

            # For Component, if _children is empty but _child exists, use it
            # Also try calling view() if no children are found
            if isinstance(widget, Component):
                if not children:
                    # Try _child attribute first
                    child = getattr(widget, "_child", None)
                    if child is not None:
                        children = [child]
                    else:
                        # Call view() to get the widget tree
                        try:
                            view_result = widget.view()
                            if view_result is not None:
                                children = [view_result]
                        except Exception:
                            pass  # view() may fail, ignore

            for child in children:
                self._traverse_and_register(child, parent_id=semantic_id)

        return semantic_id

    def register_a2ui_surface(self, surface: Any) -> None:
        """Register all widgets from an A2UI surface.

        A2UI components have stable string IDs that are preserved during
        the surface lifetime. This method registers all widgets with their
        component IDs as semantic IDs.

        Args:
            surface: An A2UISurface object
        """
        self._a2ui_surfaces[surface.surface_id] = surface

        # Register all widgets from the surface
        widgets = getattr(surface, "_widgets", {})
        for comp_id, widget in widgets.items():
            self.register(widget, a2ui_id=comp_id)

    def unregister_a2ui_surface(self, surface_id: str) -> None:
        """Unregister all widgets from an A2UI surface."""
        if surface_id in self._a2ui_surfaces:
            surface = self._a2ui_surfaces[surface_id]
            widgets = getattr(surface, "_widgets", {})
            for comp_id in widgets.keys():
                self.unregister(comp_id)
            del self._a2ui_surfaces[surface_id]

    def _extract_label(self, widget: "Widget") -> str | None:
        """Extract a human-readable label from a widget."""
        # Try common label attributes
        for attr in ["_text", "_label", "_title", "_placeholder"]:
            value = getattr(widget, attr, None)
            if value is not None and isinstance(value, str):
                return value

        # For Button, check text
        widget_type = type(widget).__name__
        if widget_type == "Button":
            text = getattr(widget, "_text", None)
            if text is not None:
                return text

        return None

    def _is_interactive(self, widget: "Widget") -> bool:
        """Check if a widget is interactive."""
        widget_type = type(widget).__name__
        interactive_types = {
            "Button",
            "Input",
            "MultilineInput",
            "CheckBox",
            "Switch",
            "Slider",
            "RadioButtons",
            "Tabs",
            "Tree",
            "FileTree",
            "DateTimeInput",
            "DataTable",
        }
        return widget_type in interactive_types

    def _can_focus(self, widget: "Widget") -> bool:
        """Check if a widget can receive focus."""
        widget_type = type(widget).__name__
        focusable_types = {
            "Button",
            "Input",
            "MultilineInput",
            "CheckBox",
            "Switch",
            "Slider",
            "RadioButtons",
            "DataTable",
        }
        return widget_type in focusable_types
