"""Column layout - vertical arrangement of widgets."""

from __future__ import annotations

from typing import TYPE_CHECKING, Generator, Self

from castella.core import (
    FillStyle,
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


class Column(LinearLayout, Layout):
    """Vertical layout container.

    Arranges child widgets vertically from top to bottom.
    Supports scrolling when content exceeds viewport height.
    """

    _axis = Axis.VERTICAL

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
        pin_to_bottom: bool = False,
        on_user_scroll: "callable | None" = None,
    ):
        """Create a vertical layout container.

        Args:
            children: Child widgets to arrange vertically.
            scrollable: Whether the column should scroll when content exceeds height.
            scroll_state: Optional external scroll state for persistence across rebuilds.
            pin_to_bottom: If True, always scroll to bottom on redraw.
                Useful for chat UIs. Automatically disabled when user scrolls manually.
            on_user_scroll: Optional callback called when user scrolls manually.
        """
        Layout.__init__(
            self,
            state=None,
            pos=Point(x=0, y=0),
            pos_policy=None,
            size=Size(width=0, height=0),
            width_policy=SizePolicy.EXPANDING,
            height_policy=SizePolicy.EXPANDING,
        )
        self._init_linear_layout(scrollable, scroll_state, pin_to_bottom, on_user_scroll)
        for c in children:
            self.add(c)

    def add(self, w: Widget) -> None:
        if self._scrollable and w.get_height_policy() is SizePolicy.EXPANDING:
            raise RuntimeError(
                "Scrollable Column cannot have a height-expandable child widget"
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
        self._spacer = Spacer().fixed_height(size)
        return self

    def redraw(self, p: Painter, completely: bool) -> None:
        if not self._scrollable:
            self._reset_scroll_state()
            return super().redraw(p, completely)

        self._resize_children_linear(p)
        content_height = self._content_size()
        if content_height <= self.get_height():
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

        # Apply pin_to_bottom logic: always scroll to bottom on redraw
        if self._pin_to_bottom:
            max_scroll = content_height - self.get_height()
            self._scroll_offset = max(0, max_scroll)
        else:
            self._correct_scroll_offset()
        p.translate(Point(x=0, y=-self._scroll_offset))

        orig_width = self.get_width()
        self._size = Size(
            width=max(0, self._size.width - SCROLL_BAR_SIZE), height=self._size.height
        )
        self._relocate_children_linear(p)
        self._redraw_children(p, completely)
        self._size = Size(width=orig_width, height=self._size.height)
        p.restore()

        self._render_scrollbar(p, Column._scrollbar_style, Column._scrollbox_style)

    def mouse_down(self, ev: MouseEvent) -> None:
        self._handle_scroll_mouse_down(ev)

    def mouse_up(self, _: MouseEvent) -> None:
        self._handle_scroll_mouse_up()

    def mouse_drag(self, ev: MouseEvent) -> None:
        self._handle_scroll_mouse_drag(ev)

    def mouse_wheel(self, ev: WheelEvent) -> None:
        self._handle_scroll_wheel(ev)

    def scroll_y(self, y: int) -> Self:
        """Scroll vertically by the given amount."""
        return self._scroll(y)

    def content_height(self) -> float:
        """Get total content height (for backwards compatibility)."""
        return self._content_size()

    def _relocate_children(self, p: Painter) -> None:
        self._relocate_children_linear(p)

    def _resize_children(self, p: Painter) -> None:
        self._resize_children_linear(p)

    def _move_children(self) -> None:
        self._move_children_linear()
