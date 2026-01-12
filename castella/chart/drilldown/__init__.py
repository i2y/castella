"""Drill-down chart components for hierarchical data visualization.

This module provides components for creating interactive drill-down charts
that allow users to navigate through hierarchical data.

Example:
    ```python
    from castella.chart import (
        DrillDownChart, HierarchicalChartData, HierarchicalNode,
        DataPoint, BarChart,
    )

    # Create hierarchical data
    data = HierarchicalChartData(
        title="Global Sales",
        root=HierarchicalNode(
            id="world",
            label="World",
            level_name="Region",
            data=[
                DataPoint(category="North America", value=1500),
                DataPoint(category="Europe", value=1200),
            ],
        ),
    )

    # Add children for drill-down
    data.root.add_child("North America", HierarchicalNode(
        id="na",
        label="North America",
        level_name="Country",
        data=[DataPoint(category="USA", value=900), ...],
    ))

    # Create drill-down chart
    chart = DrillDownChart(data, chart_type=BarChart)
    ```
"""

from .events import DrillDownEvent, DrillUpEvent
from .state import DrillDownState, DrillPath
from .breadcrumb import Breadcrumb
from .component import DrillDownChart
from .drillable_charts import (
    DrillableBarChart,
    DrillablePieChart,
    DrillableStackedBarChart,
    DrillableHeatmapChart,
)
from .indicator import (
    draw_drill_indicator_on_rect,
    draw_drill_indicator_on_arc,
    draw_drill_indicator_text,
)

__all__ = [
    # Events
    "DrillDownEvent",
    "DrillUpEvent",
    # State
    "DrillDownState",
    "DrillPath",
    # Components
    "DrillDownChart",
    "Breadcrumb",
    # Drillable chart variants
    "DrillableBarChart",
    "DrillablePieChart",
    "DrillableStackedBarChart",
    "DrillableHeatmapChart",
    # Indicator utilities
    "draw_drill_indicator_on_rect",
    "draw_drill_indicator_on_arc",
    "draw_drill_indicator_text",
]
