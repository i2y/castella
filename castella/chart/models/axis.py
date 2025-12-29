"""Axis configuration models for charts."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class AxisType(str, Enum):
    """Axis data type."""

    NUMERIC = "numeric"
    CATEGORICAL = "categorical"
    TIME = "time"


class AxisPosition(str, Enum):
    """Axis position options."""

    LEFT = "left"
    RIGHT = "right"
    TOP = "top"
    BOTTOM = "bottom"


class GridStyle(BaseModel):
    """Grid line styling.

    Attributes:
        show: Whether to show grid lines.
        color: Color of grid lines (hex string).
        line_width: Width of grid lines.
        dash_pattern: Optional dash pattern (e.g., (5.0, 5.0) for dashed).
    """

    model_config = ConfigDict(frozen=True)

    show: bool = True
    color: str = "#e5e7eb"
    line_width: float = Field(default=1.0, gt=0.0)
    dash_pattern: tuple[float, ...] | None = None


class AxisConfig(BaseModel):
    """Configuration for a chart axis.

    Attributes:
        title: Axis title text.
        position: Position of the axis.
        axis_type: Type of data on this axis.
        min_value: Minimum value (None = auto-calculate).
        max_value: Maximum value (None = auto-calculate).
        tick_count: Number of ticks to show.
        tick_format: Format string for tick labels (e.g., "{:.2f}").
        tick_labels: Explicit tick labels (for categorical axes).
        show_axis_line: Whether to show the axis line.
        axis_color: Color of the axis line.
        label_color: Color of tick labels.
        label_font_size: Font size for tick labels.
        title_font_size: Font size for axis title.
        grid: Grid line configuration.
    """

    model_config = ConfigDict(frozen=True)

    title: str = ""
    position: AxisPosition = AxisPosition.BOTTOM
    axis_type: AxisType = AxisType.NUMERIC

    # Range (None means auto-calculate)
    min_value: float | None = None
    max_value: float | None = None

    # Ticks
    tick_count: int = Field(default=5, ge=2)
    tick_format: str = ""
    tick_labels: tuple[str, ...] | None = None

    # Styling
    show_axis_line: bool = True
    axis_color: str = "#374151"
    label_color: str = "#6b7280"
    label_font_size: float = Field(default=12.0, gt=0.0)
    title_font_size: float = Field(default=14.0, gt=0.0)

    # Grid
    grid: GridStyle = Field(default_factory=GridStyle)

    def with_title(self, title: str) -> AxisConfig:
        """Create a copy with a different title."""
        return self.model_copy(update={"title": title})

    def with_range(
        self, min_value: float | None, max_value: float | None
    ) -> AxisConfig:
        """Create a copy with a different range."""
        return self.model_copy(update={"min_value": min_value, "max_value": max_value})


class XAxisConfig(AxisConfig):
    """X-axis specific configuration.

    Attributes:
        label_rotation: Rotation angle for labels (-90 to 90 degrees).
    """

    position: AxisPosition = AxisPosition.BOTTOM
    label_rotation: float = Field(default=0.0, ge=-90.0, le=90.0)


class YAxisConfig(AxisConfig):
    """Y-axis specific configuration."""

    position: AxisPosition = AxisPosition.LEFT
