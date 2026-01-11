from typing import Any, Callable, Self, cast

from castella.core import (
    AppearanceState,
    Font,
    FontSizePolicy,
    InputKeyEvent,
    KeyAction,
    KeyCode,
    Kind,
    MouseEvent,
    ObservableBase,
    Painter,
    Point,
    Rect,
    Size,
    SizePolicy,
    TextAlign,
    Widget,
    determine_font,
    replace_font_size,
)
from castella.font import EM


class ButtonState(ObservableBase):
    def __init__(self, text: str) -> None:
        super().__init__()
        self._text = text
        self._pushed = False
        self._focused = False

    def pushed(self, flag: bool) -> None:
        self._pushed = flag
        self.notify()

    def is_pushed(self) -> bool:
        return self._pushed

    def set_focused(self, flag: bool) -> None:
        self._focused = flag
        self.notify()

    def is_focused(self) -> bool:
        return self._focused

    def get_text(self) -> str:
        return self._text


class Button(Widget):
    def __init__(
        self,
        text: str,
        kind: Kind = Kind.NORMAL,
        align: TextAlign = TextAlign.CENTER,
        font_size: int = EM,
    ):
        self._on_click = lambda _: ...
        self._align = align
        self._kind = kind
        self._appearance_state = AppearanceState.NORMAL
        self._font_size = font_size
        self._font_size_policy = FontSizePolicy.FIXED
        super().__init__(
            state=ButtonState(text),
            size=Size(width=0, height=0),
            pos=Point(x=0, y=0),
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

    def focused(self) -> None:
        """Called when this widget receives focus."""
        state: ButtonState = cast(ButtonState, self._state)
        state.set_focused(True)

    def unfocused(self) -> None:
        """Called when this widget loses focus."""
        state: ButtonState = cast(ButtonState, self._state)
        state.set_focused(False)

    def can_focus(self) -> bool:
        """Return True if this widget can receive focus."""
        return True

    def focus_order(self) -> int:
        """Return the tab order (lower = earlier in tab sequence)."""
        return self._tab_index

    def input_key(self, ev: InputKeyEvent) -> None:
        """Handle keyboard input when focused."""
        if ev.action == KeyAction.RELEASE:
            return
        # Trigger click on Enter or Space
        if ev.key in (KeyCode.ENTER, KeyCode.SPACE):
            self._on_click(MouseEvent(pos=Point(x=0, y=0)))

    def on_click(self, callback: Callable[[MouseEvent], Any]) -> Self:
        self._on_click = callback
        return self

    def kind(self, kind: Kind) -> Self:
        """Set the button's semantic kind for styling."""
        self._kind = kind
        self._on_update_widget_styles()
        return self

    def get_label(self) -> str:
        state: ButtonState = cast(ButtonState, self._state)
        return state.get_text()

    def redraw(self, p: Painter, _: bool) -> None:
        from castella.core import StrokeStyle, Style, get_theme

        state: ButtonState = cast(ButtonState, self._state)

        rect = Rect(origin=Point(x=0, y=0), size=self.get_size())
        if state.is_pushed():
            p.style(self._pushed_style)
            p.fill_rect(rect)
            p.stroke_rect(rect)
        elif state.is_focused():
            # Use focus ring color
            focus_color = get_theme().colors.border_focus
            focused_style = Style(
                fill=self._style.fill,
                stroke=StrokeStyle(color=focus_color),
                border_radius=self._style.border_radius,
                shadow=self._style.shadow,
            )
            p.style(focused_style)
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
            self._text_style.model_copy(
                update={
                    "font": Font(
                        family=self._text_style.font.family,
                        size=self._text_style.font.size,
                        size_policy=self._font_size_policy,
                    )
                }
            ),
            state.get_text(),
        )
        p.style(
            self._text_style.model_copy(
                update={
                    "font": Font(
                        family=font_family,
                        size=font_size,
                        size_policy=self._font_size_policy,
                    )
                }
            ),
        )

        if self._align is TextAlign.CENTER:
            pos = Point(
                x=width / 2 - p.measure_text(str(state.get_text())) / 2,
                y=height / 2 + p.get_font_metrics().cap_height / 2,
            )
        elif self._align is TextAlign.RIGHT:
            pos = Point(
                x=width - p.measure_text(str(state.get_text())) - self._style.padding,
                y=height / 2 + p.get_font_metrics().cap_height / 2,
            )
        else:
            pos = Point(
                x=self._style.padding,
                y=height / 2 + p.get_font_metrics().cap_height / 2,
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
        # For FIXED policy, return the fixed size
        width = self._size.width if self._width_policy is SizePolicy.FIXED else None
        height = self._size.height if self._height_policy is SizePolicy.FIXED else None

        # Only measure content if needed
        if width is None or height is None:
            p.save()
            p.style(self._text_style)
            state: ButtonState = cast(ButtonState, self._state)
            if width is None:
                width = p.measure_text(state.get_text()) + 2 * self._style.padding
            if height is None:
                height = self._text_style.font.size
            p.restore()

        return Size(width=width, height=height)
