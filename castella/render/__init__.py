"""Render node system for layout and paint operations.

This package provides the RenderNode abstraction that separates
layout/paint concerns from Widget behavior.

Key classes:
- RenderNode: Protocol for render operations
- RenderNodeBase: Default implementation delegating to Widget
- LayoutRenderNode: For layout containers with z-order caching
- ScrollableLayoutRenderNode: For scrollable containers

Example:
    # Widgets automatically use RenderNodeBase
    class MyWidget(Widget):
        def redraw(self, p, completely):
            # Existing code works unchanged
            ...

    # Custom render behavior
    class MyRenderNode(RenderNodeBase):
        def paint(self, painter, completely):
            # Custom paint logic
            ...

    class MyWidget(Widget):
        def _create_render_node(self):
            return MyRenderNode(self)
"""

from castella.render.node import RenderNode, RenderNodeBase
from castella.render.layout_node import LayoutRenderNode, ScrollableLayoutRenderNode

__all__ = [
    "RenderNode",
    "RenderNodeBase",
    "LayoutRenderNode",
    "ScrollableLayoutRenderNode",
]
