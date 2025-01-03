from dataclasses import replace
from typing import Any, Self, cast

from .core import (
    AppearanceState,
    Font,
    FontSizePolicy,
    Kind,
    Painter,
    Point,
    Rect,
    SimpleValue,
    Size,
    SizePolicy,
    State,
    TextAlign,
    Widget,
    determine_font,
    replace_font_size,
)


class Text(Widget):
    def __init__(
        self,
        text: Any,
        kind: Kind = Kind.NORMAL,
        align: TextAlign = TextAlign.CENTER,
        font_size: int | None = None,
    ):
        if isinstance(text, SimpleValue):
            state = text
        else:
            state = State(str(text))

        self._kind = kind
        self._font_size = font_size
        self._align = align

        super().__init__(
            state=state,
            size=Size(0, 0),
            pos=Point(0, 0),
            pos_policy=None,
            width_policy=SizePolicy.EXPANDING,
            height_policy=SizePolicy.EXPANDING,
        )

    def _on_update_widget_styles(self) -> None:
        self._rect_style, self._text_style = self._get_painter_styles(
            self._kind, AppearanceState.NORMAL
        )
        if self._font_size is not None:
            self._text_style = replace_font_size(
                self._text_style, self._font_size, FontSizePolicy.FIXED
            )

    def redraw(self, p: Painter, _: bool) -> None:
        state: State = cast(State, self._state)

        p.style(self._rect_style)
        size = self.get_size()
        rect = Rect(origin=Point(0, 0), size=size)
        p.fill_rect(rect)
        p.stroke_rect(rect)

        width = size.width
        height = size.height
        font_family, font_size = determine_font(
            width,
            height,
            self._text_style,
            str(state),
        )
        p.style(
            replace(
                self._text_style,
                font=Font(
                    font_family,
                    font_size,
                ),
            ),
        )

        if self._align is TextAlign.CENTER:
            pos = Point(
                width / 2 - p.measure_text(str(state)) / 2,
                height / 2 + p.get_font_metrics().cap_height / 2,
            )
        elif self._align is TextAlign.RIGHT:
            pos = Point(
                width - p.measure_text(str(state)) - (self._rect_style.padding + 0.1),
                height / 2 + p.get_font_metrics().cap_height / 2,
            )
        else:
            pos = Point(
                self._rect_style.padding + 0.1,
                height / 2 + p.get_font_metrics().cap_height / 2,
            )

        p.fill_text(
            text=str(state),
            pos=pos,
            max_width=width,
        )

    def width_policy(self, sp: SizePolicy) -> Self:
        if (
            sp is SizePolicy.CONTENT
            and self._text_style.font.size_policy is not FontSizePolicy.FIXED
        ):
            raise RuntimeError(
                "Text doesn't accept SizePolicy.CONTENT because the font size policy is not FIXED"
            )
        return super().width_policy(sp)

    def height_policy(self, sp: SizePolicy) -> Self:
        if (
            sp is SizePolicy.CONTENT
            and self._text_style.font.size_policy is not FontSizePolicy.FIXED
        ):
            raise RuntimeError(
                "Text doesn't accept SizePolicy.CONTENT because the font size policy is not FIXED"
            )
        return super().height_policy(sp)

    def measure(self, p: Painter) -> Size:
        p.save()
        p.style(self._text_style)
        state: State = cast(State, self._state)
        s = Size(p.measure_text(str(state)), self._text_style.font.size)
        p.restore()
        return s


class SimpleText(Widget):
    def __init__(
        self,
        text: Any,
        kind: Kind = Kind.NORMAL,
        align: TextAlign = TextAlign.CENTER,
        font_size: int | None = None,
    ):
        if isinstance(text, SimpleValue):
            state = text
        else:
            state = State(str(text))

        self._kind = kind
        self._font_size = font_size
        self._align = align

        super().__init__(
            state=state,
            size=Size(0, 0),
            pos=Point(0, 0),
            pos_policy=None,
            width_policy=SizePolicy.EXPANDING,
            height_policy=SizePolicy.EXPANDING,
        )

    def _on_update_widget_styles(self) -> None:
        self._rect_style, self._text_style = self._get_painter_styles(
            self._kind, AppearanceState.NORMAL
        )
        if self._font_size is not None:
            self._text_style = replace_font_size(
                self._text_style, self._font_size, FontSizePolicy.FIXED
            )

    def redraw(self, p: Painter, _: bool) -> None:
        state: State = cast(State, self._state)

        p.style(self._rect_style)
        size = self.get_size()
        rect = Rect(origin=Point(0, 0), size=size)
        p.fill_rect(rect)
        # p.stroke_rect(rect)

        width = size.width
        height = size.height
        font_family, font_size = determine_font(
            width,
            height,
            self._text_style,
            str(state),
        )
        p.style(
            replace(
                self._text_style,
                font=Font(
                    font_family,
                    font_size,
                ),
            ),
        )

        if self._align is TextAlign.CENTER:
            pos = Point(
                width / 2 - p.measure_text(str(state)) / 2,
                height / 2 + p.get_font_metrics().cap_height / 2,
            )
        elif self._align is TextAlign.RIGHT:
            pos = Point(
                width - p.measure_text(str(state)) - (self._rect_style.padding + 0.1),
                height / 2 + p.get_font_metrics().cap_height / 2,
            )
        else:
            pos = Point(
                self._rect_style.padding + 0.1,
                height / 2 + p.get_font_metrics().cap_height / 2,
            )

        p.fill_text(
            text=str(state),
            pos=pos,
            max_width=width,
        )

    def width_policy(self, sp: SizePolicy) -> Self:
        if (
            sp is SizePolicy.CONTENT
            and self._text_style.font.size_policy is not FontSizePolicy.FIXED
        ):
            raise RuntimeError(
                "Text doesn't accept SizePolicy.CONTENT because the font size policy is not FIXED"
            )
        return super().width_policy(sp)

    def height_policy(self, sp: SizePolicy) -> Self:
        if (
            sp is SizePolicy.CONTENT
            and self._text_style.font.size_policy is not FontSizePolicy.FIXED
        ):
            raise RuntimeError(
                "Text doesn't accept SizePolicy.CONTENT because the font size policy is not FIXED"
            )
        return super().height_policy(sp)

    def measure(self, p: Painter) -> Size:
        p.save()
        p.style(self._text_style)
        state: State = cast(State, self._state)
        s = Size(p.measure_text(str(state)), self._text_style.font.size)
        p.restore()
        return s
