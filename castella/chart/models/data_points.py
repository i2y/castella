"""Data point models for charts."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class DataPoint(BaseModel):
    """Immutable data point for categorical charts (Bar, Pie).

    Attributes:
        value: The numeric value of this data point.
        label: Optional label for display (e.g., tooltip).
        category: The category this point belongs to.
        metadata: Optional additional data for custom use.
    """

    model_config = ConfigDict(frozen=True)

    value: float
    label: str = ""
    category: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


class NumericDataPoint(BaseModel):
    """Immutable data point for numeric/continuous charts (Line, Scatter, Area).

    Attributes:
        x: X-axis value.
        y: Y-axis value.
        label: Optional label for display.
        metadata: Optional additional data.
    """

    model_config = ConfigDict(frozen=True)

    x: float
    y: float
    label: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


class GaugeDataPoint(BaseModel):
    """Immutable data point for gauge charts.

    Attributes:
        value: Current value to display.
        min_value: Minimum value of the gauge range.
        max_value: Maximum value of the gauge range.
        label: Optional label for display.
    """

    model_config = ConfigDict(frozen=True)

    value: float = Field(default=0.0, ge=0.0)
    min_value: float = Field(default=0.0)
    max_value: float = Field(default=100.0)
    label: str = ""

    @property
    def percentage(self) -> float:
        """Get value as percentage of range."""
        range_val = self.max_value - self.min_value
        if range_val == 0:
            return 0.0
        return (self.value - self.min_value) / range_val
