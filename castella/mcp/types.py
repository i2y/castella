"""MCP types for Castella UI introspection and control."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ElementInfo(BaseModel):
    """Information about a UI element for MCP."""

    id: str
    type: str  # Widget type: Button, Input, CheckBox, etc.
    label: str | None = None
    value: Any = None  # Current value for inputs
    checked: bool | None = None  # For checkboxes/switches
    enabled: bool = True
    focused: bool = False
    visible: bool = True
    interactive: bool = True
    bounds: dict[str, float] | None = None  # x, y, width, height
    children: list[str] = Field(default_factory=list)
    a2ui_component_id: str | None = None  # If from A2UI surface


class UITreeNode(BaseModel):
    """Node in the UI tree structure."""

    id: str
    type: str
    label: str | None = None
    children: list[UITreeNode] = Field(default_factory=list)
    properties: dict[str, Any] = Field(default_factory=dict)


class FocusInfo(BaseModel):
    """Information about the currently focused element."""

    element_id: str | None = None
    element_type: str | None = None
    element_label: str | None = None


class ActionResult(BaseModel):
    """Result of an MCP tool action."""

    success: bool
    message: str | None = None
    element_id: str | None = None
    new_value: Any = None


class WidgetMetadata(BaseModel):
    """Metadata for a registered widget in the semantic registry."""

    semantic_id: str
    widget_type: str
    label: str | None = None
    is_interactive: bool = False
    can_focus: bool = False
    parent_id: str | None = None
    a2ui_component_id: str | None = None
