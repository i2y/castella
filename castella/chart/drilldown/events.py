"""Drill-down event models."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class DrillDownEvent(BaseModel):
    """Event emitted when drilling down into a child node.

    This event is fired after navigation completes, providing information
    about the source and destination nodes.

    Attributes:
        from_node_id: ID of the node being navigated from.
        to_node_id: ID of the node being navigated to.
        clicked_key: The category/label that was clicked.
        new_depth: The depth of the destination node (0 = root).
    """

    model_config = ConfigDict(frozen=True)

    from_node_id: str
    to_node_id: str
    clicked_key: str
    new_depth: int


class DrillUpEvent(BaseModel):
    """Event emitted when drilling up to a parent node.

    This event is fired after navigation completes, providing information
    about the source and destination nodes.

    Attributes:
        from_node_id: ID of the node being navigated from.
        to_node_id: ID of the node being navigated to.
        new_depth: The depth of the destination node (0 = root).
    """

    model_config = ConfigDict(frozen=True)

    from_node_id: str
    to_node_id: str
    new_depth: int
