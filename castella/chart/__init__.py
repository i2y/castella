"""Castella Chart - Native interactive chart widgets.

This module provides cross-platform chart widgets with:
- Native Skia/CanvasKit rendering (no Matplotlib dependency)
- Full interactivity: tooltips, hover, click, zoom/pan
- Pydantic v2 data models
- Theme integration
"""

from castella.chart.models import (
    # Data points
    DataPoint,
    NumericDataPoint,
    GaugeDataPoint,
    # Series
    SeriesStyle,
    CategoricalSeries,
    NumericSeries,
    # Axis
    AxisType,
    AxisPosition,
    GridStyle,
    AxisConfig,
    XAxisConfig,
    YAxisConfig,
    # Legend
    LegendPosition,
    LegendConfig,
    # Animation
    EasingFunction,
    AnimationConfig,
    # Chart data
    ChartDataBase,
    CategoricalChartData,
    NumericChartData,
    GaugeChartData,
)

from castella.chart.events import (
    ChartHoverEvent,
    ChartClickEvent,
    ChartSelectionEvent,
    ZoomEvent,
)

from castella.chart.base import BaseChart, ChartMargins, ChartLayout
from castella.chart.scales import LinearScale, BandScale, PolarScale
from castella.chart.theme import ChartTheme, get_chart_theme
from castella.chart.hit_testing import (
    HitTestable,
    RectElement,
    CircleElement,
    ArcElement,
    hit_test,
)
from castella.chart.transform import ChartTransform, ViewBounds

# Chart widgets
from castella.chart.bar_chart import BarChart
from castella.chart.line_chart import LineChart
from castella.chart.pie_chart import PieChart
from castella.chart.scatter_chart import ScatterChart, PointShape
from castella.chart.area_chart import AreaChart
from castella.chart.stacked_bar_chart import StackedBarChart
from castella.chart.gauge_chart import GaugeChart, GaugeStyle, GaugeThreshold, DonutChart

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
    # Events
    "ChartHoverEvent",
    "ChartClickEvent",
    "ChartSelectionEvent",
    "ZoomEvent",
    # Base chart
    "BaseChart",
    "ChartMargins",
    "ChartLayout",
    # Scales
    "LinearScale",
    "BandScale",
    "PolarScale",
    # Theme
    "ChartTheme",
    "get_chart_theme",
    # Hit testing
    "HitTestable",
    "RectElement",
    "CircleElement",
    "ArcElement",
    "hit_test",
    # Transform
    "ChartTransform",
    "ViewBounds",
    # Chart widgets
    "BarChart",
    "LineChart",
    "PieChart",
    "ScatterChart",
    "PointShape",
    "AreaChart",
    "StackedBarChart",
    "GaugeChart",
    "GaugeStyle",
    "GaugeThreshold",
    "DonutChart",
]
