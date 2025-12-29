from typing import Callable, Self, cast

from castella.core import (
    AppearanceState,
    CaretDrawable,
    FillStyle,
    FontSizePolicy,
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
        self._last_display_lines: list[tuple[int, str, int]] | None = None  # For click handling
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
        border_width = self._border_width

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
            font_size * num_lines
            + line_spacing * max(0, num_lines - 1)
            + padding * 2
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
        p.clip(Rect(
            origin=Point(x=border_width, y=border_width),
            size=Size(width=content_width, height=visible_height)
        ))
        p.translate(Point(x=0, y=-state._scroll_y))

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
        state = cast(MultilineInputState, self._state)
        # Only start editing if not already (mouse_down may have started it)
        if not state.is_in_editing():
            state.start_editing()

    def unfocused(self) -> None:
        state = cast(MultilineInputState, self._state)
        state.finish_editing()

    def input_char(self, ev: InputCharEvent) -> None:
        state = cast(MultilineInputState, self._state)
        state.insert(ev.char)
        state._manual_scroll = False  # Reset manual scroll on input
        self._callback(state.raw_value())
        # Request redraw without triggering component re-render
        self.update(True)

    def input_key(self, ev: InputKeyEvent) -> None:
        if ev.action is KeyAction.RELEASE:
            return

        state = cast(MultilineInputState, self._state)
        state._manual_scroll = False  # Reset manual scroll on any key input

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
        # Request redraw without triggering component re-render
        self.update(True)

    def on_change(self, callback: Callable[[str], None]) -> Self:
        """Register callback for text changes."""
        self._callback = callback
        return self

    def is_scrollable(self) -> bool:
        """Return True when widget can potentially scroll."""
        # Always return True so wheel events are received
        # Actual scrolling is handled in mouse_wheel based on content size
        return True

    def dispatch_to_scrollable(
        self, p: Point, is_direction_x: bool
    ) -> tuple["Widget | None", "Point | None"]:
        """Return self if this widget can handle scroll events at point p."""
        if not is_direction_x and self.contain(p):
            # Handle vertical scrolling
            return self, p
        return None, None

    def mouse_down(self, ev: MouseEvent) -> None:
        """Handle mouse down for scrollbar dragging or cursor positioning."""
        # Check if click is on scrollbar
        if self._scroll_box_y is not None and self._scroll_box_y.contain(ev.pos):
            self._under_dragging_y = True
            self._last_drag_pos = ev.pos
            return

        # Click in text area - position cursor
        state = cast(MultilineInputState, self._state)
        # Start editing if not already (click to focus)
        if not state.is_in_editing():
            state._editing = True  # Start editing without resetting cursor

        # Calculate which display line was clicked
        padding = self._padding
        font_size = self._font_size
        line_spacing = self._line_spacing
        border_width = self._border_width

        # Account for scroll offset
        click_y = ev.pos.y + state._scroll_y - border_width

        # Find the display line index
        if click_y < padding:
            display_line_idx = 0
        else:
            display_line_idx = int((click_y - padding) / (font_size + line_spacing))

        # Mark that cursor will be set by click (prevents start_editing from resetting)
        state._cursor_set_by_click = True

        # Get display lines (need to recalculate here)
        # Store last calculated display_lines in state for click handling
        if not hasattr(self, '_last_display_lines') or self._last_display_lines is None:
            # Can't calculate exact position, but flag is set to prevent cursor reset
            self._dirty = True
            if self._parent is not None:
                self.ask_parent_to_render(True)
            return

        display_lines = self._last_display_lines
        display_line_idx = max(0, min(display_line_idx, len(display_lines) - 1))

        if display_line_idx < len(display_lines):
            logical_row, text, start_col = display_lines[display_line_idx]

            # Find column based on x position
            click_x = ev.pos.x - padding - border_width
            if click_x <= 0:
                col = start_col
            else:
                # Find character position
                col = start_col
                for i in range(len(text) + 1):
                    # We need a painter to measure, but we don't have one here
                    # Use approximate calculation based on average char width
                    char_width = font_size * 0.5  # Approximate (adjusted for typical fonts)
                    if i * char_width >= click_x:
                        col = start_col + max(0, i - 1)
                        break
                    col = start_col + i

            # Update cursor position
            state._row = logical_row
            state._col = min(col, len(state.get_line(logical_row)))
            state._target_col = None
            state._manual_scroll = False  # Allow auto-scroll to cursor
            # Don't call state.notify() - just redraw the widget
            self._dirty = True
            if self._parent is not None:
                self.ask_parent_to_render(True)
            else:
                self.update(True)

    def mouse_up(self, _: MouseEvent) -> None:
        """Handle mouse up to stop scrollbar dragging."""
        self._under_dragging_y = False
        self._last_drag_pos = None

    def mouse_drag(self, ev: MouseEvent) -> None:
        """Handle mouse drag for scrollbar."""
        if not self._under_dragging_y or self._last_drag_pos is None:
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

        thumb_height = max(
            20, (visible_height / self._content_height) * visible_height
        )
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
