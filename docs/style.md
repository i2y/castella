# Styling

Castella provides a comprehensive theming system with design tokens (colors, typography, spacing) and per-widget styling options.

## Theme System

The theme system is located in `castella.theme` and provides:

- **ColorPalette**: All color definitions (backgrounds, text, borders)
- **Typography**: Font settings (family, size, scale)
- **Spacing**: Layout measurements (padding, margin, border radius)
- **ThemeManager**: Singleton for dynamic theme switching

### Automatic Theming

Castella automatically detects dark/light mode from the operating system and applies appropriate colors. Two built-in themes are provided:

- **DARK_THEME**: Neon-style colors on a dark background
- **LIGHT_THEME**: Soft pastel colors on a light background

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
from castella import Text, Kind

Text("Normal text", kind=Kind.NORMAL)   # Default styling
Text("Info message", kind=Kind.INFO)    # Cyan/blue tones
Text("Success!", kind=Kind.SUCCESS)     # Green tones
Text("Warning!", kind=Kind.WARNING)     # Yellow/amber tones
Text("Error!", kind=Kind.DANGER)        # Red/pink tones
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

### Dark Theme (DARK_PALETTE)

```python
{
    "bg_canvas": "#1e1e1e",
    "fg": "#f8f8f2",
    "text_info": "#00ffff",      # Neon cyan
    "text_danger": "#ff6347",    # Neon red
    "text_success": "#32cd32",   # Neon green
    "text_warning": "#ffd700",   # Neon yellow
    "border_primary": "#bd93f9", # Neon purple
}
```

### Light Theme (LIGHT_PALETTE)

```python
{
    "bg_canvas": "#fff0f6",      # Light pink
    "fg": "#212121",             # Dark text
    "text_info": "#7e57c2",      # Purple
    "text_danger": "#ec407a",    # Pink
    "text_success": "#66bb6a",   # Light green
    "text_warning": "#ffb300",   # Amber
    "border_primary": "#ba68c8", # Light purple
}
```

## Example: Theme Demo

Run the theme demo to see all features in action:

```bash
uv run python examples/theme_demo.py
```

This example demonstrates:

- Dark/light mode toggle
- Custom theme application (Cyberpunk, Ocean themes)
- Theme derivation
- Widget showcase with different Kinds
- Typography and spacing information display
