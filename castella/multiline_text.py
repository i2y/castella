import re
from typing import Generator, cast

from castella.core import (
    App,
    AppearanceState,
    FillStyle,
    FontSizePolicy,
    InputKeyEvent,
    KeyAction,
    KeyCode,
    Kind,
    MouseEvent,
    Painter,
    Point,
    Rect,
    SimpleValue,
    Size,
    SizePolicy,
    State,
    Style,
    Widget,
    get_theme,
    replace_font_size,
)


class MultilineText(Widget):
    # Selection highlight style
    _selection_style = Style(fill=FillStyle(color=get_theme().colors.bg_selected))

    def __init__(
        self,
        text: str | SimpleValue[str],
        font_size: int,
        padding: int = 8,
        line_spacing: int = 4,
        kind: Kind = Kind.NORMAL,
        wrap: bool = False,  # only works if the size policy of width is not SizePolicy.CONTENT
    ):
        if isinstance(text, SimpleValue):
            state = text
        else:
            state = State(text)

        self._kind = kind
        self._font_size = font_size
        self._padding = padding
        self._border_width = 1  # currently this is fixed value, probably this will become variable later.
        self._line_spacing = line_spacing
        self._wrap = wrap

        # Selection state
        self._selection_start: tuple[int, int] | None = None  # (row, col)
        self._selection_end: tuple[int, int] | None = None  # (row, col)
        self._is_selecting: bool = False
        self._last_lines: list[str] | None = None  # Cache for click handling
        # Cache for accurate character position calculation
        self._char_positions_cache: list[list[float]] | None = None

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

    # Selection methods
    def has_selection(self) -> bool:
        """Check if there is an active selection."""
        return (
            self._selection_start is not None
            and self._selection_end is not None
            and self._selection_start != self._selection_end
        )

    def get_selection_range(
        self,
    ) -> tuple[tuple[int, int], tuple[int, int]] | None:
        """Get normalized selection range (start <= end)."""
        if not self.has_selection():
            return None
        start = self._selection_start
        end = self._selection_end
        assert start is not None and end is not None
        # Normalize: ensure start <= end
        if (start[0] > end[0]) or (start[0] == end[0] and start[1] > end[1]):
            start, end = end, start
        return (start, end)

    def get_selected_text(self) -> str:
        """Get the currently selected text."""
        range_result = self.get_selection_range()
        if range_result is None or self._last_lines is None:
            return ""
        (start_row, start_col), (end_row, end_col) = range_result
        lines = self._last_lines

        if start_row >= len(lines) or end_row >= len(lines):
            return ""

        if start_row == end_row:
            return lines[start_row][start_col:end_col]

        result = [lines[start_row][start_col:]]
        for row in range(start_row + 1, end_row):
            result.append(lines[row])
        result.append(lines[end_row][:end_col])
        return "\n".join(result)

    def clear_selection(self) -> None:
        """Clear any active selection."""
        self._selection_start = None
        self._selection_end = None
        self._is_selecting = False

    def select_all(self) -> None:
        """Select all text."""
        if not self._last_lines or len(self._last_lines) == 0:
            return
        self._selection_start = (0, 0)
        last_row = len(self._last_lines) - 1
        self._selection_end = (last_row, len(self._last_lines[last_row]))
        self._is_selecting = False

    def _pos_from_point(self, point: Point) -> tuple[int, int]:
        """Convert screen point to (row, col) position."""
        padding = self._padding
        font_size = self._font_size
        line_spacing = self._line_spacing
        border_width = self._border_width

        click_y = point.y - border_width

        # Find the line index
        if click_y < padding:
            line_idx = 0
        else:
            line_idx = int((click_y - padding) / (font_size + line_spacing))

        lines = self._last_lines or []
        if not lines:
            return (0, 0)

        line_idx = max(0, min(line_idx, len(lines) - 1))
        text = lines[line_idx]

        # Find column based on x position
        # Text is drawn at padding + 0.1, so account for that offset
        click_x = point.x - padding - 0.1
        if click_x <= 0:
            col = 0
        else:
            # Use cached character positions if available
            if self._char_positions_cache is not None and line_idx < len(
                self._char_positions_cache
            ):
                positions = self._char_positions_cache[line_idx]
                col = 0
                for i in range(len(positions)):
                    if positions[i] > click_x:
                        # Check if click is closer to this char or previous
                        if i > 0 and (click_x - positions[i - 1]) < (
                            positions[i] - click_x
                        ):
                            col = i - 1
                        else:
                            col = i
                        break
                    col = i
            else:
                # Fallback to approximate calculation
                char_width = font_size * 0.5
                col = 0
                for i in range(len(text) + 1):
                    if i * char_width >= click_x:
                        col = max(0, i - 1)
                        break
                    col = i
            col = min(col, len(text))

        return (line_idx, col)

    def mouse_down(self, ev: MouseEvent) -> None:
        """Handle mouse down to start selection."""
        row, col = self._pos_from_point(ev.pos)
        self.clear_selection()
        self._selection_start = (row, col)
        self._selection_end = (row, col)
        self._is_selecting = True
        self.update(True)

    def mouse_drag(self, ev: MouseEvent) -> None:
        """Handle mouse drag for text selection."""
        if self._is_selecting:
            row, col = self._pos_from_point(ev.pos)
            self._selection_end = (row, col)
            self.update(True)

    def mouse_up(self, _: MouseEvent) -> None:
        """Handle mouse up to end selection."""
        self._is_selecting = False

    def input_key(self, ev: InputKeyEvent) -> None:
        """Handle Cmd+C / Ctrl+C for copy."""
        if ev.action is KeyAction.RELEASE:
            return

        # Handle Cmd+C / Ctrl+C (Copy)
        if ev.is_cmd_or_ctrl and ev.key is KeyCode.C:
            text = self.get_selected_text()
            if text:
                App.get().set_clipboard_text(text)
            return

        # Handle Cmd+A / Ctrl+A (Select All)
        if ev.is_cmd_or_ctrl and ev.key is KeyCode.A:
            self.select_all()
            self.update(True)
            return

    def _draw_selection_highlight(self, p: Painter, lines: list[str]) -> None:
        """Draw selection highlight rectangles."""
        range_result = self.get_selection_range()
        if range_result is None:
            return

        (start_row, start_col), (end_row, end_col) = range_result
        padding = self._padding
        font_size = self._font_size
        line_spacing = self._line_spacing

        p.save()
        # Apply text style first for accurate text measurement
        p.style(self._text_style)

        for line_idx, text in enumerate(lines):
            if line_idx < start_row or line_idx > end_row:
                continue

            # Determine selection range for this line
            if line_idx == start_row:
                sel_start = start_col
            else:
                sel_start = 0

            if line_idx == end_row:
                sel_end = end_col
            else:
                sel_end = len(text)

            if sel_start >= sel_end:
                continue

            # Calculate pixel positions using text style (same 0.1 offset as text drawing)
            y = padding + line_idx * (font_size + line_spacing)
            x_start = padding + 0.1 + p.measure_text(text[:sel_start])
            x_end = padding + 0.1 + p.measure_text(text[:sel_end])

            # Switch to selection style for drawing
            p.style(MultilineText._selection_style)

            # Draw selection rectangle
            selection_rect = Rect(
                origin=Point(x=x_start, y=y),
                size=Size(width=x_end - x_start, height=font_size),
            )
            p.fill_rect(selection_rect)

            # Restore text style for next iteration's measurement
            p.style(self._text_style)

        p.restore()

    def redraw(self, p: Painter, _: bool) -> None:
        padding = self._padding
        line_spacing = self._line_spacing

        p.style(self._rect_style)
        rect = Rect(origin=Point(x=0, y=0), size=self.get_size())
        p.fill_rect(rect)
        p.stroke_rect(rect)

        # Cache lines for selection handling
        lines = list(self._get_lines(p))
        self._last_lines = lines

        # Set text style BEFORE building character position cache
        # This ensures measure_text uses the correct font
        p.style(self._text_style)

        # Build character position cache for accurate click detection
        self._char_positions_cache = []
        for text in lines:
            positions = [0.0]  # Position before first character
            for i in range(len(text)):
                positions.append(p.measure_text(text[: i + 1]))
            self._char_positions_cache.append(positions)

        # Draw selection highlight before text
        if self.has_selection():
            self._draw_selection_highlight(p, lines)
        h = self._text_style.font.size
        y = h + padding
        for line in lines:
            p.fill_text(line, Point(x=padding + 0.1, y=y), None)
            y += h + line_spacing

    def _get_lines(self, p: Painter) -> Generator[str, None, None]:
        state: SimpleValue[str] = cast(SimpleValue[str], self._state)
        text = state.value()

        if self._size.width == 0:
            yield from []

        if self._wrap and self._width_policy is not SizePolicy.CONTENT:
            # for now, support only languages like English.
            # later a little, I will add other languages support.
            line_width = self._size.width - (self._padding + self._border_width) * 2
            for line in text.splitlines():
                retval_words = []
                words_width = 0
                for word in re.split(r"(?<=\s)", line):
                    word_width = p.measure_text(word)
                    words_width += word_width
                    if words_width > line_width:
                        yield "".join(retval_words)
                        retval_words = [word]
                        words_width = word_width
                    else:
                        retval_words.append(word)
                yield "".join(retval_words)
        else:
            yield from text.splitlines()

    def measure(self, p: Painter) -> Size:
        padding = self._padding
        border_width = self._border_width
        line_spacing = self._line_spacing

        w, h = 0, 0
        p.save()
        p.style(self._text_style)
        lines = list(self._get_lines(p))
        w = max(p.measure_text(line) for line in lines) + (padding + border_width) * 2
        h = (
            self._text_style.font.size * len(lines)
            + line_spacing * (len(lines) - 1)
            + padding * 2
            + border_width * 2
        )
        p.restore()
        return Size(width=w, height=h)
