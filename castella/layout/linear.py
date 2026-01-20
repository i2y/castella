"""Linear layout base class for Row and Column."""

from __future__ import annotations

import functools
from enum import Enum, auto
from typing import TYPE_CHECKING, Self

from castella.models.geometry import Point, Rect, Size
from castella.models.style import SizePolicy

if TYPE_CHECKING:
    from castella.core import (
        Layout,
        MouseEvent,
        Painter,
        ScrollState,
        WheelEvent,
        Widget,
    )


class Axis(Enum):
    """Layout axis direction."""

    HORIZONTAL = auto()  # Row
    VERTICAL = auto()  # Column


SCROLL_BAR_SIZE = 10


class LinearLayout:
    """
    Mixin providing shared logic for Row and Column layouts.

    This mixin abstracts the common patterns between Row and Column:
    - Scrolling (horizontal for Row, vertical for Column)
    - Child resizing and positioning
    - Content size calculation
    - Scroll bar rendering

    To use this mixin, inherit from it along with Layout and set the _axis class attribute.
    """

    _axis: Axis  # Must be set by subclass

    def _init_linear_layout(
        self,
        scrollable: bool = False,
        scroll_state: "ScrollState | None" = None,
        pin_to_bottom: bool = False,
        on_user_scroll: "callable | None" = None,
    ) -> None:
        """Initialize linear layout state. Call from __init__.

        Args:
            scrollable: Whether the layout is scrollable.
            scroll_state: Optional external scroll state for persistence.
            pin_to_bottom: If True, always scroll to bottom on redraw.
                Automatically disabled when user scrolls manually.
            on_user_scroll: Optional callback called when user scrolls manually.
        """
        self._spacer = None
        self._spacing = 0
        self._scroll_state = scroll_state
        # Internal scroll offset (used when no external state provided)
        # For LinearLayout, we use x for Row, y for Column
        if scroll_state is not None:
            self.__scroll_offset = (
                scroll_state.x if self._is_horizontal else scroll_state.y
            )
        else:
            self.__scroll_offset = 0
        self._scrollable = scrollable
        self._scroll_box: Rect | None = None
        self._under_dragging = False
        self._last_drag_pos: Point | None = None
        self._pin_to_bottom = pin_to_bottom
        self._on_user_scroll = on_user_scroll

    @property
    def _scroll_offset(self) -> int:
        """Get scroll offset (x for Row, y for Column)."""
        if self._scroll_state is not None:
            return self._scroll_state.x if self._is_horizontal else self._scroll_state.y
        return self.__scroll_offset

    @_scroll_offset.setter
    def _scroll_offset(self, value: int) -> None:
        """Set scroll offset (x for Row, y for Column)."""
        if self._scroll_state is not None:
            if self._is_horizontal:
                self._scroll_state.x = value
            else:
                self._scroll_state.y = value
        else:
            self.__scroll_offset = value

    # ========== Axis-Dependent Properties ==========

    @property
    def _is_horizontal(self) -> bool:
        return self._axis == Axis.HORIZONTAL

    def _get_primary_size(self: "Layout") -> float:
        """Get size along primary axis (width for Row, height for Column)."""
        if self._is_horizontal:
            return self.get_width()
        return self.get_height()

    def _get_secondary_size(self: "Layout") -> float:
        """Get size along secondary axis (height for Row, width for Column)."""
        if self._is_horizontal:
            return self.get_height()
        return self.get_width()

    def _get_child_primary_size(self, child: "Widget") -> float:
        """Get child's size along primary axis."""
        if self._is_horizontal:
            return child.get_width()
        return child.get_height()

    def _set_child_primary_size(self, child: "Widget", size: float) -> None:
        """Set child's size along primary axis."""
        if self._is_horizontal:
            child.width(size)
        else:
            child.height(size)

    def _get_child_secondary_size(self, child: "Widget") -> float:
        """Get child's size along secondary axis."""
        if self._is_horizontal:
            return child.get_height()
        return child.get_width()

    def _set_child_secondary_size(self, child: "Widget", size: float) -> None:
        """Set child's size along secondary axis."""
        if self._is_horizontal:
            child.height(size)
        else:
            child.width(size)

    def _get_primary_policy(self, child: "Widget") -> SizePolicy:
        """Get child's size policy along primary axis."""
        if self._is_horizontal:
            return child.get_width_policy()
        return child.get_height_policy()

    def _get_secondary_policy(self, child: "Widget") -> SizePolicy:
        """Get child's size policy along secondary axis."""
        if self._is_horizontal:
            return child.get_height_policy()
        return child.get_width_policy()

    def _get_primary_measure(self, child: "Widget", p: "Painter") -> float:
        """Get child's measured size along primary axis."""
        if self._is_horizontal:
            return child.measure(p).width
        return child.measure(p).height

    def _get_secondary_measure(self, child: "Widget", p: "Painter") -> float:
        """Get child's measured size along secondary axis."""
        if self._is_horizontal:
            return child.measure(p).height
        return child.measure(p).width

    # ========== Content Size ==========

    def _content_size(self: "Layout") -> float:
        """Total content size along primary axis."""
        return functools.reduce(
            lambda total, child: total + self._get_child_primary_size(child),
            self.get_children(),
            0.0,
        )

    def measure(self: "Layout", p: "Painter") -> Size:
        """Measure the layout size based on children."""
        if self._is_horizontal:
            width = functools.reduce(
                lambda total, child: total + child.measure(p).width,
                self.get_children(),
                0.0,
            )
            height = max(
                (0.0, *map(lambda c: c.measure(p).height, self.get_children()))
            )
        else:
            width = max((0.0, *map(lambda c: c.measure(p).width, self.get_children())))
            height = functools.reduce(
                lambda total, child: total + child.measure(p).height,
                self.get_children(),
                0.0,
            )
        return Size(width=width, height=height)

    # ========== Scrolling ==========

    def _reset_scroll_state(self) -> None:
        """Reset scroll-related state.

        Note: If an external ScrollState is provided, we preserve the scroll offset
        to maintain scroll position across view rebuilds.
        """
        # Only reset scroll offset if no external state is provided
        if self._scroll_state is None:
            self._scroll_offset = 0
        self._scroll_box = None
        self._under_dragging = False
        self._last_drag_pos = None

    def _correct_scroll_offset(self: "Layout") -> None:
        """Correct scroll offset to valid range."""
        if self._scroll_offset > 0:
            max_scroll = self._content_size() - self._get_primary_size()
            self._scroll_offset = min(self._scroll_offset, max_scroll)

    def _scroll(self: "Layout", delta: int) -> Self:
        """Apply scroll delta. Returns self for chaining."""
        content_size = self._content_size()
        viewport_size = self._get_primary_size()
        max_scroll = content_size - viewport_size

        if delta > 0:
            if self._scroll_offset >= max_scroll:
                return self
            self._scroll_offset = min(max_scroll, self._scroll_offset + delta)
        else:
            if self._scroll_offset <= 0:
                return self
            self._scroll_offset = max(0, self._scroll_offset + delta)

        # Request redraw
        if hasattr(self, "_parent") and self._parent is not None:
            self._dirty = True
            self.ask_parent_to_render(True)
        else:
            self.update(True)

        return self

    def _adjust_pos(self, p: Point) -> Point:
        """Adjust position for scroll offset."""
        if self._is_horizontal:
            return Point(x=p.x + self._scroll_offset, y=p.y)
        return Point(x=p.x, y=p.y + self._scroll_offset)

    def is_scrollable(self) -> bool:
        """Check if this layout is scrollable."""
        return self._scrollable

    def set_pin_to_bottom(self, value: bool) -> Self:
        """Set pin_to_bottom state programmatically.

        Useful for implementing a 'scroll to bottom' button in chat UIs.

        Args:
            value: True to pin to bottom, False to unpin.

        Returns:
            Self for method chaining.
        """
        self._pin_to_bottom = value
        return self

    def has_scrollbar(self, is_direction_x: bool) -> bool:
        """Check if scroll bar is visible for given direction."""
        if self._scroll_box is None:
            return False
        return is_direction_x == self._is_horizontal

    # ========== Mouse Events for Scrolling ==========

    def _handle_scroll_mouse_down(self, ev: "MouseEvent") -> None:
        """Handle mouse down for scroll box dragging."""
        if self._scroll_box is not None:
            self._under_dragging = self._scroll_box.contain(ev.pos)
            self._last_drag_pos = ev.pos

    def _handle_scroll_mouse_up(self) -> None:
        """Handle mouse up to stop dragging."""
        self._under_dragging = False

    def _handle_scroll_mouse_drag(self: "Layout", ev: "MouseEvent") -> None:
        """Handle mouse drag for scroll box."""
        last_pos = self._last_drag_pos
        self._last_drag_pos = ev.pos

        if self._under_dragging and last_pos is not None:
            # Disable pin_to_bottom when user scrolls manually
            self._pin_to_bottom = False

            if self._is_horizontal:
                delta = ev.pos.x - last_pos.x
            else:
                delta = ev.pos.y - last_pos.y

            content_size = self._content_size()
            viewport_size = self._get_primary_size()
            scroll_delta = int(delta * (content_size / viewport_size))
            self._scroll(scroll_delta)

            # Call user scroll callback
            if self._on_user_scroll is not None:
                self._on_user_scroll()

    def _handle_scroll_wheel(self: "Layout", ev: "WheelEvent") -> None:
        """Handle mouse wheel for scrolling."""
        # Disable pin_to_bottom when user scrolls manually
        self._pin_to_bottom = False

        if self._is_horizontal:
            self._scroll(int(ev.x_offset))
        else:
            self._scroll(int(ev.y_offset))

        # Call user scroll callback
        if self._on_user_scroll is not None:
            self._on_user_scroll()

    # ========== Content Area ==========

    def contain_in_content_area(self: "Layout", p: Point) -> bool:
        """Check if point is in content area (excluding scrollbar)."""
        if not self._scrollable or self._content_size() <= self._get_primary_size():
            return self.contain_in_my_area(p)

        pos = self._pos
        size = self._size

        if self._is_horizontal:
            # Row: scrollbar at bottom
            return (pos.x < p.x < pos.x + size.width) and (
                pos.y < p.y < pos.y + size.height - SCROLL_BAR_SIZE
            )
        else:
            # Column: scrollbar on right
            return (pos.x < p.x < pos.x + size.width - SCROLL_BAR_SIZE) and (
                pos.y < p.y < pos.y + size.height
            )

    def contain_in_my_area(self: "Layout", p: Point) -> bool:
        """Check if point is in the layout area."""
        pos = self._pos
        size = self._size
        return (pos.x < p.x < pos.x + size.width) and (
            pos.y < p.y < pos.y + size.height
        )

    # ========== Child Resizing ==========

    def _resize_children_linear(self: "Layout", p: "Painter") -> None:
        """Resize children based on size policies."""
        if len(self._children) == 0:
            return

        remaining = self._get_primary_size()
        expanding_children: list["Widget"] = []
        total_flex = 0

        # First pass: handle CONTENT and FIXED, collect EXPANDING
        for c in self.get_children():
            policy = self._get_primary_policy(c)

            if policy is SizePolicy.CONTENT:
                size = self._get_primary_measure(c, p)
                self._set_child_primary_size(c, size)

            if policy is SizePolicy.EXPANDING:
                expanding_children.append(c)
                total_flex += c.get_flex()
            else:
                remaining -= self._get_child_primary_size(c)

        # Second pass: distribute remaining space to EXPANDING children
        if total_flex > 0 and remaining > 0:
            fraction = remaining % total_flex
            for c in expanding_children:
                flex = c.get_flex()
                size = (remaining * flex) / total_flex
                if fraction > 0:
                    size += flex
                    fraction -= flex
                self._set_child_primary_size(c, int(size))

        # Third pass: handle secondary axis
        for c in self.get_children():
            secondary_policy = self._get_secondary_policy(c)
            match secondary_policy:
                case SizePolicy.EXPANDING:
                    self._set_child_secondary_size(c, self._get_secondary_size())
                case SizePolicy.CONTENT:
                    self._set_child_secondary_size(c, self._get_secondary_measure(c, p))

    def _move_children_linear(self: "Layout") -> None:
        """Position children along primary axis."""
        pos = self.get_pos()

        if self._is_horizontal:
            acc = pos.x
            for c in self.get_children():
                c.move_x(acc)
                c.move_y(pos.y)
                acc += c.get_width()
        else:
            acc = pos.y
            for c in self.get_children():
                c.move_x(pos.x)
                c.move_y(acc)
                acc += c.get_height()

    def _relocate_children_linear(self: "Layout", p: "Painter") -> None:
        """Resize and reposition children."""
        self._resize_children_linear(p)
        self._move_children_linear()

    # ========== Scroll Bar Rendering ==========

    def _render_scrollbar(
        self: "Layout",
        p: "Painter",
        scrollbar_style,
        scrollbox_style,
    ) -> None:
        """Render scroll bar if needed."""
        content_size = self._content_size()
        viewport_size = self._get_primary_size()

        if content_size <= viewport_size:
            return

        p.save()
        p.style(scrollbar_style)

        # Draw scroll bar background
        if self._is_horizontal:
            bar_rect = Rect(
                origin=Point(x=0, y=self.get_height() - SCROLL_BAR_SIZE),
                size=Size(width=self.get_width(), height=SCROLL_BAR_SIZE),
            )
        else:
            bar_rect = Rect(
                origin=Point(x=self.get_width() - SCROLL_BAR_SIZE, y=0),
                size=Size(width=SCROLL_BAR_SIZE, height=self.get_height()),
            )

        p.fill_rect(bar_rect)

        # Draw scroll box
        p.style(scrollbox_style)

        if content_size > 0 and viewport_size > 0:
            box_size = viewport_size * viewport_size / content_size
            box_offset = (self._scroll_offset / content_size) * viewport_size

            if self._is_horizontal:
                self._scroll_box = Rect(
                    origin=Point(x=box_offset, y=self.get_height() - SCROLL_BAR_SIZE),
                    size=Size(width=box_size, height=SCROLL_BAR_SIZE),
                )
            else:
                self._scroll_box = Rect(
                    origin=Point(x=self.get_width() - SCROLL_BAR_SIZE, y=box_offset),
                    size=Size(width=SCROLL_BAR_SIZE, height=box_size),
                )

            p.fill_rect(self._scroll_box)

        p.restore()
