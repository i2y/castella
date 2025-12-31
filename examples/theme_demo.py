"""Theme System Demo

Demonstrates the new theme system features:
- Dark/Light mode toggle
- Custom theme creation
- Theme derivation
- Real-time theme switching
"""

from castella import (
    App,
    Button,
    Column,
    Component,
    Input,
    Row,
    State,
    Text,
    Kind,
)
from castella.frame import Frame
from castella.theme import (
    ThemeManager,
    DARK_THEME,
    LIGHT_THEME,
    Theme,
    ColorPalette,
    Typography,
    Spacing,
)


# Custom theme: Cyberpunk (neon green on black)
CYBERPUNK_PALETTE = ColorPalette(
    bg_canvas="#0a0a0a",
    bg_primary="#0a0a0a",
    bg_secondary="#121212",
    bg_tertiary="#1a1a2e",
    bg_overlay="#00ff41",
    bg_info="#0a0a0a",
    bg_danger="#0a0a0a",
    bg_success="#0a0a0a",
    bg_warning="#0a0a0a",
    bg_pushed="#1a1a2e",
    bg_selected="#00ff41",
    fg="#00ff41",
    text_primary="#00ff41",
    text_info="#00d4ff",
    text_danger="#ff0055",
    text_success="#00ff41",
    text_warning="#ffff00",
    border_primary="#00ff41",
    border_secondary="#00d4ff",
    border_info="#00d4ff",
    border_danger="#ff0055",
    border_success="#00ff41",
    border_warning="#ffff00",
)

CYBERPUNK_THEME = Theme(
    name="cyberpunk",
    is_dark=True,
    colors=CYBERPUNK_PALETTE,
    typography=Typography(base_size=14),
    spacing=Spacing(),
    code_pygments_style="monokai",
)

# Custom theme: Ocean (blue tones)
OCEAN_PALETTE = ColorPalette(
    bg_canvas="#0d1b2a",
    bg_primary="#0d1b2a",
    bg_secondary="#1b263b",
    bg_tertiary="#415a77",
    bg_overlay="#778da9",
    bg_info="#1b263b",
    bg_danger="#1b263b",
    bg_success="#1b263b",
    bg_warning="#1b263b",
    bg_pushed="#415a77",
    bg_selected="#778da9",
    fg="#e0e1dd",
    text_primary="#e0e1dd",
    text_info="#48cae4",
    text_danger="#f72585",
    text_success="#80ed99",
    text_warning="#ffd60a",
    border_primary="#778da9",
    border_secondary="#48cae4",
    border_info="#48cae4",
    border_danger="#f72585",
    border_success="#80ed99",
    border_warning="#ffd60a",
)

OCEAN_THEME = Theme(
    name="ocean",
    is_dark=True,
    colors=OCEAN_PALETTE,
    typography=Typography(base_size=14),
    spacing=Spacing(),
    code_pygments_style="monokai",
)


class ThemeDemo(Component):
    def __init__(self):
        super().__init__()
        self._theme_name = State("castella-dark")
        self._theme_name.attach(self)
        self._input_text = State("Type here...")
        self._manager = ThemeManager()

    def _set_theme(self, theme: Theme):
        """Apply a theme and update state."""
        if theme.is_dark:
            self._manager.set_dark_theme(theme)
            self._manager.prefer_dark(True)
        else:
            self._manager.set_light_theme(theme)
            self._manager.prefer_dark(False)
        self._theme_name.set(theme.name)

    def _toggle_dark_light(self, _):
        """Toggle between current dark and light themes."""
        self._manager.toggle_dark_mode()
        self._theme_name.set(self._manager.current.name)

    def _apply_default_dark(self, _):
        self._set_theme(DARK_THEME)

    def _apply_default_light(self, _):
        self._set_theme(LIGHT_THEME)

    def _apply_cyberpunk(self, _):
        self._set_theme(CYBERPUNK_THEME)

    def _apply_ocean(self, _):
        self._set_theme(OCEAN_THEME)

    def _apply_custom(self, _):
        """Create and apply a custom derived theme."""
        custom = DARK_THEME.derive(
            colors={
                "border_primary": "#ff6b6b",
                "border_secondary": "#feca57",
                "text_info": "#54a0ff",
                "bg_overlay": "#ff6b6b",
                "bg_selected": "#ff6b6b",
            },
            name="custom-derived",
        )
        self._set_theme(custom)

    def view(self):
        theme = self._manager.current

        return Column(
            # Header
            Text(f"Theme Demo - Current: {self._theme_name()}").fixed_height(40),

            # Theme info
            Row(
                Text(f"Dark mode: {theme.is_dark}").fixed_width(150),
                Text(f"BG: {theme.colors.bg_canvas}").fixed_width(150),
                Text(f"Text: {theme.colors.text_primary}").fixed_width(150),
            ).fixed_height(30),

            # Divider
            Text("--- Theme Selection ---").fixed_height(30),

            # Theme buttons row 1
            Row(
                Button("Toggle Dark/Light").on_click(self._toggle_dark_light),
                Button("Default Dark").on_click(self._apply_default_dark),
                Button("Default Light").on_click(self._apply_default_light),
            ).fixed_height(50),

            # Theme buttons row 2
            Row(
                Button("Cyberpunk").on_click(self._apply_cyberpunk),
                Button("Ocean").on_click(self._apply_ocean),
                Button("Custom Derived").on_click(self._apply_custom),
            ).fixed_height(50),

            # Divider
            Text("--- Widget Showcase ---").fixed_height(30),

            # Sample widgets
            Row(
                Column(
                    Text("Normal Text"),
                    Text("Info Text", kind=Kind.INFO),
                    Text("Success Text", kind=Kind.SUCCESS),
                    Text("Warning Text", kind=Kind.WARNING),
                    Text("Danger Text", kind=Kind.DANGER),
                ).fixed_width(200),
                Column(
                    Button("Normal Button"),
                    Button("Hover me!"),
                    Input(self._input_text()).on_change(lambda t: self._input_text.set(t)),
                ).fixed_width(200),
            ).fixed_height(200),

            # Typography info
            Text("--- Typography ---").fixed_height(30),
            Text(f"Font family: {theme.typography.font_family or 'system default'}").fixed_height(24),
            Text(f"Base size: {theme.typography.base_size}px").fixed_height(24),
            Text(f"Scale ratio: {theme.typography.scale_ratio}").fixed_height(24),

            # Spacing info
            Text("--- Spacing ---").fixed_height(30),
            Text(f"Padding: sm={theme.spacing.padding_sm}, md={theme.spacing.padding_md}, lg={theme.spacing.padding_lg}").fixed_height(24),
            Text(f"Border radius: {theme.spacing.border_radius}px").fixed_height(24),
        )


if __name__ == "__main__":
    App(Frame("Theme Demo", 800, 700), ThemeDemo()).run()
