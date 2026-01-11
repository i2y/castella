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
    border_focus="#00ffff",  # Neon cyan for focus ring
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
    border_focus="#7e57c2",  # Purple for focus ring
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
    border_focus="#0a84ff",  # Focus ring (System Blue)
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
    border_focus="#007aff",  # Focus ring (System Blue)
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


# Material Design 3 Dark palette
MATERIAL_DARK_PALETTE = ColorPalette(
    # Surface colors (dark theme uses elevated surfaces)
    bg_canvas="#121212",  # Surface
    bg_primary="#1e1e1e",  # Surface +1
    bg_secondary="#232323",  # Surface +2
    bg_tertiary="#2c2c2c",  # Surface +3 (buttons, cards)
    bg_overlay="#383838",  # Surface +5 (hover)
    bg_info="#1a237e",  # Info container (Indigo dark)
    bg_danger="#b71c1c",  # Error container
    bg_success="#1b5e20",  # Success container (Green dark)
    bg_warning="#e65100",  # Warning container (Orange dark)
    bg_pushed="#424242",  # Pressed state
    bg_selected="#bb86fc",  # Primary (Purple)
    # Text colors (on-surface)
    fg="#e1e1e1",  # On-surface
    text_primary="#e1e1e1",  # On-surface
    text_info="#82b1ff",  # Info (Light blue)
    text_danger="#cf6679",  # Error
    text_success="#81c784",  # Success (Light green)
    text_warning="#ffb74d",  # Warning (Orange light)
    # Border/outline colors
    border_primary="#444444",  # Outline
    border_secondary="#666666",  # Outline variant
    border_info="#536dfe",  # Info (Indigo)
    border_danger="#cf6679",  # Error
    border_success="#4caf50",  # Success (Green)
    border_warning="#ff9800",  # Warning (Orange)
    border_focus="#bb86fc",  # Focus ring (Primary Purple)
)

# Material Design 3 Light palette
MATERIAL_LIGHT_PALETTE = ColorPalette(
    # Surface colors
    bg_canvas="#fefefe",  # Surface
    bg_primary="#ffffff",  # Surface
    bg_secondary="#f5f5f5",  # Surface variant
    bg_tertiary="#e8e8e8",  # Surface container (buttons)
    bg_overlay="#d0d0d0",  # Hover state
    bg_info="#e8eaf6",  # Info container (Indigo light)
    bg_danger="#ffebee",  # Error container
    bg_success="#e8f5e9",  # Success container (Green light)
    bg_warning="#fff3e0",  # Warning container (Orange light)
    bg_pushed="#bdbdbd",  # Pressed state
    bg_selected="#6200ee",  # Primary (Purple)
    # Text colors
    fg="#1c1b1f",  # On-surface
    text_primary="#1c1b1f",  # On-surface
    text_info="#3f51b5",  # Info (Indigo)
    text_danger="#b00020",  # Error
    text_success="#2e7d32",  # Success (Green)
    text_warning="#e65100",  # Warning (Orange)
    # Border/outline colors
    border_primary="#c4c4c4",  # Outline
    border_secondary="#e0e0e0",  # Outline variant
    border_info="#3f51b5",  # Info (Indigo)
    border_danger="#b00020",  # Error
    border_success="#4caf50",  # Success (Green)
    border_warning="#ff9800",  # Warning (Orange)
    border_focus="#6200ee",  # Focus ring (Primary Purple)
)

# Material spacing with rounded corners
MATERIAL_SPACING = Spacing(
    padding_sm=4,
    padding_md=8,
    padding_lg=16,
    margin_sm=4,
    margin_md=8,
    margin_lg=16,
    border_radius=12,  # Material 3 uses larger radius
    border_width=1.0,
)

# Material typography (Roboto)
MATERIAL_TYPOGRAPHY = Typography(
    font_family="Roboto, 'Noto Sans', 'Segoe UI', sans-serif",
    font_family_mono="'Roboto Mono', 'Fira Code', monospace",
    base_size=14,  # Material default body size
    scale_ratio=1.25,
)

MATERIAL_DARK_THEME = Theme(
    name="material-dark",
    is_dark=True,
    colors=MATERIAL_DARK_PALETTE,
    typography=MATERIAL_TYPOGRAPHY,
    spacing=MATERIAL_SPACING,
    code_pygments_style="monokai",
)

MATERIAL_LIGHT_THEME = Theme(
    name="material-light",
    is_dark=False,
    colors=MATERIAL_LIGHT_PALETTE,
    typography=MATERIAL_TYPOGRAPHY,
    spacing=MATERIAL_SPACING,
    code_pygments_style="default",
)


# Tokyo Night Dark palette (Storm variant)
TOKYO_NIGHT_DARK_PALETTE = ColorPalette(
    # Background colors
    bg_canvas="#1a1b26",  # Background
    bg_primary="#1a1b26",  # Background
    bg_secondary="#24283b",  # Background highlight
    bg_tertiary="#414868",  # Overlay
    bg_overlay="#565f89",  # Subtle overlay
    bg_info="#24283b",  # Info background
    bg_danger="#24283b",  # Danger background
    bg_success="#24283b",  # Success background
    bg_warning="#24283b",  # Warning background
    bg_pushed="#3b4261",  # Pressed state
    bg_selected="#7aa2f7",  # Blue selection
    # Foreground/Text colors
    fg="#c0caf5",  # Foreground
    text_primary="#c0caf5",  # Foreground
    text_info="#7dcfff",  # Cyan
    text_danger="#f7768e",  # Red
    text_success="#9ece6a",  # Green
    text_warning="#e0af68",  # Yellow
    # Border colors
    border_primary="#565f89",  # Comment/dark5
    border_secondary="#414868",  # Dark3
    border_info="#7aa2f7",  # Blue
    border_danger="#f7768e",  # Red
    border_success="#9ece6a",  # Green
    border_warning="#ff9e64",  # Orange
    border_focus="#7aa2f7",  # Focus ring (Blue)
)

# Tokyo Night Light palette (Day variant)
TOKYO_NIGHT_LIGHT_PALETTE = ColorPalette(
    # Background colors
    bg_canvas="#d5d6db",  # Background
    bg_primary="#d5d6db",  # Background
    bg_secondary="#e9e9ed",  # Background highlight
    bg_tertiary="#c4c8da",  # Overlay
    bg_overlay="#b4b5b9",  # Subtle overlay
    bg_info="#e9e9ed",  # Info background
    bg_danger="#e9e9ed",  # Danger background
    bg_success="#e9e9ed",  # Success background
    bg_warning="#e9e9ed",  # Warning background
    bg_pushed="#a9aab1",  # Pressed state
    bg_selected="#2e7de9",  # Blue selection
    # Foreground/Text colors (darkened for better contrast on light backgrounds)
    fg="#1a1b26",  # Dark navy (Tokyo Night Dark fg)
    text_primary="#1a1b26",  # Dark navy
    text_info="#005a7a",  # Darker cyan
    text_danger="#c41e3a",  # Darker red
    text_success="#3d5229",  # Darker green
    text_warning="#6a4e1f",  # Darker orange/brown
    # Border colors
    border_primary="#6172b0",  # Comment
    border_secondary="#a8aecb",  # Dark3
    border_info="#2e7de9",  # Blue
    border_danger="#f52a65",  # Red
    border_success="#587539",  # Green
    border_warning="#b15c00",  # Orange
    border_focus="#2e7de9",  # Focus ring (Blue)
)

# Tokyo Night typography
TOKYO_NIGHT_TYPOGRAPHY = Typography(
    font_family="'JetBrains Mono', 'Fira Code', 'Consolas', monospace",
    font_family_mono="'JetBrains Mono', 'Fira Code', 'Consolas', monospace",
    base_size=14,
    scale_ratio=1.2,
)

# Tokyo Night spacing (subtle rounded corners)
TOKYO_NIGHT_SPACING = Spacing(
    padding_sm=4,
    padding_md=8,
    padding_lg=16,
    margin_sm=4,
    margin_md=8,
    margin_lg=16,
    border_radius=6,  # Subtle rounded corners
    border_width=1.0,
)

TOKYO_NIGHT_DARK_THEME = Theme(
    name="tokyo-night-dark",
    is_dark=True,
    colors=TOKYO_NIGHT_DARK_PALETTE,
    typography=TOKYO_NIGHT_TYPOGRAPHY,
    spacing=TOKYO_NIGHT_SPACING,
    code_pygments_style="monokai",
)

TOKYO_NIGHT_LIGHT_THEME = Theme(
    name="tokyo-night-light",
    is_dark=False,
    colors=TOKYO_NIGHT_LIGHT_PALETTE,
    typography=TOKYO_NIGHT_TYPOGRAPHY,
    spacing=TOKYO_NIGHT_SPACING,
    code_pygments_style="default",
)
