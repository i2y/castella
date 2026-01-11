from typing import Callable, Self, cast

from castella.core import (
    AppearanceState,
    CaretDrawable,
    FillStyle,
    FontSizePolicy,
    IMEPreeditEvent,
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
    SCROLL_BAR_SIZE,
    Size,
    SizePolicy,
    StrokeStyle,
    Style,
    WheelEvent,
    Widget,
    get_theme,
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
        # Scroll state (persists across widget re-creation)
        self._scroll_y: int = 0
        self._manual_scroll: bool = False
        self._cursor_set_by_click: bool = False  # Flag to prevent cursor reset
        # Selection state
        self._selection_start: tuple[int, int] | None = None  # (row, col)
        self._selection_end: tuple[int, int] | None = None  # (row, col)
        self._is_selecting: bool = False
        # IME preedit state
        self._preedit_text: str = ""
        self._preedit_cursor: int = 0

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
        # Only set cursor to end if not set by a click
        if not self._cursor_set_by_click:
            self._row = len(self._lines) - 1
            self._col = len(self._lines[-1])
        self._cursor_set_by_click = False  # Reset flag
        self.notify()

    def finish_editing(self) -> None:
        """Exit editing mode."""
        if not self._editing:
            return
        self._editing = False
        self.notify()

    def set_preedit(self, text: str, cursor: int) -> None:
        """Set IME preedit (composition) text."""
        self._preedit_text = text
        self._preedit_cursor = cursor
        self.notify()

    def clear_preedit(self) -> None:
        """Clear IME preedit text."""
        self._preedit_text = ""
        self._preedit_cursor = 0
        self.notify()

    def get_preedit(self) -> tuple[str, int]:
        """Get current preedit text and cursor position."""
        return (self._preedit_text, self._preedit_cursor)

    def has_preedit(self) -> bool:
        """Check if there is active preedit text."""
        return bool(self._preedit_text)

    def insert(self, char: str) -> None:
        """Insert character at cursor position."""
        if not self._editing:
            return
        line = self._lines[self._row]
        self._lines[self._row] = line[: self._col] + char + line[self._col :]
        self._col += len(char)
        self._target_col = None
        # Don't call notify() - widget handles redraw, on_change handles external updates

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
        # Don't call notify() - widget handles redraw

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
        # Don't call notify() - widget handles redraw

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
        # Don't call notify() - widget handles redraw

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
        # Don't call notify() - widget handles redraw

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
        # Don't call notify() - widget handles redraw

    def move_up(self) -> None:
        """Move cursor up one line."""
        if not self._editing or self._row == 0:
            return
        if self._target_col is None:
            self._target_col = self._col
        self._row -= 1
        self._col = min(self._target_col, len(self._lines[self._row]))
        # Don't call notify() - widget handles redraw

    def move_down(self) -> None:
        """Move cursor down one line."""
        if not self._editing or self._row >= len(self._lines) - 1:
            return
        if self._target_col is None:
            self._target_col = self._col
        self._row += 1
        self._col = min(self._target_col, len(self._lines[self._row]))
        # Don't call notify() - widget handles redraw

    # Selection methods
    def has_selection(self) -> bool:
        """Check if there is an active selection."""
        return (
            self._selection_start is not None
            and self._selection_end is not None
            and self._selection_start != self._selection_end
        )

    def start_selection(self, row: int, col: int) -> None:
        """Start a new selection at the given position."""
        self._selection_start = (row, col)
        self._selection_end = (row, col)
        self._is_selecting = True

    def update_selection(self, row: int, col: int) -> None:
        """Update the selection endpoint."""
        if self._is_selecting:
            self._selection_end = (row, col)

    def end_selection(self) -> None:
        """Finish selection (mouse up)."""
        self._is_selecting = False

    def clear_selection(self) -> None:
        """Clear any active selection."""
        self._selection_start = None
        self._selection_end = None
        self._is_selecting = False

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
        if range_result is None:
            return ""
        (start_row, start_col), (end_row, end_col) = range_result

        if start_row == end_row:
            return self._lines[start_row][start_col:end_col]

        result = [self._lines[start_row][start_col:]]
        for row in range(start_row + 1, end_row):
            result.append(self._lines[row])
        result.append(self._lines[end_row][:end_col])
        return "\n".join(result)

    def delete_selection(self) -> str:
        """Delete selected text and return it. Returns empty string if no selection."""
        text = self.get_selected_text()
        if not text:
            return ""

        range_result = self.get_selection_range()
        assert range_result is not None
        (start_row, start_col), (end_row, end_col) = range_result

        if start_row == end_row:
            # Single line deletion
            line = self._lines[start_row]
            self._lines[start_row] = line[:start_col] + line[end_col:]
        else:
            # Multi-line deletion
            first_line = self._lines[start_row][:start_col]
            last_line = self._lines[end_row][end_col:]
            self._lines[start_row] = first_line + last_line
            del self._lines[start_row + 1 : end_row + 1]

        # Move cursor to selection start
        self._row = start_row
        self._col = start_col
        self.clear_selection()
        return text

    def select_all(self) -> None:
        """Select all text."""
        if len(self._lines) == 0:
            return
        self._selection_start = (0, 0)
        last_row = len(self._lines) - 1
        self._selection_end = (last_row, len(self._lines[last_row]))
        self._is_selecting = False


class MultilineInput(Widget):
    """Multi-line text input widget with optional word wrapping."""

    # Scrollbar styles
    _scrollbar_widget_style = get_theme().scrollbar
    _scrollbox_widget_style = get_theme().scrollbox
    _scrollbar_style = Style(
        fill=FillStyle(color=_scrollbar_widget_style.bg_color),
        stroke=StrokeStyle(color=_scrollbar_widget_style.border_color),
    )
    _scrollbox_style = Style(fill=FillStyle(color=_scrollbox_widget_style.bg_color))
    # Selection highlight style
    _selection_style = Style(fill=FillStyle(color=get_theme().colors.bg_selected))

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
        self._content_height: float = 0  # Total content height (calculated in redraw)
        self._scroll_box_y: Rect | None = None  # Scrollbar thumb rect
        self._under_dragging_y = False
        self._last_drag_pos: Point | None = None
        self._last_display_lines: list[tuple[int, str, int]] | None = (
            None  # For click handling
        )
        # Cache for accurate character position calculation
        # List of (cumulative_widths) for each display line
        # cumulative_widths[i] = width from start of line to character i
        self._char_positions_cache: list[list[float]] | None = None
        # Note: scroll_y and manual_scroll are stored in state to persist across re-renders

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

        # Get preedit info
        preedit_text, _ = state.get_preedit()
        cursor_row, cursor_col = state.get_cursor_pos()

        if not self._wrap or line_width <= 0:
            for row_idx in range(state.line_count()):
                line = state.get_line(row_idx)
                # Insert preedit at cursor position
                if preedit_text and row_idx == cursor_row:
                    line = line[:cursor_col] + preedit_text + line[cursor_col:]
                display_lines.append((row_idx, line, 0))
            return display_lines

        for row_idx in range(state.line_count()):
            line = state.get_line(row_idx)
            # Insert preedit at cursor position
            if preedit_text and row_idx == cursor_row:
                line = line[:cursor_col] + preedit_text + line[cursor_col:]

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

        # Adjust cursor column for preedit text
        preedit_text, preedit_cursor = state.get_preedit()
        display_cursor_col = cursor_col
        if preedit_text:
            # Position cursor within the preedit text
            display_cursor_col = cursor_col + preedit_cursor

        for display_idx, (logical_row, text, start_col) in enumerate(display_lines):
            if logical_row != cursor_row:
                continue

            end_col = start_col + len(text)
            if start_col <= display_cursor_col <= end_col:
                text_before = text[: display_cursor_col - start_col]
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
        border_width = self._border_width

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

        p.style(self._text_style)
        cap_height = p.get_font_metrics().cap_height

        # Calculate line width (account for scrollbar if needed later)
        scrollbar_width = SCROLL_BAR_SIZE
        line_width = size.width - (padding + border_width) * 2 - scrollbar_width
        display_lines = self._get_wrapped_lines(p, line_width)

        # Calculate total content height
        num_lines = len(display_lines)
        self._content_height = (
            font_size * num_lines + line_spacing * max(0, num_lines - 1) + padding * 2
        )

        # Calculate visible area height
        visible_height = size.height - border_width * 2

        # Determine if scrollbar is needed
        needs_scrollbar = self._content_height > size.height

        # Recalculate line width without scrollbar if not needed
        if not needs_scrollbar:
            line_width = size.width - (padding + border_width) * 2
            display_lines = self._get_wrapped_lines(p, line_width)
            num_lines = len(display_lines)
            self._content_height = (
                font_size * num_lines
                + line_spacing * max(0, num_lines - 1)
                + padding * 2
            )
            self._scroll_box_y = None
            scrollbar_width = 0

        # Store display_lines for click handling
        self._last_display_lines = display_lines

        # Build character position cache for accurate click detection
        self._char_positions_cache = []
        for _, text, _ in display_lines:
            positions = [0.0]  # Position before first character
            for i in range(len(text)):
                positions.append(p.measure_text(text[: i + 1]))
            self._char_positions_cache.append(positions)

        # Auto-scroll to keep cursor visible when editing (but not if user manually scrolled)
        if state.is_in_editing() and not state._manual_scroll:
            display_idx, _ = self._find_cursor_display_pos(p, display_lines)
            cursor_top = padding + display_idx * (font_size + line_spacing)
            cursor_bottom = cursor_top + font_size

            # Scroll up if cursor is above visible area
            if cursor_top - state._scroll_y < 0:
                state._scroll_y = max(0, cursor_top)
            # Scroll down if cursor is below visible area
            elif cursor_bottom - state._scroll_y > visible_height:
                state._scroll_y = int(cursor_bottom - visible_height)

        # Clamp scroll position
        max_scroll = max(0, int(self._content_height - size.height))
        state._scroll_y = max(0, min(state._scroll_y, max_scroll))

        # Clip content area and apply scroll offset
        content_width = max(0, size.width - border_width * 2 - scrollbar_width)
        p.save()
        p.clip(
            Rect(
                origin=Point(x=border_width, y=border_width),
                size=Size(width=content_width, height=visible_height),
            )
        )
        p.translate(Point(x=0, y=-state._scroll_y))

        # Draw selection highlight before text
        if state.has_selection():
            self._draw_selection_highlight(p, display_lines)

        p.style(self._text_style)
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

        p.restore()

        # Draw scrollbar if needed
        if needs_scrollbar:
            p.save()
            # Scrollbar track
            p.style(MultilineInput._scrollbar_style)
            scrollbar_x = size.width - scrollbar_width - border_width
            p.fill_rect(
                Rect(
                    origin=Point(x=scrollbar_x, y=border_width),
                    size=Size(width=scrollbar_width, height=visible_height),
                )
            )
            # Scrollbar thumb
            p.style(MultilineInput._scrollbox_style)
            if self._content_height > 0:
                thumb_height = max(
                    20, (visible_height / self._content_height) * visible_height
                )
                scroll_range = self._content_height - size.height
                if scroll_range > 0:
                    thumb_y = (state._scroll_y / scroll_range) * (
                        visible_height - thumb_height
                    )
                else:
                    thumb_y = 0
                scroll_box = Rect(
                    origin=Point(x=scrollbar_x, y=border_width + thumb_y),
                    size=Size(width=scrollbar_width, height=thumb_height),
                )
                self._scroll_box_y = scroll_box
                p.fill_rect(scroll_box)
            p.restore()

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
        from castella.core import App

        state = cast(MultilineInputState, self._state)
        # Only start editing if not already (mouse_down may have started it)
        if not state.is_in_editing():
            state.start_editing()

        # Show software keyboard on mobile platforms
        # Pass current text so the hidden input field stays in sync
        app = App.get()
        if app is not None:
            app._frame.show_keyboard(state.raw_value())

    def unfocused(self) -> None:
        from castella.core import App

        state = cast(MultilineInputState, self._state)
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
        state = cast(MultilineInputState, self._state)
        # Clear any preedit when text is committed
        if state.has_preedit():
            state.clear_preedit()
        # Delete selection if any before inserting
        if state.has_selection():
            state.delete_selection()
        state.insert(ev.char)
        state._manual_scroll = False  # Reset manual scroll on input
        self._callback(state.raw_value())
        # Request redraw without triggering component re-render
        self.update(True)

    def ime_preedit(self, ev: IMEPreeditEvent) -> None:
        """Handle IME preedit (composition) event."""
        state = cast(MultilineInputState, self._state)
        if ev.text:
            state.set_preedit(ev.text, ev.cursor_pos)
        else:
            state.clear_preedit()

    def input_key(self, ev: InputKeyEvent) -> None:
        if ev.action is KeyAction.RELEASE:
            return

        state = cast(MultilineInputState, self._state)

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

        state._manual_scroll = False  # Reset manual scroll on any key input

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
            self.update(True)
            return

        # Clear selection on navigation keys
        if ev.key in (KeyCode.LEFT, KeyCode.RIGHT, KeyCode.UP, KeyCode.DOWN):
            state.clear_selection()

        # Delete selection on content-modifying keys
        if ev.key in (KeyCode.BACKSPACE, KeyCode.DELETE) and state.has_selection():
            state.delete_selection()
            self._callback(state.raw_value())
            self.update(True)
            return

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
            # Delete selection before inserting newline
            if state.has_selection():
                state.delete_selection()
            state.insert_newline()
            self._callback(state.raw_value())
        # Request redraw without triggering component re-render
        self.update(True)

    def _handle_copy(self) -> None:
        """Copy selected text to clipboard."""
        from castella.core import App

        state = cast(MultilineInputState, self._state)
        text = state.get_selected_text()
        if text:
            App.get().set_clipboard_text(text)

    def _handle_cut(self) -> None:
        """Cut selected text to clipboard."""
        from castella.core import App

        state = cast(MultilineInputState, self._state)
        text = state.delete_selection()
        if text:
            App.get().set_clipboard_text(text)
            self._callback(state.raw_value())
            self.update(True)

    def _handle_paste(self) -> None:
        """Paste text from clipboard."""
        from castella.core import App

        state = cast(MultilineInputState, self._state)
        text = App.get().get_clipboard_text()
        if text:
            # Delete selection if any
            if state.has_selection():
                state.delete_selection()
            # Insert pasted text (handle multi-line)
            for char in text:
                if char == "\n":
                    state.insert_newline()
                else:
                    state.insert(char)
            self._callback(state.raw_value())
            self.update(True)

    def on_change(self, callback: Callable[[str], None]) -> Self:
        """Register callback for text changes."""
        self._callback = callback
        return self

    def _draw_selection_highlight(
        self, p: Painter, display_lines: list[tuple[int, str, int]]
    ) -> None:
        """Draw selection highlight rectangles."""
        state = cast(MultilineInputState, self._state)
        range_result = state.get_selection_range()
        if range_result is None:
            return

        (start_row, start_col), (end_row, end_col) = range_result
        padding = self._padding
        font_size = self._font_size
        line_spacing = self._line_spacing

        p.save()
        # Apply text style first for accurate text measurement
        p.style(self._text_style)

        for display_idx, (logical_row, text, line_start_col) in enumerate(
            display_lines
        ):
            if logical_row < start_row or logical_row > end_row:
                continue

            line_end_col = line_start_col + len(text)

            # Determine selection range for this display line
            if logical_row == start_row:
                sel_start = max(start_col, line_start_col) - line_start_col
            else:
                sel_start = 0

            if logical_row == end_row:
                sel_end = min(end_col, line_end_col) - line_start_col
            else:
                sel_end = len(text)

            if sel_start >= sel_end:
                continue

            # Calculate pixel positions using text style (same 0.1 offset as text drawing)
            y = padding + display_idx * (font_size + line_spacing)
            x_start = padding + 0.1 + p.measure_text(text[:sel_start])
            x_end = padding + 0.1 + p.measure_text(text[:sel_end])

            # Switch to selection style for drawing
            p.style(MultilineInput._selection_style)

            # Draw selection rectangle
            selection_rect = Rect(
                origin=Point(x=x_start, y=y),
                size=Size(width=x_end - x_start, height=font_size),
            )
            p.fill_rect(selection_rect)

            # Restore text style for next iteration's measurement
            p.style(self._text_style)

        p.restore()

    def is_scrollable(self) -> bool:
        """Return True when widget can potentially scroll."""
        # Always return True so wheel events are received
        # Actual scrolling is handled in mouse_wheel based on content size
        return True

    def _pos_from_point(self, point: Point) -> tuple[int, int]:
        """Convert screen point to (row, col) position."""
        state = cast(MultilineInputState, self._state)
        padding = self._padding
        font_size = self._font_size
        line_spacing = self._line_spacing
        border_width = self._border_width

        # Account for scroll offset
        click_y = point.y + state._scroll_y - border_width

        # Find the display line index
        if click_y < padding:
            display_line_idx = 0
        else:
            display_line_idx = int((click_y - padding) / (font_size + line_spacing))

        display_lines = self._last_display_lines or []
        if not display_lines:
            return (0, 0)

        display_line_idx = max(0, min(display_line_idx, len(display_lines) - 1))
        logical_row, text, start_col = display_lines[display_line_idx]

        # Find column based on x position
        # Text is drawn at padding + 0.1, so account for that offset
        click_x = point.x - padding - 0.1
        if click_x <= 0:
            col = start_col
        else:
            # Use cached character positions if available
            if self._char_positions_cache is not None and display_line_idx < len(
                self._char_positions_cache
            ):
                positions = self._char_positions_cache[display_line_idx]
                # Binary search for the closest character position
                col = start_col
                for i in range(len(positions)):
                    if positions[i] > click_x:
                        # Check if click is closer to this char or previous
                        if i > 0 and (click_x - positions[i - 1]) < (
                            positions[i] - click_x
                        ):
                            col = start_col + i - 1
                        else:
                            col = start_col + i
                        break
                    col = start_col + i
            else:
                # Fallback to approximate calculation
                char_width = font_size * 0.5
                for i in range(len(text) + 1):
                    if i * char_width >= click_x:
                        col = start_col + max(0, i - 1)
                        break
                    col = start_col + i

        col = min(col, len(state.get_line(logical_row)))
        return (logical_row, col)

    def dispatch_to_scrollable(
        self, p: Point, is_direction_x: bool
    ) -> tuple["Widget | None", "Point | None"]:
        """Return self if this widget can handle scroll events at point p."""
        if not is_direction_x and self.contain(p):
            # Handle vertical scrolling
            return self, p
        return None, None

    def mouse_down(self, ev: MouseEvent) -> None:
        """Handle mouse down for scrollbar dragging or text selection."""
        # Check if click is on scrollbar
        if self._scroll_box_y is not None and self._scroll_box_y.contain(ev.pos):
            self._under_dragging_y = True
            self._last_drag_pos = ev.pos
            return

        # Click in text area - start selection and position cursor
        state = cast(MultilineInputState, self._state)
        # Start editing if not already (click to focus)
        if not state.is_in_editing():
            state._editing = True  # Start editing without resetting cursor

        # Mark that cursor will be set by click (prevents start_editing from resetting)
        state._cursor_set_by_click = True

        # Get position from click
        row, col = self._pos_from_point(ev.pos)

        # Clear previous selection and start new one
        state.clear_selection()
        state.start_selection(row, col)

        # Update cursor position
        state._row = row
        state._col = col
        state._target_col = None
        state._manual_scroll = False  # Allow auto-scroll to cursor

        # Redraw
        self._dirty = True
        if self._parent is not None:
            self.ask_parent_to_render(True)
        else:
            self.update(True)

    def mouse_up(self, _: MouseEvent) -> None:
        """Handle mouse up to stop scrollbar dragging or text selection."""
        state = cast(MultilineInputState, self._state)
        state.end_selection()
        self._under_dragging_y = False
        self._last_drag_pos = None

    def mouse_drag(self, ev: MouseEvent) -> None:
        """Handle mouse drag for scrollbar or text selection."""
        state = cast(MultilineInputState, self._state)

        # Check scrollbar drag first
        if self._under_dragging_y and self._last_drag_pos is not None:
            self._handle_scrollbar_drag(ev)
            return

        # Text selection drag
        if state._is_selecting:
            row, col = self._pos_from_point(ev.pos)
            state.update_selection(row, col)
            # Move cursor to selection end
            state._row = row
            state._col = col
            self.update(True)
            return

    def _handle_scrollbar_drag(self, ev: MouseEvent) -> None:
        """Handle scrollbar thumb dragging."""
        if self._last_drag_pos is None:
            return

        state = cast(MultilineInputState, self._state)
        delta_y = ev.pos.y - self._last_drag_pos.y
        self._last_drag_pos = ev.pos

        if delta_y == 0:
            return

        # Calculate scroll based on drag distance
        visible_height = self._size.height - self._border_width * 2
        scroll_range = self._content_height - self._size.height
        if scroll_range <= 0:
            return

        thumb_height = max(20, (visible_height / self._content_height) * visible_height)
        track_range = visible_height - thumb_height
        if track_range <= 0:
            return

        # Convert drag to scroll position
        scroll_delta = (delta_y / track_range) * scroll_range
        new_scroll = state._scroll_y + int(scroll_delta)
        new_scroll = max(0, min(new_scroll, int(scroll_range)))

        if new_scroll != state._scroll_y:
            state._scroll_y = new_scroll
            state._manual_scroll = True  # Mark as manual scroll
            self._dirty = True
            if self._parent is not None:
                self.ask_parent_to_render(True)
            else:
                self.update(True)

    def mouse_wheel(self, ev: WheelEvent) -> None:
        """Handle mouse wheel for vertical scrolling."""
        if ev.y_offset == 0:
            return

        state = cast(MultilineInputState, self._state)
        max_scroll = max(0, int(self._content_height - self._size.height))
        if max_scroll == 0:
            return

        # Scroll by wheel offset (negative y_offset means scroll down)
        new_scroll = state._scroll_y + int(ev.y_offset)
        new_scroll = max(0, min(new_scroll, max_scroll))

        if new_scroll != state._scroll_y:
            state._scroll_y = new_scroll
            state._manual_scroll = True  # Mark as manual scroll
            self._dirty = True
            if self._parent is not None:
                self.ask_parent_to_render(True)
            else:
                self.update(True)
