"""Predefined theme presets.

This module provides built-in dark and light themes.
"""

from .core import Theme
from .tokens import ColorPalette, Spacing, Typography


# Dark palette (Castella Dark Theme)
DARK_PALETTE = ColorPalette(
    # Background colors
    bg_canvas="#1e1e1e",
    bg_primary="#1e1e1e",
    bg_secondary="#1e1e1e",
    bg_tertiary="#282a36",  # Dark background
    bg_overlay="#ff79c6",  # Neon pink
    bg_info="#1e1e1e",
    bg_danger="#1e1e1e",
    bg_success="#1e1e1e",
    bg_warning="#1e1e1e",
    bg_pushed="#1e1e1e",
    bg_selected="#ff79c6",  # Neon pink
    # Foreground/Text colors
    fg="#f8f8f2",  # Light foreground
    text_primary="#f8f8f2",
    text_info="#00ffff",  # Neon cyan
    text_danger="#ff6347",  # Neon red
    text_success="#32cd32",  # Neon green
    text_warning="#ffd700",  # Neon yellow
    # Border colors
    border_primary="#bd93f9",  # Neon purple
    border_secondary="#ff79c6",  # Neon pink
    border_info="#00ffff",  # Neon cyan
    border_danger="#ff6347",  # Neon red
    border_success="#32cd32",  # Neon green
    border_warning="#ffd700",  # Neon yellow
)

# Light palette (Castella Unicorn Light Theme)
LIGHT_PALETTE = ColorPalette(
    # Background colors
    bg_canvas="#fff0f6",  # Very light pink background
    bg_primary="#fff0f6",  # Same as canvas
    bg_secondary="#fce4ec",  # Light pink
    bg_tertiary="#e8eaf6",  # Light lavender
    bg_overlay="#ffccf9",  # Light pink overlay
    bg_info="#e1f5fe",  # Light cyan background for info
    bg_danger="#fce4ec",  # Light pink background for danger
    bg_success="#e8f5e9",  # Light green background for success
    bg_warning="#fff9c4",  # Light yellow background for warning
    bg_pushed="#f8bbd0",  # Slightly darker pink when pushed
    bg_selected="#f8bbd0",  # Slightly darker pink for selection
    # Foreground/Text colors
    fg="#212121",  # Dark text
    text_primary="#212121",  # Dark text
    text_info="#7e57c2",  # Purple text
    text_danger="#ec407a",  # Pink text
    text_success="#66bb6a",  # Light green text
    text_warning="#ffb300",  # Amber text
    # Border colors
    border_primary="#ba68c8",  # Light purple border
    border_secondary="#f48fb1",  # Light pink border
    border_info="#81d4fa",  # Light blue border
    border_danger="#f06292",  # Pink border
    border_success="#a5d6a7",  # Light green border
    border_warning="#ffcc80",  # Light orange border
)


DARK_THEME = Theme(
    name="castella-dark",
    is_dark=True,
    colors=DARK_PALETTE,
    typography=Typography(),
    spacing=Spacing(),
    code_pygments_style="monokai",
)

LIGHT_THEME = Theme(
    name="castella-light",
    is_dark=False,
    colors=LIGHT_PALETTE,
    typography=Typography(),
    spacing=Spacing(),
    code_pygments_style="default",
)
