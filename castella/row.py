"""Row layout - horizontal arrangement of widgets."""

from __future__ import annotations

from typing import TYPE_CHECKING, Generator, Self

from castella.core import (
    AppearanceState,
    FillStyle,
    Kind,
    Layout,
    Painter,
    Rect,
    Size,
    SizePolicy,
    StrokeStyle,
    Style,
    Widget,
    get_theme,
)
from castella.layout.linear import Axis, LinearLayout, SCROLL_BAR_SIZE
from castella.models.geometry import Point
from castella.models.events import MouseEvent, WheelEvent
from castella.spacer import Spacer

if TYPE_CHECKING:
    from castella.core import ScrollState


class Row(LinearLayout, Layout):
    """Horizontal layout container.

    Arranges child widgets horizontally from left to right.
    Supports scrolling when content exceeds viewport width.
    """

    _axis = Axis.HORIZONTAL

    _scrollbar_widget_style = get_theme().scrollbar
    _scrollbox_widget_style = get_theme().scrollbox
    _scrollbar_style = Style(
        fill=FillStyle(color=_scrollbar_widget_style.bg_color),
        stroke=StrokeStyle(color=_scrollbar_widget_style.border_color),
    )
    _scrollbox_style = Style(fill=FillStyle(color=_scrollbox_widget_style.bg_color))

    def __init__(
        self,
        *children: Widget,
        scrollable: bool = False,
        scroll_state: "ScrollState | None" = None,
    ):
        Layout.__init__(
            self,
            state=None,
            pos=Point(x=0, y=0),
            pos_policy=None,
            size=Size(width=0, height=0),
            width_policy=SizePolicy.EXPANDING,
            height_policy=SizePolicy.EXPANDING,
        )
        self._init_linear_layout(scrollable, scroll_state)
        for c in children:
            self.add(c)

    def add(self, w: Widget) -> None:
        if self._scrollable and w.get_width_policy() is SizePolicy.EXPANDING:
            raise RuntimeError(
                "Scrollable Row cannot have a width-expandable child widget"
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
            self._reset_scroll_state()
            return super().redraw(p, completely)

        self._resize_children_linear(p)
        content_width = self._content_size()
        if content_width <= self.get_width():
            self._reset_scroll_state()
            return super().redraw(p, completely)

        p.save()
        p.style(self._style)
        if completely or self.is_dirty():
            p.fill_rect(
                Rect(
                    origin=Point(x=0, y=0),
                    size=self.get_size() + Size(width=1, height=1),
                )
            )

        self._correct_scroll_offset()
        p.translate(Point(x=-self._scroll_offset, y=0))

        orig_height = self.get_height()
        self._size = Size(
            width=self._size.width, height=max(0, self._size.height - SCROLL_BAR_SIZE)
        )
        self._relocate_children_linear(p)
        self._redraw_children(p, completely)
        self._size = Size(width=self._size.width, height=orig_height)
        p.restore()

        self._render_scrollbar(p, Row._scrollbar_style, Row._scrollbox_style)

    def mouse_down(self, ev: MouseEvent) -> None:
        self._handle_scroll_mouse_down(ev)

    def mouse_up(self, _: MouseEvent) -> None:
        self._handle_scroll_mouse_up()

    def mouse_drag(self, ev: MouseEvent) -> None:
        self._handle_scroll_mouse_drag(ev)

    def mouse_wheel(self, ev: WheelEvent) -> None:
        self._handle_scroll_wheel(ev)

    def scroll_x(self, x: int) -> Self:
        """Scroll horizontally by the given amount."""
        return self._scroll(x)

    def content_width(self) -> float:
        """Get total content width (for backwards compatibility)."""
        return self._content_size()

    def _relocate_children(self, p: Painter) -> None:
        self._relocate_children_linear(p)

    def _resize_children(self, p: Painter) -> None:
        self._resize_children_linear(p)

    def _move_children(self) -> None:
        self._move_children_linear()

    def _on_update_widget_styles(self) -> None:
        self._style = self._get_painter_styles(Kind.NORMAL, AppearanceState.NORMAL)[0]
