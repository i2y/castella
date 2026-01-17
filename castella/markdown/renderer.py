"""Markdown AST renderer."""

import re
from dataclasses import dataclass
from typing import Any, Callable

# numpy is optional - used only for math rendering
try:
    import numpy as np

    NUMPY_AVAILABLE = True
except ImportError:
    np = None  # type: ignore
    NUMPY_AVAILABLE = False

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
from castella.markdown.code_text_renderer import CodeTextRenderer
from castella.markdown.math_renderer import MathRenderer
from castella.markdown.models import (
    AdmonitionNode,
    BlockquoteNode,
    CodeBlockNode,
    CodeInlineNode,
    DefinitionDescNode,
    DefinitionListNode,
    DefinitionTermNode,
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
    MermaidNode,
    ParagraphNode,
    SoftBreakNode,
    StrikethroughNode,
    StrongNode,
    TableCellNode,
    TableNode,
    TableRowNode,
    TaskItemNode,
    TextNode,
    TOCNode,
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
class MathSegment:
    """A segment containing inline math."""

    latex: str
    inline: bool = True


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
        code_renderer: CodeTextRenderer | None = None,
        math_renderer: MathRenderer | None = None,
        on_link_click: Callable[[str], None] | None = None,
    ):
        self._theme = theme
        self._code_renderer = code_renderer or CodeTextRenderer(
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
        self._headings: list[tuple[int, str, str]] = []  # (level, text, id) for TOC
        self._heading_positions: dict[str, float] = {}  # heading_id -> y_position
        self._heading_id_counts: dict[str, int] = {}  # for deduplication
        self._hovered_href: str | None = None  # Currently hovered link

    def render(
        self,
        painter: Painter,
        ast: DocumentNode,
        width: float,
        height: float,
        padding: float = 8.0,
        hovered_href: str | None = None,
    ) -> float:
        """Render AST and return total content height.

        Args:
            painter: Painter to render with
            ast: Document AST to render
            width: Available width
            height: Available height
            padding: Padding around content
            hovered_href: Currently hovered link href (for visual feedback)

        Returns:
            Total height of rendered content
        """
        self._cursor_x = padding
        self._cursor_y = padding
        self._line_height = self._theme.base_font_size * 1.5
        self._link_regions.clear()
        self._list_depth = 0
        self._list_counters = []
        self._heading_positions.clear()
        self._heading_id_counts.clear()
        self._heading_render_index = 0  # Track which heading we're rendering
        self._hovered_href = hovered_href  # Track hovered link for highlighting

        # Collect headings for TOC (also pre-generates heading IDs)
        self._headings = self._collect_headings(ast)

        content_width = max(1.0, width - padding * 2)

        for node in ast.children:
            self._render_node(painter, node, content_width)

        return self._cursor_y + padding

    def _collect_headings(self, ast: DocumentNode) -> list[tuple[int, str, str]]:
        """Collect all headings from the AST for TOC generation.

        Returns:
            List of (level, text, heading_id) tuples
        """
        headings: list[tuple[int, str, str]] = []
        # Reset ID counts for consistent generation
        self._heading_id_counts.clear()
        for node in ast.children:
            if isinstance(node, HeadingNode):
                # Extract text from heading children
                text = self._extract_text(node.children)
                # Generate unique heading ID
                heading_id = self._generate_heading_id(text, node.level)
                headings.append((node.level, text, heading_id))
        return headings

    def _extract_text(self, nodes: list[MarkdownNode]) -> str:
        """Extract plain text from a list of nodes."""
        parts: list[str] = []
        for node in nodes:
            if isinstance(node, TextNode):
                parts.append(node.content)
            elif isinstance(node, CodeInlineNode):
                parts.append(node.content)
            elif hasattr(node, "children"):
                parts.append(self._extract_text(node.children))
        return "".join(parts)

    def _generate_heading_id(self, text: str, level: int) -> str:
        """Generate URL-safe heading ID from text.

        Args:
            text: Heading text content
            level: Heading level (1-6)

        Returns:
            Unique heading ID like "heading-2-hello-world"
        """
        # Convert to lowercase and replace spaces with hyphens
        slug = text.lower().replace(" ", "-")
        # Remove non-alphanumeric characters except hyphens
        slug = re.sub(r"[^\w\-]", "", slug)
        # Create base ID
        base_id = f"heading-{level}-{slug}"

        # Handle duplicates by adding suffix
        if base_id in self._heading_id_counts:
            self._heading_id_counts[base_id] += 1
            return f"{base_id}-{self._heading_id_counts[base_id]}"
        else:
            self._heading_id_counts[base_id] = 0
            return base_id

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
        # Extended syntax nodes
        elif isinstance(node, AdmonitionNode):
            self._render_admonition(p, node, width)
        elif isinstance(node, DefinitionListNode):
            self._render_deflist(p, node, width)
        elif isinstance(node, MermaidNode):
            self._render_mermaid(p, node, width)
        elif isinstance(node, TOCNode):
            self._render_toc(p, node, width)

    def _render_heading(self, p: Painter, node: HeadingNode, width: float) -> None:
        """Render a heading."""
        font_size = self._theme.get_heading_size(node.level)

        self._cursor_y += self._theme.block_spacing

        segments = self._collect_segments(node.children, RenderContext())
        text = "".join(s.text for s in segments if isinstance(s, TextSegment))

        # Use pre-generated heading ID from collection phase
        if self._heading_render_index < len(self._headings):
            _, _, heading_id = self._headings[self._heading_render_index]
            self._heading_render_index += 1
        else:
            # Fallback: generate new ID (shouldn't happen normally)
            heading_id = self._generate_heading_id(text, node.level)

        # Record position for TOC navigation
        self._heading_positions[heading_id] = self._cursor_y

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
            # Handle MathSegment (inline math)
            if isinstance(segment, MathSegment):
                if x > self._cursor_x + self._list_depth * self._theme.list_indent:
                    self._cursor_y += line_height
                    x = self._cursor_x + self._list_depth * self._theme.list_indent

                # Check if painter supports numpy arrays
                if hasattr(p, "draw_np_array_as_an_image_rect") and NUMPY_AVAILABLE:
                    # Use numpy array rendering
                    math_array = self._math_renderer.render(
                        segment.latex, inline=segment.inline
                    )
                    img_height = math_array.shape[0]
                    img_width = math_array.shape[1]
                    arr = np.ascontiguousarray(math_array)
                    p.draw_np_array_as_an_image_rect(
                        arr,
                        Rect(
                            origin=Point(x=x, y=self._cursor_y),
                            size=Size(width=img_width, height=img_height),
                        ),
                    )
                    self._cursor_y += img_height
                elif hasattr(p, "draw_image"):
                    # Use file-based rendering
                    file_path, img_width, img_height = (
                        self._math_renderer.render_to_file(
                            segment.latex, inline=segment.inline
                        )
                    )
                    if file_path:
                        p.draw_image(
                            file_path,
                            Rect(
                                origin=Point(x=x, y=self._cursor_y),
                                size=Size(width=img_width, height=img_height),
                            ),
                        )
                    self._cursor_y += img_height
                else:
                    # Fallback: render as plain text
                    text_style = Style(
                        fill=FillStyle(color=self._theme.code_color),
                        font=Font(
                            family=self._theme.code_font,
                            size=self._theme.base_font_size,
                        ),
                    )
                    p.style(text_style)
                    p.fill_text(
                        f"${segment.latex}$", Point(x=x, y=self._cursor_y), None
                    )
                    self._cursor_y += self._theme.base_font_size
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
                    # Draw underline if hovered
                    if self._hovered_href == segment.href:
                        underline_y = self._cursor_y + self._theme.base_font_size + 2
                        underline_style = Style(
                            fill=FillStyle(color=self._theme.link_color)
                        )
                        p.style(underline_style)
                        p.fill_rect(
                            Rect(
                                origin=Point(x=x, y=underline_y),
                                size=Size(width=word_width, height=2),
                            )
                        )

                x += word_width

        self._cursor_y += line_height + self._theme.paragraph_spacing

    def _render_code_block(self, p: Painter, node: CodeBlockNode, width: float) -> None:
        """Render a fenced code block as styled text."""
        # Get styled code lines
        code_lines = self._code_renderer.highlight(
            node.content,
            language=node.language,
        )

        # Calculate dimensions
        code_font_size = self._theme.base_font_size
        line_height = code_font_size + 4
        padding = 8
        line_num_width = 40  # Width reserved for line numbers

        # Calculate block height
        block_height = len(code_lines) * line_height + padding * 2
        rect_width = max(1.0, width)

        # Draw background
        bg_style = Style(fill=FillStyle(color=self._code_renderer.background_color))
        p.style(bg_style)
        p.fill_rect(
            Rect(
                origin=Point(x=self._cursor_x, y=self._cursor_y),
                size=Size(width=rect_width, height=block_height),
            )
        )

        # Draw each line
        # Add code_font_size to y because fill_text uses baseline positioning
        y = self._cursor_y + padding + code_font_size
        for line in code_lines:
            x = self._cursor_x + padding

            # Draw line number
            line_num_style = Style(
                fill=FillStyle(color=self._code_renderer.line_number_color),
                font=Font(
                    family=self._theme.code_font,
                    size=code_font_size,
                ),
            )
            p.style(line_num_style)
            line_num_text = f"{line.line_number:3}"
            p.fill_text(line_num_text, Point(x=x, y=y), None)
            x += line_num_width

            # Draw tokens
            for token in line.tokens:
                token_style = Style(
                    fill=FillStyle(color=token.color),
                    font=Font(
                        family=self._theme.code_font,
                        size=code_font_size,
                        weight=FontWeight.BOLD if token.bold else FontWeight.NORMAL,
                        slant=FontSlant.ITALIC if token.italic else FontSlant.UPRIGHT,
                    ),
                )
                p.style(token_style)
                p.fill_text(token.text, Point(x=x, y=y), None)
                # Measure text to advance x
                text_width = p.measure_text(token.text)
                x += text_width

            y += line_height

        self._cursor_y += block_height + self._theme.block_spacing

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
                # Draw checkmark (✓)
                check_style = Style(
                    fill=FillStyle(color=self._theme.link_color),
                    font=Font(
                        family=self._theme.text_font,
                        size=self._theme.base_font_size,
                    ),
                )
                p.style(check_style)
                p.fill_text("✓", Point(x=marker_x + 1, y=marker_y - 1), None)
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
        # Check if painter supports numpy arrays
        if hasattr(p, "draw_np_array_as_an_image_rect") and NUMPY_AVAILABLE:
            # Use numpy array rendering
            math_array = self._math_renderer.render(node.content, inline=False)
            img_height = math_array.shape[0]
            img_width = math_array.shape[1]
            x = self._cursor_x + (width - img_width) / 2

            arr = np.ascontiguousarray(math_array)
            p.draw_np_array_as_an_image_rect(
                arr,
                Rect(
                    origin=Point(x=x, y=self._cursor_y),
                    size=Size(width=img_width, height=img_height),
                ),
            )
            self._cursor_y += img_height + self._theme.block_spacing
        elif hasattr(p, "draw_image"):
            # Use file-based rendering
            file_path, img_width, img_height = self._math_renderer.render_to_file(
                node.content, inline=False
            )
            if file_path:
                x = self._cursor_x + (width - img_width) / 2
                p.draw_image(
                    file_path,
                    Rect(
                        origin=Point(x=x, y=self._cursor_y),
                        size=Size(width=img_width, height=img_height),
                    ),
                )
            self._cursor_y += img_height + self._theme.block_spacing
        else:
            # Fallback: render as plain text
            text_style = Style(
                fill=FillStyle(color=self._theme.code_color),
                font=Font(
                    family=self._theme.code_font, size=self._theme.base_font_size
                ),
            )
            p.style(text_style)
            p.fill_text(
                f"$${node.content}$$", Point(x=self._cursor_x, y=self._cursor_y), width
            )
            self._cursor_y += self._theme.base_font_size + self._theme.block_spacing

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
    ) -> list[TextSegment | Any]:
        """Collect text segments from nodes (may include numpy arrays for math)."""
        segments: list[TextSegment | Any] = []

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
                # Store latex for later rendering (allows choosing render method based on painter)
                segments.append(MathSegment(latex=node.content, inline=True))
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

    def get_heading_position(self, heading_id: str) -> float | None:
        """Get the Y position of a heading by its ID.

        Args:
            heading_id: The heading ID (e.g., "heading-2-hello-world")

        Returns:
            Y position of the heading, or None if not found
        """
        return self._heading_positions.get(heading_id)

    def measure_height(
        self, p: Painter, ast: DocumentNode, width: float, padding: float = 8.0
    ) -> float:
        """Measure the height required to render the document.

        This is an approximation - actual rendering may differ slightly.
        """
        # Collect headings for TOC height estimation
        self._headings = self._collect_headings(ast)

        total_height = padding * 2

        # Ensure width is positive to avoid issues in child calculations
        effective_width = max(1.0, width - padding * 2)

        for node in ast.children:
            total_height += self._estimate_node_height(p, node, effective_width)

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
            # Avoid division by zero when width is very small
            safe_width = max(1.0, width)
            lines = max(1, int(text_width / safe_width) + 1)

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
            child_width = max(1.0, width - self._theme.list_indent)
            for child in node.children:
                height += self._estimate_node_height(p, child, child_width)
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
            child_width = max(1.0, width - self._theme.blockquote_indent)
            for child in node.children:
                height += self._estimate_node_height(p, child, child_width)
            return height
        elif isinstance(node, AdmonitionNode):
            height = self._theme.base_font_size * 2  # Header
            child_width = max(1.0, width - 48)
            for child in node.children:
                height += self._estimate_node_height(p, child, child_width)
            return height + self._theme.block_spacing
        elif isinstance(node, DefinitionListNode):
            height = 0.0
            for child in node.children:
                height += self._estimate_node_height(p, child, width)
            return height
        elif isinstance(node, (DefinitionTermNode, DefinitionDescNode)):
            return self._theme.base_font_size * 1.5
        elif isinstance(node, MermaidNode):
            # Calculate actual Mermaid diagram height
            try:
                from castella.markdown.mermaid import parse_mermaid
                from castella.markdown.mermaid.layout import (
                    calculate_diagram_height,
                    layout_diagram,
                )

                diagram = parse_mermaid(node.content)
                layout_diagram(diagram, max_width=width, padding=20)
                height = calculate_diagram_height(diagram)
                return height + self._theme.block_spacing
            except Exception:
                # Fallback to placeholder height on error
                return 200 + self._theme.block_spacing
        elif isinstance(node, TOCNode):
            # Estimate TOC height based on number of headings
            if hasattr(self, "_headings") and self._headings:
                num_headings = len(self._headings)
                line_height = (
                    self._theme.base_font_size * 1.8
                )  # Slightly more than actual
                return num_headings * line_height + self._theme.block_spacing * 3
            return 100 + self._theme.block_spacing

        return self._theme.base_font_size * 1.5

    # Extended syntax render methods

    def _render_admonition(
        self, p: Painter, node: AdmonitionNode, width: float
    ) -> None:
        """Render a GitHub-style admonition block."""
        admon_colors = self._theme.get_admonition_colors(node.admonition_type.value)

        border_width = 4
        padding = 12
        icon_size = self._theme.base_font_size + 4
        header_height = icon_size + padding

        start_y = self._cursor_y

        # First pass: render children to measure content height
        # Save cursor position
        saved_x = self._cursor_x
        saved_y = self._cursor_y

        self._cursor_x += border_width + padding
        self._cursor_y += header_height

        content_start_y = self._cursor_y
        content_width = width - border_width - padding * 2

        for child in node.children:
            self._render_node(p, child, content_width)

        content_height = self._cursor_y - content_start_y
        total_height = header_height + content_height + padding

        # Restore and draw background
        self._cursor_x = saved_x
        self._cursor_y = saved_y

        # Draw background
        bg_style = Style(fill=FillStyle(color=admon_colors.bg_color))
        p.style(bg_style)
        p.fill_rect(
            Rect(
                origin=Point(x=self._cursor_x + border_width, y=start_y),
                size=Size(width=width - border_width, height=total_height),
            )
        )

        # Draw left border
        border_style = Style(fill=FillStyle(color=admon_colors.border_color))
        p.style(border_style)
        p.fill_rect(
            Rect(
                origin=Point(x=self._cursor_x, y=start_y),
                size=Size(width=border_width, height=total_height),
            )
        )

        # Draw icon and type label
        icon_style = Style(
            fill=FillStyle(color=admon_colors.border_color),
            font=Font(family=self._theme.text_font, size=icon_size),
        )
        p.style(icon_style)
        p.fill_text(
            admon_colors.icon,
            Point(
                x=self._cursor_x + border_width + padding,
                y=start_y + padding + icon_size * 0.85,
            ),
            None,
        )

        # Draw type label
        label = node.admonition_type.value.capitalize()
        if node.title:
            label = node.title

        label_style = Style(
            fill=FillStyle(color=admon_colors.border_color),
            font=Font(
                family=self._theme.text_font,
                size=self._theme.base_font_size,
                weight=FontWeight.BOLD,
            ),
        )
        p.style(label_style)
        p.fill_text(
            label,
            Point(
                x=self._cursor_x + border_width + padding + icon_size + 8,
                y=start_y + padding + self._theme.base_font_size,
            ),
            None,
        )

        # Re-render content (over the background)
        self._cursor_x = saved_x + border_width + padding
        self._cursor_y = saved_y + header_height

        for child in node.children:
            self._render_node(p, child, content_width)

        self._cursor_x = saved_x
        self._cursor_y = start_y + total_height + self._theme.block_spacing

    def _render_deflist(
        self, p: Painter, node: DefinitionListNode, width: float
    ) -> None:
        """Render a definition list."""
        for child in node.children:
            if isinstance(child, DefinitionTermNode):
                self._render_defterm(p, child, width)
            elif isinstance(child, DefinitionDescNode):
                self._render_defdesc(p, child, width)

    def _render_defterm(
        self, p: Painter, node: DefinitionTermNode, width: float
    ) -> None:
        """Render a definition term (dt)."""
        segments = self._collect_segments(node.children, RenderContext(bold=True))
        text = "".join(s.text for s in segments if isinstance(s, TextSegment))

        term_color = self._theme.deflist_term_color or self._theme.heading_color

        style = Style(
            fill=FillStyle(color=term_color),
            font=Font(
                family=self._theme.text_font,
                size=self._theme.base_font_size,
                weight=FontWeight.BOLD,
            ),
        )
        p.style(style)
        p.fill_text(
            text,
            Point(x=self._cursor_x, y=self._cursor_y + self._theme.base_font_size),
            width,
        )

        self._cursor_y += self._theme.base_font_size * 1.5

    def _render_defdesc(
        self, p: Painter, node: DefinitionDescNode, width: float
    ) -> None:
        """Render a definition description (dd)."""
        indent = self._theme.deflist_indent
        self._cursor_x += indent

        for child in node.children:
            self._render_node(p, child, width - indent)

        self._cursor_x -= indent

    def _render_mermaid(self, p: Painter, node: MermaidNode, width: float) -> None:
        """Render a Mermaid diagram.

        Currently displays as a code block with placeholder.
        Full Mermaid rendering will be implemented separately.
        """
        # Try to use the mermaid renderer if available
        try:
            from castella.markdown.mermaid import MermaidDiagramRenderer

            diagram_renderer = MermaidDiagramRenderer(self._theme)
            height = diagram_renderer.render(p, node.content, width, self._cursor_y)
            if height > 0:
                self._cursor_y += height + self._theme.block_spacing
                return
            # If height is 0, fall through to fallback rendering
        except Exception:
            # On any error, fall back to placeholder rendering
            pass

        # Fallback: render as styled code block with indicator
        placeholder_height = 60
        content_height = node.content.count("\n") * 14 + placeholder_height

        # Draw background
        bg_style = Style(fill=FillStyle(color=self._theme.code_bg_color))
        p.style(bg_style)
        p.fill_rect(
            Rect(
                origin=Point(x=self._cursor_x, y=self._cursor_y),
                size=Size(width=width, height=content_height),
            )
        )

        # Draw "Mermaid Diagram" label
        label_style = Style(
            fill=FillStyle(color=self._theme.text_color),
            font=Font(
                family=self._theme.text_font,
                size=self._theme.base_font_size,
                weight=FontWeight.BOLD,
            ),
        )
        p.style(label_style)
        p.fill_text(
            "📊 Mermaid Diagram",
            Point(x=self._cursor_x + 8, y=self._cursor_y + 20),
            None,
        )

        # Draw code content
        code_style = Style(
            fill=FillStyle(color=self._theme.code_color),
            font=Font(
                family=self._theme.code_font, size=self._theme.base_font_size - 2
            ),
        )
        p.style(code_style)

        y = self._cursor_y + 40
        for line in node.content.split("\n")[:10]:  # Show first 10 lines
            p.fill_text(line, Point(x=self._cursor_x + 8, y=y), width - 16)
            y += 14

        if node.content.count("\n") > 10:
            p.fill_text("...", Point(x=self._cursor_x + 8, y=y), None)

        self._cursor_y += content_height + self._theme.block_spacing

    def _render_toc(self, p: Painter, node: TOCNode, width: float) -> None:
        """Render a Table of Contents from collected headings."""
        if not self._headings:
            return

        font_size = self._theme.base_font_size
        line_height = font_size * 1.6
        padding = 12
        indent_per_level = 16

        # Calculate TOC height
        toc_height = padding * 2 + len(self._headings) * line_height + font_size

        # Draw background
        bg_style = Style(fill=FillStyle(color=self._theme.blockquote_bg_color))
        p.style(bg_style)
        p.fill_rect(
            Rect(
                origin=Point(x=self._cursor_x, y=self._cursor_y),
                size=Size(width=width, height=toc_height),
            )
        )

        # Draw title "Table of Contents"
        title_style = Style(
            fill=FillStyle(color=self._theme.heading_color),
            font=Font(
                family=self._theme.text_font,
                size=font_size,
                weight=FontWeight.BOLD,
            ),
        )
        p.style(title_style)
        p.fill_text(
            "Table of Contents",
            Point(x=self._cursor_x + padding, y=self._cursor_y + padding + font_size),
            None,
        )

        # Draw heading entries with clickable links
        item_style = Style(
            fill=FillStyle(color=self._theme.link_color),
            font=Font(family=self._theme.text_font, size=font_size - 1),
        )
        p.style(item_style)

        y = self._cursor_y + padding + font_size + line_height
        min_level = min(h[0] for h in self._headings) if self._headings else 1

        for level, text, heading_id in self._headings:
            indent = (level - min_level) * indent_per_level
            # Bullet point based on level
            bullet = "•" if level == min_level else "◦"
            display_text = f"{bullet} {text}"

            entry_x = self._cursor_x + padding + indent
            link_href = f"#{heading_id}"
            is_hovered = self._hovered_href == link_href

            # Set text style before each entry (in case underline changed it)
            p.style(item_style)
            p.fill_text(
                display_text,
                Point(x=entry_x, y=y),
                width - padding * 2 - indent,
            )

            # Measure text width for click region
            text_width = p.measure_text(display_text)

            # Draw underline if hovered
            if is_hovered:
                underline_y = y + 2  # Slightly below text baseline
                underline_style = Style(fill=FillStyle(color=self._theme.link_color))
                p.style(underline_style)
                p.fill_rect(
                    Rect(
                        origin=Point(x=entry_x, y=underline_y),
                        size=Size(width=text_width, height=2),
                    )
                )

            # Register click region for internal link
            self._link_regions.append(
                ClickRegion(
                    rect=Rect(
                        origin=Point(x=entry_x, y=y - font_size),
                        size=Size(width=text_width, height=line_height),
                    ),
                    href=link_href,
                )
            )

            y += line_height

        self._cursor_y += toc_height + self._theme.block_spacing
