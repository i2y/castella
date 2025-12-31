"""Chart theme integration with Castella theme system."""

from __future__ import annotations

from dataclasses import dataclass, field

from castella.theme import ThemeManager, ColorPalette


# Default chart color palette (used when theme colors aren't available)
DEFAULT_SERIES_COLORS = [
    "#3b82f6",  # Blue
    "#22c55e",  # Green
    "#f59e0b",  # Amber
    "#ef4444",  # Red
    "#8b5cf6",  # Violet
    "#06b6d4",  # Cyan
    "#ec4899",  # Pink
    "#84cc16",  # Lime
]


@dataclass
class ChartTheme:
    """Chart-specific theme derived from Castella theme.

    This class extracts and organizes theme colors for use in charts,
    ensuring consistent styling with the rest of the application.

    Attributes:
        background: Background color for the chart area.
        axis_color: Color for axis lines.
        grid_color: Color for grid lines.
        text_color: Primary text color.
        text_secondary: Secondary text color (for less important text).
        title_color: Color for chart title.
        border_color: Border color.
        tooltip_bg: Tooltip background color.
        tooltip_border: Tooltip border color.
        tooltip_text: Tooltip text color.
        series_colors: List of colors for data series.
        is_dark: Whether this is a dark theme.
    """

    background: str = "#ffffff"
    axis_color: str = "#374151"
    grid_color: str = "#e5e7eb"
    text_color: str = "#1f2937"
    text_secondary: str = "#6b7280"
    title_color: str = "#111827"
    border_color: str = "#d1d5db"
    tooltip_bg: str = "#1f2937"
    tooltip_border: str = "#374151"
    tooltip_text: str = "#ffffff"
    series_colors: list[str] = field(
        default_factory=lambda: list(DEFAULT_SERIES_COLORS)
    )
    is_dark: bool = False

    @classmethod
    def from_palette(cls, palette: ColorPalette, is_dark: bool = False) -> ChartTheme:
        """Create a chart theme from a ColorPalette.

        Args:
            palette: The color palette to use.
            is_dark: Whether this is a dark theme.

        Returns:
            A new ChartTheme instance.
        """
        # Build series colors from semantic colors
        series_colors = [
            palette.text_info,
            palette.text_success,
            palette.text_warning,
            palette.text_danger,
        ]
        # Add more colors from defaults if needed
        series_colors.extend(c for c in DEFAULT_SERIES_COLORS if c not in series_colors)

        # Use border_secondary as a secondary text color (lighter/dimmer)
        text_secondary = palette.border_primary

        # Tooltip text should contrast with tooltip_bg (bg_secondary)
        # For dark themes, bg_secondary is dark so use light text
        # For light themes, bg_secondary is light so use dark text
        tooltip_text = "#ffffff" if is_dark else palette.text_primary

        return cls(
            background=palette.bg_primary,
            axis_color=palette.border_primary,
            grid_color=palette.border_secondary,
            text_color=palette.text_primary,
            text_secondary=text_secondary,
            title_color=palette.text_primary,
            border_color=palette.border_primary,
            tooltip_bg=palette.bg_secondary,
            tooltip_border=palette.border_primary,
            tooltip_text=tooltip_text,
            series_colors=series_colors,
            is_dark=is_dark,
        )

    @classmethod
    def from_current_theme(cls) -> ChartTheme:
        """Create a chart theme from the current ThemeManager theme.

        Returns:
            A new ChartTheme instance matching the current theme.
        """
        manager = ThemeManager()
        theme = manager.current
        return cls.from_palette(theme.colors, theme.is_dark)

    def get_series_color(self, index: int) -> str:
        """Get the color for a series by index.

        Args:
            index: Series index.

        Returns:
            Hex color string.
        """
        return self.series_colors[index % len(self.series_colors)]

    def with_series_colors(self, colors: list[str]) -> ChartTheme:
        """Create a copy with custom series colors.

        Args:
            colors: List of hex color strings.

        Returns:
            A new ChartTheme with the custom colors.
        """
        return ChartTheme(
            background=self.background,
            axis_color=self.axis_color,
            grid_color=self.grid_color,
            text_color=self.text_color,
            text_secondary=self.text_secondary,
            title_color=self.title_color,
            border_color=self.border_color,
            tooltip_bg=self.tooltip_bg,
            tooltip_border=self.tooltip_border,
            tooltip_text=self.tooltip_text,
            series_colors=colors,
            is_dark=self.is_dark,
        )


# Convenience function
def get_chart_theme() -> ChartTheme:
    """Get the current chart theme.

    Returns:
        ChartTheme matching the current application theme.
    """
    return ChartTheme.from_current_theme()
