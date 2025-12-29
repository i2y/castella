"""Legend configuration models for charts."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class LegendPosition(str, Enum):
    """Legend position options."""

    TOP = "top"
    BOTTOM = "bottom"
    LEFT = "left"
    RIGHT = "right"
    TOP_LEFT = "top_left"
    TOP_RIGHT = "top_right"
    BOTTOM_LEFT = "bottom_left"
    BOTTOM_RIGHT = "bottom_right"
    NONE = "none"  # Hide legend


class LegendConfig(BaseModel):
    """Legend configuration.

    Attributes:
        position: Position of the legend.
        show: Whether to show the legend.
        font_size: Font size for legend text.
        text_color: Color of legend text.
        background_color: Background color (None = transparent).
        padding: Padding inside the legend box.
        item_spacing: Spacing between legend items.
        interactive: Whether clicking legend items toggles series visibility.
    """

    model_config = ConfigDict(frozen=True)

    position: LegendPosition = LegendPosition.TOP_RIGHT
    show: bool = True
    font_size: float = Field(default=12.0, gt=0.0)
    text_color: str = "#374151"
    background_color: str | None = None
    padding: float = Field(default=8.0, ge=0.0)
    item_spacing: float = Field(default=16.0, ge=0.0)
    interactive: bool = True

    def hidden(self) -> LegendConfig:
        """Create a copy with legend hidden."""
        return self.model_copy(update={"show": False})

    def at_position(self, position: LegendPosition) -> LegendConfig:
        """Create a copy with a different position."""
        return self.model_copy(update={"position": position})
