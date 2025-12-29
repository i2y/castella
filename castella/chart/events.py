"""Chart event models."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from castella.models.geometry import Point


class ChartHoverEvent(BaseModel):
    """Event emitted when hovering over a chart element.

    Attributes:
        series_index: Index of the series containing the hovered element.
        data_index: Index of the data point within the series.
        value: The value at this data point.
        label: The label of this data point.
        position: Screen position of the cursor.
    """

    model_config = ConfigDict(frozen=True)

    series_index: int
    data_index: int
    value: float
    label: str
    position: Point


class ChartClickEvent(BaseModel):
    """Event emitted when clicking on a chart element.

    Attributes:
        series_index: Index of the series containing the clicked element.
        data_index: Index of the data point within the series.
        value: The value at this data point.
        label: The label of this data point.
        position: Screen position of the click.
        is_double_click: Whether this was a double-click.
    """

    model_config = ConfigDict(frozen=True)

    series_index: int
    data_index: int
    value: float
    label: str
    position: Point
    is_double_click: bool = False


class ChartSelectionEvent(BaseModel):
    """Event emitted when selection changes.

    Attributes:
        selected_indices: List of (series_index, data_index) tuples for selected points.
    """

    model_config = ConfigDict(frozen=True)

    selected_indices: list[tuple[int, int]] = Field(default_factory=list)


class SeriesVisibilityEvent(BaseModel):
    """Event emitted when series visibility changes via legend.

    Attributes:
        series_index: Index of the series.
        series_name: Name of the series.
        visible: Whether the series is now visible.
    """

    model_config = ConfigDict(frozen=True)

    series_index: int
    series_name: str
    visible: bool


class ZoomEvent(BaseModel):
    """Event emitted when zoom level changes.

    Attributes:
        zoom_level: Current zoom level (1.0 = no zoom).
        view_x_min: Minimum X value in current view.
        view_x_max: Maximum X value in current view.
        view_y_min: Minimum Y value in current view.
        view_y_max: Maximum Y value in current view.
    """

    model_config = ConfigDict(frozen=True)

    zoom_level: float
    view_x_min: float
    view_x_max: float
    view_y_min: float
    view_y_max: float


class PanEvent(BaseModel):
    """Event emitted when chart is panned.

    Attributes:
        pan_x: Pan amount in data X units.
        pan_y: Pan amount in data Y units.
    """

    model_config = ConfigDict(frozen=True)

    pan_x: float
    pan_y: float
