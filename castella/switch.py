from typing import Callable, Self, cast

from castella.core import (
    AppearanceState,
    Circle,
    Kind,
    MouseEvent,
    Painter,
    Point,
    Rect,
    SimpleValue,
    Size,
    SizePolicy,
    State,
    Widget,
)


class Switch(Widget):
    def __init__(self, selected: bool | SimpleValue[bool]):
        self._kind = Kind.NORMAL
        self._callback = lambda _: ...
        super().__init__(
            state=selected if isinstance(selected, SimpleValue) else State(selected),
            size=Size(width=0, height=0),
            pos=Point(x=0, y=0),
            pos_policy=None,
            width_policy=SizePolicy.EXPANDING,
            height_policy=SizePolicy.EXPANDING,
        )

    def mouse_up(self, ev: MouseEvent) -> None:
        state = cast(SimpleValue[bool], self._state)
        new_value = not state.value()
        state.set(new_value)
        self._callback(new_value)

    def _on_update_widget_styles(self) -> None:
        self._bg_style, self._fg_style = self._get_painter_styles(
            self._kind, AppearanceState.NORMAL
        )
        self._selected_bg_style, _ = self._get_painter_styles(
            self._kind, AppearanceState.SELECTED
        )

    def redraw(self, p: Painter, _: bool) -> None:
        self._draw_background(p)
        self._draw_knob(p)

    def _draw_background(self, p: Painter) -> None:
        s = self.get_size()
        r = s.height / 2 - 0.5
        left_circle = Circle(center=Point(x=r, y=r), radius=r)
        center_rect = Rect(origin=Point(x=r, y=0), size=s - Size(width=r * 2, height=0))
        right_circle = Circle(center=Point(x=s.width - r, y=r), radius=r)

        state = cast(SimpleValue[bool], self._state)
        if state.value():
            p.style(self._selected_bg_style)
        else:
            p.style(self._bg_style)
        p.fill_circle(left_circle)
        p.fill_rect(center_rect)
        p.fill_circle(right_circle)

    def _draw_knob(self, p: Painter) -> None:
        s = self.get_size()
        r = s.height / 2 - 0.5
        inner_r = s.height * 0.75 / 2 - 0.5
        w = s.width
        state = cast(SimpleValue[bool], self._state)
        p.style(self._fg_style)
        if state.value():
            knob = Circle(center=Point(x=w - r, y=r), radius=inner_r)
        else:
            knob = Circle(center=Point(x=r, y=r), radius=inner_r)
        p.fill_circle(knob)

    def width_policy(self, sp: SizePolicy) -> Self:
        if sp is SizePolicy.CONTENT:
            raise RuntimeError("The switch doesn't accept SizePolicy.CONTENT")
        return super().width_policy(sp)

    def height_policy(self, sp: SizePolicy) -> Self:
        if sp is SizePolicy.CONTENT:
            raise RuntimeError("The switch doesn't accept SizePolicy.CONTENT")
        return super().height_policy(sp)

    def on_change(self, callback: Callable[[bool], None]) -> Self:
        self._callback = callback
        return self
