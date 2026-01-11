"""Markdown rendering widget for Castella."""

import webbrowser
from typing import Callable, Self

from castella.core import (
    AppearanceState,
    Kind,
    MouseEvent,
    ObservableBase,
    Painter,
    Point,
    Rect,
    ScrollState,
    SimpleValue,
    Size,
    SizePolicy,
    State,
    Widget,
)
from castella.markdown.code_text_renderer import CodeTextRenderer
from castella.markdown.math_renderer import MathRenderer
from castella.markdown.models import DocumentNode
from castella.markdown.parser import MarkdownParser
from castella.markdown.renderer import MarkdownRenderer
from castella.markdown.theme import MarkdownTheme


class MarkdownState(ObservableBase):
    """Observable state for Markdown content."""

    def __init__(self, content: str):
        super().__init__()
        self._content = content
        self._parsed_ast: DocumentNode | None = None

    def value(self) -> str:
        """Get the markdown content."""
        return self._content

    def set(self, content: str) -> None:
        """Set new markdown content."""
        self._content = content
        self._parsed_ast = None
        self.notify()


class Markdown(Widget):
    """Full-featured Markdown renderer widget.

    Supports:
    - Headings (H1-H6)
    - Bold, italic, strikethrough
    - Lists (ordered, unordered, task lists)
    - Code blocks with syntax highlighting
    - Inline code
    - Links (clickable)
    - Tables (GFM-style)
    - Images (placeholder)
    - Blockquotes
    - Math expressions (LaTeX)
    - Horizontal rules

    Example:
        md = Markdown('''
        # Hello World

        This is **bold** and *italic* text.

        ```python
        def hello():
            print("Hello!")
        ```
        ''')
    """

    def __init__(
        self,
        content: str | MarkdownState | SimpleValue[str],
        *,
        base_font_size: int = 14,
        code_theme: str = "monokai",
        enable_math: bool = True,
        enable_syntax_highlight: bool = True,
        enable_admonitions: bool = True,
        enable_mermaid: bool = True,
        enable_deflist: bool = True,
        enable_toc: bool = True,
        enable_emoji: bool = True,
        link_color: str | None = None,
        on_link_click: Callable[[str], None] | None = None,
        scroll_state: ScrollState | None = None,
        padding: int = 8,
        kind: Kind = Kind.NORMAL,
    ):
        if isinstance(content, MarkdownState):
            state = content
        elif isinstance(content, SimpleValue):
            state = content
        else:
            state = MarkdownState(content)

        self._kind = kind
        self._padding = padding
        self._base_font_size = base_font_size
        self._code_theme = code_theme
        self._enable_math = enable_math
        self._enable_syntax_highlight = enable_syntax_highlight
        self._enable_admonitions = enable_admonitions
        self._enable_mermaid = enable_mermaid
        self._enable_deflist = enable_deflist
        self._enable_toc = enable_toc
        self._enable_emoji = enable_emoji
        self._link_color = link_color
        self._link_callback = on_link_click
        self._scroll_state = scroll_state
        self._hovered_href: str | None = None  # Track hovered link for visual feedback

        self._parser = MarkdownParser(
            enable_math=enable_math,
            enable_admonitions=enable_admonitions,
            enable_mermaid=enable_mermaid,
            enable_deflist=enable_deflist,
            enable_toc=enable_toc,
        )
        self._theme: MarkdownTheme | None = None
        self._renderer: MarkdownRenderer | None = None
        self._cached_ast: DocumentNode | None = None
        self._cached_content: str = ""

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

        self._theme = MarkdownTheme.from_castella_theme()
        self._theme = MarkdownTheme(
            text_color=self._theme.text_color,
            heading_color=self._theme.heading_color,
            link_color=self._link_color or self._theme.link_color,
            code_color=self._theme.code_color,
            bg_color=self._theme.bg_color,
            code_bg_color=self._theme.code_bg_color,
            blockquote_bg_color=self._theme.blockquote_bg_color,
            table_header_bg=self._theme.table_header_bg,
            table_cell_bg=self._theme.table_cell_bg,
            text_font=self._theme.text_font,
            code_font=self._theme.code_font,
            base_font_size=self._base_font_size,
            h1_size=int(self._base_font_size * 2.2),
            h2_size=int(self._base_font_size * 1.9),
            h3_size=int(self._base_font_size * 1.6),
            h4_size=int(self._base_font_size * 1.3),
            h5_size=int(self._base_font_size * 1.1),
            h6_size=self._base_font_size,
            code_pygments_style=self._code_theme,
            paragraph_spacing=self._theme.paragraph_spacing,
            block_spacing=self._theme.block_spacing,
            list_indent=self._theme.list_indent,
            blockquote_indent=self._theme.blockquote_indent,
            table_row_height=self._theme.table_row_height,
            is_dark=self._theme.is_dark,
        )

        code_renderer = None
        if self._enable_syntax_highlight:
            code_renderer = CodeTextRenderer(
                style=self._code_theme,
            )

        math_renderer = None
        if self._enable_math:
            math_renderer = MathRenderer(
                font_size=self._base_font_size,
                text_color=self._theme.text_color,
            )

        self._renderer = MarkdownRenderer(
            theme=self._theme,
            code_renderer=code_renderer,
            math_renderer=math_renderer,
            on_link_click=self._link_callback,
        )

    def _get_content(self) -> str:
        """Get current content from state."""
        if isinstance(self._state, MarkdownState):
            content = self._state.value()
        elif isinstance(self._state, SimpleValue):
            content = self._state.value()
        else:
            content = ""

        # Apply emoji shortcode conversion if enabled
        if self._enable_emoji and content:
            from castella.markdown.emoji_map import convert_emoji_shortcodes

            content = convert_emoji_shortcodes(content)

        return content

    def _get_ast(self) -> DocumentNode:
        """Get or parse AST."""
        content = self._get_content()

        if self._cached_ast is not None and self._cached_content == content:
            return self._cached_ast

        self._cached_ast = self._parser.parse(content)
        self._cached_content = content
        return self._cached_ast

    def redraw(self, p: Painter, _: bool) -> None:
        if self._renderer is None or self._theme is None:
            return

        p.style(self._rect_style)
        rect = Rect(origin=Point(x=0, y=0), size=self.get_size())
        p.fill_rect(rect)

        ast = self._get_ast()
        size = self.get_size()
        self._renderer.render(
            p, ast, size.width, size.height, float(self._padding), self._hovered_href
        )

    def measure(self, p: Painter) -> Size:
        if self._renderer is None or self._theme is None:
            return Size(width=100, height=100)

        ast = self._get_ast()

        width = self._size.width if self._size.width > 0 else 400
        height = self._renderer.measure_height(p, ast, width, float(self._padding))

        return Size(width=width, height=height)

    def cursor_pos(self, ev: MouseEvent) -> None:
        """Handle cursor position for link hover effects."""
        if self._renderer is None:
            return

        # ev.pos is already in content coordinates (parent Column adds scroll offset)
        # ClickRegions are registered in content coordinates, so use ev.pos directly
        href = self._renderer.get_link_at(ev.pos)
        if href != self._hovered_href:
            self._hovered_href = href
            # Trigger redraw to show/hide hover effect
            self.update(True)

    def mouse_up(self, ev: MouseEvent) -> None:
        """Handle link clicks."""
        if self._renderer is None:
            return

        # ev.pos is already in content coordinates (parent Column adds scroll offset)
        href = self._renderer.get_link_at(ev.pos)
        if not href:
            return

        if href.startswith("#"):
            # Internal link - scroll to heading
            heading_id = href[1:]  # Remove '#' prefix
            self._scroll_to_heading(heading_id)
        elif self._link_callback:
            # External link with custom callback
            self._link_callback(href)
        else:
            # Default: open external link in browser
            if href.startswith(("http://", "https://", "mailto:")):
                webbrowser.open(href)

    def _scroll_to_heading(self, heading_id: str) -> None:
        """Scroll to the heading with the given ID."""
        if self._scroll_state is None or self._renderer is None:
            return

        target_y = self._renderer.get_heading_position(heading_id)
        if target_y is not None:
            self._scroll_state.y = int(target_y)
            # Trigger redraw to reflect the scroll change
            self.update(True)

    def on_link_click(self, callback: Callable[[str], None]) -> Self:
        """Register callback for link clicks."""
        self._link_callback = callback
        if self._renderer:
            self._renderer._on_link_click = callback
        return self

    def scroll_state(self, state: ScrollState) -> Self:
        """Set scroll state for TOC navigation."""
        self._scroll_state = state
        return self

    def set_content(self, content: str) -> None:
        """Update the markdown content."""
        if isinstance(self._state, MarkdownState):
            self._state.set(content)
        elif isinstance(self._state, State):
            self._state.set(content)


__all__ = [
    "Markdown",
    "MarkdownState",
    "MarkdownTheme",
    "MarkdownParser",
    "MarkdownRenderer",
    "CodeTextRenderer",
    "MathRenderer",
]
