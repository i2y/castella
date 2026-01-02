"""Pydantic models for Markdown AST nodes."""

from enum import Enum
from typing import Union

from pydantic import BaseModel, ConfigDict, Field


class NodeType(str, Enum):
    """Types of Markdown AST nodes."""

    DOCUMENT = "document"
    HEADING = "heading"
    PARAGRAPH = "paragraph"
    TEXT = "text"
    STRONG = "strong"
    EMPHASIS = "emphasis"
    STRIKETHROUGH = "strikethrough"
    CODE_INLINE = "code_inline"
    CODE_BLOCK = "code_block"
    BLOCKQUOTE = "blockquote"
    LIST = "list"
    LIST_ITEM = "list_item"
    TASK_ITEM = "task_item"
    LINK = "link"
    IMAGE = "image"
    TABLE = "table"
    TABLE_ROW = "table_row"
    TABLE_CELL = "table_cell"
    HORIZONTAL_RULE = "horizontal_rule"
    SOFT_BREAK = "soft_break"
    HARD_BREAK = "hard_break"
    MATH_INLINE = "math_inline"
    MATH_BLOCK = "math_block"
    FOOTNOTE_REF = "footnote_ref"
    FOOTNOTE_DEF = "footnote_def"
    # Extended syntax
    ADMONITION = "admonition"
    DEFINITION_LIST = "definition_list"
    DEFINITION_TERM = "definition_term"
    DEFINITION_DESC = "definition_desc"
    TOC = "toc"
    MERMAID = "mermaid"


class AdmonitionType(str, Enum):
    """Types of admonition/callout blocks."""

    NOTE = "note"
    TIP = "tip"
    IMPORTANT = "important"
    WARNING = "warning"
    CAUTION = "caution"


class MarkdownNode(BaseModel):
    """Base AST node for Markdown elements."""

    model_config = ConfigDict(frozen=True)

    type: NodeType
    children: list["MarkdownNode"] = Field(default_factory=list)


class HeadingNode(MarkdownNode):
    """Heading node (H1-H6)."""

    type: NodeType = NodeType.HEADING
    level: int = Field(ge=1, le=6)


class TextNode(MarkdownNode):
    """Plain text node."""

    type: NodeType = NodeType.TEXT
    content: str = ""


class StrongNode(MarkdownNode):
    """Bold text node."""

    type: NodeType = NodeType.STRONG


class EmphasisNode(MarkdownNode):
    """Italic text node."""

    type: NodeType = NodeType.EMPHASIS


class StrikethroughNode(MarkdownNode):
    """Strikethrough text node."""

    type: NodeType = NodeType.STRIKETHROUGH


class CodeInlineNode(MarkdownNode):
    """Inline code node."""

    type: NodeType = NodeType.CODE_INLINE
    content: str = ""


class CodeBlockNode(MarkdownNode):
    """Fenced code block node."""

    type: NodeType = NodeType.CODE_BLOCK
    language: str = ""
    content: str = ""


class BlockquoteNode(MarkdownNode):
    """Blockquote node."""

    type: NodeType = NodeType.BLOCKQUOTE


class ListNode(MarkdownNode):
    """List container node."""

    type: NodeType = NodeType.LIST
    ordered: bool = False
    start: int = 1


class ListItemNode(MarkdownNode):
    """List item node."""

    type: NodeType = NodeType.LIST_ITEM


class TaskItemNode(MarkdownNode):
    """Task list item node with checkbox."""

    type: NodeType = NodeType.TASK_ITEM
    checked: bool = False


class LinkNode(MarkdownNode):
    """Hyperlink node."""

    type: NodeType = NodeType.LINK
    href: str = ""
    title: str = ""


class ImageNode(MarkdownNode):
    """Image node."""

    type: NodeType = NodeType.IMAGE
    src: str = ""
    alt: str = ""
    title: str = ""


class TableNode(MarkdownNode):
    """Table container node."""

    type: NodeType = NodeType.TABLE
    alignments: list[str] = Field(default_factory=list)  # "left", "center", "right"


class TableRowNode(MarkdownNode):
    """Table row node."""

    type: NodeType = NodeType.TABLE_ROW
    is_header: bool = False


class TableCellNode(MarkdownNode):
    """Table cell node."""

    type: NodeType = NodeType.TABLE_CELL
    align: str = "left"


class HorizontalRuleNode(MarkdownNode):
    """Horizontal rule node."""

    type: NodeType = NodeType.HORIZONTAL_RULE


class SoftBreakNode(MarkdownNode):
    """Soft line break node."""

    type: NodeType = NodeType.SOFT_BREAK


class HardBreakNode(MarkdownNode):
    """Hard line break node."""

    type: NodeType = NodeType.HARD_BREAK


class MathInlineNode(MarkdownNode):
    """Inline math expression node."""

    type: NodeType = NodeType.MATH_INLINE
    content: str = ""


class MathBlockNode(MarkdownNode):
    """Block math expression node."""

    type: NodeType = NodeType.MATH_BLOCK
    content: str = ""


class FootnoteRefNode(MarkdownNode):
    """Footnote reference node."""

    type: NodeType = NodeType.FOOTNOTE_REF
    label: str = ""


class FootnoteDefNode(MarkdownNode):
    """Footnote definition node."""

    type: NodeType = NodeType.FOOTNOTE_DEF
    label: str = ""


class ParagraphNode(MarkdownNode):
    """Paragraph container node."""

    type: NodeType = NodeType.PARAGRAPH


class DocumentNode(MarkdownNode):
    """Root document node."""

    type: NodeType = NodeType.DOCUMENT


# Extended syntax nodes


class AdmonitionNode(MarkdownNode):
    """GitHub-style admonition/callout block.

    Syntax:
        > [!NOTE]
        > This is a note

        > [!WARNING]
        > This is a warning
    """

    type: NodeType = NodeType.ADMONITION
    admonition_type: AdmonitionType = AdmonitionType.NOTE
    title: str = ""  # Custom title if provided


class DefinitionListNode(MarkdownNode):
    """Definition list container.

    Syntax:
        Term
        :   Definition here
    """

    type: NodeType = NodeType.DEFINITION_LIST


class DefinitionTermNode(MarkdownNode):
    """Definition term (dt)."""

    type: NodeType = NodeType.DEFINITION_TERM


class DefinitionDescNode(MarkdownNode):
    """Definition description (dd)."""

    type: NodeType = NodeType.DEFINITION_DESC


class TOCNode(MarkdownNode):
    """Table of Contents placeholder.

    Syntax:
        [TOC] or [[toc]]
    """

    type: NodeType = NodeType.TOC
    max_level: int = 3  # Include h1-h3 by default


class MermaidNode(MarkdownNode):
    """Mermaid diagram block.

    Syntax:
        ```mermaid
        graph TD
            A --> B
        ```
    """

    type: NodeType = NodeType.MERMAID
    content: str = ""


# Type alias for all node types
ASTNode = Union[
    MarkdownNode,
    DocumentNode,
    HeadingNode,
    ParagraphNode,
    TextNode,
    StrongNode,
    EmphasisNode,
    StrikethroughNode,
    CodeInlineNode,
    CodeBlockNode,
    BlockquoteNode,
    ListNode,
    ListItemNode,
    TaskItemNode,
    LinkNode,
    ImageNode,
    TableNode,
    TableRowNode,
    TableCellNode,
    HorizontalRuleNode,
    SoftBreakNode,
    HardBreakNode,
    MathInlineNode,
    MathBlockNode,
    FootnoteRefNode,
    FootnoteDefNode,
    # Extended syntax
    AdmonitionNode,
    DefinitionListNode,
    DefinitionTermNode,
    DefinitionDescNode,
    TOCNode,
    MermaidNode,
]
