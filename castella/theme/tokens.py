"""Design tokens for the Castella theme system.

This module defines the foundational design tokens:
- ColorPalette: Semantic color definitions
- Typography: Font settings and sizing
- Spacing: Padding, margin, and layout measurements
"""

from pydantic import BaseModel


class ColorPalette(BaseModel):
    """Semantic color palette for theming.

    All colors are specified as hex strings (e.g., "#1e1e1e").
    """

    model_config = {"frozen": True}

    # Background colors
    bg_canvas: str
    bg_primary: str
    bg_secondary: str
    bg_tertiary: str
    bg_overlay: str
    bg_info: str
    bg_danger: str
    bg_success: str
    bg_warning: str
    bg_pushed: str
    bg_selected: str

    # Foreground/Text colors
    fg: str
    text_primary: str
    text_info: str
    text_danger: str
    text_success: str
    text_warning: str

    # Border colors
    border_primary: str
    border_secondary: str
    border_info: str
    border_danger: str
    border_success: str
    border_warning: str
    border_focus: str


class Typography(BaseModel):
    """Typography design tokens.

    Controls font families and size calculations.
    """

    model_config = {"frozen": True}

    font_family: str = ""  # Empty string means system default
    font_family_mono: str = "monospace"
    base_size: int = 14
    scale_ratio: float = 1.25  # Used for heading size calculation

    def heading_size(self, level: int) -> int:
        """Calculate font size for a heading level (1-6).

        Higher levels (h1) get larger sizes, h6 gets base_size.
        """
        exponent = max(0, 6 - level)  # h1=5, h2=4, ..., h6=0
        return int(self.base_size * (self.scale_ratio ** (exponent * 0.5)))


class Spacing(BaseModel):
    """Spacing design tokens.

    Controls padding, margins, and other layout measurements.
    """

    model_config = {"frozen": True}

    padding_sm: int = 4
    padding_md: int = 8
    padding_lg: int = 16
    margin_sm: int = 4
    margin_md: int = 8
    margin_lg: int = 16
    border_radius: int = 4
    border_width: float = 1.0
