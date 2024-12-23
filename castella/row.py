import functools
from typing import Generator, Self

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
from .spacer import Spacer


class Row(Layout):
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
            width_policy=SizePolicy.EXPANDING,
            height_policy=SizePolicy.EXPANDING,
        )
        self._spacer = None
        self._spacing = 0
        self._scroll_x = 0
        self._scrollable = scrollable
        self._scroll_box = None
        self._under_dragging = False
        self._last_drag_pos = None
        for c in children:
            self.add(c)

    def add(self, w: Widget) -> None:
        if self._scrollable and w.get_width_policy() is SizePolicy.EXPANDING:
            raise RuntimeError(
                "Scrollable Row cannot have an width expandable child widget"
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

    def spacing(self, size: int) -> Self:
        self._spacing = size
        self._spacer = Spacer().fixed_width(size)
        return self

    def redraw(self, p: Painter, completely: bool) -> None:
        if not self._scrollable:
            self._scroll_box = None
            self._scroll_x = 0
            self._last_drag_pos = None
            self._under_dragging = False
            return super().redraw(p, completely)

        self._resize_children(p)
        content_width = self.content_width()
        if content_width <= self.get_width():
            self._scroll_box = None
            self._scroll_x = 0
            self._last_drag_pos = None
            self._under_dragging = False
            return super().redraw(p, completely)

        scroll_bar_height = SCROLL_BAR_SIZE
        p.save()
        p.style(self._style)
        if completely or self.is_dirty():
            p.fill_rect(Rect(origin=Point(0, 0), size=self.get_size() + Size(1, 1)))

        self.correct_scroll_x()
        p.translate(Point(-self._scroll_x, 0))

        orig_height = self.get_height()
        self._size.height -= scroll_bar_height
        self._relocate_children(p)
        self._redraw_children(p, completely)
        self._size.height = orig_height
        p.restore()

        p.save()
        p.style(Row._scrollbar_style)
        p.fill_rect(
            Rect(
                origin=Point(0, orig_height - scroll_bar_height),
                size=Size(self.get_width(), scroll_bar_height),
            )
        )
        # p.stroke_rect(
        #     Rect(
        #         origin=Point(-1, orig_height - scroll_bar_height),
        #         size=Size(self.get_width() + 2, scroll_bar_height),
        #     )
        # )
        p.style(Row._scrollbox_style)
        if content_width != 0 and self.get_width() != 0:
            scroll_box_width = self.get_width() * self.get_width() / content_width
            scroll_box = Rect(
                origin=Point(
                    (self._scroll_x / content_width) * self.get_width(),
                    orig_height - scroll_bar_height,
                ),
                size=Size(scroll_box_width, scroll_bar_height),
            )
            self._scroll_box = scroll_box
            p.fill_rect(scroll_box)
        p.restore()

    def correct_scroll_x(self):
        if self._scroll_x > 0:
            max_scroll_x = self.content_width() - self.get_width()
            self._scroll_x = min(self._scroll_x, max_scroll_x)

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
            self.scroll_x(
                int(
                    (ev.pos.x - last_drag_pos.x)
                    * (self.content_width() / self.get_width())
                )
            )

    def mouse_wheel(self, ev: WheelEvent) -> None:
        self.scroll_x(int(ev.x_offset))

    def has_scrollbar(self, is_direction_x: bool) -> bool:
        return is_direction_x and self._scroll_box is not None

    def scroll_x(self, x: int) -> Self:
        if x > 0:
            max_scroll_x = self.content_width() - self.get_width()
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

    def is_scrollable(self) -> bool:
        return self._scrollable

    def measure(self, p: Painter) -> Size:
        width = functools.reduce(
            lambda total, child: total + child.measure(p).width, self.get_children(), 0
        )
        height = max((0, *map(lambda c: c.measure(p).height, self.get_children())))
        return Size(width, height)

    def content_width(self) -> float:
        return functools.reduce(
            lambda total, child: total + child.get_width(), self.get_children(), 0
        )

    def _adjust_pos(self, p: Point) -> Point:
        return p + Point(self._scroll_x, 0)

    def contain_in_content_area(self, p: Point) -> bool:
        if self._scrollable and self.content_width() > self.get_width():
            return (self._pos.x < p.x < self._pos.x + self._size.width) and (
                self._pos.y < p.y < self._pos.y + self._size.height - SCROLL_BAR_SIZE
            )
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

        remaining_width = self.get_width()
        remaining_children: list[Widget] = []
        total_flex = 0

        for c in self.get_children():
            wp = c.get_width_policy()
            if wp is SizePolicy.CONTENT:
                c.width(c.measure(p).width)

            if wp is SizePolicy.EXPANDING:
                remaining_children.append(c)
                total_flex = total_flex + c.get_flex()
            else:
                remaining_width = remaining_width - c.get_width()

        fraction = (
            remaining_width % total_flex
            if remaining_width > 0 and total_flex > 0
            else 0
        )
        for rc in remaining_children:
            flex = rc.get_flex()
            width = (remaining_width * flex) / total_flex
            if fraction > 0:
                width += flex
                fraction -= flex
            rc.width(int(width))

        for c in self.get_children():
            match c.get_height_policy():
                case SizePolicy.EXPANDING:
                    c.height(self.get_height())
                case SizePolicy.CONTENT:
                    c.height(c.measure(p).height)

    def _move_children(self) -> None:
        acc_x = self.get_pos().x
        for c in self.get_children():
            c.move_x(acc_x)
            acc_x += c.get_width()
            c.move_y(self.get_pos().y)
