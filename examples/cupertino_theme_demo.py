"""Cupertino Theme Demo

Demonstrates the Cupertino-style (Apple-inspired) theme with:
- Rounded corners on buttons and inputs
- Native color palette (System Blue, grays, etc.)
- San Francisco font family
- Dark/Light mode toggle
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
    Switch,
    CheckBox,
)
from castella.frame import Frame
from castella.theme import (
    ThemeManager,
    CUPERTINO_DARK_THEME,
    CUPERTINO_LIGHT_THEME,
    DARK_THEME,
    LIGHT_THEME,
)


class CupertinoThemeDemo(Component):
    def __init__(self):
        super().__init__()
        self._manager = ThemeManager()

        # Set Cupertino themes as default
        self._manager.set_dark_theme(CUPERTINO_DARK_THEME)
        self._manager.set_light_theme(CUPERTINO_LIGHT_THEME)

        self._theme_name = State(self._manager.current.name)
        self._theme_name.attach(self)
        self._is_cupertino_theme = State(True)
        self._input_text = State("Type something...")
        self._switch_state = State(True)
        self._checkbox_state = State(False)

    def _toggle_dark_light(self, _):
        """Toggle between dark and light modes."""
        self._manager.toggle_dark_mode()
        self._theme_name.set(self._manager.current.name)

    def _toggle_theme_style(self, _):
        """Toggle between Cupertino and default Castella themes."""
        use_cupertino = not self._is_cupertino_theme()
        self._is_cupertino_theme.set(use_cupertino)

        if use_cupertino:
            self._manager.set_dark_theme(CUPERTINO_DARK_THEME)
            self._manager.set_light_theme(CUPERTINO_LIGHT_THEME)
        else:
            self._manager.set_dark_theme(DARK_THEME)
            self._manager.set_light_theme(LIGHT_THEME)

        # Force theme refresh
        is_dark = self._manager.is_dark
        self._manager.prefer_dark(is_dark)
        self._theme_name.set(self._manager.current.name)

    def view(self):
        theme = self._manager.current
        is_cupertino = self._is_cupertino_theme()

        return Column(
            # Header
            Text("Cupertino Theme Demo").fixed_height(40),

            # Theme info section
            Row(
                Column(
                    Text(f"Theme: {theme.name}").fixed_height(24),
                    Text(f"Mode: {'Dark' if theme.is_dark else 'Light'}").fixed_height(24),
                    Text(f"Border Radius: {theme.spacing.border_radius}px").fixed_height(24),
                ).fixed_width(250),
                Column(
                    Text(f"Font: {theme.typography.font_family[:35]}...").fixed_height(24),
                    Text(f"Base Size: {theme.typography.base_size}px").fixed_height(24),
                    Text(f"Border Width: {theme.spacing.border_width}px").fixed_height(24),
                ),
            ).fixed_height(80),

            # Divider
            Text("").fixed_height(10),

            # Theme toggle buttons
            Row(
                Button("Toggle Dark/Light").on_click(self._toggle_dark_light),
                Button(f"Style: {'Cupertino' if is_cupertino else 'Castella'}").on_click(self._toggle_theme_style),
            ).fixed_height(50),

            # Divider
            Text("--- Button Kinds (semantic colors) ---").fixed_height(35),

            # Button showcase with different Kinds
            Row(
                Button("Normal", kind=Kind.NORMAL),
                Button("Info", kind=Kind.INFO),
                Button("Success", kind=Kind.SUCCESS),
                Button("Warning", kind=Kind.WARNING),
                Button("Danger", kind=Kind.DANGER),
            ).fixed_height(50),

            # Divider
            Text("--- Input Fields ---").fixed_height(35),

            # Input showcase
            Row(
                Input(self._input_text()).on_change(lambda t: self._input_text.set(t)),
            ).fixed_height(40),

            # Divider
            Text("--- Toggle Controls ---").fixed_height(35),

            # Switch and Checkbox
            Row(
                Column(
                    Text("Switch:").fixed_height(24),
                    Switch(self._switch_state),
                ).fixed_width(150),
                Column(
                    Text("Checkbox:").fixed_height(24),
                    CheckBox(self._checkbox_state),
                ).fixed_width(150),
            ).fixed_height(60),

            # Divider
            Text("--- Text Styles ---").fixed_height(35),

            # Text with different kinds
            Row(
                Text("Normal").fixed_width(100),
                Text("Info", kind=Kind.INFO).fixed_width(100),
                Text("Success", kind=Kind.SUCCESS).fixed_width(100),
                Text("Warning", kind=Kind.WARNING).fixed_width(100),
                Text("Danger", kind=Kind.DANGER).fixed_width(100),
            ).fixed_height(30),

            # Divider
            Text("--- Color Palette ---").fixed_height(35),

            # Colors info
            Row(
                Column(
                    Text(f"Canvas: {theme.colors.bg_canvas}").fixed_height(20),
                    Text(f"Primary: {theme.colors.bg_primary}").fixed_height(20),
                    Text(f"Tertiary: {theme.colors.bg_tertiary}").fixed_height(20),
                ).fixed_width(200),
                Column(
                    Text(f"Text: {theme.colors.text_primary}").fixed_height(20),
                    Text(f"Border: {theme.colors.border_primary}").fixed_height(20),
                    Text(f"Selected: {theme.colors.bg_selected}").fixed_height(20),
                ).fixed_width(200),
            ).fixed_height(70),

            # Footer note
            Text("").fixed_height(20),
            Text("Notice: Rounded corners are visible on buttons and inputs!").fixed_height(24),
        )


if __name__ == "__main__":
    App(Frame("Cupertino Theme Demo", 700, 650), CupertinoThemeDemo()).run()
