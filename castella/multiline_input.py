from typing import Callable, Self, cast

from castella.core import (
    AppearanceState,
    CaretDrawable,
    FontSizePolicy,
    InputCharEvent,
    InputKeyEvent,
    KeyAction,
    KeyCode,
    Kind,
    ObservableBase,
    Painter,
    Point,
    Rect,
    Size,
    SizePolicy,
    Widget,
    replace_font_size,
)


class MultilineInputState(ObservableBase):
    """Observable state for multi-line text input."""

    def __init__(self, text: str):
        super().__init__()
        self._lines: list[str] = text.split("\n") if text else [""]
        self._editing: bool = False
        self._row: int = len(self._lines) - 1
        self._col: int = len(self._lines[-1])
        self._target_col: int | None = None

    def value(self) -> str:
        """Return full text as a single string joined with newlines."""
        return "\n".join(self._lines)

    def raw_value(self) -> str:
        """Return full text without transformation."""
        return self.value()

    def set(self, value: str) -> None:
        """Replace entire text content."""
        self._lines = value.split("\n") if value else [""]
        self._row = len(self._lines) - 1
        self._col = len(self._lines[-1])
        self._target_col = None
        self.notify()

    def __str__(self) -> str:
        return self.value()

    def get_cursor_pos(self) -> tuple[int, int]:
        """Return cursor position as (row, col) tuple."""
        return (self._row, self._col)

    def get_line(self, row: int) -> str:
        """Return content of a specific line."""
        if 0 <= row < len(self._lines):
            return self._lines[row]
        return ""

    def line_count(self) -> int:
        """Return number of lines."""
        return len(self._lines)

    def is_in_editing(self) -> bool:
        """Return whether in editing mode."""
        return self._editing

    def start_editing(self) -> None:
        """Enter editing mode."""
        if self._editing:
            return
        self._editing = True
        self._row = len(self._lines) - 1
        self._col = len(self._lines[-1])
        self.notify()

    def finish_editing(self) -> None:
        """Exit editing mode."""
        if not self._editing:
            return
        self._editing = False
        self.notify()

    def insert(self, char: str) -> None:
        """Insert character at cursor position."""
        if not self._editing:
            return
        line = self._lines[self._row]
        self._lines[self._row] = line[: self._col] + char + line[self._col :]
        self._col += len(char)
        self._target_col = None
        self.notify()

    def insert_newline(self) -> None:
        """Insert newline at cursor, splitting current line."""
        if not self._editing:
            return
        line = self._lines[self._row]
        before = line[: self._col]
        after = line[self._col :]
        self._lines[self._row] = before
        self._lines.insert(self._row + 1, after)
        self._row += 1
        self._col = 0
        self._target_col = None
        self.notify()

    def delete_prev(self) -> None:
        """Delete character before cursor (backspace)."""
        if not self._editing:
            return
        if self._col > 0:
            line = self._lines[self._row]
            self._lines[self._row] = line[: self._col - 1] + line[self._col :]
            self._col -= 1
        elif self._row > 0:
            prev_line = self._lines[self._row - 1]
            curr_line = self._lines[self._row]
            self._lines[self._row - 1] = prev_line + curr_line
            del self._lines[self._row]
            self._row -= 1
            self._col = len(prev_line)
        self._target_col = None
        self.notify()

    def delete_next(self) -> None:
        """Delete character at cursor (delete key)."""
        if not self._editing:
            return
        line = self._lines[self._row]
        if self._col < len(line):
            self._lines[self._row] = line[: self._col] + line[self._col + 1 :]
        elif self._row < len(self._lines) - 1:
            next_line = self._lines[self._row + 1]
            self._lines[self._row] = line + next_line
            del self._lines[self._row + 1]
        self._target_col = None
        self.notify()

    def move_left(self) -> None:
        """Move cursor left."""
        if not self._editing:
            return
        if self._col > 0:
            self._col -= 1
        elif self._row > 0:
            self._row -= 1
            self._col = len(self._lines[self._row])
        self._target_col = None
        self.notify()

    def move_right(self) -> None:
        """Move cursor right."""
        if not self._editing:
            return
        line = self._lines[self._row]
        if self._col < len(line):
            self._col += 1
        elif self._row < len(self._lines) - 1:
            self._row += 1
            self._col = 0
        self._target_col = None
        self.notify()

    def move_up(self) -> None:
        """Move cursor up one line."""
        if not self._editing or self._row == 0:
            return
        if self._target_col is None:
            self._target_col = self._col
        self._row -= 1
        self._col = min(self._target_col, len(self._lines[self._row]))
        self.notify()

    def move_down(self) -> None:
        """Move cursor down one line."""
        if not self._editing or self._row >= len(self._lines) - 1:
            return
        if self._target_col is None:
            self._target_col = self._col
        self._row += 1
        self._col = min(self._target_col, len(self._lines[self._row]))
        self.notify()


class MultilineInput(Widget):
    """Multi-line text input widget with optional word wrapping."""

    def __init__(
        self,
        text: str | MultilineInputState,
        font_size: int,
        padding: int = 8,
        line_spacing: int = 4,
        kind: Kind = Kind.NORMAL,
        wrap: bool = True,
    ):
        if isinstance(text, MultilineInputState):
            state = text
        else:
            state = MultilineInputState(text)

        self._kind = kind
        self._font_size = font_size
        self._padding = padding
        self._border_width = 1
        self._line_spacing = line_spacing
        self._wrap = wrap
        self._callback: Callable[[str], None] = lambda v: ...

        super().__init__(
            state=state,
            size=Size(width=0, height=0),
            pos=Point(x=0, y=0),
            pos_policy=None,
            width_policy=SizePolicy.EXPANDING,
            height_policy=SizePolicy.CONTENT,
        )

    def _on_update_widget_styles(self) -> None:
        self._rect_style, self._text_style = self._get_painter_styles(
            self._kind, AppearanceState.NORMAL
        )
        self._text_style = replace_font_size(
            self._text_style, self._font_size, FontSizePolicy.FIXED
        )

    def _get_wrapped_lines(
        self, p: Painter, line_width: float
    ) -> list[tuple[int, str, int]]:
        """Get display lines with wrapping.

        Returns list of (logical_row, display_text, start_col) tuples.
        """
        state = cast(MultilineInputState, self._state)
        display_lines: list[tuple[int, str, int]] = []

        if not self._wrap or line_width <= 0:
            for row_idx in range(state.line_count()):
                display_lines.append((row_idx, state.get_line(row_idx), 0))
            return display_lines

        for row_idx in range(state.line_count()):
            line = state.get_line(row_idx)
            if not line:
                display_lines.append((row_idx, "", 0))
                continue

            col_offset = 0
            remaining = line

            while remaining:
                if p.measure_text(remaining) <= line_width:
                    display_lines.append((row_idx, remaining, col_offset))
                    break

                # Find break point
                break_idx = len(remaining)
                for i in range(1, len(remaining) + 1):
                    if p.measure_text(remaining[:i]) > line_width:
                        break_idx = max(1, i - 1)
                        break

                # Try to break at word boundary
                space_idx = remaining.rfind(" ", 0, break_idx + 1)
                if space_idx > 0:
                    break_idx = space_idx + 1

                display_lines.append((row_idx, remaining[:break_idx], col_offset))
                col_offset += break_idx
                remaining = remaining[break_idx:]

        return display_lines

    def _find_cursor_display_pos(
        self, p: Painter, display_lines: list[tuple[int, str, int]]
    ) -> tuple[int, float]:
        """Find which display line the cursor is on and its x position.

        Returns (display_line_index, x_offset).
        """
        state = cast(MultilineInputState, self._state)
        cursor_row, cursor_col = state.get_cursor_pos()

        for display_idx, (logical_row, text, start_col) in enumerate(display_lines):
            if logical_row != cursor_row:
                continue

            end_col = start_col + len(text)
            if start_col <= cursor_col <= end_col:
                text_before = text[: cursor_col - start_col]
                x_offset = p.measure_text(text_before)
                return (display_idx, x_offset)

        # Fallback: cursor at end of last line of its logical row
        for display_idx in range(len(display_lines) - 1, -1, -1):
            logical_row, text, start_col = display_lines[display_idx]
            if logical_row == cursor_row:
                x_offset = p.measure_text(text)
                return (display_idx, x_offset)

        return (0, 0.0)

    def redraw(self, p: Painter, _: bool) -> None:
        state = cast(MultilineInputState, self._state)
        padding = self._padding
        line_spacing = self._line_spacing
        font_size = self._font_size

        p.style(self._rect_style)
        size = self.get_size()
        rect = Rect(origin=Point(x=0, y=0), size=size)
        p.fill_rect(rect)
        p.stroke_rect(rect)

        p.style(self._text_style)
        cap_height = p.get_font_metrics().cap_height

        line_width = size.width - (padding + self._border_width) * 2
        display_lines = self._get_wrapped_lines(p, line_width)

        for display_idx, (_, text, _) in enumerate(display_lines):
            y = padding + font_size + display_idx * (font_size + line_spacing)
            p.fill_text(text, Point(x=padding + 0.1, y=y), None)

        if state.is_in_editing():
            display_idx, x_offset = self._find_cursor_display_pos(p, display_lines)
            caret_x = padding + x_offset
            text_y = padding + font_size + display_idx * (font_size + line_spacing)
            caret_y = text_y - cap_height - (font_size - cap_height) / 2

            caret_pos = Point(x=caret_x, y=caret_y)
            if isinstance(p, CaretDrawable):
                p.draw_caret(caret_pos, font_size)
            else:
                p.fill_rect(
                    Rect(origin=caret_pos, size=Size(width=2, height=font_size))
                )

    def measure(self, p: Painter) -> Size:
        state = cast(MultilineInputState, self._state)
        padding = self._padding
        border_width = self._border_width
        line_spacing = self._line_spacing
        font_size = self._font_size

        p.save()
        p.style(self._text_style)

        if self._wrap and self._size.width > 0:
            line_width = self._size.width - (padding + border_width) * 2
            display_lines = self._get_wrapped_lines(p, line_width)
            num_lines = len(display_lines)
            w = self._size.width
        else:
            max_width = 0.0
            for row_idx in range(state.line_count()):
                line = state.get_line(row_idx)
                line_width = p.measure_text(line)
                if line_width > max_width:
                    max_width = line_width
            num_lines = state.line_count()
            w = max_width + (padding + border_width) * 2

        h = (
            font_size * num_lines
            + line_spacing * max(0, num_lines - 1)
            + padding * 2
            + border_width * 2
        )

        p.restore()
        return Size(width=w, height=h)

    def focused(self) -> None:
        state = cast(MultilineInputState, self._state)
        state.start_editing()

    def unfocused(self) -> None:
        state = cast(MultilineInputState, self._state)
        state.finish_editing()

    def input_char(self, ev: InputCharEvent) -> None:
        state = cast(MultilineInputState, self._state)
        state.insert(ev.char)
        self._callback(state.raw_value())

    def input_key(self, ev: InputKeyEvent) -> None:
        if ev.action is KeyAction.RELEASE:
            return

        state = cast(MultilineInputState, self._state)
        if ev.key is KeyCode.BACKSPACE:
            state.delete_prev()
            self._callback(state.raw_value())
        elif ev.key is KeyCode.DELETE:
            state.delete_next()
            self._callback(state.raw_value())
        elif ev.key is KeyCode.LEFT:
            state.move_left()
        elif ev.key is KeyCode.RIGHT:
            state.move_right()
        elif ev.key is KeyCode.UP:
            state.move_up()
        elif ev.key is KeyCode.DOWN:
            state.move_down()
        elif ev.key is KeyCode.ENTER:
            state.insert_newline()
            self._callback(state.raw_value())

    def on_change(self, callback: Callable[[str], None]) -> Self:
        """Register callback for text changes."""
        self._callback = callback
        return self
