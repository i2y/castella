# Castella Theme System

Comprehensive theming with design tokens for consistent styling.

## ThemeManager

Singleton for theme management:

```python
from castella.theme import ThemeManager

manager = ThemeManager()

# Get current theme
theme = manager.current
print(f"{theme.name}, dark={theme.is_dark}")

# Toggle dark/light mode
manager.toggle_dark_mode()

# Force dark mode
manager.prefer_dark(True)
```

## Built-in Themes

### Tokyo Night (Default)
Purple/blue aesthetic with 6px rounded corners.

```python
from castella.theme import TOKYO_NIGHT_DARK_THEME, TOKYO_NIGHT_LIGHT_THEME

manager.set_dark_theme(TOKYO_NIGHT_DARK_THEME)
manager.set_light_theme(TOKYO_NIGHT_LIGHT_THEME)
```

### Cupertino
Apple-inspired design with 8px rounded corners.

```python
from castella.theme import CUPERTINO_DARK_THEME, CUPERTINO_LIGHT_THEME

manager.set_dark_theme(CUPERTINO_DARK_THEME)
manager.set_light_theme(CUPERTINO_LIGHT_THEME)
```

### Material Design 3
Google's Material design with 12px rounded corners.

```python
from castella.theme import MATERIAL_DARK_THEME, MATERIAL_LIGHT_THEME

manager.set_dark_theme(MATERIAL_DARK_THEME)
manager.set_light_theme(MATERIAL_LIGHT_THEME)
```

### Classic Castella
Original neon/pastel themes.

```python
from castella.theme import DARK_THEME, LIGHT_THEME
```

## Theme Properties

### Colors (ColorPalette)

```python
theme = manager.current

# Background colors
theme.colors.bg_canvas      # Main background
theme.colors.bg_primary     # Primary surface
theme.colors.bg_secondary   # Secondary surface
theme.colors.bg_tertiary    # Tertiary surface

# Text colors
theme.colors.text_primary   # Main text
theme.colors.text_secondary # Secondary text
theme.colors.text_muted     # Muted text

# Semantic colors
theme.colors.text_info      # Info blue
theme.colors.text_success   # Success green
theme.colors.text_warning   # Warning yellow
theme.colors.text_danger    # Danger red

# Border colors
theme.colors.border_primary
theme.colors.border_secondary
```

### Typography

```python
theme.typography.font_family       # Default font
theme.typography.font_family_mono  # Monospace font
theme.typography.base_size         # Base font size (px)
theme.typography.scale_ratio       # Size scaling ratio
```

### Spacing

```python
theme.spacing.padding_sm    # Small padding
theme.spacing.padding_md    # Medium padding
theme.spacing.padding_lg    # Large padding
theme.spacing.margin_sm     # Small margin
theme.spacing.margin_md     # Medium margin
theme.spacing.margin_lg     # Large margin
theme.spacing.border_radius # Corner radius
theme.spacing.border_width  # Border width
```

## Creating Custom Themes

### Derive from Existing Theme

Partial override of an existing theme:

```python
from castella.theme import TOKYO_NIGHT_DARK_THEME

custom = TOKYO_NIGHT_DARK_THEME.derive(
    colors={
        "border_primary": "#00ff00",
        "text_info": "#00ffff",
    },
    typography={"base_size": 16},
    spacing={"border_radius": 12},
)

manager.set_dark_theme(custom)
```

### Create New Theme

Complete custom theme:

```python
from castella.theme import Theme, ColorPalette, Typography, Spacing

my_palette = ColorPalette(
    bg_canvas="#0a0a0a",
    bg_primary="#121212",
    bg_secondary="#1a1a1a",
    bg_tertiary="#242424",
    text_primary="#ffffff",
    text_secondary="#b0b0b0",
    text_muted="#707070",
    text_info="#64b5f6",
    text_success="#81c784",
    text_warning="#ffb74d",
    text_danger="#e57373",
    border_primary="#333333",
    border_secondary="#444444",
)

my_theme = Theme(
    name="my-custom-theme",
    is_dark=True,
    colors=my_palette,
    typography=Typography(
        font_family="Inter",
        font_family_mono="JetBrains Mono",
        base_size=14,
        scale_ratio=1.25,
    ),
    spacing=Spacing(
        padding_sm=4,
        padding_md=8,
        padding_lg=16,
        margin_sm=4,
        margin_md=8,
        margin_lg=16,
        border_radius=8,
        border_width=1,
    ),
    code_pygments_style="monokai",
)

manager.set_dark_theme(my_theme)
```

## Widget Styles

Themes provide default styles for widgets:

```python
theme.button        # Button styles by Kind and AppearanceState
theme.input         # Input field styles
theme.text          # Text styles
theme.scrollbar     # Scrollbar styles
theme.scrollbox     # Scrollbox container styles
```

## Environment Variables

Override theme at runtime:

```bash
CASTELLA_DARK_MODE=true   # Force dark mode
CASTELLA_DARK_MODE=false  # Force light mode
```

## Theme Demos

Run built-in theme demos:

```bash
uv run python examples/tokyo_night_theme_demo.py
uv run python examples/cupertino_theme_demo.py
uv run python examples/material_theme_demo.py
```
