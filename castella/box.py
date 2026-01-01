from __future__ import annotations

from typing import TYPE_CHECKING, Self

from castella.core import (
    SCROLL_BAR_SIZE,
    FillStyle,
    Layout,
    MouseEvent,
    Painter,
    Point,
    Rect,
    Size,
    SizePolicy,
    StrokeStyle,
    Style,
    WheelEvent,
    Widget,
    get_theme,
)

if TYPE_CHECKING:
    from castella.core import ScrollState


class Box(Layout):
    """A container that stacks children on top of each other.

    Children are rendered in z_index order (lower first, higher on top).
    All children occupy the same space and overlap.
    Supports scrolling when content exceeds the box size.
    """

    _scrollbar_widget_style = get_theme().scrollbar
    _scrollbox_widget_style = get_theme().scrollbox
    _scrollbar_style = Style(
        fill=FillStyle(color=_scrollbar_widget_style.bg_color),
        stroke=StrokeStyle(color=_scrollbar_widget_style.border_color),
    )
    _scrollbox_style = Style(fill=FillStyle(color=_scrollbox_widget_style.bg_color))

    def __init__(self, *children: Widget, scroll_state: "ScrollState | None" = None):
        super().__init__(
            state=None,
            pos=Point(x=0, y=0),
            pos_policy=None,
            size=Size(width=0, height=0),
            width_policy=SizePolicy.EXPANDING,
            height_policy=SizePolicy.EXPANDING,
        )
        for child in children:
            self.add(child)
        self._under_dragging_x = False
        self._under_dragging_y = False
        self._last_drag_pos = None
        self._scroll_state = scroll_state
        # Internal scroll values (used when no external state provided)
        self.__scroll_x = scroll_state.x if scroll_state else 0
        self.__scroll_y = scroll_state.y if scroll_state else 0
        self._scroll_box_x = None
        self._scroll_box_y = None

    @property
    def _scroll_x(self) -> int:
        """Get horizontal scroll position."""
        if self._scroll_state is not None:
            return self._scroll_state.x
        return self.__scroll_x

    @_scroll_x.setter
    def _scroll_x(self, value: int) -> None:
        """Set horizontal scroll position."""
        if self._scroll_state is not None:
            self._scroll_state.x = value
        else:
            self.__scroll_x = value

    @property
    def _scroll_y(self) -> int:
        """Get vertical scroll position."""
        if self._scroll_state is not None:
            return self._scroll_state.y
        return self.__scroll_y

    @_scroll_y.setter
    def _scroll_y(self, value: int) -> None:
        """Set vertical scroll position."""
        if self._scroll_state is not None:
            self._scroll_state.y = value
        else:
            self.__scroll_y = value

    def add(self, w: Widget) -> None:
        super().add(w)

    def redraw(self, p: Painter, completely: bool) -> None:
        self_size = self._size
        self_height = self_size.height
        self_width = self_size.width
        if self_width == 0 or self_height == 0:
            return

        if len(self._children) == 0:
            return

        self._resize_children(p)
        content_width, content_height = self.content_size()
        x_scroll_bar_height = 0
        y_scroll_bar_width = 0

        if content_width > self_width - y_scroll_bar_width:
            x_scroll_bar_height = SCROLL_BAR_SIZE

        if content_height > self_height - x_scroll_bar_height:
            y_scroll_bar_width = SCROLL_BAR_SIZE

        if content_width > self_width - y_scroll_bar_width:
            x_scroll_bar_height = SCROLL_BAR_SIZE

        # Check if any child needs scrolling
        needs_x_scroll = any(
            c.get_width_policy() is not SizePolicy.EXPANDING for c in self._children
        )
        needs_y_scroll = any(
            c.get_height_policy() is not SizePolicy.EXPANDING for c in self._children
        )

        if not needs_x_scroll or x_scroll_bar_height == 0:
            # Only reset scroll if no external state is provided
            if self._scroll_state is None:
                self._scroll_x = 0
            self._scroll_box_x = None
            x_scroll_bar_height = 0

        if not needs_y_scroll or y_scroll_bar_width == 0:
            # Only reset scroll if no external state is provided
            if self._scroll_state is None:
                self._scroll_y = 0
            self._scroll_box_y = None
            y_scroll_bar_width = 0

        p.save()
        p.style(self._style)
        if completely or self.is_dirty():
            p.fill_rect(
                Rect(origin=Point(x=0, y=0), size=self_size + Size(width=1, height=1))
            )

        self._size.height -= x_scroll_bar_height
        self._size.width -= y_scroll_bar_width
        self._relocate_children(p)

        content_width, content_height = self.content_size()
        self._size.height = self_height
        self._size.width = self_width

        self.correct_scroll_x_y(content_width, content_height)
        p.translate(
            Point(
                x=-self._scroll_x * (self_width + y_scroll_bar_width) / self_width,
                y=-self._scroll_y * (self_height + x_scroll_bar_height) / self_height,
            )
        )
        self._redraw_children(p, completely)

        p.restore()

        p.save()
        if x_scroll_bar_height > 0:
            p.style(Box._scrollbar_style)
            p.fill_rect(
                Rect(
                    origin=Point(x=0, y=self_height - x_scroll_bar_height),
                    size=Size(
                        width=self_width - y_scroll_bar_width,
                        height=x_scroll_bar_height,
                    ),
                )
            )
            p.style(Box._scrollbox_style)
            if content_width != 0 and self_width != 0:
                scroll_box_width = (
                    self_width - y_scroll_bar_width
                ) ** 2 / content_width
                scroll_box = Rect(
                    origin=Point(
                        x=(self._scroll_x / content_width)
                        * (self_width - y_scroll_bar_width),
                        y=self_height - x_scroll_bar_height,
                    ),
                    size=Size(width=scroll_box_width, height=x_scroll_bar_height),
                )
                self._scroll_box_x = scroll_box
                p.fill_rect(scroll_box)

        if y_scroll_bar_width > 0:
            p.style(Box._scrollbar_style)
            p.fill_rect(
                Rect(
                    origin=Point(x=self_width - y_scroll_bar_width, y=0),
                    size=Size(
                        width=y_scroll_bar_width,
                        height=self_height - x_scroll_bar_height,
                    ),
                )
            )
            p.style(Box._scrollbox_style)
            if content_height != 0 and self_height != 0:
                scroll_box_height = (
                    self_height - x_scroll_bar_height
                ) ** 2 / content_height
                scroll_box = Rect(
                    origin=Point(
                        x=self_width - y_scroll_bar_width,
                        y=(self._scroll_y / content_height)
                        * (self_height - x_scroll_bar_height),
                    ),
                    size=Size(width=y_scroll_bar_width, height=scroll_box_height),
                )
                self._scroll_box_y = scroll_box
                p.fill_rect(scroll_box)
        p.restore()

    def correct_scroll_x_y(self, content_width, content_height):
        if self._scroll_x > 0:
            max_scroll_x = (
                content_width
                - self.get_width()
                + (0 if self._scroll_box_y is None else SCROLL_BAR_SIZE)
            )
            self._scroll_x = min(self._scroll_x, max_scroll_x)

        if self._scroll_y > 0:
            max_scroll_y = (
                content_height
                - self.get_height()
                + (0 if self._scroll_box_x is None else SCROLL_BAR_SIZE)
            )
            self._scroll_y = min(self._scroll_y, max_scroll_y)

    def is_scrollable(self) -> bool:
        return True

    def mouse_down(self, ev: MouseEvent) -> None:
        if self._scroll_box_x is not None:
            self._under_dragging_x = self._scroll_box_x.contain(ev.pos)
            self._last_drag_pos = ev.pos
        if not self._under_dragging_x and self._scroll_box_y is not None:
            self._under_dragging_y = self._scroll_box_y.contain(ev.pos)
            self._last_drag_pos = ev.pos

    def mouse_up(self, _: MouseEvent) -> None:
        self._under_dragging_x = False
        self._under_dragging_y = False

    def mouse_drag(self, ev: MouseEvent) -> None:
        w, h = self.content_size()
        last_drag_pos = self._last_drag_pos
        self._last_drag_pos = ev.pos
        if last_drag_pos is None:
            return

        if self._under_dragging_x:
            self.scroll_x(w, int((ev.pos.x - last_drag_pos.x) * (w / self.get_width())))
        elif self._under_dragging_y:
            self.scroll_y(
                h, int((ev.pos.y - last_drag_pos.y) * (h / self.get_height()))
            )

    def mouse_wheel(self, ev: WheelEvent) -> None:
        w, h = self.content_size()
        if ev.x_offset != 0:
            self.scroll_x(w, int(ev.x_offset))
        if ev.y_offset != 0:
            self.scroll_y(h, int(ev.y_offset))

    def has_scrollbar(self, is_direction_x: bool) -> bool:
        if is_direction_x:
            return self._scroll_box_x is not None
        else:
            return self._scroll_box_y is not None

    def scroll_x(self, w: float, x: int):  # -> Self:
        if x > 0:
            max_scroll_x = (
                w
                - self.get_width()
                + (0 if self._scroll_box_y is None else SCROLL_BAR_SIZE)
            )
            if self._scroll_x == max_scroll_x:
                return self
            self._scroll_x += x
            self._scroll_x = min(max_scroll_x, self._scroll_x)
            if self._parent is not None:
                self._dirty = True
                self.ask_parent_to_render(True)
            else:
                self.update(True)
            return self
        else:
            if self._scroll_x == 0:
                return self
            self._scroll_x += x
            self._scroll_x = max(0, self._scroll_x)
            if self._parent is not None:
                self._dirty = True
                self.ask_parent_to_render(True)
            else:
                self.update(True)
            return self

    def scroll_y(self, h: float, y: int) -> Self:
        if y > 0:
            max_scroll_y = (
                h
                - self.get_height()
                + (0 if self._scroll_box_x is None else SCROLL_BAR_SIZE)
            )
            if self._scroll_y == max_scroll_y:
                return self
            self._scroll_y += y
            self._scroll_y = min(max_scroll_y, self._scroll_y)
            if self._parent is not None:
                self._dirty = True
                self.ask_parent_to_render(True)
            else:
                self.update(True)
            return self
        else:
            if self._scroll_y == 0:
                return self
            self._scroll_y += y
            self._scroll_y = max(0, self._scroll_y)
            if self._parent is not None:
                self._dirty = True
                self.ask_parent_to_render(True)
            else:
                self.update(True)
            return self

    def measure(self, p: Painter) -> Size:
        if len(self._children) == 0:
            return Size(width=0, height=0)
        # Return max size of all children
        max_width = 0.0
        max_height = 0.0
        for c in self._children:
            size = c.measure(p)
            max_width = max(max_width, size.width)
            max_height = max(max_height, size.height)
        return Size(width=max_width, height=max_height)

    def content_size(self) -> tuple[float, float]:
        if len(self._children) == 0:
            return (0, 0)
        # Return max size of all children
        max_width = 0.0
        max_height = 0.0
        for c in self._children:
            size = c.get_size()
            max_width = max(max_width, size.width)
            max_height = max(max_height, size.height)
        return (max_width, max_height)

    def _adjust_pos(self, p: Point) -> Point:
        return p + Point(x=self._scroll_x, y=self._scroll_y)

    def contain_in_content_area(self, p: Point) -> bool:
        return (
            self._pos.x
            < p.x
            < self._pos.x
            + self._size.width
            - (0 if self._scroll_box_y is None else SCROLL_BAR_SIZE)
        ) and (
            self._pos.y
            < p.y
            < self._pos.y
            + self._size.height
            - (0 if self._scroll_box_x is None else SCROLL_BAR_SIZE)
        )

    def contain_in_my_area(self, p: Point) -> bool:
        return (self._pos.x < p.x < self._pos.x + self._size.width) and (
            self._pos.y < p.y < self._pos.y + self._size.height
        )

    def _relocate_children(self, p: Painter) -> None:
        if len(self._children) == 0:
            return
        self._resize_children(p)
        self._move_children()

    def _resize_children(self, p: Painter) -> None:
        for c in self._children:
            match c.get_width_policy():
                case SizePolicy.CONTENT:
                    c.width(c.measure(p).width)
                case SizePolicy.EXPANDING:
                    c.width(self.get_width())

            match c.get_height_policy():
                case SizePolicy.CONTENT:
                    c.height(c.measure(p).height)
                case SizePolicy.EXPANDING:
                    c.height(self.get_height())

    def _move_children(self) -> None:
        # All children are positioned at the same location (stacked)
        # Fixed-size children are centered within the Box
        box_pos = self.get_pos()
        box_width = self.get_width()
        box_height = self.get_height()

        for c in self._children:
            child_width = c.get_width()
            child_height = c.get_height()

            # Center horizontally if child is smaller than box
            if c.get_width_policy() is SizePolicy.FIXED and child_width < box_width:
                c.move_x(box_pos.x + (box_width - child_width) / 2)
            else:
                c.move_x(box_pos.x)

            # Center vertically if child is smaller than box
            if c.get_height_policy() is SizePolicy.FIXED and child_height < box_height:
                c.move_y(box_pos.y + (box_height - child_height) / 2)
            else:
                c.move_y(box_pos.y)

    def _redraw_children(self, p: Painter, completely: bool) -> None:
        # For overlapping children in Box, we must redraw ALL children
        # when ANY child is dirty OR the Box itself is dirty to maintain proper z-ordering
        # Use cached z-order (lower z_index first, higher on top)
        sorted_children = list(self._layout_render_node.iter_paint_order())
        needs_redraw = (
            completely or self.is_dirty() or any(c.is_dirty() for c in sorted_children)
        )

        if not needs_redraw:
            return

        for c in sorted_children:
            p.save()
            p.translate((c.get_pos() - self.get_pos()))
            # Clip to child's actual size for proper bounds
            p.clip(Rect(origin=Point(x=0, y=0), size=c.get_size()))
            c.redraw(p, True)  # Always completely redraw for z-order correctness
            p.restore()
            c.dirty(False)
