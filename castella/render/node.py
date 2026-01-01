"""RenderNode - Abstraction for layout and paint operations.

This module separates layout/paint concerns from Widget behavior.

Key features:
- Fine-grained dirty tracking (layout vs paint)
- Cached measurements
- Clean separation of concerns
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

from castella.models.geometry import Point, Size

if TYPE_CHECKING:
    from castella.core import Painter, Widget


@runtime_checkable
class RenderNode(Protocol):
    """Protocol for render nodes that handle layout and paint.

    RenderNode separates layout/paint logic from widget behavior.
    This enables:
    - Fine-grained dirty tracking (layout_dirty vs paint_dirty)
    - Cached z-order sorting
    - Independent testing of render logic
    - Future optimizations (relayout without repaint)

    Widgets can optionally provide a custom RenderNode via
    _create_render_node() to customize layout/paint behavior.
    """

    # ========== Dirty Tracking ==========

    def is_layout_dirty(self) -> bool:
        """Check if layout needs to be recalculated."""
        ...

    def is_paint_dirty(self) -> bool:
        """Check if the node needs to be repainted."""
        ...

    def mark_layout_dirty(self) -> None:
        """Mark layout as needing recalculation."""
        ...

    def mark_paint_dirty(self) -> None:
        """Mark the node as needing repaint."""
        ...

    def clear_dirty(self) -> None:
        """Clear all dirty flags after layout/paint."""
        ...

    # ========== Layout ==========

    def measure(self, painter: "Painter") -> Size:
        """Measure the preferred size of this node."""
        ...

    def layout(self, pos: Point, size: Size) -> None:
        """Set the position and size after layout calculation."""
        ...

    def get_pos(self) -> Point:
        """Get the current position."""
        ...

    def get_size(self) -> Size:
        """Get the current size."""
        ...

    # ========== Paint ==========

    def paint(self, painter: "Painter", completely: bool) -> None:
        """Paint this node to the painter."""
        ...

    # ========== Hit Testing ==========

    def hit_test(self, point: Point) -> bool:
        """Test if a point is within this node's bounds."""
        ...


class RenderNodeBase:
    """Default RenderNode implementation that delegates to Widget.

    This base implementation:
    - Delegates measure/paint to the widget's existing methods
    - Provides fine-grained dirty tracking
    - Maintains backward compatibility with existing widgets

    Widgets don't need to change anything - RenderNodeBase wraps
    their existing behavior transparently.

    Example:
        # Widget automatically gets a RenderNodeBase
        class MyWidget(Widget):
            def redraw(self, p, completely):
                # Existing code works unchanged
                ...

        # Or customize with a subclass:
        class MyRenderNode(RenderNodeBase):
            def paint(self, painter, completely):
                # Custom paint logic
                ...

        class MyWidget(Widget):
            def _create_render_node(self):
                return MyRenderNode(self)
    """

    __slots__ = (
        "_widget",
        "_pos",
        "_size",
        "_layout_dirty",
        "_paint_dirty",
        "_measured_size",
    )

    def __init__(self, widget: "Widget") -> None:
        self._widget = widget
        self._pos = Point(x=0, y=0)
        self._size = Size(width=0, height=0)
        self._layout_dirty = True
        self._paint_dirty = True
        self._measured_size: Size | None = None

    @property
    def widget(self) -> "Widget":
        """The widget this render node is attached to."""
        return self._widget

    # ========== Dirty Tracking ==========

    def is_layout_dirty(self) -> bool:
        """Check if layout needs recalculation."""
        return self._layout_dirty

    def is_paint_dirty(self) -> bool:
        """Check if repaint is needed."""
        return self._paint_dirty

    def mark_layout_dirty(self) -> None:
        """Mark layout as dirty (implies paint dirty too)."""
        self._layout_dirty = True
        self._paint_dirty = True
        self._measured_size = None  # Invalidate cached measurement

    def mark_paint_dirty(self) -> None:
        """Mark paint as dirty without affecting layout."""
        self._paint_dirty = True

    def clear_dirty(self) -> None:
        """Clear all dirty flags."""
        self._layout_dirty = False
        self._paint_dirty = False

    # ========== Layout ==========

    def measure(self, painter: "Painter") -> Size:
        """Measure using the widget's measure method.

        Caches the result until layout is marked dirty.
        """
        if self._measured_size is None or self._layout_dirty:
            self._measured_size = self._widget.measure(painter)
        return self._measured_size

    def layout(self, pos: Point, size: Size) -> None:
        """Set position and size."""
        self._pos = pos
        self._size = size
        self._layout_dirty = False

    def get_pos(self) -> Point:
        """Get current position."""
        return self._pos

    def get_size(self) -> Size:
        """Get current size."""
        return self._size

    # ========== Paint ==========

    def paint(self, painter: "Painter", completely: bool) -> None:
        """Paint using the widget's redraw method."""
        self._widget.redraw(painter, completely)
        self._paint_dirty = False

    # ========== Hit Testing ==========

    def hit_test(self, point: Point) -> bool:
        """Test if point is within bounds."""
        return self._widget.contain(point)
