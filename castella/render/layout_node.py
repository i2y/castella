"""LayoutRenderNode - Render node for layout containers.

Provides z-order caching and child management for layouts
like Column, Row, and Box.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Iterator

from castella.models.geometry import Point, Size
from castella.render.node import RenderNodeBase

if TYPE_CHECKING:
    from castella.core import Layout, Painter, Widget


class LayoutRenderNode(RenderNodeBase):
    """Render node for layout containers with children.

    Features:
    - Cached z-order sorting for efficient rendering/hit testing
    - Child dirty propagation
    - Layout-specific optimizations

    The z-order cache is invalidated when:
    - A child is added or removed
    - A child's z-index changes (via invalidate_z_order())

    This avoids O(n log n) sorting on every frame.

    Example:
        class MyLayout(Layout):
            def _create_render_node(self):
                return LayoutRenderNode(self)

            def add(self, child):
                super().add(child)
                self._render_node.add_child(child)
    """

    __slots__ = ("_children", "_sorted_children", "_z_order_dirty")

    def __init__(self, layout: "Layout") -> None:
        super().__init__(layout)
        self._children: list[Widget] = []
        self._sorted_children: list[Widget] | None = None
        self._z_order_dirty = True

    @property
    def layout_widget(self) -> "Layout":
        """The layout widget this node is attached to."""
        return self._widget  # type: ignore

    # ========== Child Management ==========

    def add_child(self, child: "Widget") -> None:
        """Add a child widget."""
        if child not in self._children:
            self._children.append(child)
            self._z_order_dirty = True
            self.mark_layout_dirty()

    def remove_child(self, child: "Widget") -> None:
        """Remove a child widget."""
        if child in self._children:
            self._children.remove(child)
            self._z_order_dirty = True
            self.mark_layout_dirty()

    def clear_children(self) -> None:
        """Remove all children."""
        self._children.clear()
        self._sorted_children = None
        self._z_order_dirty = True
        self.mark_layout_dirty()

    @property
    def child_count(self) -> int:
        """Number of children."""
        return len(self._children)

    def get_children(self) -> list["Widget"]:
        """Get children in insertion order."""
        return self._children.copy()

    # ========== Z-Order Management ==========

    def invalidate_z_order(self) -> None:
        """Invalidate the z-order cache.

        Call this when a child's z-index changes.
        """
        self._z_order_dirty = True
        self._sorted_children = None

    def get_sorted_children(self, reverse: bool = False) -> list["Widget"]:
        """Get children sorted by z-index.

        Args:
            reverse: If True, higher z-index first (for hit testing).
                     If False, lower z-index first (for painting).

        Returns:
            List of children sorted by z-index.
        """
        if self._z_order_dirty or self._sorted_children is None:
            self._sorted_children = sorted(
                self._children, key=lambda c: c.get_z_index()
            )
            self._z_order_dirty = False

        if reverse:
            return list(reversed(self._sorted_children))
        return self._sorted_children

    def iter_paint_order(self) -> Iterator["Widget"]:
        """Iterate children in paint order (lower z-index first)."""
        return iter(self.get_sorted_children(reverse=False))

    def iter_hit_test_order(self) -> Iterator["Widget"]:
        """Iterate children in hit test order (higher z-index first)."""
        return iter(self.get_sorted_children(reverse=True))

    # ========== Dirty Propagation ==========

    def is_any_child_dirty(self) -> bool:
        """Check if any child needs repainting."""
        return any(c.is_dirty() for c in self._children)

    def mark_children_clean(self) -> None:
        """Mark all children as clean."""
        for child in self._children:
            child.dirty(False)

    # ========== Layout Override ==========

    def layout(self, pos: Point, size: Size) -> None:
        """Set position/size and sync with widget."""
        super().layout(pos, size)
        # Sync back to widget for backward compatibility
        self._widget.move(pos)
        self._widget.resize(size)

    # ========== Paint Override ==========

    def paint(self, painter: "Painter", completely: bool) -> None:
        """Paint this layout and its children.

        Uses cached z-order sorting for efficiency.
        """
        # Paint self first (background, borders, etc.)
        self._widget.redraw(painter, completely)

        # Paint children in z-order
        for child in self.iter_paint_order():
            if completely or child.is_dirty():
                painter.save()
                painter.translate(child.get_pos())
                child_size = child.get_size()
                from castella.models.geometry import Rect

                painter.clip(Rect(origin=Point(x=0, y=0), size=child_size))
                child.redraw(painter, completely)
                painter.restore()
                child.dirty(False)

        self._paint_dirty = False


class ScrollableLayoutRenderNode(LayoutRenderNode):
    """Render node for scrollable layouts.

    Extends LayoutRenderNode with scroll offset tracking
    and visible area culling.
    """

    __slots__ = ("_scroll_x", "_scroll_y", "_viewport_size")

    def __init__(self, layout: "Layout") -> None:
        super().__init__(layout)
        self._scroll_x: float = 0
        self._scroll_y: float = 0
        self._viewport_size: Size | None = None

    @property
    def scroll_x(self) -> float:
        """Horizontal scroll offset."""
        return self._scroll_x

    @scroll_x.setter
    def scroll_x(self, value: float) -> None:
        if self._scroll_x != value:
            self._scroll_x = value
            self.mark_paint_dirty()

    @property
    def scroll_y(self) -> float:
        """Vertical scroll offset."""
        return self._scroll_y

    @scroll_y.setter
    def scroll_y(self, value: float) -> None:
        if self._scroll_y != value:
            self._scroll_y = value
            self.mark_paint_dirty()

    def set_viewport_size(self, size: Size) -> None:
        """Set the visible viewport size."""
        self._viewport_size = size

    def is_child_visible(self, child: "Widget") -> bool:
        """Check if a child is within the visible viewport."""
        if self._viewport_size is None:
            return True  # No culling if viewport unknown

        child_pos = child.get_pos()
        child_size = child.get_size()

        # Check if child intersects viewport
        child_left = child_pos.x - self._scroll_x
        child_top = child_pos.y - self._scroll_y
        child_right = child_left + child_size.width
        child_bottom = child_top + child_size.height

        viewport_right = self._viewport_size.width
        viewport_bottom = self._viewport_size.height

        return not (
            child_right < 0
            or child_left > viewport_right
            or child_bottom < 0
            or child_top > viewport_bottom
        )

    def iter_visible_children(self) -> Iterator["Widget"]:
        """Iterate only children within the visible viewport."""
        for child in self.iter_paint_order():
            if self.is_child_visible(child):
                yield child
