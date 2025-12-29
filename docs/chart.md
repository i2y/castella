# Charts

Castella provides native interactive chart widgets with GPU rendering via Skia (desktop) and CanvasKit (web). No external dependencies like Matplotlib required.

## Features

- **7 Chart Types**: Bar, Line, Pie, Scatter, Area, Stacked Bar, Gauge
- **Full Interactivity**: Tooltips, hover effects, click events
- **Pydantic v2 Models**: Type-safe, validated data models
- **Theme Integration**: Automatically uses current Castella theme
- **Observable Pattern**: Charts auto-update when data changes

## Quick Start

```python
from castella.chart import BarChart, CategoricalChartData, CategoricalSeries, SeriesStyle

# Create data
data = CategoricalChartData(title="Sales by Quarter")
data.add_series(CategoricalSeries.from_values(
    name="2024",
    categories=["Q1", "Q2", "Q3", "Q4"],
    values=[100, 120, 90, 150],
    style=SeriesStyle(color="#3b82f6"),
))

# Create chart
chart = BarChart(data, show_values=True)
```

## Data Models

### CategoricalChartData

For charts with category labels (Bar, Pie, Stacked Bar):

```python
from castella.chart import CategoricalChartData, CategoricalSeries, SeriesStyle

data = CategoricalChartData(title="Monthly Sales")
data.add_series(CategoricalSeries.from_values(
    name="Product A",
    categories=["Jan", "Feb", "Mar", "Apr"],
    values=[50, 75, 60, 90],
    style=SeriesStyle(color="#3b82f6"),
))
data.add_series(CategoricalSeries.from_values(
    name="Product B",
    categories=["Jan", "Feb", "Mar", "Apr"],
    values=[40, 55, 70, 65],
    style=SeriesStyle(color="#22c55e"),
))
```

### NumericChartData

For charts with numeric X/Y data (Line, Scatter, Area):

```python
from castella.chart import NumericChartData, NumericSeries, SeriesStyle

data = NumericChartData(title="Temperature Over Time")

# Y values only (X auto-generated as 0, 1, 2, ...)
data.add_series(NumericSeries.from_y_values(
    name="Sensor A",
    y_values=[20, 22, 21, 25, 24, 23],
    style=SeriesStyle(color="#3b82f6"),
))

# Explicit X and Y values
data.add_series(NumericSeries.from_values(
    name="Sensor B",
    x_values=[0, 1, 2, 3, 4, 5],
    y_values=[18, 19, 20, 22, 21, 20],
    style=SeriesStyle(color="#22c55e"),
))
```

### GaugeChartData

For gauge/meter charts:

```python
from castella.chart import GaugeChartData

data = GaugeChartData(
    title="CPU Usage",
    value=67,
    min_value=0,
    max_value=100,
    value_format="{:.0f}%",
    thresholds=[
        (0.0, "#22c55e"),   # Green for 0-50%
        (0.5, "#f59e0b"),   # Yellow for 50-80%
        (0.8, "#ef4444"),   # Red for 80-100%
    ],
)
```

## Chart Types

### BarChart

Vertical bar chart for categorical data:

```python
from castella.chart import BarChart, CategoricalChartData, CategoricalSeries

data = CategoricalChartData(title="Sales")
data.add_series(CategoricalSeries.from_values(
    name="Revenue",
    categories=["Q1", "Q2", "Q3", "Q4"],
    values=[100, 150, 120, 180],
))

chart = BarChart(
    data,
    show_values=True,      # Show value labels on bars
    bar_width_ratio=0.7,   # Bar width as ratio of available space
    enable_tooltip=True,   # Show tooltips on hover
)
```

### LineChart

Line chart with optional points:

```python
from castella.chart import LineChart, NumericChartData, NumericSeries

data = NumericChartData(title="Stock Price")
data.add_series(NumericSeries.from_y_values(
    name="AAPL",
    y_values=[150, 155, 148, 160, 158, 165],
))

chart = LineChart(
    data,
    show_points=True,     # Show data points
    point_radius=4.0,     # Point size
    line_width=2.0,       # Line thickness
    smooth=False,         # Use straight lines (True for curves)
)
```

### PieChart

Pie and donut charts:

```python
from castella.chart import PieChart, CategoricalChartData, CategoricalSeries

data = CategoricalChartData(title="Market Share")
data.add_series(CategoricalSeries.from_values(
    name="Companies",
    categories=["Company A", "Company B", "Company C", "Others"],
    values=[35, 28, 22, 15],
))

chart = PieChart(
    data,
    inner_radius_ratio=0.0,  # 0.0 for pie, 0.5+ for donut
    show_labels=True,        # Show category labels
    show_percentages=True,   # Show percentage values
)
```

### ScatterChart

Scatter plot with customizable point shapes:

```python
from castella.chart import ScatterChart, PointShape, NumericChartData, NumericSeries

data = NumericChartData(title="Height vs Weight")
data.add_series(NumericSeries.from_values(
    name="Male",
    x_values=[170, 175, 180, 185],
    y_values=[70, 75, 80, 85],
))

chart = ScatterChart(
    data,
    point_radius=6,
    point_shape=PointShape.CIRCLE,  # CIRCLE, SQUARE, DIAMOND, TRIANGLE
    show_grid=True,
)
```

### AreaChart

Filled area chart:

```python
from castella.chart import AreaChart, NumericChartData, NumericSeries

data = NumericChartData(title="Website Traffic")
data.add_series(NumericSeries.from_y_values(
    name="Visitors",
    y_values=[1200, 1500, 1300, 1800, 2100],
))

chart = AreaChart(
    data,
    fill_opacity=0.3,    # Area fill transparency
    show_points=True,    # Show data points
    stacked=False,       # Stack multiple series
)
```

### StackedBarChart

Stacked bar chart for comparing parts of a whole:

```python
from castella.chart import StackedBarChart, CategoricalChartData, CategoricalSeries

data = CategoricalChartData(title="Revenue by Region")
data.add_series(CategoricalSeries.from_values(
    name="North", categories=["Q1", "Q2", "Q3", "Q4"], values=[100, 120, 90, 150],
))
data.add_series(CategoricalSeries.from_values(
    name="South", categories=["Q1", "Q2", "Q3", "Q4"], values=[80, 100, 110, 95],
))
data.add_series(CategoricalSeries.from_values(
    name="East", categories=["Q1", "Q2", "Q3", "Q4"], values=[60, 75, 85, 70],
))

chart = StackedBarChart(
    data,
    normalized=False,    # True for 100% stacked chart
    show_values=False,
)
```

### GaugeChart

Gauge/meter chart with threshold colors:

```python
from castella.chart import GaugeChart, GaugeStyle, GaugeChartData

data = GaugeChartData(
    title="CPU Usage",
    value=67,
    min_value=0,
    max_value=100,
    value_format="{:.0f}%",
    thresholds=[
        (0.0, "#22c55e"),   # Green
        (0.5, "#f59e0b"),   # Yellow
        (0.8, "#ef4444"),   # Red
    ],
)

chart = GaugeChart(
    data,
    style=GaugeStyle.HALF_CIRCLE,  # HALF_CIRCLE, THREE_QUARTER, FULL_CIRCLE
    show_ticks=True,
    arc_width=25,
)
```

## Interactivity

### Event Handlers

All charts support hover and click events:

```python
chart = BarChart(data).on_click(on_bar_click).on_hover(on_bar_hover)

def on_bar_click(event):
    print(f"Clicked: {event.label} = {event.value}")
    print(f"Series: {event.series_index}, Data: {event.data_index}")

def on_bar_hover(event):
    print(f"Hovering: {event.label}")
```

### Tooltips

Tooltips are enabled by default and show on hover:

```python
chart = LineChart(data, enable_tooltip=True)  # Default
chart = LineChart(data, enable_tooltip=False)  # Disable
```

### Series Visibility

Toggle series visibility (useful with legends):

```python
# Hide/show series
data.set_series_visibility(series_index=1, visible=False)
data.toggle_series_visibility(series_index=0)

# Check visibility
if data.is_series_visible(0):
    print("Series 0 is visible")
```

## Reactive Updates

Charts automatically re-render when their data changes:

```python
class LiveChart(Component):
    def __init__(self):
        super().__init__()
        self._data = GaugeChartData(title="CPU", value=50, max_value=100)
        self._data.attach(self)  # Re-render on data change

    def view(self):
        return Column(
            GaugeChart(self._data, style=GaugeStyle.HALF_CIRCLE),
            Button("Update").on_click(self._update),
        )

    def _update(self, _):
        import random
        self._data.set_value(random.randint(0, 100))  # Triggers re-render
```

## SeriesStyle

Customize series appearance:

```python
from castella.chart import SeriesStyle

style = SeriesStyle(
    color="#3b82f6",       # Primary color
    fill_opacity=0.3,      # Fill transparency (for area charts)
    line_width=2.0,        # Line thickness
    point_radius=4.0,      # Point size
)

series = CategoricalSeries.from_values(
    name="Sales",
    categories=["A", "B", "C"],
    values=[10, 20, 30],
    style=style,
)
```

## Complete Example

```python
from castella import App, Component, Column, Row, Button, SizePolicy
from castella.frame import Frame
from castella.chart import (
    BarChart, LineChart, PieChart, GaugeChart, GaugeStyle,
    CategoricalChartData, NumericChartData, GaugeChartData,
    CategoricalSeries, NumericSeries, SeriesStyle,
)


class ChartDemo(Component):
    def __init__(self):
        super().__init__()

        # Bar chart data
        self._bar_data = CategoricalChartData(title="Quarterly Sales")
        self._bar_data.add_series(CategoricalSeries.from_values(
            name="2024",
            categories=["Q1", "Q2", "Q3", "Q4"],
            values=[120, 150, 130, 180],
            style=SeriesStyle(color="#3b82f6"),
        ))
        self._bar_data.attach(self)

        # Line chart data
        self._line_data = NumericChartData(title="Daily Views")
        self._line_data.add_series(NumericSeries.from_y_values(
            name="Page Views",
            y_values=[100, 120, 90, 150, 180, 160, 200],
            style=SeriesStyle(color="#22c55e"),
        ))
        self._line_data.attach(self)

        # Gauge data
        self._gauge_data = GaugeChartData(
            title="Performance",
            value=75,
            max_value=100,
            value_format="{:.0f}%",
        )
        self._gauge_data.attach(self)

    def view(self):
        return Column(
            Row(
                BarChart(self._bar_data, show_values=True)
                    .on_click(lambda e: print(f"Bar: {e.label}")),
                LineChart(self._line_data, show_points=True)
                    .on_hover(lambda e: print(f"Line: {e.value}")),
            ),
            Row(
                GaugeChart(self._gauge_data, style=GaugeStyle.HALF_CIRCLE),
                Button("Randomize").on_click(self._randomize),
            ).height(200).height_policy(SizePolicy.FIXED),
        )

    def _randomize(self, _):
        import random
        self._gauge_data.set_value(random.randint(0, 100))


App(Frame("Chart Demo", 1000, 700), ChartDemo()).run()
```
