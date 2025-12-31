"""Widget introspection for MCP resources."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .types import ElementInfo, UITreeNode

if TYPE_CHECKING:
    from castella.core import Widget, App
    from .registry import SemanticWidgetRegistry


class WidgetIntrospector:
    """Extracts information from widget trees for MCP resources.

    This class traverses the widget tree and extracts semantic information
    for MCP clients to consume.
    """

    def __init__(self, registry: "SemanticWidgetRegistry") -> None:
        self._registry = registry

    def build_tree(self, root: "Widget") -> UITreeNode:
        """Build a complete UI tree from root widget."""
        return self._build_node(root)

    def _build_node(self, widget: "Widget") -> UITreeNode:
        """Build a single node in the UI tree."""
        from castella.core import Layout

        semantic_id = self._registry.get_semantic_id(widget)
        if semantic_id is None:
            # Register if not already registered
            semantic_id = self._registry.register(widget)

        node = UITreeNode(
            id=semantic_id,
            type=type(widget).__name__,
            label=self.get_label(widget),
            children=[],
            properties=self._extract_properties(widget),
        )

        # Add children for layouts
        if isinstance(widget, Layout):
            children = getattr(widget, "_children", [])
            for child in children:
                node.children.append(self._build_node(child))

        return node

    def get_element_info(
        self, widget: "Widget", app: "App | None" = None
    ) -> ElementInfo:
        """Extract detailed info from a single widget."""
        semantic_id = self._registry.get_semantic_id(widget)
        if semantic_id is None:
            semantic_id = self._registry.register(widget)

        # Determine if focused
        focused = False
        if app is not None:
            focused = app._focused is widget

        # Get children IDs
        from castella.core import Layout

        children_ids = []
        if isinstance(widget, Layout):
            children = getattr(widget, "_children", [])
            for child in children:
                child_id = self._registry.get_semantic_id(child)
                if child_id is None:
                    child_id = self._registry.register(child)
                children_ids.append(child_id)

        # Get A2UI component ID if available
        metadata = self._registry.get_metadata(semantic_id)
        a2ui_id = metadata.a2ui_component_id if metadata else None

        return ElementInfo(
            id=semantic_id,
            type=type(widget).__name__,
            label=self.get_label(widget),
            value=self.get_current_value(widget),
            checked=self._get_checked(widget),
            enabled=self._is_enabled(widget),
            focused=focused,
            visible=True,  # Assume visible if in tree
            interactive=self._is_interactive(widget),
            bounds=self._get_bounds(widget),
            children=children_ids,
            a2ui_component_id=a2ui_id,
        )

    def get_interactive_elements(
        self, root: "Widget", app: "App | None" = None
    ) -> list[ElementInfo]:
        """Get all elements that can be interacted with."""
        elements = []
        self._collect_interactive(root, elements, app)
        return elements

    def _collect_interactive(
        self,
        widget: "Widget",
        elements: list[ElementInfo],
        app: "App | None",
    ) -> None:
        """Recursively collect interactive elements."""
        from castella.core import Layout

        if self._is_interactive(widget):
            elements.append(self.get_element_info(widget, app))

        if isinstance(widget, Layout):
            children = getattr(widget, "_children", [])
            for child in children:
                self._collect_interactive(child, elements, app)

    def get_label(self, widget: "Widget") -> str | None:
        """Extract label from widget."""
        widget_type = type(widget).__name__

        # Button text
        if widget_type == "Button":
            state = getattr(widget, "_state", None)
            if state is not None:
                return getattr(state, "_text", None)

        # Text widget
        if widget_type in ("Text", "SimpleText"):
            state = getattr(widget, "_state", None)
            if state is not None:
                return getattr(state, "_text", None)

        # Input placeholder or label
        if widget_type == "Input":
            # Try to get current text as label hint
            state = getattr(widget, "_state", None)
            if state is not None:
                text = getattr(state, "_text", "")
                if text:
                    return (
                        f"Input: {text[:20]}..." if len(text) > 20 else f"Input: {text}"
                    )
            return "Input"

        # MultilineInput
        if widget_type == "MultilineInput":
            return "MultilineInput"

        # CheckBox
        if widget_type == "CheckBox":
            on_label = getattr(widget, "_on_label", None)
            off_label = getattr(widget, "_off_label", None)
            if on_label or off_label:
                return f"{on_label}/{off_label}"
            return "CheckBox"

        # Slider
        if widget_type == "Slider":
            state = getattr(widget, "_state", None)
            if state is not None:
                value = getattr(state, "_value", 0)
                return f"Slider: {value}"
            return "Slider"

        # ProgressBar
        if widget_type == "ProgressBar":
            state = getattr(widget, "_state", None)
            if state is not None:
                value = getattr(state, "_value", 0)
                max_val = getattr(state, "_max", 100)
                percent = int((value / max_val) * 100) if max_val > 0 else 0
                return f"ProgressBar: {percent}%"
            return "ProgressBar"

        # Tabs
        if widget_type == "Tabs":
            state = getattr(widget, "_state", None)
            if state is not None:
                selected = getattr(state, "_selected_id", None)
                return f"Tabs: {selected}"
            return "Tabs"

        # DateTimeInput
        if widget_type == "DateTimeInput":
            state = getattr(widget, "_state", None)
            if state is not None:
                value = (
                    state.to_display_string()
                    if hasattr(state, "to_display_string")
                    else None
                )
                return f"DateTimeInput: {value}" if value else "DateTimeInput"
            return "DateTimeInput"

        # Try semantic_id_hint
        hint = getattr(widget, "_semantic_id_hint", None)
        if hint:
            return hint

        return None

    def get_current_value(self, widget: "Widget") -> Any:
        """Extract current value from input widgets."""
        widget_type = type(widget).__name__

        # Input
        if widget_type == "Input":
            state = getattr(widget, "_state", None)
            if state is not None:
                return getattr(state, "_text", None)

        # MultilineInput
        if widget_type == "MultilineInput":
            state = getattr(widget, "_state", None)
            if state is not None and hasattr(state, "get_text"):
                return state.get_text()

        # Slider
        if widget_type == "Slider":
            state = getattr(widget, "_state", None)
            if state is not None:
                return getattr(state, "_value", None)

        # ProgressBar
        if widget_type == "ProgressBar":
            state = getattr(widget, "_state", None)
            if state is not None:
                return getattr(state, "_value", None)

        # CheckBox
        if widget_type == "CheckBox":
            state = getattr(widget, "_state", None)
            if state is not None:
                return state()  # State[bool] is callable

        # DateTimeInput
        if widget_type == "DateTimeInput":
            state = getattr(widget, "_state", None)
            if state is not None and hasattr(state, "to_iso"):
                return state.to_iso()

        return None

    def _get_checked(self, widget: "Widget") -> bool | None:
        """Get checked state for checkboxes/switches."""
        widget_type = type(widget).__name__

        if widget_type in ("CheckBox", "Switch"):
            state = getattr(widget, "_state", None)
            if state is not None:
                return state()  # State[bool] is callable

        return None

    def _is_enabled(self, widget: "Widget") -> bool:
        """Check if widget is enabled."""
        # Currently Castella doesn't have a disabled state
        # Could check for disabled appearance state in future
        return True

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

    def _get_bounds(self, widget: "Widget") -> dict[str, float]:
        """Get widget bounds as a dictionary."""
        pos = widget.get_pos()
        size = widget.get_size()
        return {
            "x": pos.x,
            "y": pos.y,
            "width": size.width,
            "height": size.height,
        }

    def _extract_properties(self, widget: "Widget") -> dict[str, Any]:
        """Extract additional properties from widget."""
        props: dict[str, Any] = {}

        # Kind (semantic type)
        kind = getattr(widget, "_kind", None)
        if kind is not None:
            props["kind"] = kind.value

        # Z-index
        z_index = getattr(widget, "_z_index", None)
        if z_index is not None and z_index != 1:
            props["z_index"] = z_index

        # Size policies
        width_policy = getattr(widget, "_width_policy", None)
        height_policy = getattr(widget, "_height_policy", None)
        if width_policy is not None:
            props["width_policy"] = width_policy.value
        if height_policy is not None:
            props["height_policy"] = height_policy.value

        # Semantic ID hint
        hint = getattr(widget, "_semantic_id_hint", None)
        if hint is not None:
            props["semantic_id_hint"] = hint

        return props
