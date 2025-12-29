from typing import Callable, Self, cast

from castella.core import (
    CaretDrawable,
    Font,
    InputCharEvent,
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
    TextAlign,
    determine_font,
)
from castella.text import Text


class InputState(ObservableBase):
    def __init__(self, text: str):
        super().__init__()
        self._text = text
        self._editing = False
        self._caret = len(text)
        self._caret_set_by_click = False

    def set(self, value: str) -> None:
        self._text = value
        self.notify()

    def value(self) -> str:
        return self._text

    def raw_value(self) -> str:
        return self._text

    def __str__(self) -> str:
        return self.value()

    def get_caret_pos(self) -> int:
        return self._caret

    def is_in_editing(self) -> bool:
        return self._editing

    def start_editing(self) -> None:
        if self._editing:
            return
        self._editing = True
        if not self._caret_set_by_click:
            self._caret = len(self._text)
        self._caret_set_by_click = False
        self.notify()

    def finish_editing(self) -> None:
        if not self._editing:
            return
        self._editing = False
        self.notify()

    def insert(self, text: str) -> None:
        if not self._editing:
            return
        self._text = self._text[: self._caret] + text + self._text[self._caret :]
        self._caret += len(text)
        self.notify()

    def delete_prev(self) -> None:
        if not self._editing:
            return
        if self._caret == 0:
            return
        self._text = self._text[: self._caret - 1] + self._text[self._caret :]
        self._caret -= 1
        self.notify()

    def delete_next(self) -> None:
        if not self._editing:
            return
        if len(self._text[self._caret :]) == 0:
            return
        self._text = self._text[: self._caret] + self._text[self._caret + 1 :]
        self.notify()

    def move_to_prev(self) -> None:
        if not self._editing:
            return
        if self._caret > 0:
            self._caret -= 1
            self.notify()

    def move_to_next(self) -> None:
        if not self._editing:
            return
        if len(self._text) > self._caret:
            self._caret += 1
            self.notify()

    def set_caret_by_click(self, pos: int) -> None:
        """Set caret position from a click event."""
        self._caret = max(0, min(pos, len(self._text)))
        self._caret_set_by_click = True


class Input(Text):
    def __init__(
        self,
        text: str | InputState,
        align: TextAlign = TextAlign.LEFT,
        font_size: int | None = None,
    ):
        if isinstance(text, InputState):
            super().__init__(text, Kind.NORMAL, align, font_size)
        else:
            super().__init__(InputState(text), Kind.NORMAL, align, font_size)
        self._callback = lambda v: ...
        # For click-to-position calculation
        self._last_font_size: float = 14.0
        self._last_text_x: float = 0.0

    def redraw(self, p: Painter, _: bool) -> None:
        state: InputState = cast(InputState, self._state)

        p.style(self._rect_style)
        size = self.get_size()
        rect = Rect(origin=Point(x=0, y=0), size=size)
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
            self._text_style.model_copy(
                update={"font": Font(family=font_family, size=font_size)}
            ),
        )

        cap_height = p.get_font_metrics().cap_height
        if self._align is TextAlign.CENTER:
            pos = Point(
                x=width / 2 - p.measure_text(str(state)) / 2,
                y=height / 2 + cap_height / 2,
            )
        elif self._align is TextAlign.RIGHT:
            pos = Point(
                x=width - p.measure_text(str(state)) - self._rect_style.padding,
                y=height / 2 + cap_height / 2,
            )
        else:
            pos = Point(
                x=self._rect_style.padding + 0.1,
                y=height / 2 + cap_height / 2,
            )

        p.fill_text(
            text=str(state),
            pos=pos,
            max_width=width,
        )

        # Store for click-to-position calculation
        self._last_font_size = font_size
        self._last_text_x = pos.x

        if state.is_in_editing():
            caret_pos_x = p.measure_text(str(state)[: state.get_caret_pos()])
            caret_pos = Point(
                x=pos.x + caret_pos_x,
                y=pos.y - cap_height - (font_size - cap_height) / 2,
            )
            if isinstance(p, CaretDrawable):
                p.draw_caret(caret_pos, font_size)
            else:
                p.fill_rect(
                    Rect(origin=caret_pos, size=Size(width=5, height=font_size))
                )

    def focused(self) -> None:
        state = cast(InputState, self._state)
        state.start_editing()

    def unfocused(self) -> None:
        state = cast(InputState, self._state)
        state.finish_editing()

    def input_char(self, ev: InputCharEvent) -> None:
        state = cast(InputState, self._state)
        state.insert(ev.char)
        self._callback(state.raw_value())

    def input_key(self, ev: InputKeyEvent) -> None:
        if ev.action is KeyAction.RELEASE:
            return

        state = cast(InputState, self._state)
        if ev.key is KeyCode.BACKSPACE:
            state.delete_prev()
            self._callback(state.raw_value())
        elif ev.key is KeyCode.DELETE:
            state.delete_next()
            self._callback(state.raw_value())
        elif ev.key is KeyCode.LEFT:
            state.move_to_prev()
        elif ev.key is KeyCode.RIGHT:
            state.move_to_next()

    def on_change(self, callback: Callable[[str], None]) -> Self:
        self._callback = callback
        return self

    def mouse_down(self, ev: MouseEvent) -> None:
        state: InputState = cast(InputState, self._state)
        text = str(state)

        # Calculate click position relative to text start
        click_x = ev.pos.x - self._last_text_x

        if click_x <= 0:
            state.set_caret_by_click(0)
            return

        # Approximate character width
        char_width = self._last_font_size * 0.5

        # Calculate character position
        char_pos = int(click_x / char_width)
        char_pos = max(0, min(char_pos, len(text)))

        state.set_caret_by_click(char_pos)
