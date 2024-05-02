from dataclasses import replace
from typing import Any, Callable, Self, cast

from castella.core import (
    AppearanceState,
    Font,
    FontSizePolicy,
    Kind,
    MouseEvent,
    ObservableBase,
    Painter,
    Point,
    Rect,
    Size,
    SizePolicy,
    State,
    TextAlign,
    Widget,
    determine_font,
    replace_font_size,
)


class ButtonState(ObservableBase):
    def __init__(self, text: str) -> None:
        super().__init__()
        self._text = text
        self._pushed = False

    def pushed(self, flag: bool) -> None:
        self._pushed = flag
        self.notify()

    def is_pushed(self) -> bool:
        return self._pushed

    def get_text(self) -> str:
        return self._text


class Button(Widget):
    def __init__(
        self,
        text: str,
        align: TextAlign = TextAlign.CENTER,
        font_size: int | None = None,
    ):
        self._on_click = lambda _: ...
        self._align = align
        self._kind = Kind.NORMAL
        self._appearance_state = AppearanceState.NORMAL
        if font_size is None:
            self._font_size = 0
            self._font_size_policy = FontSizePolicy.EXPANDING
        else:
            self._font_size = font_size
            self._font_size_policy = FontSizePolicy.FIXED
        super().__init__(
            state=ButtonState(text),
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
        self._pushed_style, self._pushed_text_style = self._get_painter_styles(
            self._kind, AppearanceState.PUSHED
        )

        if self._font_size != 0:
            self._text_style = replace_font_size(
                self._text_style, self._font_size, FontSizePolicy.FIXED
            )
            self._pushed_text_style = replace_font_size(
                self._pushed_text_style, self._font_size, FontSizePolicy.FIXED
            )

    def mouse_down(self, ev: MouseEvent) -> None:
        state: ButtonState = cast(ButtonState, self._state)
        state.pushed(True)

    def mouse_up(self, ev: MouseEvent) -> None:
        state: ButtonState = cast(ButtonState, self._state)
        state.pushed(False)
        self._on_click(ev)

    def mouse_over(self) -> None:
        self._style, self._text_style = self._get_painter_styles(
            self._kind, AppearanceState.HOVER
        )
        self._text_style = replace_font_size(
            self._text_style, self._font_size, self._font_size_policy
        )
        self.update()

    def mouse_out(self) -> None:
        self._style, self._text_style = self._get_painter_styles(
            self._kind, AppearanceState.NORMAL
        )
        self._text_style = replace_font_size(
            self._text_style, self._font_size, self._font_size_policy
        )
        self.update()

    def on_click(self, callback: Callable[[MouseEvent], Any]) -> Self:
        self._on_click = callback
        return self

    def get_label(self) -> str:
        state: ButtonState = cast(ButtonState, self._state)
        return state.get_text()

    def redraw(self, p: Painter, _: bool) -> None:
        state: ButtonState = cast(ButtonState, self._state)

        rect = Rect(origin=Point(0, 0), size=self.get_size())
        if state.is_pushed():
            p.style(self._pushed_style)
            p.fill_rect(rect)
            p.stroke_rect(rect)
        else:
            p.style(self._style)
            p.fill_rect(rect)
            p.stroke_rect(rect)

        width = self.get_width()
        height = self.get_height()
        font_family, font_size = determine_font(
            width,
            height,
            replace(
                self._text_style,
                font=Font(
                    self._text_style.font.family,
                    self._text_style.font.size,
                    self._font_size_policy,
                ),
            ),
            state.get_text(),
        )
        p.style(
            replace(
                self._text_style,
                font=Font(
                    font_family,
                    font_size,
                    self._font_size_policy,
                ),
            ),
        )

        if self._align is TextAlign.CENTER:
            pos = Point(
                width / 2 - p.measure_text(str(state.get_text())) / 2,
                height / 2 + p.get_font_metrics().cap_height / 2,
            )
        elif self._align is TextAlign.RIGHT:
            pos = Point(
                width - p.measure_text(str(state.get_text())) - self._style.padding,
                height / 2 + p.get_font_metrics().cap_height / 2,
            )
        else:
            pos = Point(
                self._style.padding,
                height / 2 + p.get_font_metrics().cap_height / 2,
            )

        p.fill_text(
            text=state.get_text(),
            pos=pos,
            max_width=width - 2 * self._style.padding,
        )

    def width_policy(self, sp: SizePolicy) -> Self:
        if (
            sp is SizePolicy.CONTENT
            and self._text_style.font.size_policy is not FontSizePolicy.FIXED
        ):
            raise RuntimeError(
                "The button doesn't accept SizePolicy.CONTENT because the font size policy is not FIXED"
            )
        return super().width_policy(sp)

    def height_policy(self, sp: SizePolicy) -> Self:
        if (
            sp is SizePolicy.CONTENT
            and self._text_style.font.size_policy is not FontSizePolicy.FIXED
        ):
            raise RuntimeError(
                "The button doesn't accept SizePolicy.CONTENT because the font size policy is not FIXED"
            )
        return super().height_policy(sp)

    def measure(self, p: Painter) -> Size:
        p.save()
        p.style(self._text_style)
        state: ButtonState = cast(ButtonState, self._state)
        s = Size(
            p.measure_text(state.get_text()) + 2 * self._style.padding,
            self._text_style.font.size,
        )
        p.restore()
        return s
