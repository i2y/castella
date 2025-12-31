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
from castella.models.events import IMEPreeditEvent
from castella.text import Text


class InputState(ObservableBase):
    def __init__(self, text: str):
        super().__init__()
        self._text = text
        self._editing = False
        self._caret = len(text)
        self._caret_set_by_click = False
        # IME preedit state
        self._preedit_text: str = ""
        self._preedit_cursor: int = 0

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

    # ========== IME Preedit Methods ==========

    def set_preedit(self, text: str, cursor: int) -> None:
        """Set IME preedit (composition) text.

        Args:
            text: The preedit text being composed
            cursor: Cursor position within the preedit text
        """
        self._preedit_text = text
        self._preedit_cursor = cursor
        self.notify()

    def clear_preedit(self) -> None:
        """Clear IME preedit text."""
        self._preedit_text = ""
        self._preedit_cursor = 0
        self.notify()

    def get_preedit(self) -> tuple[str, int]:
        """Get preedit text and cursor position.

        Returns:
            Tuple of (preedit_text, cursor_position)
        """
        return (self._preedit_text, self._preedit_cursor)

    def has_preedit(self) -> bool:
        """Check if there is preedit text."""
        return bool(self._preedit_text)

    def get_display_text(self) -> str:
        """Get full display text including preedit.

        Returns the text as it should be displayed, with preedit
        text inserted at the current caret position.
        """
        if not self._preedit_text:
            return self._text
        return (
            self._text[: self._caret]
            + self._preedit_text
            + self._text[self._caret :]
        )


class Input(Text):
    def __init__(
        self,
        text: str | InputState,
        align: TextAlign = TextAlign.LEFT,
        font_size: int | None = None,
        password: bool = False,
    ):
        if isinstance(text, InputState):
            super().__init__(text, Kind.NORMAL, align, font_size)
        else:
            super().__init__(InputState(text), Kind.NORMAL, align, font_size)
        self._callback = lambda v: ...
        # For click-to-position calculation
        self._last_font_size: float = 14.0
        self._last_text_x: float = 0.0
        # Password mode: mask input with bullets
        self._password = password

    def redraw(self, p: Painter, _: bool) -> None:
        state: InputState = cast(InputState, self._state)

        p.style(self._rect_style)
        size = self.get_size()
        rect = Rect(origin=Point(x=0, y=0), size=size)
        p.fill_rect(rect)
        p.stroke_rect(rect)

        width = size.width
        height = size.height

        # Get preedit text if any
        preedit_text, preedit_cursor = state.get_preedit()
        caret_pos_in_text = state.get_caret_pos()

        # Determine display text (with preedit inserted at caret position)
        actual_text = str(state)
        if preedit_text:
            # Insert preedit at caret position
            display_text_raw = (
                actual_text[:caret_pos_in_text]
                + preedit_text
                + actual_text[caret_pos_in_text:]
            )
        else:
            display_text_raw = actual_text

        # Apply password masking (but show preedit text for IME visibility)
        if self._password:
            if preedit_text:
                # Mask confirmed text but show preedit for composition visibility
                display_text = (
                    "●" * caret_pos_in_text
                    + preedit_text
                    + "●" * (len(actual_text) - caret_pos_in_text)
                )
            else:
                display_text = "●" * len(actual_text)
        else:
            display_text = display_text_raw

        font_family, font_size = determine_font(
            width,
            height,
            self._text_style,
            display_text,
        )
        p.style(
            self._text_style.model_copy(
                update={"font": Font(family=font_family, size=font_size)}
            ),
        )

        cap_height = p.get_font_metrics().cap_height
        if self._align is TextAlign.CENTER:
            pos = Point(
                x=width / 2 - p.measure_text(display_text) / 2,
                y=height / 2 + cap_height / 2,
            )
        elif self._align is TextAlign.RIGHT:
            pos = Point(
                x=width - p.measure_text(display_text) - self._rect_style.padding,
                y=height / 2 + cap_height / 2,
            )
        else:
            pos = Point(
                x=self._rect_style.padding + 0.1,
                y=height / 2 + cap_height / 2,
            )

        p.fill_text(
            text=display_text,
            pos=pos,
            max_width=width,
        )

        # Draw preedit underline if composing
        if preedit_text and state.is_in_editing():
            # Calculate preedit text position
            if self._password:
                text_before_preedit = "●" * caret_pos_in_text
            else:
                text_before_preedit = actual_text[:caret_pos_in_text]

            preedit_start_x = pos.x + p.measure_text(text_before_preedit)
            preedit_width = p.measure_text(preedit_text)
            underline_y = pos.y + 2

            # Draw underline for preedit text
            p.fill_rect(
                Rect(
                    origin=Point(x=preedit_start_x, y=underline_y),
                    size=Size(width=preedit_width, height=2),
                )
            )

        # Store for click-to-position calculation
        self._last_font_size = font_size
        self._last_text_x = pos.x

        if state.is_in_editing():
            # Caret position: after confirmed text + preedit cursor position
            if preedit_text:
                # During preedit, caret is within preedit text
                if self._password:
                    text_before_caret = "●" * caret_pos_in_text + preedit_text[:preedit_cursor]
                else:
                    text_before_caret = actual_text[:caret_pos_in_text] + preedit_text[:preedit_cursor]
            else:
                if self._password:
                    text_before_caret = "●" * caret_pos_in_text
                else:
                    text_before_caret = display_text[:caret_pos_in_text]

            caret_pos_x = p.measure_text(text_before_caret)
            caret_pos = Point(
                x=pos.x + caret_pos_x,
                y=pos.y - cap_height - (font_size - cap_height) / 2,
            )
            if isinstance(p, CaretDrawable):
                p.draw_caret(caret_pos, font_size)
            else:
                p.fill_rect(
                    Rect(origin=caret_pos, size=Size(width=2, height=font_size))
                )

            # Notify IME of cursor position for candidate window
            self._notify_ime_cursor_rect(pos, caret_pos_x, font_size)

    def _notify_ime_cursor_rect(
        self, text_pos: Point, caret_offset_x: float, font_size: float
    ) -> None:
        """Notify the frame of cursor position for IME candidate window."""
        from castella.core import App

        app = App.get()
        if app is None:
            return

        frame = app._frame
        if not hasattr(frame, "set_ime_cursor_rect"):
            return

        # Calculate absolute cursor position
        widget_pos = self.get_pos()
        frame.set_ime_cursor_rect(
            int(widget_pos.x + text_pos.x + caret_offset_x),
            int(widget_pos.y),
            1,
            int(self.get_size().height),
        )

    def focused(self) -> None:
        state = cast(InputState, self._state)
        state.start_editing()

    def unfocused(self) -> None:
        state = cast(InputState, self._state)
        state.finish_editing()

    def input_char(self, ev: InputCharEvent) -> None:
        state = cast(InputState, self._state)
        # Clear any preedit when text is committed
        if state.has_preedit():
            state.clear_preedit()
        state.insert(ev.char)
        self._callback(state.raw_value())

    def ime_preedit(self, ev: IMEPreeditEvent) -> None:
        """Handle IME preedit (composition) event."""
        state = cast(InputState, self._state)
        if ev.text:
            state.set_preedit(ev.text, ev.cursor_pos)
        else:
            state.clear_preedit()

    def input_key(self, ev: InputKeyEvent) -> None:
        if ev.action is KeyAction.RELEASE:
            return

        state = cast(InputState, self._state)

        # During IME preedit, let IME handle key events
        if state.has_preedit():
            return

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
