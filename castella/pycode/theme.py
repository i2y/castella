"""Theme configuration for pycode.

Uses the Lithium theme from Castella's official theme presets.
"""

from castella.theme import (
    LITHIUM_DARK_THEME,
    LITHIUM_LIGHT_THEME,
    ThemeManager,
)


def apply_pycode_theme(dark_mode: bool = True) -> None:
    """Apply the pycode theme (Lithium) globally.

    Args:
        dark_mode: Use dark theme (default) or light theme
    """
    manager = ThemeManager()
    manager.set_dark_theme(LITHIUM_DARK_THEME)
    manager.set_light_theme(LITHIUM_LIGHT_THEME)
    manager.prefer_dark(dark_mode)
