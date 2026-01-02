"""Markdown parser using markdown-it-py."""

import re

from markdown_it import MarkdownIt
from markdown_it.token import Token
from mdit_py_plugins.footnote import footnote_plugin
from mdit_py_plugins.tasklists import tasklists_plugin

from castella.markdown.models import (
    AdmonitionNode,
    AdmonitionType,
    BlockquoteNode,
    CodeBlockNode,
    CodeInlineNode,
    DefinitionDescNode,
    DefinitionListNode,
    DefinitionTermNode,
    DocumentNode,
    EmphasisNode,
    FootnoteRefNode,
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

# Pattern to match GitHub-style admonition markers
_TOC_PATTERN = re.compile(r"^\s*\[\[?toc\]?\]\s*$", re.I)
_ADMONITION_PATTERN = re.compile(r"^\[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]$", re.I)


class MarkdownParser:
    """Parses Markdown text into AST nodes."""

    def __init__(
        self,
        enable_math: bool = True,
        enable_admonitions: bool = True,
        enable_mermaid: bool = True,
        enable_deflist: bool = True,
        enable_toc: bool = True,
    ):
        self._md = MarkdownIt("gfm-like", {"linkify": False})
        self._md.enable("table")
        self._md.enable("strikethrough")

        footnote_plugin(self._md)
        tasklists_plugin(self._md)

        # Try to load definition list plugin if available
        if enable_deflist:
            try:
                from mdit_py_plugins.deflist import deflist_plugin

                deflist_plugin(self._md)
            except ImportError:
                pass

        self._enable_math = enable_math
        self._enable_admonitions = enable_admonitions
        self._enable_mermaid = enable_mermaid
        self._enable_deflist = enable_deflist
        self._enable_toc = enable_toc

    def parse(self, content: str) -> DocumentNode:
        """Parse Markdown text into AST.

        Args:
            content: Markdown text to parse

        Returns:
            DocumentNode containing the parsed AST
        """
        tokens = self._md.parse(content)
        children = self._tokens_to_ast(tokens)
        return DocumentNode(children=children)

    def _tokens_to_ast(self, tokens: list[Token]) -> list[MarkdownNode]:
        """Convert markdown-it tokens to AST nodes."""
        nodes: list[MarkdownNode] = []
        i = 0

        while i < len(tokens):
            token = tokens[i]

            if token.type == "heading_open":
                level = int(token.tag[1])
                i += 1
                inline_token = tokens[i]
                children = (
                    self._parse_inline(inline_token) if inline_token.children else []
                )
                nodes.append(HeadingNode(level=level, children=children))
                i += 2
            elif token.type == "paragraph_open":
                i += 1
                inline_token = tokens[i]
                # Check for TOC marker
                raw_content = (
                    inline_token.content.strip() if inline_token.content else ""
                )
                if self._enable_toc and _TOC_PATTERN.match(raw_content):
                    nodes.append(TOCNode())
                else:
                    children = (
                        self._parse_inline(inline_token)
                        if inline_token.children
                        else []
                    )
                    nodes.append(ParagraphNode(children=children))
                i += 2
            elif token.type == "fence":
                lang = token.info.strip() if token.info else ""
                content = token.content
                if self._enable_math and lang in ("math", "latex"):
                    nodes.append(MathBlockNode(content=content.strip()))
                elif self._enable_mermaid and lang == "mermaid":
                    nodes.append(MermaidNode(content=content.strip()))
                else:
                    nodes.append(CodeBlockNode(language=lang, content=content))
                i += 1
            elif token.type == "code_block":
                nodes.append(CodeBlockNode(content=token.content))
                i += 1
            elif token.type == "blockquote_open":
                end_idx = self._find_closing(
                    tokens, i, "blockquote_open", "blockquote_close"
                )
                inner_tokens = tokens[i + 1 : end_idx]
                children = self._tokens_to_ast(inner_tokens)

                # Check if this is a GitHub-style admonition
                admon_result = self._check_admonition(children)
                if self._enable_admonitions and admon_result:
                    admon_type, title, admon_children = admon_result
                    nodes.append(
                        AdmonitionNode(
                            admonition_type=admon_type,
                            title=title,
                            children=admon_children,
                        )
                    )
                else:
                    nodes.append(BlockquoteNode(children=children))
                i = end_idx + 1
            elif token.type == "bullet_list_open":
                end_idx = self._find_closing(
                    tokens, i, "bullet_list_open", "bullet_list_close"
                )
                inner_tokens = tokens[i + 1 : end_idx]
                children = self._parse_list_items(inner_tokens)
                nodes.append(ListNode(ordered=False, children=children))
                i = end_idx + 1
            elif token.type == "ordered_list_open":
                start = int(token.attrs.get("start", 1)) if token.attrs else 1
                end_idx = self._find_closing(
                    tokens, i, "ordered_list_open", "ordered_list_close"
                )
                inner_tokens = tokens[i + 1 : end_idx]
                children = self._parse_list_items(inner_tokens)
                nodes.append(ListNode(ordered=True, start=start, children=children))
                i = end_idx + 1
            elif token.type == "table_open":
                end_idx = self._find_closing(tokens, i, "table_open", "table_close")
                inner_tokens = tokens[i + 1 : end_idx]
                table_node = self._parse_table(inner_tokens)
                nodes.append(table_node)
                i = end_idx + 1
            elif token.type == "hr":
                nodes.append(HorizontalRuleNode())
                i += 1
            elif token.type == "footnote_ref":
                label = token.meta.get("label", "") if token.meta else ""
                nodes.append(FootnoteRefNode(label=label))
                i += 1
            elif token.type == "footnote_block_open":
                end_idx = self._find_closing(
                    tokens, i, "footnote_block_open", "footnote_block_close"
                )
                i = end_idx + 1
            elif token.type == "dl_open":
                # Definition list
                end_idx = self._find_closing(tokens, i, "dl_open", "dl_close")
                inner_tokens = tokens[i + 1 : end_idx]
                children = self._parse_deflist_items(inner_tokens)
                nodes.append(DefinitionListNode(children=children))
                i = end_idx + 1
            else:
                i += 1

        return nodes

    def _parse_inline(self, token: Token) -> list[MarkdownNode]:
        """Parse inline tokens."""
        if not token.children:
            return []

        nodes: list[MarkdownNode] = []
        i = 0
        children = token.children

        while i < len(children):
            child = children[i]

            if child.type == "text":
                content = child.content
                if self._enable_math and "$" in content:
                    math_nodes = self._parse_inline_math(content)
                    nodes.extend(math_nodes)
                else:
                    nodes.append(TextNode(content=content))
                i += 1
            elif child.type == "code_inline":
                nodes.append(CodeInlineNode(content=child.content))
                i += 1
            elif child.type == "strong_open":
                end_idx = self._find_inline_closing(
                    children, i, "strong_open", "strong_close"
                )
                inner_children = children[i + 1 : end_idx]
                inner_nodes = self._parse_inline_children(inner_children)
                nodes.append(StrongNode(children=inner_nodes))
                i = end_idx + 1
            elif child.type == "em_open":
                end_idx = self._find_inline_closing(children, i, "em_open", "em_close")
                inner_children = children[i + 1 : end_idx]
                inner_nodes = self._parse_inline_children(inner_children)
                nodes.append(EmphasisNode(children=inner_nodes))
                i = end_idx + 1
            elif child.type == "s_open":
                end_idx = self._find_inline_closing(children, i, "s_open", "s_close")
                inner_children = children[i + 1 : end_idx]
                inner_nodes = self._parse_inline_children(inner_children)
                nodes.append(StrikethroughNode(children=inner_nodes))
                i = end_idx + 1
            elif child.type == "link_open":
                href = child.attrs.get("href", "") if child.attrs else ""
                title = child.attrs.get("title", "") if child.attrs else ""
                end_idx = self._find_inline_closing(
                    children, i, "link_open", "link_close"
                )
                inner_children = children[i + 1 : end_idx]
                inner_nodes = self._parse_inline_children(inner_children)
                nodes.append(LinkNode(href=href, title=title, children=inner_nodes))
                i = end_idx + 1
            elif child.type == "image":
                src = child.attrs.get("src", "") if child.attrs else ""
                alt = child.attrs.get("alt", "") if child.attrs else ""
                title = child.attrs.get("title", "") if child.attrs else ""
                if not alt and child.content:
                    alt = child.content
                nodes.append(ImageNode(src=src, alt=alt, title=title))
                i += 1
            elif child.type == "softbreak":
                nodes.append(SoftBreakNode())
                i += 1
            elif child.type == "hardbreak":
                nodes.append(HardBreakNode())
                i += 1
            else:
                i += 1

        return nodes

    def _parse_inline_children(self, children: list[Token]) -> list[MarkdownNode]:
        """Parse a list of inline tokens."""
        nodes: list[MarkdownNode] = []
        i = 0

        while i < len(children):
            child = children[i]

            if child.type == "text":
                nodes.append(TextNode(content=child.content))
                i += 1
            elif child.type == "code_inline":
                nodes.append(CodeInlineNode(content=child.content))
                i += 1
            elif child.type == "strong_open":
                end_idx = self._find_inline_closing(
                    children, i, "strong_open", "strong_close"
                )
                inner_children = children[i + 1 : end_idx]
                inner_nodes = self._parse_inline_children(inner_children)
                nodes.append(StrongNode(children=inner_nodes))
                i = end_idx + 1
            elif child.type == "em_open":
                end_idx = self._find_inline_closing(children, i, "em_open", "em_close")
                inner_children = children[i + 1 : end_idx]
                inner_nodes = self._parse_inline_children(inner_children)
                nodes.append(EmphasisNode(children=inner_nodes))
                i = end_idx + 1
            elif child.type == "s_open":
                end_idx = self._find_inline_closing(children, i, "s_open", "s_close")
                inner_children = children[i + 1 : end_idx]
                inner_nodes = self._parse_inline_children(inner_children)
                nodes.append(StrikethroughNode(children=inner_nodes))
                i = end_idx + 1
            else:
                i += 1

        return nodes

    def _parse_inline_math(self, content: str) -> list[MarkdownNode]:
        """Parse inline math expressions from text."""
        nodes: list[MarkdownNode] = []
        parts = content.split("$")

        for idx, part in enumerate(parts):
            if idx % 2 == 0:
                if part:
                    nodes.append(TextNode(content=part))
            else:
                if part:
                    nodes.append(MathInlineNode(content=part))

        return nodes

    def _parse_list_items(self, tokens: list[Token]) -> list[MarkdownNode]:
        """Parse list item tokens."""
        items: list[MarkdownNode] = []
        i = 0

        while i < len(tokens):
            token = tokens[i]

            if token.type == "list_item_open":
                is_task = False
                checked = False
                if token.attrs:
                    class_attr = token.attrs.get("class", "")
                    if "task-list-item" in class_attr:
                        is_task = True

                end_idx = self._find_closing(
                    tokens, i, "list_item_open", "list_item_close"
                )
                inner_tokens = tokens[i + 1 : end_idx]
                children = self._tokens_to_ast(inner_tokens)

                if is_task:
                    # Check for checked state in inner tokens (html_inline with checkbox)
                    for inner_token in inner_tokens:
                        if inner_token.type == "inline" and inner_token.children:
                            for child_token in inner_token.children:
                                if child_token.type == "html_inline":
                                    html_content = child_token.content
                                    if 'checked="checked"' in html_content:
                                        checked = True
                                        break
                            break

                    # Clean up leading space in first text node
                    if children:
                        first_child = children[0]
                        if (
                            isinstance(first_child, ParagraphNode)
                            and first_child.children
                        ):
                            first_inline = first_child.children[0]
                            if isinstance(first_inline, TextNode):
                                text = first_inline.content
                                # Strip leading space added by tasklists plugin
                                if text.startswith(" "):
                                    new_text = text[1:]
                                    new_children = [TextNode(content=new_text)] + list(
                                        first_child.children[1:]
                                    )
                                    children = [
                                        ParagraphNode(children=new_children)
                                    ] + children[1:]

                    items.append(TaskItemNode(checked=checked, children=children))
                else:
                    items.append(ListItemNode(children=children))

                i = end_idx + 1
            else:
                i += 1

        return items

    def _parse_table(self, tokens: list[Token]) -> TableNode:
        """Parse table tokens."""
        rows: list[MarkdownNode] = []
        alignments: list[str] = []
        i = 0

        while i < len(tokens):
            token = tokens[i]

            if token.type == "thead_open":
                end_idx = self._find_closing(tokens, i, "thead_open", "thead_close")
                inner_tokens = tokens[i + 1 : end_idx]
                header_rows = self._parse_table_rows(inner_tokens, is_header=True)
                rows.extend(header_rows)
                i = end_idx + 1
            elif token.type == "tbody_open":
                end_idx = self._find_closing(tokens, i, "tbody_open", "tbody_close")
                inner_tokens = tokens[i + 1 : end_idx]
                body_rows = self._parse_table_rows(inner_tokens, is_header=False)
                rows.extend(body_rows)
                i = end_idx + 1
            else:
                i += 1

        return TableNode(alignments=alignments, children=rows)

    def _parse_table_rows(
        self, tokens: list[Token], is_header: bool
    ) -> list[TableRowNode]:
        """Parse table row tokens."""
        rows: list[TableRowNode] = []
        i = 0

        while i < len(tokens):
            token = tokens[i]

            if token.type == "tr_open":
                end_idx = self._find_closing(tokens, i, "tr_open", "tr_close")
                inner_tokens = tokens[i + 1 : end_idx]
                cells = self._parse_table_cells(inner_tokens)
                rows.append(TableRowNode(is_header=is_header, children=cells))
                i = end_idx + 1
            else:
                i += 1

        return rows

    def _parse_table_cells(self, tokens: list[Token]) -> list[TableCellNode]:
        """Parse table cell tokens."""
        cells: list[TableCellNode] = []
        i = 0

        while i < len(tokens):
            token = tokens[i]

            if token.type in ("th_open", "td_open"):
                close_type = "th_close" if token.type == "th_open" else "td_close"
                align = "left"
                if token.attrs and "style" in token.attrs:
                    style = token.attrs["style"]
                    if "center" in style:
                        align = "center"
                    elif "right" in style:
                        align = "right"

                end_idx = self._find_closing(tokens, i, token.type, close_type)
                inner_tokens = tokens[i + 1 : end_idx]

                children: list[MarkdownNode] = []
                for inner_token in inner_tokens:
                    if inner_token.type == "inline" and inner_token.children:
                        children.extend(self._parse_inline(inner_token))

                cells.append(TableCellNode(align=align, children=children))
                i = end_idx + 1
            else:
                i += 1

        return cells

    def _find_closing(
        self, tokens: list[Token], start: int, open_type: str, close_type: str
    ) -> int:
        """Find matching closing token."""
        depth = 1
        for i in range(start + 1, len(tokens)):
            if tokens[i].type == open_type:
                depth += 1
            elif tokens[i].type == close_type:
                depth -= 1
                if depth == 0:
                    return i
        return len(tokens) - 1

    def _find_inline_closing(
        self, tokens: list[Token], start: int, open_type: str, close_type: str
    ) -> int:
        """Find matching closing inline token."""
        depth = 1
        for i in range(start + 1, len(tokens)):
            if tokens[i].type == open_type:
                depth += 1
            elif tokens[i].type == close_type:
                depth -= 1
                if depth == 0:
                    return i
        return len(tokens) - 1

    def _check_admonition(
        self, children: list[MarkdownNode]
    ) -> tuple[AdmonitionType, str, list[MarkdownNode]] | None:
        """Check if blockquote children represent a GitHub-style admonition.

        GitHub-style admonition syntax:
            > [!NOTE]
            > Content here

            > [!WARNING]
            > Some warning message

        Returns:
            Tuple of (admonition_type, title, remaining_children) if admonition,
            None otherwise.
        """
        if not children:
            return None

        first_child = children[0]
        if not isinstance(first_child, ParagraphNode):
            return None

        if not first_child.children:
            return None

        first_inline = first_child.children[0]
        if not isinstance(first_inline, TextNode):
            return None

        text = first_inline.content.strip()
        match = _ADMONITION_PATTERN.match(text)
        if not match:
            return None

        # Found admonition marker
        type_str = match.group(1).upper()
        try:
            admon_type = AdmonitionType(type_str.lower())
        except ValueError:
            return None

        # Build remaining children (remove the [!TYPE] marker)
        remaining_text = text[match.end() :].strip()
        new_first_children: list[MarkdownNode] = []

        if remaining_text:
            new_first_children.append(TextNode(content=remaining_text))
        new_first_children.extend(first_child.children[1:])

        if new_first_children:
            new_first_para = ParagraphNode(children=new_first_children)
            return (admon_type, "", [new_first_para] + list(children[1:]))
        else:
            return (admon_type, "", list(children[1:]))

    def _parse_deflist_items(self, tokens: list[Token]) -> list[MarkdownNode]:
        """Parse definition list items (dt/dd)."""
        items: list[MarkdownNode] = []
        i = 0

        while i < len(tokens):
            token = tokens[i]

            if token.type == "dt_open":
                end_idx = self._find_closing(tokens, i, "dt_open", "dt_close")
                inner_tokens = tokens[i + 1 : end_idx]
                children: list[MarkdownNode] = []
                for inner_token in inner_tokens:
                    if inner_token.type == "inline" and inner_token.children:
                        children.extend(self._parse_inline(inner_token))
                items.append(DefinitionTermNode(children=children))
                i = end_idx + 1
            elif token.type == "dd_open":
                end_idx = self._find_closing(tokens, i, "dd_open", "dd_close")
                inner_tokens = tokens[i + 1 : end_idx]
                children = self._tokens_to_ast(inner_tokens)
                items.append(DefinitionDescNode(children=children))
                i = end_idx + 1
            else:
                i += 1

        return items
