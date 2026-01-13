# Styling

Castella provides a comprehensive theming system with design tokens (colors, typography, spacing) and per-widget styling options.

## Theme System

The theme system is located in `castella.theme` and provides:

- **ColorPalette**: All color definitions (backgrounds, text, borders)
- **Typography**: Font settings (family, size, scale)
- **Spacing**: Layout measurements (padding, margin, border radius)
- **ThemeManager**: Singleton for dynamic theme switching

### Automatic Theming

Castella automatically detects dark/light mode from the operating system and applies appropriate colors.

### Built-in Themes

Castella includes several professionally designed themes:

| Theme | Style | Border Radius | Font |
|-------|-------|---------------|------|
| **Tokyo Night** (default) | Purple/blue aesthetic | 6px | JetBrains Mono |
| **Cupertino** | Apple-inspired design | 8px | SF Pro / Helvetica Neue |
| **Material Design 3** | Google's Material design | 12px | Roboto |
| **Castella Dark** | Neon colors on dark | 0px | System default |
| **Castella Light** | Soft pastels on light | 0px | System default |

### Environment Variables

Override the automatic theme detection:

| Variable | Values | Description |
|----------|--------|-------------|
| `CASTELLA_DARK_MODE` | `true` / `false` | Force dark or light mode |
| `CASTELLA_FONT_SIZE` | Integer (e.g., `14`) | Override default font size |

```bash
# Force dark mode
CASTELLA_DARK_MODE=true python my_app.py

# Use larger font
CASTELLA_FONT_SIZE=18 python my_app.py
```

## Using ThemeManager

### Get Current Theme

```python
from castella.theme import ThemeManager

manager = ThemeManager()
theme = manager.current

print(f"Theme: {theme.name}")
print(f"Is dark: {theme.is_dark}")
print(f"Background: {theme.colors.bg_canvas}")
```

### Toggle Dark/Light Mode

```python
from castella import Button
from castella.theme import ThemeManager

manager = ThemeManager()

# Toggle button
Button("Toggle Theme").on_click(lambda _: manager.toggle_dark_mode())
```

### Force Dark or Light Mode

```python
# Force dark mode
manager.prefer_dark(True)

# Force light mode
manager.prefer_dark(False)

# Return to automatic detection
manager.prefer_dark(None)
```

### Using Different Built-in Themes

```python
from castella.theme import (
    ThemeManager,
    CUPERTINO_DARK_THEME, CUPERTINO_LIGHT_THEME,
    MATERIAL_DARK_THEME, MATERIAL_LIGHT_THEME,
    TOKYO_NIGHT_DARK_THEME, TOKYO_NIGHT_LIGHT_THEME,
    DARK_THEME, LIGHT_THEME,  # Classic Castella themes
)

manager = ThemeManager()

# Use Material Design theme
manager.set_dark_theme(MATERIAL_DARK_THEME)
manager.set_light_theme(MATERIAL_LIGHT_THEME)

# Or Cupertino (Apple-style) theme
manager.set_dark_theme(CUPERTINO_DARK_THEME)
manager.set_light_theme(CUPERTINO_LIGHT_THEME)
```

## Custom Themes

### Derive from Existing Theme

The easiest way to customize is using `Theme.derive()` for partial overrides:

```python
from castella.theme import ThemeManager, DARK_THEME

# Override just a few colors
custom = DARK_THEME.derive(
    colors={
        "border_primary": "#00ff00",  # Green borders
        "text_info": "#00ffff",       # Cyan info text
        "bg_overlay": "#ff6b6b",      # Custom hover color
    },
    typography={
        "base_size": 16,              # Larger font
    },
)

manager = ThemeManager()
manager.set_dark_theme(custom)
```

### Create Complete Custom Theme

For full control, create a new `ColorPalette`:

```python
from castella.theme import (
    Theme,
    ColorPalette,
    Typography,
    Spacing,
    ThemeManager,
)

# Cyberpunk theme
cyberpunk_palette = ColorPalette(
    # Backgrounds
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
    # Text
    fg="#00ff41",
    text_primary="#00ff41",
    text_info="#00d4ff",
    text_danger="#ff0055",
    text_success="#00ff41",
    text_warning="#ffff00",
    # Borders
    border_primary="#00ff41",
    border_secondary="#00d4ff",
    border_info="#00d4ff",
    border_danger="#ff0055",
    border_success="#00ff41",
    border_warning="#ffff00",
)

cyberpunk_theme = Theme(
    name="cyberpunk",
    is_dark=True,
    colors=cyberpunk_palette,
    typography=Typography(base_size=14),
    spacing=Spacing(),
    code_pygments_style="monokai",
)

manager = ThemeManager()
manager.set_dark_theme(cyberpunk_theme)
manager.prefer_dark(True)
```

## Widget Kinds

Many widgets support the `kind` parameter for semantic coloring:

```python
from castella import Text, Button, Kind

# Text with different kinds
Text("Normal text", kind=Kind.NORMAL)   # Default styling
Text("Info message", kind=Kind.INFO)    # Cyan/blue tones
Text("Success!", kind=Kind.SUCCESS)     # Green tones
Text("Warning!", kind=Kind.WARNING)     # Yellow/amber tones
Text("Error!", kind=Kind.DANGER)        # Red/pink tones

# Buttons with different kinds
Button("Normal", kind=Kind.NORMAL)      # Default button
Button("Info", kind=Kind.INFO)          # Info-styled button
Button("Success", kind=Kind.SUCCESS)    # Success-styled button
Button("Warning", kind=Kind.WARNING)    # Warning-styled button
Button("Danger", kind=Kind.DANGER)      # Danger-styled button

# Fluent API also works
Button("Delete").kind(Kind.DANGER)
```

### Available Kinds

| Kind | Use Case | Dark Theme Colors |
|------|----------|-------------------|
| `Kind.NORMAL` | Default content | Light gray text |
| `Kind.INFO` | Informational messages | Neon cyan |
| `Kind.SUCCESS` | Success states | Neon green |
| `Kind.WARNING` | Warnings, caution | Neon yellow |
| `Kind.DANGER` | Errors, destructive actions | Neon red |

## Per-Widget Styling

### Background and Text Colors

Override colors on individual widgets:

```python
# Custom background color
Text("Custom").bg_color("#ff0000")

# Custom text color
Text("Custom").text_color("#ffffff")

# Both
Text("Custom").bg_color("#1a1a2e").text_color("#eee")
```

### Border Styling

```python
# Set border color
widget.border_color("#ff00ff")

# Show border with theme's default color (or custom color)
widget.show_border()              # Use theme's default border color
widget.show_border("#ff00ff")     # Use custom color

# Make border match background (effectively hides it)
widget.erase_border()
```

## Text Alignment

Control text alignment within widgets:

```python
from castella import Text
from castella.models.style import TextAlign

Text("Left aligned", align=TextAlign.LEFT)
Text("Centered", align=TextAlign.CENTER)   # Default
Text("Right aligned", align=TextAlign.RIGHT)
```

## Design Tokens Reference

### ColorPalette Properties

| Property | Description |
|----------|-------------|
| `bg_canvas` | Main application background |
| `bg_primary` | Primary widget background |
| `bg_secondary` | Secondary widget background |
| `bg_tertiary` | Tertiary/accent background |
| `bg_overlay` | Overlay/hover background |
| `bg_pushed` | Button pressed state |
| `bg_selected` | Selected item background |
| `bg_info` | Info kind background |
| `bg_danger` | Danger kind background |
| `bg_success` | Success kind background |
| `bg_warning` | Warning kind background |
| `fg` | Default foreground |
| `text_primary` | Primary text |
| `text_info` | Info kind text |
| `text_danger` | Danger kind text |
| `text_success` | Success kind text |
| `text_warning` | Warning kind text |
| `border_primary` | Primary border |
| `border_secondary` | Secondary border |
| `border_info` | Info kind border |
| `border_danger` | Danger kind border |
| `border_success` | Success kind border |
| `border_warning` | Warning kind border |

### Typography Properties

| Property | Default | Description |
|----------|---------|-------------|
| `font_family` | `""` (system) | Font family name |
| `font_family_mono` | `"monospace"` | Monospace font for code |
| `base_size` | `14` | Base font size in pixels |
| `scale_ratio` | `1.25` | Ratio for heading size calculation |

Use `typography.heading_size(level)` to get computed heading sizes.

### Spacing Properties

| Property | Default | Description |
|----------|---------|-------------|
| `padding_sm` | `4` | Small padding |
| `padding_md` | `8` | Medium padding |
| `padding_lg` | `16` | Large padding |
| `margin_sm` | `4` | Small margin |
| `margin_md` | `8` | Medium margin |
| `margin_lg` | `16` | Large margin |
| `border_radius` | `4` | Border corner radius |
| `border_width` | `1.0` | Border line width |

## Built-in Theme Colors

### Tokyo Night (Default)

```python
# Dark variant
{
    "bg_canvas": "#1a1b26",      # Deep blue-black
    "fg": "#c0caf5",             # Light purple-white
    "text_info": "#7dcfff",      # Cyan
    "text_danger": "#f7768e",    # Red
    "text_success": "#9ece6a",   # Green
    "text_warning": "#e0af68",   # Yellow
    "border_primary": "#565f89", # Muted purple
}
```

### Material Design 3

```python
# Dark variant
{
    "bg_canvas": "#121212",      # Material dark surface
    "fg": "#e1e1e1",             # On-surface
    "text_info": "#82b1ff",      # Light blue
    "text_danger": "#cf6679",    # Error
    "text_success": "#81c784",   # Light green
    "text_warning": "#ffb74d",   # Orange
    "border_primary": "#444444", # Outline
}
```

### Cupertino (Apple-style)

```python
# Dark variant
{
    "bg_canvas": "#1e1e1e",      # Window background
    "fg": "#ffffff",             # Primary label
    "text_info": "#64d2ff",      # System Cyan
    "text_danger": "#ff6961",    # System Red
    "text_success": "#30d158",   # System Green
    "text_warning": "#ffd60a",   # System Yellow
    "border_primary": "#48484a", # Separator
}
```

## Example: Theme Demos

Run the theme demos to see all features in action:

```bash
# Tokyo Night theme demo (default)
uv run python examples/tokyo_night_theme_demo.py

# Cupertino (Apple-style) theme demo
uv run python examples/cupertino_theme_demo.py

# Material Design 3 theme demo
uv run python examples/material_theme_demo.py
```

These examples demonstrate:

- Dark/light mode toggle
- Theme switching between different styles
- Button Kind variants (Normal, Info, Success, Warning, Danger)
- Rounded corners and modern UI aesthetics
- Typography and spacing information display
