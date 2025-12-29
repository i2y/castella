"""Material Design Theme Demo

Demonstrates the Material Design 3 theme with:
- Rounded corners (12px radius)
- Material color system (Surface, Primary, Error, etc.)
- Roboto font family
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
    SizePolicy,
    Kind,
    Switch,
    CheckBox,
)
from castella.frame import Frame
from castella.theme import (
    ThemeManager,
    MATERIAL_DARK_THEME,
    MATERIAL_LIGHT_THEME,
    DARK_THEME,
    LIGHT_THEME,
)


class MaterialThemeDemo(Component):
    def __init__(self):
        super().__init__()
        self._manager = ThemeManager()

        # Set Material themes as default
        self._manager.set_dark_theme(MATERIAL_DARK_THEME)
        self._manager.set_light_theme(MATERIAL_LIGHT_THEME)

        self._theme_name = State(self._manager.current.name)
        self._theme_name.attach(self)
        self._is_material_theme = State(True)
        self._input_text = State("Type something...")
        self._switch_state = State(True)
        self._checkbox_state = State(False)

    def _toggle_dark_light(self, _):
        """Toggle between dark and light modes."""
        self._manager.toggle_dark_mode()
        self._theme_name.set(self._manager.current.name)

    def _toggle_theme_style(self, _):
        """Toggle between Material and default Castella themes."""
        use_material = not self._is_material_theme()
        self._is_material_theme.set(use_material)

        if use_material:
            self._manager.set_dark_theme(MATERIAL_DARK_THEME)
            self._manager.set_light_theme(MATERIAL_LIGHT_THEME)
        else:
            self._manager.set_dark_theme(DARK_THEME)
            self._manager.set_light_theme(LIGHT_THEME)

        # Force theme refresh
        is_dark = self._manager.is_dark
        self._manager.prefer_dark(is_dark)
        self._theme_name.set(self._manager.current.name)

    def view(self):
        theme = self._manager.current
        is_material = self._is_material_theme()

        return Column(
            # Header
            Text("Material Design Theme Demo").height(40).height_policy(SizePolicy.FIXED),

            # Theme info section
            Row(
                Column(
                    Text(f"Theme: {theme.name}").height(24).height_policy(SizePolicy.FIXED),
                    Text(f"Mode: {'Dark' if theme.is_dark else 'Light'}").height(24).height_policy(SizePolicy.FIXED),
                    Text(f"Border Radius: {theme.spacing.border_radius}px").height(24).height_policy(SizePolicy.FIXED),
                ).width(250).width_policy(SizePolicy.FIXED),
                Column(
                    Text(f"Font: {theme.typography.font_family[:30]}...").height(24).height_policy(SizePolicy.FIXED),
                    Text(f"Base Size: {theme.typography.base_size}px").height(24).height_policy(SizePolicy.FIXED),
                    Text(f"Border Width: {theme.spacing.border_width}px").height(24).height_policy(SizePolicy.FIXED),
                ),
            ).height(80).height_policy(SizePolicy.FIXED),

            # Divider
            Text("").height(10).height_policy(SizePolicy.FIXED),

            # Theme toggle buttons
            Row(
                Button("Toggle Dark/Light").on_click(self._toggle_dark_light),
                Button(f"Style: {'Material' if is_material else 'Castella'}").on_click(self._toggle_theme_style),
            ).height(50).height_policy(SizePolicy.FIXED),

            # Divider
            Text("--- Buttons (Material rounded corners) ---").height(35).height_policy(SizePolicy.FIXED),

            # Button showcase
            Row(
                Button("Primary"),
                Button("Secondary"),
                Button("Action"),
                Button("Submit"),
            ).height(50).height_policy(SizePolicy.FIXED),

            # Divider
            Text("--- Input Fields ---").height(35).height_policy(SizePolicy.FIXED),

            # Input showcase
            Row(
                Input(self._input_text()).on_change(lambda t: self._input_text.set(t)),
            ).height(40).height_policy(SizePolicy.FIXED),

            # Divider
            Text("--- Toggle Controls ---").height(35).height_policy(SizePolicy.FIXED),

            # Switch and Checkbox
            Row(
                Column(
                    Text("Switch:").height(24).height_policy(SizePolicy.FIXED),
                    Switch(self._switch_state),
                ).width(150).width_policy(SizePolicy.FIXED),
                Column(
                    Text("Checkbox:").height(24).height_policy(SizePolicy.FIXED),
                    CheckBox(self._checkbox_state),
                ).width(150).width_policy(SizePolicy.FIXED),
            ).height(60).height_policy(SizePolicy.FIXED),

            # Divider
            Text("--- Text Styles (Material colors) ---").height(35).height_policy(SizePolicy.FIXED),

            # Text with different kinds
            Row(
                Text("On-Surface").width(100).width_policy(SizePolicy.FIXED),
                Text("Info", kind=Kind.INFO).width(100).width_policy(SizePolicy.FIXED),
                Text("Success", kind=Kind.SUCCESS).width(100).width_policy(SizePolicy.FIXED),
                Text("Warning", kind=Kind.WARNING).width(100).width_policy(SizePolicy.FIXED),
                Text("Error", kind=Kind.DANGER).width(100).width_policy(SizePolicy.FIXED),
            ).height(30).height_policy(SizePolicy.FIXED),

            # Divider
            Text("--- Surface Colors ---").height(35).height_policy(SizePolicy.FIXED),

            # Colors info
            Row(
                Column(
                    Text(f"Canvas: {theme.colors.bg_canvas}").height(20).height_policy(SizePolicy.FIXED),
                    Text(f"Surface: {theme.colors.bg_primary}").height(20).height_policy(SizePolicy.FIXED),
                    Text(f"Container: {theme.colors.bg_tertiary}").height(20).height_policy(SizePolicy.FIXED),
                ).width(200).width_policy(SizePolicy.FIXED),
                Column(
                    Text(f"On-Surface: {theme.colors.text_primary}").height(20).height_policy(SizePolicy.FIXED),
                    Text(f"Outline: {theme.colors.border_primary}").height(20).height_policy(SizePolicy.FIXED),
                    Text(f"Primary: {theme.colors.bg_selected}").height(20).height_policy(SizePolicy.FIXED),
                ).width(200).width_policy(SizePolicy.FIXED),
            ).height(70).height_policy(SizePolicy.FIXED),

            # Footer note
            Text("").height(20).height_policy(SizePolicy.FIXED),
            Text("Material Design 3 with 12px rounded corners").height(24).height_policy(SizePolicy.FIXED),
        )


if __name__ == "__main__":
    App(Frame("Material Theme Demo", 700, 650), MaterialThemeDemo()).run()
