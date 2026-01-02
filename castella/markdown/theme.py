"""Theme configuration for Markdown rendering."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from castella.theme import Theme


@dataclass
class AdmonitionColors:
    """Colors for a specific admonition type."""

    bg_color: str
    border_color: str
    icon: str


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

    # Admonition colors (GitHub-style)
    admon_note_bg: str = "#1e3a5f"
    admon_note_border: str = "#58a6ff"
    admon_tip_bg: str = "#1a3d2e"
    admon_tip_border: str = "#3fb950"
    admon_important_bg: str = "#2d1f3d"
    admon_important_border: str = "#a371f7"
    admon_warning_bg: str = "#3d2e1a"
    admon_warning_border: str = "#d29922"
    admon_caution_bg: str = "#3d1a1a"
    admon_caution_border: str = "#f85149"

    # Definition list styling
    deflist_term_color: str = ""  # Will use heading_color if empty
    deflist_indent: int = 24

    def get_admonition_colors(self, admon_type: str) -> AdmonitionColors:
        """Get colors for an admonition type."""
        icons = {
            "note": "\u2139\ufe0f",  # ℹ️
            "tip": "\U0001f4a1",  # 💡
            "important": "\u2757",  # ❗
            "warning": "\u26a0\ufe0f",  # ⚠️
            "caution": "\U0001f6d1",  # 🛑
        }

        colors = {
            "note": (self.admon_note_bg, self.admon_note_border),
            "tip": (self.admon_tip_bg, self.admon_tip_border),
            "important": (self.admon_important_bg, self.admon_important_border),
            "warning": (self.admon_warning_bg, self.admon_warning_border),
            "caution": (self.admon_caution_bg, self.admon_caution_border),
        }

        bg, border = colors.get(
            admon_type, (self.admon_note_bg, self.admon_note_border)
        )
        icon = icons.get(admon_type, "\u2139\ufe0f")

        return AdmonitionColors(bg_color=bg, border_color=border, icon=icon)

    @classmethod
    def from_theme(cls, theme: "Theme | None" = None) -> "MarkdownTheme":
        """Create MarkdownTheme from a Theme object.

        Args:
            theme: The theme to derive from. If None, uses current theme.
        """
        if theme is None:
            from castella.theme import ThemeManager

            theme = ThemeManager().current

        colors = theme.colors
        typography = theme.typography
        spacing = theme.spacing

        return cls(
            text_color=colors.text_primary,
            heading_color=colors.text_primary,
            link_color=colors.text_info,
            code_color=colors.text_warning,
            bg_color=colors.bg_primary,
            code_bg_color=colors.bg_tertiary,
            blockquote_bg_color=colors.bg_secondary,
            table_header_bg=colors.bg_tertiary,
            table_cell_bg=colors.bg_primary,
            text_font=typography.font_family,
            code_font=typography.font_family_mono,
            base_font_size=typography.base_size,
            h1_size=typography.heading_size(1),
            h2_size=typography.heading_size(2),
            h3_size=typography.heading_size(3),
            h4_size=typography.heading_size(4),
            h5_size=typography.heading_size(5),
            h6_size=typography.heading_size(6),
            code_pygments_style=theme.code_pygments_style,
            paragraph_spacing=spacing.margin_md + 4,
            block_spacing=spacing.margin_lg,
            list_indent=spacing.padding_lg + 8,
            blockquote_indent=spacing.padding_lg + 4,
            table_row_height=28,
            is_dark=theme.is_dark,
        )

    @classmethod
    def from_castella_theme(cls, dark_mode: bool | None = None) -> "MarkdownTheme":
        """Create MarkdownTheme from current Castella theme.

        DEPRECATED: Use from_theme() instead.
        """
        from castella.theme import ThemeManager

        theme = ThemeManager().current
        if dark_mode is not None and dark_mode != theme.is_dark:
            # If explicitly requesting different mode, derive appropriate theme
            from castella.theme import DARK_THEME, LIGHT_THEME

            theme = DARK_THEME if dark_mode else LIGHT_THEME
        return cls.from_theme(theme)

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
