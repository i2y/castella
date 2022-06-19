import functools
from typing import Generator

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
from castella.spacer import Spacer


class Column(Layout):
    _scrollbar_widget_style = get_theme().scrollbar
    _scrollbox_widget_style = get_theme().scrollbox
    _scrollbar_style = Style(
        FillStyle(color=_scrollbar_widget_style.bg_color),
        StrokeStyle(color=_scrollbar_widget_style.border_color),
    )
    _scrollbox_style = Style(FillStyle(color=_scrollbox_widget_style.bg_color))

    def __init__(self, *children: Widget, scrollable: bool = False):
        super().__init__(
            state=None,
            pos=Point(0, 0),
            pos_policy=None,
            size=Size(0, 0),
            height_policy=SizePolicy.EXPANDING,
            width_policy=SizePolicy.EXPANDING,
        )
        self._spacer = None
        self._spacing = 0
        self._scroll_y = 0
        self._scrollable = scrollable
        self._scroll_box = None
        self._under_dragging = False
        self._last_drag_pos = None
        for c in children:
            self.add(c)

    def add(self, w: Widget) -> None:
        if self._scrollable and w.get_height_policy() is SizePolicy.EXPANDING:
            raise RuntimeError(
                "Scrollable Column cannot have an hight expandable child widget"
            )
        super().add(w)

    def get_children(self) -> Generator[Widget, None, None]:
        if self._spacer is None:
            yield from self._children
            return

        for c in self._children:
            yield self._spacer
            yield c
        yield self._spacer

    def spacing(self, size: int):  # -> Self:
        self._spacing = size
        self._spacer = Spacer().fixed_height(size)
        return self

    def redraw(self, p: Painter, completely: bool) -> None:
        if not self._scrollable:
            self._scroll_box = None
            self._scroll_y = 0
            self._last_drag_pos = None
            self._under_dragging = False
            return super().redraw(p, completely)

        self._resize_children(p)
        content_height = self.content_height()
        if content_height <= self.get_height():
            self._scroll_box = None
            self._scroll_y = 0
            self._last_drag_pos = None
            self._under_dragging = False
            return super().redraw(p, completely)

        scroll_bar_width = SCROLL_BAR_SIZE
        p.save()
        p.style(self._style)
        if completely or self.is_dirty():
            p.fill_rect(Rect(origin=Point(0, 0), size=self.get_size() + Size(1, 1)))
        p.translate(Point(0, -self._scroll_y))

        orig_width = self.get_width()
        self._size.width -= scroll_bar_width
        self._relocate_children(p)
        self._redraw_children(p, completely)
        self._size.width = orig_width
        p.restore()

        p.save()
        p.style(Column._scrollbar_style)
        p.fill_rect(
            Rect(
                origin=Point(orig_width - scroll_bar_width, 0),
                size=Size(scroll_bar_width, self.get_height()),
            )
        )
        p.stroke_rect(
            Rect(
                origin=Point(orig_width - scroll_bar_width, -1),
                size=Size(scroll_bar_width, self.get_height() + 2),
            )
        )
        p.style(Column._scrollbox_style)
        if content_height != 0 and self.get_height() != 0:
            scroll_box_height = self.get_height() * self.get_height() / content_height
            scroll_box = Rect(
                origin=Point(
                    orig_width - scroll_bar_width,
                    (self._scroll_y / content_height) * self.get_height(),
                ),
                size=Size(scroll_bar_width, scroll_box_height),
            )
            self._scroll_box = scroll_box
            p.fill_rect(scroll_box)
        p.restore()

    def is_scrollable(self) -> bool:
        return self._scrollable

    def mouse_down(self, ev: MouseEvent) -> None:
        if self._scroll_box is not None:
            self._under_dragging = self._scroll_box.contain(ev.pos)
            self._last_drag_pos = ev.pos

    def mouse_up(self, _: MouseEvent) -> None:
        self._under_dragging = False

    def mouse_drag(self, ev: MouseEvent) -> None:
        last_drag_pos = self._last_drag_pos
        self._last_drag_pos = ev.pos
        if self._under_dragging and last_drag_pos is not None:
            self.scroll_y(
                int(
                    (ev.pos.y - last_drag_pos.y)
                    * (self.content_height() / self.get_height())
                )
            )

    def mouse_wheel(self, ev: WheelEvent) -> None:
        self.scroll_y(int(ev.y_offset))

    def has_scrollbar(self, is_direction_x: bool) -> bool:
        return (not is_direction_x) and self._scroll_box is not None

    def scroll_y(self, y: int):  # -> Self:
        if y > 0:
            max_scroll_y = self.content_height() - self.get_height()
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
        width = max((0, *map(lambda c: c.measure(p).width, self.get_children())))
        height = functools.reduce(
            lambda total, child: total + child.measure(p).height, self.get_children(), 0
        )
        return Size(width, height)

    def content_height(self) -> float:
        return functools.reduce(
            lambda total, child: total + child.get_height(), self.get_children(), 0
        )

    def _adjust_pos(self, p: Point) -> Point:
        return p + Point(0, self._scroll_y)

    def contain_in_content_area(self, p: Point) -> bool:
        if self._scrollable and self.content_height() > self.get_height():
            return (
                self._pos.x < p.x < self._pos.x + self._size.width - SCROLL_BAR_SIZE
            ) and (self._pos.y < p.y < self._pos.y + self._size.height)
        return self.contain_in_my_area(p)

    def contain_in_my_area(self, p: Point) -> bool:
        return (self._pos.x < p.x < self._pos.x + self._size.width) and (
            self._pos.y < p.y < self._pos.y + self._size.height
        )

    def _relocate_children(self, p: Painter) -> None:
        self._resize_children(p)
        self._move_children()

    def _resize_children(self, p: Painter) -> None:
        if len(self._children) == 0:
            return

        remaining_height = self.get_height()
        remaining_children: list[Widget] = []
        total_flex = 0

        for c in self.get_children():
            hp = c.get_height_policy()
            if hp is SizePolicy.CONTENT:
                c.height(c.measure(p).height)

            if hp is SizePolicy.EXPANDING:
                remaining_children.append(c)
                total_flex = total_flex + c.get_flex()
            else:
                remaining_height = remaining_height - c.get_height()

        fraction = (
            remaining_height % total_flex
            if remaining_height > 0 and total_flex > 0
            else 0
        )
        for rc in remaining_children:
            flex = rc.get_flex()
            height = (remaining_height * flex) / total_flex
            if fraction > 0:
                height += flex
                fraction -= flex
            rc.height(int(height))

        for c in self.get_children():
            match c.get_width_policy():
                case SizePolicy.EXPANDING:
                    c.width(self.get_width())
                case SizePolicy.CONTENT:
                    c.width(c.measure(p).width)

    def _move_children(self) -> None:
        acc_y = self.get_pos().y
        for c in self.get_children():
            c.move_y(acc_y)
            acc_y += c.get_height()
            c.move_x(self.get_pos().x)
