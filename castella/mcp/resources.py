"""MCP resource handlers for Castella UI introspection."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .types import FocusInfo

if TYPE_CHECKING:
    from castella.core import App
    from .registry import SemanticWidgetRegistry
    from .introspection import WidgetIntrospector


def get_ui_tree(
    app: "App",
    registry: "SemanticWidgetRegistry",
    introspector: "WidgetIntrospector",
) -> dict[str, Any]:
    """Get the complete UI tree with all widgets.

    Returns a hierarchical representation of the UI with semantic IDs,
    types, labels, and properties for each widget.
    """
    root = app._root_widget
    if root is None:
        return {"error": "No root widget"}

    # Rebuild registry from current tree
    registry.rebuild_from_tree(root)

    # Build tree structure
    tree = introspector.build_tree(root)
    return tree.model_dump()


def get_focus_info(
    app: "App",
    registry: "SemanticWidgetRegistry",
    introspector: "WidgetIntrospector",
) -> dict[str, Any]:
    """Get information about the currently focused element."""
    focused = app._focused
    if focused is None:
        return FocusInfo(element_id=None).model_dump()

    semantic_id = registry.get_semantic_id(focused)
    if semantic_id is None:
        # Try to register it
        semantic_id = registry.register(focused)

    return FocusInfo(
        element_id=semantic_id,
        element_type=type(focused).__name__,
        element_label=introspector.get_label(focused),
    ).model_dump()


def list_elements(
    app: "App",
    registry: "SemanticWidgetRegistry",
    introspector: "WidgetIntrospector",
) -> list[dict[str, Any]]:
    """Get all interactive/actionable elements."""
    root = app._root_widget
    if root is None:
        return []

    # Rebuild registry
    registry.rebuild_from_tree(root)

    # Get interactive elements
    elements = introspector.get_interactive_elements(root, app)
    return [e.model_dump() for e in elements]


def get_element_by_id(
    element_id: str,
    app: "App",
    registry: "SemanticWidgetRegistry",
    introspector: "WidgetIntrospector",
) -> dict[str, Any]:
    """Get detailed information about a specific element."""
    widget = registry.get_widget(element_id)
    if widget is None:
        return {"error": f"Element not found: {element_id}"}

    element_info = introspector.get_element_info(widget, app)
    return element_info.model_dump()


def list_a2ui_surfaces(
    registry: "SemanticWidgetRegistry",
) -> list[dict[str, Any]]:
    """List all registered A2UI surfaces."""
    surfaces = []
    for surface_id, surface in registry._a2ui_surfaces.items():
        root_widget = getattr(surface, "root_widget", None)
        root_type = type(root_widget).__name__ if root_widget else None
        surfaces.append(
            {
                "surface_id": surface_id,
                "root_widget_type": root_type,
                "widget_count": len(getattr(surface, "_widgets", {})),
            }
        )
    return surfaces


def register_resources(
    mcp: Any,
    app: "App",
    registry: "SemanticWidgetRegistry",
    introspector: "WidgetIntrospector",
) -> None:
    """Register all UI resources with the MCP server.

    Args:
        mcp: FastMCP server instance
        app: Castella App instance
        registry: SemanticWidgetRegistry instance
        introspector: WidgetIntrospector instance
    """

    @mcp.resource("ui://tree")
    def resource_ui_tree() -> dict[str, Any]:
        """Get the complete UI tree with all widgets.

        Returns a hierarchical representation of the UI including:
        - id: Stable semantic ID for each widget
        - type: Widget type (Button, Input, etc.)
        - label: Human-readable label if available
        - children: Child widget IDs for layouts
        - properties: Additional widget properties
        """
        return get_ui_tree(app, registry, introspector)

    @mcp.resource("ui://focus")
    def resource_ui_focus() -> dict[str, Any]:
        """Get information about the currently focused element.

        Returns:
        - element_id: Semantic ID of focused element (or null)
        - element_type: Widget type if focused
        - element_label: Label if available
        """
        return get_focus_info(app, registry, introspector)

    @mcp.resource("ui://elements")
    def resource_ui_elements() -> list[dict[str, Any]]:
        """Get all interactive/actionable elements.

        Returns a list of elements that can be clicked, typed into,
        or otherwise interacted with. Each element includes:
        - id: Semantic ID for use with tools
        - type: Widget type
        - label: Human-readable label
        - value: Current value (for inputs)
        - checked: Boolean state (for checkboxes)
        - focused: Whether currently focused
        """
        return list_elements(app, registry, introspector)

    @mcp.resource("ui://element/{element_id}")
    def resource_element_by_id(element_id: str) -> dict[str, Any]:
        """Get detailed information about a specific element.

        Args:
            element_id: The semantic ID of the element

        Returns detailed element info including bounds, children,
        and all available properties.
        """
        return get_element_by_id(element_id, app, registry, introspector)

    @mcp.resource("a2ui://surfaces")
    def resource_a2ui_surfaces() -> list[dict[str, Any]]:
        """List all registered A2UI surfaces.

        Returns information about A2UI surfaces including:
        - surface_id: Unique surface identifier
        - root_widget_type: Type of the root widget
        - widget_count: Number of widgets in the surface
        """
        return list_a2ui_surfaces(registry)
