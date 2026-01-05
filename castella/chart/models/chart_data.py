"""Chart data models - Observable containers for chart data."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Generator, Self

from pydantic import BaseModel, ConfigDict, Field, PrivateAttr

from castella.chart.models.axis import AxisType, XAxisConfig, YAxisConfig
from castella.chart.models.legend import LegendConfig
from castella.chart.models.animation import AnimationConfig
from castella.chart.models.series import CategoricalSeries, NumericSeries


class ChartDataBase(BaseModel):
    """Base observable chart data model.

    This class combines Pydantic validation with the Observer pattern
    for reactive updates.

    Attributes:
        title: Chart title.
        subtitle: Optional subtitle.
        legend: Legend configuration.
        animation: Animation configuration.
    """

    model_config = ConfigDict(validate_assignment=True)

    title: str = ""
    subtitle: str = ""
    legend: LegendConfig = Field(default_factory=LegendConfig)
    animation: AnimationConfig = Field(default_factory=AnimationConfig)

    # Observable pattern - private attributes
    _observers: list[Any] = PrivateAttr(default_factory=list)
    _series_visibility: dict[int, bool] = PrivateAttr(default_factory=dict)
    _data_visibility: dict[tuple[int, int], bool] = PrivateAttr(default_factory=dict)
    _selected_points: set[tuple[int, int]] = PrivateAttr(default_factory=set)
    _batch_updating: bool = PrivateAttr(default=False)

    def attach(self, observer: Any) -> None:
        """Attach an observer to be notified of changes.

        Duplicate observers are ignored to prevent accumulation.

        Args:
            observer: An object with on_notify() and optionally on_attach() methods.
        """
        if observer not in self._observers:
            self._observers.append(observer)
            if hasattr(observer, "on_attach"):
                observer.on_attach(self)

    def detach(self, observer: Any) -> None:
        """Detach an observer.

        Args:
            observer: The observer to remove.
        """
        if observer in self._observers:
            self._observers.remove(observer)
            if hasattr(observer, "on_detach"):
                observer.on_detach(self)

    def notify(self, event: Any = None) -> None:
        """Notify all observers of a change.

        Notifications are skipped when inside a batch_update() context.

        Args:
            event: Optional event data to pass to observers.
        """
        if self._batch_updating:
            return
        for observer in self._observers:
            observer.on_notify(event)

    @contextmanager
    def batch_update(self) -> Generator[None, None, None]:
        """Context manager for batch updates.

        While inside this context, notify() calls are suppressed.
        A single notify() is called when the context exits.

        Example:
            with chart_data.batch_update():
                chart_data.series = new_series1
                chart_data.set_series([series1, series2])
            # notify() is called once here
        """
        self._batch_updating = True
        try:
            yield
        finally:
            self._batch_updating = False
            self.notify()

    # Series visibility management

    def is_series_visible(self, series_index: int) -> bool:
        """Check if a series is visible.

        Args:
            series_index: Index of the series.

        Returns:
            True if visible (default), False if hidden.
        """
        return self._series_visibility.get(series_index, True)

    def set_series_visibility(self, series_index: int, visible: bool) -> Self:
        """Set visibility of a series.

        Args:
            series_index: Index of the series.
            visible: Whether the series should be visible.

        Returns:
            Self for chaining.
        """
        self._series_visibility[series_index] = visible
        self.notify()
        return self

    def toggle_series_visibility(self, series_index: int) -> Self:
        """Toggle visibility of a series.

        Args:
            series_index: Index of the series.

        Returns:
            Self for chaining.
        """
        current = self.is_series_visible(series_index)
        return self.set_series_visibility(series_index, not current)

    # Data point visibility management (for PieChart slices)

    def is_data_visible(self, series_index: int, data_index: int) -> bool:
        """Check if a data point is visible.

        Args:
            series_index: Index of the series.
            data_index: Index of the data point.

        Returns:
            True if visible (default), False if hidden.
        """
        return self._data_visibility.get((series_index, data_index), True)

    def set_data_visibility(
        self, series_index: int, data_index: int, visible: bool
    ) -> Self:
        """Set visibility of a data point.

        Args:
            series_index: Index of the series.
            data_index: Index of the data point.
            visible: Whether the data point should be visible.

        Returns:
            Self for chaining.
        """
        self._data_visibility[(series_index, data_index)] = visible
        self.notify()
        return self

    def toggle_data_visibility(self, series_index: int, data_index: int) -> Self:
        """Toggle visibility of a data point.

        Args:
            series_index: Index of the series.
            data_index: Index of the data point.

        Returns:
            Self for chaining.
        """
        current = self.is_data_visible(series_index, data_index)
        return self.set_data_visibility(series_index, data_index, not current)

    # Point selection management

    def is_selected(self, series_index: int, data_index: int) -> bool:
        """Check if a point is selected.

        Args:
            series_index: Index of the series.
            data_index: Index of the data point within the series.

        Returns:
            True if selected, False otherwise.
        """
        return (series_index, data_index) in self._selected_points

    def select_point(self, series_index: int, data_index: int) -> Self:
        """Select a data point.

        Args:
            series_index: Index of the series.
            data_index: Index of the data point.

        Returns:
            Self for chaining.
        """
        self._selected_points.add((series_index, data_index))
        self.notify()
        return self

    def deselect_point(self, series_index: int, data_index: int) -> Self:
        """Deselect a data point.

        Args:
            series_index: Index of the series.
            data_index: Index of the data point.

        Returns:
            Self for chaining.
        """
        self._selected_points.discard((series_index, data_index))
        self.notify()
        return self

    def clear_selection(self) -> Self:
        """Clear all selected points.

        Returns:
            Self for chaining.
        """
        self._selected_points.clear()
        self.notify()
        return self

    @property
    def selected_points(self) -> set[tuple[int, int]]:
        """Get the set of selected points as (series_index, data_index) tuples."""
        return self._selected_points.copy()


class CategoricalChartData(ChartDataBase):
    """Data model for categorical charts (Bar, Pie, Stacked Bar).

    Attributes:
        series: List of categorical data series.
        x_axis: X-axis configuration.
        y_axis: Y-axis configuration.
    """

    series: list[CategoricalSeries] = Field(default_factory=list)
    x_axis: XAxisConfig = Field(
        default_factory=lambda: XAxisConfig(axis_type=AxisType.CATEGORICAL)
    )
    y_axis: YAxisConfig = Field(default_factory=YAxisConfig)

    def add_series(self, series: CategoricalSeries) -> Self:
        """Add a series and notify observers.

        Args:
            series: The series to add.

        Returns:
            Self for chaining.
        """
        self.series = [*self.series, series]
        self.notify()
        return self

    def set_series(self, series: list[CategoricalSeries]) -> Self:
        """Replace all series and notify observers.

        Args:
            series: The new list of series.

        Returns:
            Self for chaining.
        """
        self.series = series
        self.notify()
        return self

    def update_series(self, index: int, series: CategoricalSeries) -> Self:
        """Update a specific series by index.

        Args:
            index: Index of the series to update.
            series: The new series data.

        Returns:
            Self for chaining.
        """
        if 0 <= index < len(self.series):
            new_series = list(self.series)
            new_series[index] = series
            self.series = new_series
            self.notify()
        return self

    @property
    def all_categories(self) -> list[str]:
        """Get all unique categories across all series."""
        categories: list[str] = []
        for s in self.series:
            for cat in s.categories:
                if cat not in categories:
                    categories.append(cat)
        return categories

    @property
    def max_value(self) -> float:
        """Get the maximum value across all visible series."""
        max_val = 0.0
        for i, s in enumerate(self.series):
            if self.is_series_visible(i) and s.values:
                max_val = max(max_val, max(s.values))
        return max_val


class NumericChartData(ChartDataBase):
    """Data model for numeric/continuous charts (Line, Scatter, Area).

    Attributes:
        series: List of numeric data series.
        x_axis: X-axis configuration.
        y_axis: Y-axis configuration.
    """

    series: list[NumericSeries] = Field(default_factory=list)
    x_axis: XAxisConfig = Field(default_factory=XAxisConfig)
    y_axis: YAxisConfig = Field(default_factory=YAxisConfig)

    def add_series(self, series: NumericSeries) -> Self:
        """Add a series and notify observers.

        Args:
            series: The series to add.

        Returns:
            Self for chaining.
        """
        self.series = [*self.series, series]
        self.notify()
        return self

    def set_series(self, series: list[NumericSeries]) -> Self:
        """Replace all series and notify observers.

        Args:
            series: The new list of series.

        Returns:
            Self for chaining.
        """
        self.series = series
        self.notify()
        return self

    def update_series(self, index: int, series: NumericSeries) -> Self:
        """Update a specific series by index.

        Args:
            index: Index of the series to update.
            series: The new series data.

        Returns:
            Self for chaining.
        """
        if 0 <= index < len(self.series):
            new_series = list(self.series)
            new_series[index] = series
            self.series = new_series
            self.notify()
        return self

    @property
    def x_range(self) -> tuple[float, float]:
        """Get the X value range across all visible series."""
        x_min = float("inf")
        x_max = float("-inf")
        for i, s in enumerate(self.series):
            if self.is_series_visible(i) and s.x_values:
                x_min = min(x_min, min(s.x_values))
                x_max = max(x_max, max(s.x_values))
        if x_min == float("inf"):
            return (0.0, 1.0)
        return (x_min, x_max)

    @property
    def y_range(self) -> tuple[float, float]:
        """Get the Y value range across all visible series."""
        y_min = float("inf")
        y_max = float("-inf")
        for i, s in enumerate(self.series):
            if self.is_series_visible(i) and s.y_values:
                y_min = min(y_min, min(s.y_values))
                y_max = max(y_max, max(s.y_values))
        if y_min == float("inf"):
            return (0.0, 1.0)
        return (y_min, y_max)


class GaugeChartData(ChartDataBase):
    """Data model for gauge/donut charts.

    Attributes:
        value: Current value to display.
        min_value: Minimum value of the gauge range.
        max_value: Maximum value of the gauge range.
        arc_width: Width of the gauge arc.
        start_angle: Starting angle in degrees (-135 = bottom-left).
        end_angle: Ending angle in degrees (135 = bottom-right).
        thresholds: Color thresholds as (percentage, color) tuples.
        background_color: Color of the unfilled arc.
        show_value: Whether to show the value text.
        value_format: Format string for the value display.
    """

    value: float = Field(default=0.0)
    min_value: float = Field(default=0.0)
    max_value: float = Field(default=100.0)

    # Gauge styling
    arc_width: float = Field(default=20.0, gt=0.0)
    start_angle: float = Field(default=-135.0)
    end_angle: float = Field(default=135.0)

    # Color thresholds (percentage -> color)
    thresholds: list[tuple[float, str]] = Field(
        default_factory=lambda: [
            (0.0, "#ef4444"),  # Red for low
            (0.33, "#f59e0b"),  # Yellow for medium
            (0.66, "#22c55e"),  # Green for high
        ]
    )

    background_color: str = "#e5e7eb"
    show_value: bool = True
    value_format: str = "{:.0f}"

    @property
    def percentage(self) -> float:
        """Get current value as percentage of range."""
        range_val = self.max_value - self.min_value
        if range_val == 0:
            return 0.0
        return (self.value - self.min_value) / range_val

    @property
    def current_color(self) -> str:
        """Get the color for the current value based on thresholds."""
        pct = self.percentage
        color = self.thresholds[0][1] if self.thresholds else "#3b82f6"
        for threshold_pct, threshold_color in self.thresholds:
            if pct >= threshold_pct:
                color = threshold_color
        return color

    def set_value(self, value: float) -> Self:
        """Set the gauge value and notify observers.

        Args:
            value: The new value.

        Returns:
            Self for chaining.
        """
        self.value = value
        self.notify()
        return self
