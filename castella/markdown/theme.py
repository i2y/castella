"""Theme configuration for Markdown rendering."""

from dataclasses import dataclass

from castella.core import _get_color_schema, _is_darkmode


@dataclass
class MarkdownTheme:
    """Theme configuration for Markdown rendering."""

    # Text colors
    text_color: str
    heading_color: str
    link_color: str
    code_color: str

    # Background colors
    bg_color: str
    code_bg_color: str
    blockquote_bg_color: str
    table_header_bg: str
    table_cell_bg: str

    # Fonts
    text_font: str
    code_font: str
    base_font_size: int

    # Heading sizes
    h1_size: int
    h2_size: int
    h3_size: int
    h4_size: int
    h5_size: int
    h6_size: int

    # Pygments theme for code
    code_pygments_style: str

    # Spacing
    paragraph_spacing: int
    block_spacing: int
    list_indent: int
    blockquote_indent: int
    table_row_height: int

    # Dark mode flag
    is_dark: bool

    @classmethod
    def from_castella_theme(cls, dark_mode: bool | None = None) -> "MarkdownTheme":
        """Create MarkdownTheme from current Castella theme."""
        if dark_mode is None:
            dark_mode = _is_darkmode()

        colors = _get_color_schema()

        return cls(
            text_color=colors["text-primary"],
            heading_color=colors["text-primary"],
            link_color=colors["text-info"],
            code_color=colors["text-warning"],
            bg_color=colors["bg-primary"],
            code_bg_color=colors["bg-tertiary"],
            blockquote_bg_color=colors["bg-secondary"],
            table_header_bg=colors["bg-tertiary"],
            table_cell_bg=colors["bg-primary"],
            text_font="",  # System default
            code_font="monospace",
            base_font_size=14,
            h1_size=32,
            h2_size=28,
            h3_size=24,
            h4_size=20,
            h5_size=16,
            h6_size=14,
            code_pygments_style="monokai" if dark_mode else "default",
            paragraph_spacing=12,
            block_spacing=16,
            list_indent=24,
            blockquote_indent=20,
            table_row_height=28,
            is_dark=dark_mode,
        )

    def get_heading_size(self, level: int) -> int:
        """Get font size for heading level."""
        sizes = {
            1: self.h1_size,
            2: self.h2_size,
            3: self.h3_size,
            4: self.h4_size,
            5: self.h5_size,
            6: self.h6_size,
        }
        return sizes.get(level, self.base_font_size)
