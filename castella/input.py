from typing import Callable, Self, cast

from castella.core import (
    CaretDrawable,
    FillStyle,
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
    StrokeStyle,
    Style,
    TextAlign,
    determine_font,
    get_theme,
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
        # Selection state
        self._selection_start: int | None = None
        self._selection_end: int | None = None
        self._is_selecting: bool = False

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
            self._text[: self._caret] + self._preedit_text + self._text[self._caret :]
        )

    # ========== Selection Methods ==========

    def has_selection(self) -> bool:
        """Check if there is an active selection."""
        return (
            self._selection_start is not None
            and self._selection_end is not None
            and self._selection_start != self._selection_end
        )

    def start_selection(self, pos: int) -> None:
        """Start a new selection at the given position."""
        pos = max(0, min(pos, len(self._text)))
        self._selection_start = pos
        self._selection_end = pos
        self._is_selecting = True

    def update_selection(self, pos: int) -> None:
        """Update the selection endpoint."""
        if self._is_selecting:
            pos = max(0, min(pos, len(self._text)))
            self._selection_end = pos

    def end_selection(self) -> None:
        """Finish selection (mouse up)."""
        self._is_selecting = False

    def clear_selection(self) -> None:
        """Clear any active selection."""
        self._selection_start = None
        self._selection_end = None
        self._is_selecting = False

    def get_selection_range(self) -> tuple[int, int] | None:
        """Get normalized selection range (start <= end)."""
        if not self.has_selection():
            return None
        start = self._selection_start
        end = self._selection_end
        assert start is not None and end is not None
        # Normalize: ensure start <= end
        if start > end:
            start, end = end, start
        return (start, end)

    def get_selected_text(self) -> str:
        """Get the currently selected text."""
        range_result = self.get_selection_range()
        if range_result is None:
            return ""
        start, end = range_result
        return self._text[start:end]

    def delete_selection(self) -> str:
        """Delete selected text and return it. Returns empty string if no selection."""
        text = self.get_selected_text()
        if not text:
            return ""

        range_result = self.get_selection_range()
        assert range_result is not None
        start, end = range_result

        self._text = self._text[:start] + self._text[end:]
        self._caret = start
        self.clear_selection()
        self.notify()
        return text

    def select_all(self) -> None:
        """Select all text."""
        if not self._text:
            return
        self._selection_start = 0
        self._selection_end = len(self._text)
        self._is_selecting = False
        self.notify()


class Input(Text):
    # Selection highlight style
    _selection_style = Style(fill=FillStyle(color=get_theme().colors.bg_selected))

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
        # Cache for accurate character position calculation
        self._char_positions_cache: list[float] | None = None
        # Password mode: mask input with bullets
        self._password = password

    def redraw(self, p: Painter, _: bool) -> None:
        state: InputState = cast(InputState, self._state)

        # Use focus ring color when editing
        if state.is_in_editing():
            focus_color = get_theme().colors.border_focus
            focused_style = Style(
                fill=self._rect_style.fill,
                stroke=StrokeStyle(color=focus_color),
                border_radius=self._rect_style.border_radius,
                shadow=self._rect_style.shadow,
            )
            p.style(focused_style)
        else:
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

        # Build character position cache for accurate click detection
        self._char_positions_cache = [0.0]
        for i in range(len(display_text)):
            self._char_positions_cache.append(p.measure_text(display_text[: i + 1]))

        # Draw selection highlight (before text, so text is drawn on top)
        if state.has_selection():
            self._draw_selection_highlight(p, pos, display_text, font_size, cap_height)

        # Re-apply text style after potential selection style change
        p.style(
            self._text_style.model_copy(
                update={"font": Font(family=font_family, size=font_size)}
            ),
        )

        p.fill_text(
            text=display_text,
            pos=pos,
            max_width=width,
        )

        if state.is_in_editing():
            # Caret position: after confirmed text + preedit cursor position
            if preedit_text:
                # During preedit, caret is within preedit text
                if self._password:
                    text_before_caret = (
                        "●" * caret_pos_in_text + preedit_text[:preedit_cursor]
                    )
                else:
                    text_before_caret = (
                        actual_text[:caret_pos_in_text] + preedit_text[:preedit_cursor]
                    )
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

    def _draw_selection_highlight(
        self,
        p: Painter,
        text_pos: Point,
        display_text: str,
        font_size: float,
        cap_height: float,
    ) -> None:
        """Draw selection highlight rectangle."""
        state: InputState = cast(InputState, self._state)
        range_result = state.get_selection_range()
        if range_result is None:
            return

        start, end = range_result

        # Clamp to display text length
        start = min(start, len(display_text))
        end = min(end, len(display_text))

        if start >= end:
            return

        # Calculate pixel positions
        x_start = text_pos.x + p.measure_text(display_text[:start])
        x_end = text_pos.x + p.measure_text(display_text[:end])

        # Selection rectangle position (centered vertically)
        y = text_pos.y - cap_height - (font_size - cap_height) / 2

        # Draw selection rectangle
        p.style(Input._selection_style)
        selection_rect = Rect(
            origin=Point(x=x_start, y=y),
            size=Size(width=x_end - x_start, height=font_size),
        )
        p.fill_rect(selection_rect)

    def focused(self) -> None:
        from castella.core import App

        state = cast(InputState, self._state)
        state.start_editing()

        # Show software keyboard on mobile platforms
        # Pass current text so the hidden input field stays in sync
        app = App.get()
        if app is not None:
            app._frame.show_keyboard(state.raw_value())

    def unfocused(self) -> None:
        from castella.core import App

        state = cast(InputState, self._state)
        state.finish_editing()

        # Hide software keyboard on mobile platforms
        app = App.get()
        if app is not None:
            app._frame.hide_keyboard()

    def can_focus(self) -> bool:
        """Return True if this widget can receive focus."""
        return True

    def focus_order(self) -> int:
        """Return the tab order (lower = earlier in tab sequence)."""
        return self._tab_index

    def input_char(self, ev: InputCharEvent) -> None:
        state = cast(InputState, self._state)
        # Clear any preedit when text is committed
        if state.has_preedit():
            state.clear_preedit()
        # Delete selection if any before inserting
        if state.has_selection():
            state.delete_selection()
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
            preedit_text, _ = state.get_preedit()
            # Workaround: When preedit has only 1 character and backspace/escape
            # is pressed, the IME may not send any callback. Handle it here.
            if len(preedit_text) == 1:
                if ev.key is KeyCode.BACKSPACE or ev.key is KeyCode.ESCAPE:
                    state.clear_preedit()
                    return
            return

        # Handle Cmd+C / Ctrl+C (Copy)
        if ev.is_cmd_or_ctrl and ev.key is KeyCode.C:
            self._handle_copy()
            return

        # Handle Cmd+X / Ctrl+X (Cut)
        if ev.is_cmd_or_ctrl and ev.key is KeyCode.X:
            self._handle_cut()
            return

        # Handle Cmd+V / Ctrl+V (Paste)
        if ev.is_cmd_or_ctrl and ev.key is KeyCode.V:
            self._handle_paste()
            return

        # Handle Cmd+A / Ctrl+A (Select All)
        if ev.is_cmd_or_ctrl and ev.key is KeyCode.A:
            state.select_all()
            return

        # Clear selection on navigation keys
        if ev.key in (KeyCode.LEFT, KeyCode.RIGHT):
            state.clear_selection()

        # Delete selection on content-modifying keys
        if ev.key in (KeyCode.BACKSPACE, KeyCode.DELETE) and state.has_selection():
            state.delete_selection()
            self._callback(state.raw_value())
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

    def _handle_copy(self) -> None:
        """Copy selected text to clipboard."""
        from castella.core import App

        state = cast(InputState, self._state)
        text = state.get_selected_text()
        if text:
            App.get().set_clipboard_text(text)

    def _handle_cut(self) -> None:
        """Cut selected text to clipboard."""
        from castella.core import App

        state = cast(InputState, self._state)
        text = state.delete_selection()
        if text:
            App.get().set_clipboard_text(text)
            self._callback(state.raw_value())

    def _handle_paste(self) -> None:
        """Paste text from clipboard."""
        from castella.core import App

        state = cast(InputState, self._state)
        text = App.get().get_clipboard_text()
        if text:
            # Delete selection if any
            if state.has_selection():
                state.delete_selection()
            # Insert pasted text (single line only - take first line)
            first_line = text.split("\n")[0]
            state.insert(first_line)
            self._callback(state.raw_value())

    def on_change(self, callback: Callable[[str], None]) -> Self:
        self._callback = callback
        return self

    def _pos_from_click(self, click_x: float) -> int:
        """Convert click x position to character position."""
        state: InputState = cast(InputState, self._state)
        text = str(state)

        # Calculate position relative to text start
        rel_x = click_x - self._last_text_x

        if rel_x <= 0:
            return 0

        # Use cached character positions if available
        if self._char_positions_cache:
            for i, pos in enumerate(self._char_positions_cache):
                if pos > rel_x:
                    # Check if click is closer to this char or previous
                    if i > 0 and (rel_x - self._char_positions_cache[i - 1]) < (
                        pos - rel_x
                    ):
                        return i - 1
                    return i
            return len(text)

        # Fallback: approximate character width
        char_width = self._last_font_size * 0.5
        char_pos = int(rel_x / char_width)
        return max(0, min(char_pos, len(text)))

    def mouse_down(self, ev: MouseEvent) -> None:
        state: InputState = cast(InputState, self._state)

        # Start editing if not already
        if not state.is_in_editing():
            state._editing = True

        # Mark that cursor will be set by click
        state._caret_set_by_click = True

        # Get position from click
        char_pos = self._pos_from_click(ev.pos.x)

        # Clear previous selection and start new one
        state.clear_selection()
        state.start_selection(char_pos)

        # Update caret position
        state.set_caret_by_click(char_pos)
        state.notify()

    def mouse_drag(self, ev: MouseEvent) -> None:
        """Handle mouse drag for text selection."""
        state: InputState = cast(InputState, self._state)

        if state._is_selecting:
            char_pos = self._pos_from_click(ev.pos.x)
            state.update_selection(char_pos)
            # Move caret to selection end
            state._caret = char_pos
            state.notify()

    def mouse_up(self, _: MouseEvent) -> None:
        """Handle mouse up to finish text selection."""
        state: InputState = cast(InputState, self._state)
        state.end_selection()
