"""Chart data models - Pydantic v2 based."""

from castella.chart.models.data_points import (
    DataPoint,
    NumericDataPoint,
    GaugeDataPoint,
)
from castella.chart.models.series import (
    SeriesStyle,
    CategoricalSeries,
    NumericSeries,
)
from castella.chart.models.axis import (
    AxisType,
    AxisPosition,
    GridStyle,
    AxisConfig,
    XAxisConfig,
    YAxisConfig,
)
from castella.chart.models.legend import (
    LegendPosition,
    LegendConfig,
)
from castella.chart.models.animation import (
    EasingFunction,
    AnimationConfig,
)
from castella.chart.models.chart_data import (
    ChartDataBase,
    CategoricalChartData,
    NumericChartData,
    GaugeChartData,
)
from castella.chart.models.heatmap_data import HeatmapChartData

__all__ = [
    # Data points
    "DataPoint",
    "NumericDataPoint",
    "GaugeDataPoint",
    # Series
    "SeriesStyle",
    "CategoricalSeries",
    "NumericSeries",
    # Axis
    "AxisType",
    "AxisPosition",
    "GridStyle",
    "AxisConfig",
    "XAxisConfig",
    "YAxisConfig",
    # Legend
    "LegendPosition",
    "LegendConfig",
    # Animation
    "EasingFunction",
    "AnimationConfig",
    # Chart data
    "ChartDataBase",
    "CategoricalChartData",
    "NumericChartData",
    "GaugeChartData",
    "HeatmapChartData",
]
