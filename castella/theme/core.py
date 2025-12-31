"""Core theme classes and style generation.

This module provides:
- Theme: The main theme configuration class
- WidgetStyle: Style definition for widget states
- Style generation utilities
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, TypeAlias

from pydantic import BaseModel

from castella.models.font import Font
from castella.models.style import Shadow

from .tokens import ColorPalette, Spacing, Typography

if TYPE_CHECKING:
    from castella.core import Widget


@dataclass(slots=True, frozen=True)
class WidgetStyle:
    """Style for a specific widget state."""

    bg_color: str = "#000000"
    border_color: str = "#FFFFFF"
    text_color: str = "#FFFFFF"
    text_font: Font = Font()
    border_radius: float = 0.0
    shadow: Shadow | None = None


WidgetStyles: TypeAlias = dict[str, WidgetStyle]


class Kind(Enum):
    """Widget semantic kind for styling."""

    NORMAL = "normal"
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    DANGER = "danger"


class AppearanceState(Enum):
    """Widget appearance state."""

    NORMAL = ""
    HOVER = "_hover"
    SELECTED = "_selected"
    DISABLED = "_disabled"
    PUSHED = "_pushed"


class Theme(BaseModel):
    """Theme configuration for the entire application.

    Contains color palette, typography, and spacing tokens.
    Themes are immutable (frozen) and can be derived to create variations.
    """

    model_config = {"frozen": True}

    name: str = "default"
    is_dark: bool = False
    colors: ColorPalette
    typography: Typography = Typography()
    spacing: Spacing = Spacing()

    # Markdown-specific setting
    code_pygments_style: str = "default"

    def derive(self, **overrides) -> "Theme":
        """Create a new theme with partial overrides.

        Supports nested updates for colors, typography, and spacing.

        Example:
            new_theme = theme.derive(
                colors={"border_primary": "#00ff00"},
                typography={"base_size": 16},
            )
        """
        updates = {}
        for key in ("colors", "typography", "spacing"):
            if key in overrides:
                current = getattr(self, key)
                nested_updates = overrides.pop(key)
                if isinstance(nested_updates, dict):
                    updates[key] = current.model_copy(update=nested_updates)
                else:
                    updates[key] = nested_updates
        updates.update(overrides)
        return self.model_copy(update=updates)

    def get_widget_styles(self, widget: "Widget") -> WidgetStyles:
        """Get styles for a widget based on its class name.

        This method provides compatibility with the legacy theme system.
        """
        from copy import deepcopy

        class_name = widget.__class__.__name__.lower()
        font = Font(family=self.typography.font_family, size=self.typography.base_size)
        radius = self.spacing.border_radius

        # Generate styles based on widget type
        if class_name in ("text", "simpletext", "multilinetext", "markdown"):
            return deepcopy(generate_text_styles(self.colors, font))
        elif class_name in ("input", "multilineinput"):
            return deepcopy(generate_input_styles(self.colors, font, radius))
        elif class_name == "button":
            return deepcopy(generate_button_styles(self.colors, font, radius))
        elif class_name == "switch":
            return deepcopy(generate_switch_styles(self.colors, font, radius))
        elif class_name == "checkbox":
            return deepcopy(generate_checkbox_styles(self.colors, font, radius))
        elif class_name in ("slider", "progressbar"):
            return deepcopy(generate_slider_styles(self.colors, font, radius))
        elif class_name in ("layout", "row", "column", "box"):
            return deepcopy(generate_layout_styles(self.colors))
        elif class_name == "tree":
            return deepcopy(generate_tree_styles(self.colors, font, radius))
        else:
            # Default: return text styles for unknown widgets
            return deepcopy(generate_text_styles(self.colors, font))

    @property
    def app(self) -> WidgetStyle:
        """Get app-level style (for background)."""
        return WidgetStyle(
            bg_color=self.colors.bg_canvas,
            border_color=self.colors.border_primary,
            text_color=self.colors.text_primary,
            text_font=Font(
                family=self.typography.font_family, size=self.typography.base_size
            ),
        )

    @property
    def scrollbar(self) -> WidgetStyle:
        """Get scrollbar style."""
        return WidgetStyle(
            bg_color=self.colors.bg_secondary,
            border_color=self.colors.border_secondary,
        )

    @property
    def scrollbox(self) -> WidgetStyle:
        """Get scrollbox (thumb) style."""
        return WidgetStyle(
            bg_color=self.colors.border_secondary,
        )

    @property
    def layout(self) -> WidgetStyles:
        """Get layout styles (for Column, Row, Box)."""
        return generate_layout_styles(self.colors)

    @property
    def row(self) -> WidgetStyles:
        """Get row styles."""
        return generate_layout_styles(self.colors)

    @property
    def text(self) -> WidgetStyles:
        """Get text styles."""
        font = Font(family=self.typography.font_family, size=self.typography.base_size)
        return generate_text_styles(self.colors, font)

    @property
    def simpletext(self) -> WidgetStyles:
        """Get simpletext styles."""
        return self.text

    @property
    def multilinetext(self) -> WidgetStyles:
        """Get multilinetext styles."""
        return self.text

    @property
    def input(self) -> WidgetStyles:
        """Get input styles."""
        font = Font(family=self.typography.font_family, size=self.typography.base_size)
        return generate_input_styles(self.colors, font, self.spacing.border_radius)

    @property
    def multilineinput(self) -> WidgetStyles:
        """Get multilineinput styles."""
        return self.input

    @property
    def markdown(self) -> WidgetStyles:
        """Get markdown styles."""
        return self.text

    @property
    def button(self) -> WidgetStyles:
        """Get button styles."""
        font = Font(family=self.typography.font_family, size=self.typography.base_size)
        return generate_button_styles(self.colors, font, self.spacing.border_radius)

    @property
    def switch(self) -> WidgetStyles:
        """Get switch styles."""
        font = Font(family=self.typography.font_family, size=self.typography.base_size)
        return generate_switch_styles(self.colors, font, self.spacing.border_radius)

    @property
    def checkbox(self) -> WidgetStyles:
        """Get checkbox styles."""
        return self.switch

    @property
    def tree(self) -> WidgetStyles:
        """Get tree styles."""
        font = Font(family=self.typography.font_family, size=self.typography.base_size)
        return generate_tree_styles(self.colors, font, self.spacing.border_radius)

    @property
    def calendar(self) -> WidgetStyles:
        """Get calendar styles for day cells and headers."""
        font = Font(family=self.typography.font_family, size=self.typography.base_size)
        return generate_calendar_styles(self.colors, font, self.spacing.border_radius)


def generate_widget_style(
    colors: ColorPalette,
    kind: Kind,
    state: AppearanceState = AppearanceState.NORMAL,
    *,
    font: Font = Font(),
    use_tertiary_bg: bool = False,
    use_secondary_bg: bool = False,
    border_radius: float = 0.0,
    shadow: Shadow | None = None,
) -> WidgetStyle:
    """Generate a WidgetStyle based on Kind and AppearanceState.

    Args:
        colors: The color palette to use
        kind: Semantic kind (NORMAL, INFO, SUCCESS, etc.)
        state: Appearance state (NORMAL, HOVER, PUSHED, etc.)
        font: Font to use
        use_tertiary_bg: Use bg_tertiary instead of kind-based bg (for buttons)
        use_secondary_bg: Use bg_secondary instead of kind-based bg (for inputs)
        border_radius: Border radius for rounded corners
        shadow: Drop shadow configuration
    """
    kind_map = {
        Kind.NORMAL: ("bg_primary", "border_primary", "text_primary"),
        Kind.INFO: ("bg_info", "border_info", "text_info"),
        Kind.SUCCESS: ("bg_success", "border_success", "text_success"),
        Kind.WARNING: ("bg_warning", "border_warning", "text_warning"),
        Kind.DANGER: ("bg_danger", "border_danger", "text_danger"),
    }

    bg_key, border_key, text_key = kind_map[kind]

    # Get base colors
    bg = getattr(colors, bg_key)
    border = getattr(colors, border_key)
    text = getattr(colors, text_key)

    # Override background for specific widget types
    if use_tertiary_bg:
        bg = colors.bg_tertiary
    elif use_secondary_bg:
        bg = colors.bg_secondary

    # Apply state modifiers
    if state == AppearanceState.HOVER:
        bg = colors.bg_overlay
    elif state == AppearanceState.PUSHED:
        bg = colors.bg_pushed
        border = colors.border_secondary
    elif state == AppearanceState.SELECTED:
        bg = colors.bg_selected
    elif state == AppearanceState.DISABLED:
        # Could add disabled-specific colors later
        pass

    return WidgetStyle(
        bg_color=bg,
        border_color=border,
        text_color=text,
        text_font=font,
        border_radius=border_radius,
        shadow=shadow,
    )


def generate_widget_styles_for_kind(
    colors: ColorPalette,
    kind: Kind,
    *,
    font: Font = Font(),
    include_hover: bool = False,
    include_pushed: bool = False,
    include_selected: bool = False,
    use_tertiary_bg: bool = False,
    use_secondary_bg: bool = False,
    border_radius: float = 0.0,
    shadow: Shadow | None = None,
) -> WidgetStyles:
    """Generate all state variants for a given Kind."""
    styles: WidgetStyles = {}
    key = kind.value

    # Normal state
    styles[key] = generate_widget_style(
        colors,
        kind,
        AppearanceState.NORMAL,
        font=font,
        use_tertiary_bg=use_tertiary_bg,
        use_secondary_bg=use_secondary_bg,
        border_radius=border_radius,
        shadow=shadow,
    )

    if include_hover:
        styles[f"{key}_hover"] = generate_widget_style(
            colors,
            kind,
            AppearanceState.HOVER,
            font=font,
            use_tertiary_bg=use_tertiary_bg,
            use_secondary_bg=use_secondary_bg,
            border_radius=border_radius,
            shadow=shadow,
        )

    if include_pushed:
        styles[f"{key}_pushed"] = generate_widget_style(
            colors,
            kind,
            AppearanceState.PUSHED,
            font=font,
            use_tertiary_bg=use_tertiary_bg,
            use_secondary_bg=use_secondary_bg,
            border_radius=border_radius,
            shadow=shadow,
        )

    if include_selected:
        styles[f"{key}_selected"] = generate_widget_style(
            colors,
            kind,
            AppearanceState.SELECTED,
            font=font,
            use_tertiary_bg=use_tertiary_bg,
            use_secondary_bg=use_secondary_bg,
            border_radius=border_radius,
            shadow=shadow,
        )

    return styles


def generate_text_styles(
    colors: ColorPalette,
    font: Font = Font(),
    border_radius: float = 0.0,
    shadow: Shadow | None = None,
) -> WidgetStyles:
    """Generate styles for text widgets (Text, SimpleText, MultilineText)."""
    styles: WidgetStyles = {}
    for kind in Kind:
        styles.update(
            generate_widget_styles_for_kind(
                colors, kind, font=font, border_radius=border_radius, shadow=shadow
            )
        )
    return styles


def generate_input_styles(
    colors: ColorPalette,
    font: Font = Font(),
    border_radius: float = 0.0,
    shadow: Shadow | None = None,
) -> WidgetStyles:
    """Generate styles for input widgets (Input, MultilineInput)."""
    styles: WidgetStyles = {}
    for kind in Kind:
        styles.update(
            generate_widget_styles_for_kind(
                colors,
                kind,
                font=font,
                use_secondary_bg=True,
                border_radius=border_radius,
                shadow=shadow,
            )
        )
    return styles


def generate_button_styles(
    colors: ColorPalette,
    font: Font = Font(),
    border_radius: float = 0.0,
    shadow: Shadow | None = None,
) -> WidgetStyles:
    """Generate styles for Button widget.

    Generates styles for all Kinds (NORMAL, INFO, SUCCESS, WARNING, DANGER)
    with hover and pushed states for each.
    """
    styles: WidgetStyles = {}
    for kind in Kind:
        styles.update(
            generate_widget_styles_for_kind(
                colors,
                kind,
                font=font,
                include_hover=True,
                include_pushed=True,
                use_tertiary_bg=(kind == Kind.NORMAL),  # Only NORMAL uses tertiary bg
                border_radius=border_radius,
                shadow=shadow,
            )
        )
    return styles


def generate_switch_styles(
    colors: ColorPalette,
    font: Font = Font(),
    border_radius: float = 0.0,
    shadow: Shadow | None = None,
) -> WidgetStyles:
    """Generate styles for Switch widget."""
    return {
        "normal": WidgetStyle(
            bg_color=colors.bg_tertiary,
            border_color=colors.border_primary,
            text_color=colors.fg,
            text_font=font,
            border_radius=border_radius,
            shadow=shadow,
        ),
        "normal_selected": WidgetStyle(
            bg_color=colors.bg_selected,
            border_color=colors.border_primary,
            text_color=colors.fg,
            text_font=font,
            border_radius=border_radius,
            shadow=shadow,
        ),
    }


def generate_checkbox_styles(
    colors: ColorPalette,
    font: Font = Font(),
    border_radius: float = 0.0,
    shadow: Shadow | None = None,
) -> WidgetStyles:
    """Generate styles for Checkbox widget."""
    return generate_switch_styles(colors, font, border_radius, shadow)


def generate_slider_styles(
    colors: ColorPalette,
    font: Font = Font(),
    border_radius: float = 0.0,
    shadow: Shadow | None = None,
) -> WidgetStyles:
    """Generate styles for Slider widget."""
    return {
        # Track (background bar)
        "normal": WidgetStyle(
            bg_color=colors.bg_tertiary,
            border_color=colors.border_primary,
            text_color=colors.fg,
            text_font=font,
            border_radius=border_radius,
            shadow=shadow,
        ),
        # Fill (progress bar)
        "normal_selected": WidgetStyle(
            bg_color=colors.bg_selected,
            border_color=colors.border_primary,
            text_color=colors.fg,
            text_font=font,
            border_radius=border_radius,
            shadow=shadow,
        ),
        # Thumb (draggable knob)
        "normal_hover": WidgetStyle(
            bg_color=colors.fg,
            border_color=colors.border_primary,
            text_color=colors.bg_primary,
            text_font=font,
            border_radius=border_radius,
            shadow=shadow,
        ),
    }


def generate_layout_styles(
    colors: ColorPalette,
    border_radius: float = 0.0,
    shadow: Shadow | None = None,
) -> WidgetStyles:
    """Generate styles for layout widgets (Column, Row, Box)."""
    return {
        "normal": WidgetStyle(
            bg_color=colors.bg_primary,
            border_color=colors.border_primary,
            border_radius=border_radius,
            shadow=shadow,
        ),
    }


def generate_tree_styles(
    colors: ColorPalette,
    font: Font = Font(),
    border_radius: float = 0.0,
    shadow: Shadow | None = None,
) -> WidgetStyles:
    """Generate styles for Tree widget.

    Includes styles for:
    - normal: Default node row
    - normal_hover: Hover state
    - normal_selected: Selected node
    """
    return {
        # Default row
        "normal": WidgetStyle(
            bg_color=colors.bg_primary,
            border_color=colors.bg_primary,  # No visible border
            text_color=colors.text_primary,
            text_font=font,
            border_radius=border_radius,
            shadow=shadow,
        ),
        # Hover row
        "normal_hover": WidgetStyle(
            bg_color=colors.bg_overlay,
            border_color=colors.bg_overlay,
            text_color=colors.text_primary,
            text_font=font,
            border_radius=border_radius,
            shadow=shadow,
        ),
        # Selected row
        "normal_selected": WidgetStyle(
            bg_color=colors.bg_selected,
            border_color=colors.bg_selected,
            text_color=colors.text_primary,
            text_font=font,
            border_radius=border_radius,
            shadow=shadow,
        ),
    }


def generate_calendar_styles(
    colors: ColorPalette,
    font: Font = Font(),
    border_radius: float = 0.0,
) -> WidgetStyles:
    """Generate styles for calendar widgets.

    Returns styles for:
    - day_normal: Regular day cells
    - day_muted: Days from previous/next month
    - day_hover: Hovered day cell
    - day_selected: Selected day cell
    - day_today: Today indicator (outline)
    - day_disabled: Disabled day cell
    - weekday_header: Weekday header row
    """
    return {
        # Regular day cell
        "day_normal": WidgetStyle(
            bg_color=colors.bg_primary,
            border_color=colors.bg_primary,
            text_color=colors.text_primary,
            text_font=font,
            border_radius=border_radius,
        ),
        # Day from previous/next month (muted)
        "day_muted": WidgetStyle(
            bg_color=colors.bg_primary,
            border_color=colors.bg_primary,
            text_color=colors.text_info,
            text_font=font,
            border_radius=border_radius,
        ),
        # Hovered day cell
        "day_hover": WidgetStyle(
            bg_color=colors.bg_overlay,
            border_color=colors.border_primary,
            text_color=colors.text_primary,
            text_font=font,
            border_radius=border_radius,
        ),
        # Selected day cell
        "day_selected": WidgetStyle(
            bg_color=colors.bg_selected,
            border_color=colors.border_info,
            text_color=colors.fg,
            text_font=font,
            border_radius=border_radius,
        ),
        # Today indicator (border only, not filled)
        "day_today": WidgetStyle(
            bg_color=colors.bg_primary,
            border_color=colors.border_info,
            text_color=colors.text_info,
            text_font=font,
            border_radius=border_radius,
        ),
        # Disabled day cell
        "day_disabled": WidgetStyle(
            bg_color=colors.bg_tertiary,
            border_color=colors.bg_tertiary,
            text_color=colors.border_secondary,
            text_font=font,
            border_radius=border_radius,
        ),
        # Weekday header row
        "weekday_header": WidgetStyle(
            bg_color=colors.bg_secondary,
            border_color=colors.bg_secondary,
            text_color=colors.text_info,
            text_font=font,
            border_radius=0.0,
        ),
    }
