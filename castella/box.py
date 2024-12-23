from dataclasses import astuple
from typing import Self

from .core import (
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


class Box(Layout):
    _scrollbar_widget_style = get_theme().scrollbar
    _scrollbox_widget_style = get_theme().scrollbox
    _scrollbar_style = Style(
        FillStyle(color=_scrollbar_widget_style.bg_color),
        StrokeStyle(color=_scrollbar_widget_style.border_color),
    )
    _scrollbox_style = Style(FillStyle(color=_scrollbox_widget_style.bg_color))

    def __init__(self, child: Widget):
        super().__init__(
            state=None,
            pos=Point(0, 0),
            pos_policy=None,
            size=Size(0, 0),
            width_policy=SizePolicy.EXPANDING,
            height_policy=SizePolicy.EXPANDING,
        )
        self.add(child)
        self._child = child
        self._under_dragging_x = False
        self._under_dragging_y = False
        self._last_drag_pos = None
        self._scroll_x = 0
        self._scroll_box_x = None
        self._scroll_y = 0
        self._scroll_box_y = None

    def add(self, w: Widget) -> None:
        if len(self._children) > 0:
            raise RuntimeError("Box cannot have more than 1 child widget")
        super().add(w)

    def redraw(self, p: Painter, completely: bool) -> None:
        self_size = self._size
        self_height = self_size.height
        self_width = self_size.width
        if self_width == 0 or self_height == 0:
            return

        c = self._child
        self._resize_child(p)
        content_width, content_height = self.content_size()
        x_scroll_bar_height = 0
        y_scroll_bar_width = 0

        if content_width > self_width - y_scroll_bar_width:
            x_scroll_bar_height = SCROLL_BAR_SIZE

        if content_height > self_height - x_scroll_bar_height:
            y_scroll_bar_width = SCROLL_BAR_SIZE

        if content_width > self_width - y_scroll_bar_width:
            x_scroll_bar_height = SCROLL_BAR_SIZE

        if c.get_width_policy() is SizePolicy.EXPANDING or x_scroll_bar_height == 0:
            self._scroll_x = 0
            self._scroll_box_x = None
            x_scroll_bar_height = 0

        if c.get_height_policy() is SizePolicy.EXPANDING or y_scroll_bar_width == 0:
            self._scroll_y = 0
            self._scroll_box_y = None
            y_scroll_bar_width = 0

        p.save()
        p.style(self._style)
        if completely or self.is_dirty():
            p.fill_rect(Rect(origin=Point(0, 0), size=self_size + Size(1, 1)))

        self._size.height -= x_scroll_bar_height
        self._size.width -= y_scroll_bar_width
        self._relocate_children(p)

        content_width, content_height = self.content_size()
        self._size.height = self_height
        self._size.width = self_width

        self.correct_scroll_x_y(content_width, content_height)
        p.translate(
            Point(
                -self._scroll_x * (self_width + y_scroll_bar_width) / self_width,
                -self._scroll_y * (self_height + x_scroll_bar_height) / self_height,
            )
        )
        self._redraw_children(p, completely)

        p.restore()

        p.save()
        if x_scroll_bar_height > 0:
            p.style(Box._scrollbar_style)
            p.fill_rect(
                Rect(
                    origin=Point(0, self_height - x_scroll_bar_height),
                    size=Size(self_width - y_scroll_bar_width, x_scroll_bar_height),
                )
            )
            p.style(Box._scrollbox_style)
            if content_width != 0 and self_width != 0:
                scroll_box_width = (
                    self_width - y_scroll_bar_width
                ) ** 2 / content_width
                scroll_box = Rect(
                    origin=Point(
                        (self._scroll_x / content_width)
                        * (self_width - y_scroll_bar_width),
                        self_height - x_scroll_bar_height,
                    ),
                    size=Size(scroll_box_width, x_scroll_bar_height),
                )
                self._scroll_box_x = scroll_box
                p.fill_rect(scroll_box)

        if y_scroll_bar_width > 0:
            p.style(Box._scrollbar_style)
            p.fill_rect(
                Rect(
                    origin=Point(self_width - y_scroll_bar_width, 0),
                    size=Size(y_scroll_bar_width, self_height - x_scroll_bar_height),
                )
            )
            p.style(Box._scrollbox_style)
            if content_height != 0 and self_height != 0:
                scroll_box_height = (
                    self_height - x_scroll_bar_height
                ) ** 2 / content_height
                scroll_box = Rect(
                    origin=Point(
                        self_width - y_scroll_bar_width,
                        (self._scroll_y / content_height)
                        * (self_height - x_scroll_bar_height),
                    ),
                    size=Size(y_scroll_bar_width, scroll_box_height),
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
        return self._child.measure(p)

    def content_size(self) -> tuple[float, float]:
        return astuple(self._child.get_size())

    def _adjust_pos(self, p: Point) -> Point:
        return p + Point(self._scroll_x, self._scroll_y)

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
        self._resize_child(p)
        self._move_child()

    def _resize_child(self, p: Painter) -> None:
        c = self._child
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

    def _move_child(self) -> None:
        c = self._child
        c.move_x(self.get_pos().x)
        c.move_y(self.get_pos().y)
