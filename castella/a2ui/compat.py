"""A2UI 0.9 specification compatibility layer.

This module provides functions to normalize A2UI 0.9 spec format
to Castella's internal A2UI format.

The main differences between formats:
- 0.9 spec uses plain values: "text": "Hello"
- Castella uses wrapped values: "text": {"literalString": "Hello"}

- 0.9 spec uses plain arrays for children: "children": ["a", "b"]
- Castella uses explicit list wrapper: "children": {"explicitList": ["a", "b"]}

- 0.9 spec updateDataModel: {"path": "/...", "op": "replace", "value": {...}}
- Castella updateDataModel: {"data": {"/path": value}}

- 0.9 spec TextField usageHint: shortText, longText, obscured
- Castella TextField usageHint: text, password, multiline
"""

from __future__ import annotations

from typing import Any


# TextField usageHint mapping from 0.9 spec to Castella
TEXTFIELD_USAGE_HINT_MAP = {
    "shortText": "text",
    "longText": "multiline",
    "obscured": "password",
    "number": "number",
    # Keep Castella's own values as-is
    "text": "text",
    "password": "password",
    "multiline": "multiline",
    "email": "email",
    "phone": "phone",
    "url": "url",
}


def normalize_value(value: Any, expected_type: str = "string") -> dict[str, Any] | Any:
    """Normalize a value to Castella's wrapped format.

    Args:
        value: The value to normalize (can be literal or already wrapped)
        expected_type: The expected type ("string", "number", "boolean")

    Returns:
        The normalized value in Castella's format
    """
    # Already in Castella format
    if isinstance(value, dict):
        if "literalString" in value:
            return value
        if "literalNumber" in value:
            return value
        if "literalBoolean" in value:
            return value
        if "path" in value:
            return value
        # Unknown dict format, return as-is
        return value

    # Plain literal values - wrap them
    if isinstance(value, str):
        return {"literalString": value}
    elif isinstance(value, bool):  # Check bool before int (bool is subclass of int)
        return {"literalBoolean": value}
    elif isinstance(value, (int, float)):
        return {"literalNumber": value}

    # Unknown type, return as-is
    return value


def normalize_children(children: Any) -> dict[str, Any] | Any:
    """Normalize children to Castella's format.

    Args:
        children: The children value (can be array or already wrapped)

    Returns:
        The normalized children in Castella's format
    """
    # Already in Castella format
    if isinstance(children, dict):
        if "explicitList" in children:
            return children
        if "componentId" in children and "path" in children:
            # Template children format - already correct
            return children
        # Legacy template format: {"template": {"componentId": "...", "dataBinding": "/..."}}
        if "template" in children:
            template = children["template"]
            if isinstance(template, dict):
                component_id = template.get("componentId", "")
                # dataBinding is the legacy name for path
                path = template.get("dataBinding") or template.get("path", "")
                return {"componentId": component_id, "path": path}
        # Unknown dict format, return as-is
        return children

    # Plain array - wrap in explicitList
    if isinstance(children, list):
        return {"explicitList": children}

    # Unknown type, return as-is
    return children


def normalize_component(component: dict[str, Any]) -> dict[str, Any]:
    """Normalize a single component to Castella's format.

    Args:
        component: The component dict from A2UI 0.9 spec

    Returns:
        The normalized component in Castella's format
    """
    result = {}

    for key, value in component.items():
        if key == "text":
            result[key] = normalize_value(value, "string")
        elif key == "label":
            result[key] = normalize_value(value, "string")
        elif key == "content":  # For Markdown
            result[key] = normalize_value(value, "string")
        elif key == "url":  # For Image - normalize to 'src'
            result["src"] = normalize_value(value, "string")
        elif key == "src":  # Already using 'src' for Image
            result[key] = normalize_value(value, "string")
        elif key == "value":
            # Could be string, number, or boolean depending on component
            result[key] = normalize_value(value)
        elif key == "checked":
            result[key] = normalize_value(value, "boolean")
        elif key == "child":
            # Singular child reference -> convert to children with explicitList
            result["children"] = {"explicitList": [value]}
        elif key == "children":
            result[key] = normalize_children(value)
        elif key == "usageHint":
            # Map 0.9 spec TextField usageHint to Castella's
            if isinstance(value, str) and value in TEXTFIELD_USAGE_HINT_MAP:
                result[key] = TEXTFIELD_USAGE_HINT_MAP[value]
            else:
                result[key] = value
        elif key == "action":
            # Normalize action context
            result[key] = normalize_action(value)
        elif key == "choices":
            # Normalize choice values
            if isinstance(value, list):
                result[key] = [normalize_value(v) for v in value]
            else:
                result[key] = value
        elif key == "selected":
            result[key] = normalize_value(value)
        elif key == "tabItems":
            # Normalize tab items
            if isinstance(value, list):
                result[key] = [normalize_tab_item(item) for item in value]
            else:
                result[key] = value
        elif key == "title":
            result[key] = normalize_value(value, "string")
        else:
            result[key] = value

    return result


def normalize_action(action: dict[str, Any] | None) -> dict[str, Any] | None:
    """Normalize an action to Castella's format.

    A2UI 0.9 spec uses:
        {"name": "...", "context": {"key": value}}

    Castella uses:
        {"name": "...", "context": [{"key": "k", "value": {...}}]}
    """
    if action is None:
        return None

    result = {"name": action.get("name", "")}
    context = action.get("context")

    if context is None:
        result["context"] = []
    elif isinstance(context, list):
        # Already in Castella format
        result["context"] = [
            {"key": item.get("key", ""), "value": normalize_value(item.get("value"))}
            for item in context
        ]
    elif isinstance(context, dict):
        # 0.9 spec format - convert object to array
        result["context"] = [
            {"key": k, "value": normalize_value(v)} for k, v in context.items()
        ]
    else:
        result["context"] = []

    return result


def normalize_tab_item(item: dict[str, Any]) -> dict[str, Any]:
    """Normalize a tab item to Castella's format."""
    result = {}
    for key, value in item.items():
        if key == "label" or key == "title":
            result["label"] = normalize_value(value, "string")
        elif key == "contentId" or key == "child":
            result["contentId"] = value
        else:
            result[key] = value
    return result


def normalize_update_data_model(msg: dict[str, Any]) -> dict[str, Any]:
    """Normalize updateDataModel message to Castella's format.

    A2UI 0.9 spec:
        {"surfaceId": "...", "path": "/...", "op": "replace", "value": {...}}

    Castella:
        {"surfaceId": "...", "data": {"/path": value}}
    """
    surface_id = msg.get("surfaceId", "default")
    path = msg.get("path", "/")
    value = msg.get("value", {})
    op = msg.get("op", "replace")

    # Castella only supports replace operation currently
    if op != "replace":
        # For add/remove, we still convert to data format
        pass

    # Convert to Castella format
    data = {}

    if path == "/" or path == "":
        # Root update - flatten the value dict
        if isinstance(value, dict):
            for k, v in value.items():
                json_pointer = f"/{k}" if not k.startswith("/") else k
                data[json_pointer] = v
        else:
            data["/"] = value
    else:
        data[path] = value

    return {"surfaceId": surface_id, "data": data}


def normalize_message(msg: dict[str, Any]) -> dict[str, Any]:
    """Normalize an A2UI message to Castella's format.

    Supports:
    - createSurface (0.9) -> createSurface (Castella)
    - updateComponents (0.9) -> updateComponents (Castella)
    - updateDataModel (0.9) -> updateDataModel (Castella)
    - deleteSurface (0.9) -> deleteSurface (Castella)

    Also handles legacy formats:
    - beginRendering -> beginRendering
    - surfaceUpdate -> updateComponents
    """
    result = {}

    # Handle createSurface
    if "createSurface" in msg:
        create = msg["createSurface"]
        result["createSurface"] = {
            "surfaceId": create.get("surfaceId", "default"),
            "catalogId": create.get("catalogId"),
        }
        if "components" in create:
            result["createSurface"]["components"] = [
                normalize_component(c) for c in create["components"]
            ]
        if "rootId" in create:
            result["createSurface"]["rootId"] = create["rootId"]

    # Handle updateComponents
    elif "updateComponents" in msg:
        update = msg["updateComponents"]
        result["updateComponents"] = {
            "surfaceId": update.get("surfaceId", "default"),
            "components": [
                normalize_component(c) for c in update.get("components", [])
            ],
        }

    # Handle updateDataModel
    elif "updateDataModel" in msg:
        update = msg["updateDataModel"]
        # Check if already in Castella format
        if "data" in update:
            result["updateDataModel"] = update
        else:
            result["updateDataModel"] = normalize_update_data_model(update)

    # Handle deleteSurface
    elif "deleteSurface" in msg:
        result["deleteSurface"] = msg["deleteSurface"]

    # Handle beginRendering (legacy)
    elif "beginRendering" in msg:
        result["beginRendering"] = msg["beginRendering"]

    # Handle surfaceUpdate (legacy) -> convert to updateComponents
    elif "surfaceUpdate" in msg:
        update = msg["surfaceUpdate"]
        components = update.get("components", [])
        # Legacy format has nested component: {"id": "...", "component": {"Column": {...}}}
        normalized_components = []
        for comp in components:
            normalized = normalize_legacy_component(comp)
            normalized_components.append(normalized)
            # Debug output
            import os

            if os.environ.get("A2UI_DEBUG"):
                print(
                    f"[COMPAT] {comp.get('id')}: {comp.get('component')} -> {normalized.get('component')}"
                )
        result["updateComponents"] = {
            "surfaceId": update.get("surfaceId", "default"),
            "components": normalized_components,
        }

    # Handle dataModelUpdate (legacy) -> convert to updateDataModel
    elif "dataModelUpdate" in msg:
        update = msg["dataModelUpdate"]
        result["updateDataModel"] = normalize_legacy_data_model_update(update)

    else:
        # Unknown message type, return as-is
        result = msg

    return result


def normalize_legacy_component(comp: dict[str, Any]) -> dict[str, Any]:
    """Normalize a legacy format component.

    Legacy format:
        {"id": "...", "component": {"Column": {"children": {...}}}}

    Target format:
        {"id": "...", "component": "Column", "children": {...}}
    """
    component_id = comp.get("id", "")
    component_def = comp.get("component", {})

    if isinstance(component_def, str):
        # Already in flat format
        return normalize_component(comp)

    if isinstance(component_def, dict):
        # Nested format - extract component type and properties
        for comp_type, props in component_def.items():
            result = {"id": component_id, "component": comp_type}
            if isinstance(props, dict):
                for key, value in props.items():
                    if key == "children":
                        result[key] = normalize_children(value)
                    elif key == "text":
                        result[key] = normalize_value(value)
                    elif key == "action":
                        result[key] = normalize_action(value)
                    elif key == "url":
                        # Normalize url to src for Image component
                        result["src"] = normalize_value(value)
                    else:
                        result[key] = value
            # Copy weight if present
            if "weight" in comp:
                result["weight"] = comp["weight"]
            return normalize_component(result)

    return comp


def normalize_legacy_data_model_update(update: dict[str, Any]) -> dict[str, Any]:
    """Normalize a legacy dataModelUpdate message.

    Legacy format:
        {"surfaceId": "...", "path": "/", "contents": [{"key": "...", "valueString": "..."}]}

    Target format:
        {"surfaceId": "...", "data": {"/key": "..."}}
    """
    surface_id = update.get("surfaceId", "default")
    path = update.get("path", "/")
    contents = update.get("contents", [])

    data = {}

    def extract_value(item: dict[str, Any]) -> Any:
        """Extract value from legacy content item."""
        if "valueString" in item:
            return item["valueString"]
        if "valueNumber" in item:
            return item["valueNumber"]
        if "valueBoolean" in item:
            return item["valueBoolean"]
        if "valueMap" in item:
            # Check if this is an "array-like" map (keys like "item0", "item1", etc.)
            # If so, convert to a list for template children compatibility
            sub_items = item["valueMap"]
            if sub_items and all(
                isinstance(si, dict)
                and si.get("key", "").startswith("item")
                and "valueMap" in si
                for si in sub_items
            ):
                # This is an array of objects disguised as a map - convert to list
                return [extract_value(si) for si in sub_items]
            else:
                # Regular nested map
                result = {}
                for sub_item in sub_items:
                    key = sub_item.get("key", "")
                    result[key] = extract_value(sub_item)
                return result
        if "valueList" in item:
            return [extract_value(v) for v in item["valueList"]]
        return None

    for content in contents:
        key = content.get("key", "")
        value = extract_value(content)
        json_pointer = f"{path}{key}" if path.endswith("/") else f"{path}/{key}"
        data[json_pointer] = value

    return {"surfaceId": surface_id, "data": data}


def is_normalized(msg: dict[str, Any]) -> bool:
    """Check if a message is already in Castella's normalized format.

    This is a heuristic check that looks for Castella-specific patterns.
    """
    if "updateComponents" in msg:
        components = msg["updateComponents"].get("components", [])
        if components:
            first = components[0]
            # Check if text is wrapped
            if "text" in first:
                text = first["text"]
                if isinstance(text, dict) and (
                    "literalString" in text or "path" in text
                ):
                    return True
    return False
