from dataclasses import replace
from typing import Any, Callable, Self, cast

from castella.core import (
    AppearanceState,
    Circle,
    Font,
    FontSizePolicy,
    Kind,
    MouseEvent,
    Painter,
    Point,
    Rect,
    Size,
    SizePolicy,
    State,
    Widget,
    determine_font,
)


class CheckBox(Widget):
    def __init__(
        self,
        checked: bool | State[bool] = False,
        on_label: str = "",
        off_label: str = "",
        is_circle: bool = False,
    ):
        self._on_label = on_label
        self._off_label = off_label
        self._is_circle = is_circle
        self._on_click = lambda _: ...
        self._kind = Kind.NORMAL
        self._appearance_state = AppearanceState.NORMAL
        super().__init__(
            state=checked if isinstance(checked, State) else State(checked),
            size=Size(0, 0),
            pos=Point(0, 0),
            pos_policy=None,
            width_policy=SizePolicy.EXPANDING,
            height_policy=SizePolicy.EXPANDING,
        )

    def _on_update_widget_styles(self) -> None:
        self._style, self._text_style = self._get_painter_styles(
            self._kind, self._appearance_state
        )
        self._checked_style, self._checked_text_style = self._get_painter_styles(
            self._kind, AppearanceState.SELECTED
        )

    def mouse_up(self, ev: MouseEvent) -> None:
        state: State[bool] = cast(State[bool], self._state)
        state.set(not state.value())
        self._on_click(ev)

    def on_click(self, callback: Callable[[MouseEvent], Any]) -> Self:
        self._on_click = callback
        return self

    def redraw(self, p: Painter, _: bool) -> None:
        state: State[bool] = cast(State[bool], self._state)

        size = self.get_size()
        if self._is_circle:
            center = Point(size.width / 2, size.height / 2)
            circle = Circle(center=center, radius=size.width / 2)
            p.style(self._style)
            p.fill_circle(circle)
            p.stroke_circle(circle)
            if state.value():
                inner_circle = Circle(
                    center=center,
                    radius=size.width * 0.6 / 2,
                )
                p.style(self._checked_style)
                p.fill_circle(inner_circle)
        else:
            rect = Rect(origin=Point(0, 0), size=size)
            p.style(self._style)
            p.fill_rect(rect)
            p.stroke_rect(rect)
            if state.value():
                inner_rect = Rect(
                    origin=Point(size.width * 0.2, size.height * 0.2),
                    size=Size(size.width * 0.6, size.height * 0.6),
                )
                p.style(self._checked_style)
                p.fill_rect(inner_rect)

        if state.value():
            label = self._on_label
            text_style = self._checked_text_style
        else:
            label = self._off_label
            text_style = self._text_style

        width = self.get_width()
        height = self.get_height()
        font_family, font_size = determine_font(
            width,
            height,
            replace(
                text_style,
                font=Font(
                    self._text_style.font.family,
                    self._text_style.font.size,
                    FontSizePolicy.EXPANDING,
                ),
            ),
            label,
        )
        p.style(
            replace(
                text_style,
                font=Font(
                    font_family,
                    font_size,
                    FontSizePolicy.EXPANDING,
                ),
            ),
        )

        pos = Point(
            width / 2 - p.measure_text(label) / 2,
            height / 2 + p.get_font_metrics().cap_height / 2,
        )

        p.fill_text(
            text=label,
            pos=pos,
            max_width=width - 2 * self._style.padding,
        )

    def width_policy(self, sp: SizePolicy) -> Self:
        if sp is SizePolicy.CONTENT:
            raise RuntimeError("CheckBox doesn't accept SizePolicy.CONTENT")
        return super().width_policy(sp)

    def height_policy(self, sp: SizePolicy) -> Self:
        if sp is SizePolicy.CONTENT:
            raise RuntimeError("CheckBox doesn't accept SizePolicy.CONTENT")
        return super().height_policy(sp)
