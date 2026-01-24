"""Castella Theme System.

This module provides a comprehensive theming system for Castella applications.

Quick Start:
    from castella.theme import ThemeManager, DARK_THEME, LIGHT_THEME

    # Use built-in themes
    manager = ThemeManager()
    manager.set_dark_theme(DARK_THEME)
    manager.set_light_theme(LIGHT_THEME)

    # Get current theme
    theme = manager.current

    # Toggle dark/light mode
    manager.toggle_dark_mode()

Custom Themes:
    # Create a custom theme by deriving from an existing one
    my_theme = DARK_THEME.derive(
        colors={"border_primary": "#00ff00"},
        typography={"base_size": 16},
    )
    manager.set_dark_theme(my_theme)

    # Or create a completely new theme
    from castella.theme import Theme, ColorPalette, Typography, Spacing

    my_palette = ColorPalette(
        bg_canvas="#000000",
        bg_primary="#111111",
        # ... other colors
    )
    my_theme = Theme(
        name="my-theme",
        is_dark=True,
        colors=my_palette,
    )
"""

from .core import (
    AppearanceState,
    Kind,
    Theme,
    WidgetStyle,
    WidgetStyles,
    generate_button_styles,
    generate_checkbox_styles,
    generate_input_styles,
    generate_layout_styles,
    generate_switch_styles,
    generate_text_styles,
    generate_widget_style,
    generate_widget_styles_for_kind,
)
from .manager import ThemeManager, ThemeObserver
from .presets import (
    CORAL_DARK_PALETTE,
    CORAL_DARK_THEME,
    CORAL_LIGHT_PALETTE,
    CORAL_LIGHT_THEME,
    CORAL_SPACING,
    CORAL_TYPOGRAPHY,
    CUPERTINO_DARK_PALETTE,
    CUPERTINO_DARK_THEME,
    CUPERTINO_LIGHT_PALETTE,
    CUPERTINO_LIGHT_THEME,
    CUPERTINO_SPACING,
    CUPERTINO_TYPOGRAPHY,
    DARK_PALETTE,
    DARK_THEME,
    LIGHT_PALETTE,
    LIGHT_THEME,
    LITHIUM_DARK_PALETTE,
    LITHIUM_DARK_THEME,
    LITHIUM_LIGHT_PALETTE,
    LITHIUM_LIGHT_THEME,
    LITHIUM_SPACING,
    LITHIUM_TYPOGRAPHY,
    MATERIAL_DARK_PALETTE,
    MATERIAL_DARK_THEME,
    MATERIAL_LIGHT_PALETTE,
    MATERIAL_LIGHT_THEME,
    MATERIAL_SPACING,
    MATERIAL_TYPOGRAPHY,
    TOKYO_NIGHT_DARK_PALETTE,
    TOKYO_NIGHT_DARK_THEME,
    TOKYO_NIGHT_LIGHT_PALETTE,
    TOKYO_NIGHT_LIGHT_THEME,
    TOKYO_NIGHT_SPACING,
    TOKYO_NIGHT_TYPOGRAPHY,
)
from .tokens import ColorPalette, Spacing, Typography

__all__ = [
    # Core classes
    "Theme",
    "WidgetStyle",
    "WidgetStyles",
    "Kind",
    "AppearanceState",
    # Tokens
    "ColorPalette",
    "Typography",
    "Spacing",
    # Manager
    "ThemeManager",
    "ThemeObserver",
    # Presets
    "DARK_THEME",
    "LIGHT_THEME",
    "DARK_PALETTE",
    "LIGHT_PALETTE",
    "CUPERTINO_DARK_THEME",
    "CUPERTINO_LIGHT_THEME",
    "CUPERTINO_DARK_PALETTE",
    "CUPERTINO_LIGHT_PALETTE",
    "CUPERTINO_SPACING",
    "CUPERTINO_TYPOGRAPHY",
    "MATERIAL_DARK_THEME",
    "MATERIAL_LIGHT_THEME",
    "MATERIAL_DARK_PALETTE",
    "MATERIAL_LIGHT_PALETTE",
    "MATERIAL_SPACING",
    "MATERIAL_TYPOGRAPHY",
    "TOKYO_NIGHT_DARK_THEME",
    "TOKYO_NIGHT_LIGHT_THEME",
    "TOKYO_NIGHT_DARK_PALETTE",
    "TOKYO_NIGHT_LIGHT_PALETTE",
    "TOKYO_NIGHT_SPACING",
    "TOKYO_NIGHT_TYPOGRAPHY",
    "LITHIUM_DARK_THEME",
    "LITHIUM_LIGHT_THEME",
    "LITHIUM_DARK_PALETTE",
    "LITHIUM_LIGHT_PALETTE",
    "LITHIUM_SPACING",
    "LITHIUM_TYPOGRAPHY",
    "CORAL_DARK_THEME",
    "CORAL_LIGHT_THEME",
    "CORAL_DARK_PALETTE",
    "CORAL_LIGHT_PALETTE",
    "CORAL_SPACING",
    "CORAL_TYPOGRAPHY",
    # Style generators
    "generate_widget_style",
    "generate_widget_styles_for_kind",
    "generate_text_styles",
    "generate_input_styles",
    "generate_button_styles",
    "generate_switch_styles",
    "generate_checkbox_styles",
    "generate_layout_styles",
]
