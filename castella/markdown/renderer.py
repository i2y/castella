"""Markdown AST renderer."""

from dataclasses import dataclass
from typing import Callable

import numpy as np

from castella.core import (
    FillStyle,
    Painter,
    Point,
    Rect,
    Size,
    Style,
    StrokeStyle,
)
from castella.models.font import Font, FontSlant, FontWeight
from castella.markdown.code_highlighter import CodeHighlighter
from castella.markdown.math_renderer import MathRenderer
from castella.markdown.models import (
    BlockquoteNode,
    CodeBlockNode,
    CodeInlineNode,
    DocumentNode,
    EmphasisNode,
    HardBreakNode,
    HeadingNode,
    HorizontalRuleNode,
    ImageNode,
    LinkNode,
    ListItemNode,
    ListNode,
    MarkdownNode,
    MathBlockNode,
    MathInlineNode,
    ParagraphNode,
    SoftBreakNode,
    StrikethroughNode,
    StrongNode,
    TableCellNode,
    TableNode,
    TableRowNode,
    TaskItemNode,
    TextNode,
)
from castella.markdown.theme import MarkdownTheme


@dataclass
class TextSegment:
    """A segment of styled text."""

    text: str
    bold: bool = False
    italic: bool = False
    strikethrough: bool = False
    code: bool = False
    href: str | None = None

    def get_font(self, theme: MarkdownTheme, size: int | None = None) -> Font:
        """Get font for this segment."""
        return Font(
            family=theme.code_font if self.code else theme.text_font,
            size=size or theme.base_font_size,
            weight=FontWeight.BOLD if self.bold else FontWeight.NORMAL,
            slant=FontSlant.ITALIC if self.italic else FontSlant.UPRIGHT,
        )

    def get_color(self, theme: MarkdownTheme) -> str:
        """Get text color for this segment."""
        if self.href:
            return theme.link_color
        if self.code:
            return theme.code_color
        return theme.text_color


@dataclass
class RenderContext:
    """Context for rendering."""

    bold: bool = False
    italic: bool = False
    strikethrough: bool = False
    code: bool = False
    href: str | None = None


@dataclass
class ClickRegion:
    """A clickable region."""

    rect: Rect
    href: str


class MarkdownRenderer:
    """Renders Markdown AST to Castella drawing commands."""

    def __init__(
        self,
        theme: MarkdownTheme,
        code_highlighter: CodeHighlighter | None = None,
        math_renderer: MathRenderer | None = None,
        on_link_click: Callable[[str], None] | None = None,
    ):
        self._theme = theme
        self._code_highlighter = code_highlighter or CodeHighlighter(
            style=theme.code_pygments_style
        )
        self._math_renderer = math_renderer or MathRenderer(
            font_size=theme.base_font_size,
            text_color=theme.text_color,
        )
        self._on_link_click = on_link_click

        self._cursor_x: float = 0.0
        self._cursor_y: float = 0.0
        self._line_height: float = 0.0
        self._link_regions: list[ClickRegion] = []
        self._list_depth: int = 0
        self._list_counters: list[int] = []

    def render(
        self,
        painter: Painter,
        ast: DocumentNode,
        width: float,
        height: float,
        padding: float = 8.0,
    ) -> float:
        """Render AST and return total content height.

        Args:
            painter: Painter to render with
            ast: Document AST to render
            width: Available width
            height: Available height
            padding: Padding around content

        Returns:
            Total height of rendered content
        """
        self._cursor_x = padding
        self._cursor_y = padding
        self._line_height = self._theme.base_font_size * 1.5
        self._link_regions.clear()
        self._list_depth = 0
        self._list_counters = []

        content_width = max(1.0, width - padding * 2)

        for node in ast.children:
            self._render_node(painter, node, content_width)

        return self._cursor_y + padding

    def _render_node(self, p: Painter, node: MarkdownNode, width: float) -> None:
        """Render a single AST node."""
        if isinstance(node, HeadingNode):
            self._render_heading(p, node, width)
        elif isinstance(node, ParagraphNode):
            self._render_paragraph(p, node, width)
        elif isinstance(node, CodeBlockNode):
            self._render_code_block(p, node, width)
        elif isinstance(node, BlockquoteNode):
            self._render_blockquote(p, node, width)
        elif isinstance(node, ListNode):
            self._render_list(p, node, width)
        elif isinstance(node, TableNode):
            self._render_table(p, node, width)
        elif isinstance(node, HorizontalRuleNode):
            self._render_hr(p, width)
        elif isinstance(node, MathBlockNode):
            self._render_math_block(p, node, width)
        elif isinstance(node, ImageNode):
            self._render_image(p, node, width)

    def _render_heading(self, p: Painter, node: HeadingNode, width: float) -> None:
        """Render a heading."""
        font_size = self._theme.get_heading_size(node.level)

        self._cursor_y += self._theme.block_spacing

        segments = self._collect_segments(node.children, RenderContext())
        text = "".join(s.text for s in segments)

        style = Style(
            fill=FillStyle(color=self._theme.heading_color),
            font=Font(
                family=self._theme.text_font,
                size=font_size,
                weight=FontWeight.BOLD,
            ),
        )
        p.style(style)
        p.fill_text(text, Point(x=self._cursor_x, y=self._cursor_y + font_size), None)

        self._cursor_y += font_size * 1.5

    def _render_paragraph(self, p: Painter, node: ParagraphNode, width: float) -> None:
        """Render a paragraph with word wrapping."""
        segments = self._collect_segments(node.children, RenderContext())

        x = self._cursor_x + self._list_depth * self._theme.list_indent
        available_width = width - self._list_depth * self._theme.list_indent
        line_height = self._theme.base_font_size * 1.5

        for segment in segments:
            if isinstance(segment, np.ndarray):
                if x > self._cursor_x + self._list_depth * self._theme.list_indent:
                    self._cursor_y += line_height
                    x = self._cursor_x + self._list_depth * self._theme.list_indent

                img_height = segment.shape[0]
                img_width = segment.shape[1]

                if hasattr(p, "draw_np_array_as_an_image_rect"):
                    arr = np.ascontiguousarray(segment)
                    p.draw_np_array_as_an_image_rect(
                        arr,
                        Rect(
                            origin=Point(x=x, y=self._cursor_y),
                            size=Size(width=img_width, height=img_height),
                        ),
                    )
                self._cursor_y += img_height
                continue

            if not isinstance(segment, TextSegment):
                continue

            font = segment.get_font(self._theme)
            color = segment.get_color(self._theme)

            style = Style(
                fill=FillStyle(color=color),
                font=font,
            )
            p.style(style)

            words = segment.text.split(" ")
            for i, word in enumerate(words):
                if i > 0:
                    word = " " + word

                word_width = p.measure_text(word)

                if (
                    x + word_width > self._cursor_x + available_width
                    and x > self._cursor_x + self._list_depth * self._theme.list_indent
                ):
                    self._cursor_y += line_height
                    x = self._cursor_x + self._list_depth * self._theme.list_indent
                    word = word.lstrip()
                    word_width = p.measure_text(word)

                p.fill_text(
                    word,
                    Point(x=x, y=self._cursor_y + self._theme.base_font_size),
                    None,
                )

                if segment.strikethrough:
                    strike_y = self._cursor_y + self._theme.base_font_size * 0.4
                    p.fill_rect(
                        Rect(
                            origin=Point(x=x, y=strike_y),
                            size=Size(width=word_width, height=1),
                        )
                    )

                if segment.href:
                    self._link_regions.append(
                        ClickRegion(
                            rect=Rect(
                                origin=Point(x=x, y=self._cursor_y),
                                size=Size(width=word_width, height=line_height),
                            ),
                            href=segment.href,
                        )
                    )

                x += word_width

        self._cursor_y += line_height + self._theme.paragraph_spacing

    def _render_code_block(self, p: Painter, node: CodeBlockNode, width: float) -> None:
        """Render a fenced code block."""
        bg_style = Style(fill=FillStyle(color=self._theme.code_bg_color))
        p.style(bg_style)

        code_array = self._code_highlighter.highlight(
            node.content,
            language=node.language,
            width=int(width),
        )

        img_height = code_array.shape[0]
        img_width = min(code_array.shape[1], max(1, int(width)))
        rect_width = max(1.0, width)

        p.fill_rect(
            Rect(
                origin=Point(x=self._cursor_x, y=self._cursor_y),
                size=Size(width=rect_width, height=img_height + 16),
            )
        )

        if hasattr(p, "draw_np_array_as_an_image_rect"):
            arr = np.ascontiguousarray(code_array)
            p.draw_np_array_as_an_image_rect(
                arr,
                Rect(
                    origin=Point(x=self._cursor_x + 8, y=self._cursor_y + 8),
                    size=Size(width=img_width, height=img_height),
                ),
            )

        self._cursor_y += img_height + 16 + self._theme.block_spacing

    def _render_blockquote(
        self, p: Painter, node: BlockquoteNode, width: float
    ) -> None:
        """Render a blockquote."""
        indent = self._theme.blockquote_indent
        bar_width = 4

        start_y = self._cursor_y

        self._cursor_x += indent
        for child in node.children:
            self._render_node(p, child, width - indent)
        self._cursor_x -= indent

        bg_style = Style(fill=FillStyle(color=self._theme.blockquote_bg_color))
        p.style(bg_style)
        p.fill_rect(
            Rect(
                origin=Point(x=self._cursor_x, y=start_y),
                size=Size(width=bar_width, height=self._cursor_y - start_y),
            )
        )

    def _render_list(self, p: Painter, node: ListNode, width: float) -> None:
        """Render a list."""
        self._list_depth += 1

        if node.ordered:
            self._list_counters.append(node.start)

        for child in node.children:
            if isinstance(child, (ListItemNode, TaskItemNode)):
                self._render_list_item(p, child, width, node.ordered)

        if node.ordered:
            self._list_counters.pop()

        self._list_depth -= 1

    def _render_list_item(
        self,
        p: Painter,
        node: ListItemNode | TaskItemNode,
        width: float,
        ordered: bool,
    ) -> None:
        """Render a list item."""
        indent = self._list_depth * self._theme.list_indent
        marker_x = self._cursor_x + indent - 16

        style = Style(
            fill=FillStyle(color=self._theme.text_color),
            font=Font(family=self._theme.text_font, size=self._theme.base_font_size),
        )
        p.style(style)

        marker_y = self._cursor_y + self._theme.base_font_size

        if isinstance(node, TaskItemNode):
            box_size = 12
            box_y = marker_y - box_size
            box_style = Style(stroke=StrokeStyle(color=self._theme.text_color))
            p.style(box_style)
            p.stroke_rect(
                Rect(
                    origin=Point(x=marker_x, y=box_y),
                    size=Size(width=box_size, height=box_size),
                )
            )
            if node.checked:
                check_style = Style(fill=FillStyle(color=self._theme.text_color))
                p.style(check_style)
                p.fill_rect(
                    Rect(
                        origin=Point(x=marker_x + 2, y=box_y + 2),
                        size=Size(width=box_size - 4, height=box_size - 4),
                    )
                )
        elif ordered:
            counter = self._list_counters[-1] if self._list_counters else 1
            marker = f"{counter}."
            self._list_counters[-1] = counter + 1
            p.fill_text(marker, Point(x=marker_x, y=marker_y), None)
        else:
            bullet = "\u2022"
            p.fill_text(bullet, Point(x=marker_x + 4, y=marker_y), None)

        for child in node.children:
            self._render_node(p, child, width)

    def _render_table(self, p: Painter, node: TableNode, width: float) -> None:
        """Render a table."""
        if not node.children:
            return

        first_row = node.children[0]
        if not isinstance(first_row, TableRowNode):
            return

        col_count = len(first_row.children)
        if col_count == 0:
            return

        col_width = width / col_count
        row_height = self._theme.table_row_height

        for row in node.children:
            if not isinstance(row, TableRowNode):
                continue

            for col_idx, cell in enumerate(row.children):
                if not isinstance(cell, TableCellNode):
                    continue

                cell_x = self._cursor_x + col_idx * col_width

                bg_color = (
                    self._theme.table_header_bg
                    if row.is_header
                    else self._theme.table_cell_bg
                )
                bg_style = Style(fill=FillStyle(color=bg_color))
                p.style(bg_style)
                p.fill_rect(
                    Rect(
                        origin=Point(x=cell_x, y=self._cursor_y),
                        size=Size(width=col_width, height=row_height),
                    )
                )

                border_style = Style(stroke=StrokeStyle(color=self._theme.text_color))
                p.style(border_style)
                p.stroke_rect(
                    Rect(
                        origin=Point(x=cell_x, y=self._cursor_y),
                        size=Size(width=col_width, height=row_height),
                    )
                )

                segments = self._collect_segments(cell.children, RenderContext())
                text = "".join(s.text for s in segments if isinstance(s, TextSegment))

                text_style = Style(
                    fill=FillStyle(color=self._theme.text_color),
                    font=Font(
                        family=self._theme.text_font,
                        size=self._theme.base_font_size,
                        weight=FontWeight.BOLD if row.is_header else FontWeight.NORMAL,
                    ),
                )
                p.style(text_style)

                text_y = self._cursor_y + row_height * 0.7
                p.fill_text(text, Point(x=cell_x + 4, y=text_y), col_width - 8)

            self._cursor_y += row_height

        self._cursor_y += self._theme.block_spacing

    def _render_hr(self, p: Painter, width: float) -> None:
        """Render a horizontal rule."""
        self._cursor_y += self._theme.block_spacing / 2

        style = Style(fill=FillStyle(color=self._theme.text_color))
        p.style(style)
        p.fill_rect(
            Rect(
                origin=Point(x=self._cursor_x, y=self._cursor_y),
                size=Size(width=width, height=1),
            )
        )

        self._cursor_y += self._theme.block_spacing / 2

    def _render_math_block(self, p: Painter, node: MathBlockNode, width: float) -> None:
        """Render a block math expression."""
        math_array = self._math_renderer.render(node.content, inline=False)

        img_height = math_array.shape[0]
        img_width = math_array.shape[1]

        x = self._cursor_x + (width - img_width) / 2

        if hasattr(p, "draw_np_array_as_an_image_rect"):
            arr = np.ascontiguousarray(math_array)
            p.draw_np_array_as_an_image_rect(
                arr,
                Rect(
                    origin=Point(x=x, y=self._cursor_y),
                    size=Size(width=img_width, height=img_height),
                ),
            )

        self._cursor_y += img_height + self._theme.block_spacing

    def _render_image(self, p: Painter, node: ImageNode, width: float) -> None:
        """Render an image placeholder."""
        placeholder_height = 100

        bg_style = Style(fill=FillStyle(color=self._theme.code_bg_color))
        p.style(bg_style)
        p.fill_rect(
            Rect(
                origin=Point(x=self._cursor_x, y=self._cursor_y),
                size=Size(width=width, height=placeholder_height),
            )
        )

        text_style = Style(
            fill=FillStyle(color=self._theme.text_color),
            font=Font(family=self._theme.text_font, size=self._theme.base_font_size),
        )
        p.style(text_style)

        label = f"[Image: {node.alt or node.src}]"
        p.fill_text(
            label,
            Point(x=self._cursor_x + 8, y=self._cursor_y + placeholder_height / 2),
            width - 16,
        )

        self._cursor_y += placeholder_height + self._theme.block_spacing

    def _collect_segments(
        self,
        nodes: list[MarkdownNode],
        ctx: RenderContext,
    ) -> list[TextSegment | np.ndarray]:
        """Collect text segments from nodes."""
        segments: list[TextSegment | np.ndarray] = []

        for node in nodes:
            if isinstance(node, TextNode):
                segments.append(
                    TextSegment(
                        text=node.content,
                        bold=ctx.bold,
                        italic=ctx.italic,
                        strikethrough=ctx.strikethrough,
                        code=ctx.code,
                        href=ctx.href,
                    )
                )
            elif isinstance(node, StrongNode):
                new_ctx = RenderContext(
                    bold=True,
                    italic=ctx.italic,
                    strikethrough=ctx.strikethrough,
                    code=ctx.code,
                    href=ctx.href,
                )
                segments.extend(self._collect_segments(node.children, new_ctx))
            elif isinstance(node, EmphasisNode):
                new_ctx = RenderContext(
                    bold=ctx.bold,
                    italic=True,
                    strikethrough=ctx.strikethrough,
                    code=ctx.code,
                    href=ctx.href,
                )
                segments.extend(self._collect_segments(node.children, new_ctx))
            elif isinstance(node, StrikethroughNode):
                new_ctx = RenderContext(
                    bold=ctx.bold,
                    italic=ctx.italic,
                    strikethrough=True,
                    code=ctx.code,
                    href=ctx.href,
                )
                segments.extend(self._collect_segments(node.children, new_ctx))
            elif isinstance(node, CodeInlineNode):
                segments.append(
                    TextSegment(
                        text=node.content,
                        bold=ctx.bold,
                        italic=ctx.italic,
                        strikethrough=ctx.strikethrough,
                        code=True,
                        href=ctx.href,
                    )
                )
            elif isinstance(node, LinkNode):
                new_ctx = RenderContext(
                    bold=ctx.bold,
                    italic=ctx.italic,
                    strikethrough=ctx.strikethrough,
                    code=ctx.code,
                    href=node.href,
                )
                segments.extend(self._collect_segments(node.children, new_ctx))
            elif isinstance(node, MathInlineNode):
                math_array = self._math_renderer.render(node.content, inline=True)
                segments.append(math_array)
            elif isinstance(node, (SoftBreakNode, HardBreakNode)):
                segments.append(TextSegment(text=" "))

        return segments

    def get_link_at(self, pos: Point) -> str | None:
        """Get link URL at position for click handling."""
        for region in self._link_regions:
            if (
                region.rect.origin.x
                <= pos.x
                <= region.rect.origin.x + region.rect.size.width
                and region.rect.origin.y
                <= pos.y
                <= region.rect.origin.y + region.rect.size.height
            ):
                return region.href
        return None

    def measure_height(
        self, p: Painter, ast: DocumentNode, width: float, padding: float = 8.0
    ) -> float:
        """Measure the height required to render the document.

        This is an approximation - actual rendering may differ slightly.
        """
        total_height = padding * 2

        for node in ast.children:
            total_height += self._estimate_node_height(p, node, width - padding * 2)

        return total_height

    def _estimate_node_height(
        self, p: Painter, node: MarkdownNode, width: float
    ) -> float:
        """Estimate height of a node."""
        if isinstance(node, HeadingNode):
            font_size = self._theme.get_heading_size(node.level)
            return font_size * 1.5 + self._theme.block_spacing
        elif isinstance(node, ParagraphNode):
            segments = self._collect_segments(node.children, RenderContext())
            text = "".join(s.text for s in segments if isinstance(s, TextSegment))

            p.style(
                Style(
                    font=Font(
                        family=self._theme.text_font, size=self._theme.base_font_size
                    )
                )
            )
            text_width = p.measure_text(text)
            lines = max(1, int(text_width / width) + 1)

            return (
                lines * self._theme.base_font_size * 1.5 + self._theme.paragraph_spacing
            )
        elif isinstance(node, CodeBlockNode):
            lines = node.content.count("\n") + 1
            return lines * 16 + 32 + self._theme.block_spacing
        elif isinstance(node, ListNode):
            height = 0.0
            for child in node.children:
                height += self._estimate_node_height(p, child, width)
            return height
        elif isinstance(node, (ListItemNode, TaskItemNode)):
            height = 0.0
            for child in node.children:
                height += self._estimate_node_height(
                    p, child, width - self._theme.list_indent
                )
            return height
        elif isinstance(node, TableNode):
            return (
                len(node.children) * self._theme.table_row_height
                + self._theme.block_spacing
            )
        elif isinstance(node, HorizontalRuleNode):
            return self._theme.block_spacing
        elif isinstance(node, MathBlockNode):
            return 60 + self._theme.block_spacing
        elif isinstance(node, ImageNode):
            return 100 + self._theme.block_spacing
        elif isinstance(node, BlockquoteNode):
            height = 0.0
            for child in node.children:
                height += self._estimate_node_height(
                    p, child, width - self._theme.blockquote_indent
                )
            return height

        return self._theme.base_font_size * 1.5
