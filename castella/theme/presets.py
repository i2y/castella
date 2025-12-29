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


# Cupertino Dark palette (Apple-inspired design)
CUPERTINO_DARK_PALETTE = ColorPalette(
    # Background colors - System grays
    bg_canvas="#1e1e1e",  # Window background
    bg_primary="#2d2d2d",  # Primary content background
    bg_secondary="#3d3d3d",  # Secondary content background
    bg_tertiary="#4a4a4a",  # Tertiary/elevated background (buttons)
    bg_overlay="#5a5a5a",  # Overlay/hover state
    bg_info="#1a3a5c",  # Info background (blue tint)
    bg_danger="#5c1a1a",  # Danger background (red tint)
    bg_success="#1a5c2e",  # Success background (green tint)
    bg_warning="#5c4a1a",  # Warning background (yellow tint)
    bg_pushed="#555555",  # Pressed state
    bg_selected="#0a84ff",  # Selection (System Blue)
    # Foreground/Text colors
    fg="#ffffff",  # Primary label
    text_primary="#ffffff",  # Primary text
    text_info="#64d2ff",  # Info text (System Cyan)
    text_danger="#ff6961",  # Danger text (System Red)
    text_success="#30d158",  # Success text (System Green)
    text_warning="#ffd60a",  # Warning text (System Yellow)
    # Border colors
    border_primary="#48484a",  # Separator color
    border_secondary="#636366",  # Secondary separator
    border_info="#0a84ff",  # Info border (System Blue)
    border_danger="#ff453a",  # Danger border (System Red)
    border_success="#32d74b",  # Success border (System Green)
    border_warning="#ffd60a",  # Warning border (System Yellow)
)

# Cupertino Light palette (Apple-inspired design)
CUPERTINO_LIGHT_PALETTE = ColorPalette(
    # Background colors - System grays (light)
    bg_canvas="#f5f5f7",  # Window background
    bg_primary="#ffffff",  # Primary content background
    bg_secondary="#f2f2f7",  # Secondary content background
    bg_tertiary="#e5e5ea",  # Tertiary/elevated background (buttons)
    bg_overlay="#d1d1d6",  # Overlay/hover state
    bg_info="#e3f2fd",  # Info background (blue tint)
    bg_danger="#ffebee",  # Danger background (red tint)
    bg_success="#e8f5e9",  # Success background (green tint)
    bg_warning="#fff8e1",  # Warning background (yellow tint)
    bg_pushed="#c7c7cc",  # Pressed state
    bg_selected="#007aff",  # Selection (System Blue)
    # Foreground/Text colors
    fg="#000000",  # Primary label
    text_primary="#000000",  # Primary text
    text_info="#007aff",  # Info text (System Blue)
    text_danger="#ff3b30",  # Danger text (System Red)
    text_success="#34c759",  # Success text (System Green)
    text_warning="#ff9500",  # Warning text (System Orange)
    # Border colors
    border_primary="#c6c6c8",  # Separator color
    border_secondary="#aeaeb2",  # Secondary separator
    border_info="#007aff",  # Info border (System Blue)
    border_danger="#ff3b30",  # Danger border (System Red)
    border_success="#34c759",  # Success border (System Green)
    border_warning="#ff9500",  # Warning border (System Orange)
)

# Cupertino spacing with rounded corners
CUPERTINO_SPACING = Spacing(
    padding_sm=4,
    padding_md=8,
    padding_lg=16,
    margin_sm=4,
    margin_md=8,
    margin_lg=16,
    border_radius=8,  # macOS uses ~8px for controls
    border_width=0.5,  # Thin borders
)

# Cupertino typography
CUPERTINO_TYPOGRAPHY = Typography(
    font_family="-apple-system, BlinkMacSystemFont, 'Helvetica Neue', sans-serif",
    font_family_mono="'SF Mono', Menlo, Monaco, monospace",
    base_size=13,  # macOS standard text size
    scale_ratio=1.2,
)

CUPERTINO_DARK_THEME = Theme(
    name="cupertino-dark",
    is_dark=True,
    colors=CUPERTINO_DARK_PALETTE,
    typography=CUPERTINO_TYPOGRAPHY,
    spacing=CUPERTINO_SPACING,
    code_pygments_style="monokai",
)

CUPERTINO_LIGHT_THEME = Theme(
    name="cupertino-light",
    is_dark=False,
    colors=CUPERTINO_LIGHT_PALETTE,
    typography=CUPERTINO_TYPOGRAPHY,
    spacing=CUPERTINO_SPACING,
    code_pygments_style="default",
)
