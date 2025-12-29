"""Series models for charts."""

from __future__ import annotations

from typing import Sequence

from pydantic import BaseModel, ConfigDict, Field

from castella.chart.models.data_points import DataPoint, NumericDataPoint


class SeriesStyle(BaseModel):
    """Styling for a data series.

    Attributes:
        color: Primary color for the series (hex string).
        fill_color: Optional fill color (for area charts). Defaults to color.
        fill_opacity: Opacity for filled areas (0.0-1.0).
        line_width: Width of lines in pixels.
        point_radius: Radius of data points in pixels.
        show_points: Whether to show data point markers.
        show_line: Whether to show connecting lines (for line charts).
    """

    model_config = ConfigDict(frozen=True)

    color: str = "#3b82f6"
    fill_color: str | None = None
    fill_opacity: float = Field(default=0.3, ge=0.0, le=1.0)
    line_width: float = Field(default=2.0, gt=0.0)
    point_radius: float = Field(default=4.0, ge=0.0)
    show_points: bool = True
    show_line: bool = True

    def with_color(self, color: str) -> SeriesStyle:
        """Create a copy with a different color."""
        return self.model_copy(update={"color": color})

    def with_opacity(self, opacity: float) -> SeriesStyle:
        """Create a copy with a different fill opacity."""
        return self.model_copy(update={"fill_opacity": opacity})


class CategoricalSeries(BaseModel):
    """Series for categorical data (Bar, Pie, Stacked Bar).

    Attributes:
        name: Display name for the series (shown in legend).
        data: Tuple of data points.
        style: Styling for this series.
    """

    model_config = ConfigDict(frozen=True)

    name: str
    data: tuple[DataPoint, ...] = Field(default_factory=tuple)
    style: SeriesStyle = Field(default_factory=SeriesStyle)

    @classmethod
    def from_values(
        cls,
        name: str,
        categories: Sequence[str],
        values: Sequence[float],
        style: SeriesStyle | None = None,
        labels: Sequence[str] | None = None,
    ) -> CategoricalSeries:
        """Create a series from parallel sequences of categories and values.

        Args:
            name: Series name.
            categories: List of category names.
            values: List of values (must match categories length).
            style: Optional style override.
            labels: Optional labels for each point.

        Returns:
            A new CategoricalSeries instance.
        """
        if len(categories) != len(values):
            raise ValueError("categories and values must have the same length")

        points = tuple(
            DataPoint(
                category=cat,
                value=val,
                label=labels[i] if labels else cat,
            )
            for i, (cat, val) in enumerate(zip(categories, values))
        )
        return cls(name=name, data=points, style=style or SeriesStyle())

    @property
    def categories(self) -> list[str]:
        """Get list of categories from data points."""
        return [p.category for p in self.data]

    @property
    def values(self) -> list[float]:
        """Get list of values from data points."""
        return [p.value for p in self.data]


class NumericSeries(BaseModel):
    """Series for numeric/continuous data (Line, Scatter, Area).

    Attributes:
        name: Display name for the series (shown in legend).
        data: Tuple of numeric data points.
        style: Styling for this series.
    """

    model_config = ConfigDict(frozen=True)

    name: str
    data: tuple[NumericDataPoint, ...] = Field(default_factory=tuple)
    style: SeriesStyle = Field(default_factory=SeriesStyle)

    @classmethod
    def from_values(
        cls,
        name: str,
        x_values: Sequence[float],
        y_values: Sequence[float],
        style: SeriesStyle | None = None,
        labels: Sequence[str] | None = None,
    ) -> NumericSeries:
        """Create a series from parallel sequences of x and y values.

        Args:
            name: Series name.
            x_values: List of X-axis values.
            y_values: List of Y-axis values (must match x_values length).
            style: Optional style override.
            labels: Optional labels for each point.

        Returns:
            A new NumericSeries instance.
        """
        if len(x_values) != len(y_values):
            raise ValueError("x_values and y_values must have the same length")

        points = tuple(
            NumericDataPoint(
                x=x,
                y=y,
                label=labels[i] if labels else f"({x}, {y})",
            )
            for i, (x, y) in enumerate(zip(x_values, y_values))
        )
        return cls(name=name, data=points, style=style or SeriesStyle())

    @classmethod
    def from_y_values(
        cls,
        name: str,
        y_values: Sequence[float],
        style: SeriesStyle | None = None,
    ) -> NumericSeries:
        """Create a series from Y values only (X will be 0, 1, 2, ...).

        Args:
            name: Series name.
            y_values: List of Y-axis values.
            style: Optional style override.

        Returns:
            A new NumericSeries instance.
        """
        x_values = list(range(len(y_values)))
        return cls.from_values(name, x_values, y_values, style)

    @property
    def x_values(self) -> list[float]:
        """Get list of X values from data points."""
        return [p.x for p in self.data]

    @property
    def y_values(self) -> list[float]:
        """Get list of Y values from data points."""
        return [p.y for p in self.data]
