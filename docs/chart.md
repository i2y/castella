# Charts

Castella provides native interactive chart widgets with GPU rendering via Skia (desktop) and CanvasKit (web). No external dependencies like Matplotlib required.

## Features

- **8 Chart Types**: Bar, Line, Pie, Scatter, Area, Stacked Bar, Gauge, Heatmap
- **Full Interactivity**: Tooltips, hover effects, click events
- **Drill-Down Navigation**: Click to explore hierarchical data (Region → Country → City)
- **Scientific Colormaps**: Viridis, Plasma, Inferno, Magma (colorblind-friendly)
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

### HeatmapChartData

For heatmap charts with 2D matrix data:

```python
from castella.chart import HeatmapChartData

# Create from 2D array
data = HeatmapChartData.from_2d_array(
    values=[
        [1.0, 0.8, 0.3],
        [0.8, 1.0, 0.5],
        [0.3, 0.5, 1.0],
    ],
    row_labels=["A", "B", "C"],
    column_labels=["X", "Y", "Z"],
    title="Correlation Matrix",
)

# Set value range for color normalization
data.set_range(min_value=-1.0, max_value=1.0)

# Update single cell
data.set_cell(row=0, col=1, value=0.9)

# Update entire matrix
data.set_values([[1.0, 0.9], [0.9, 1.0]])
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
    smooth=False,         # Use straight lines (True for Catmull-Rom splines)
)

# Smooth curves using Catmull-Rom spline interpolation
smooth_chart = LineChart(data, smooth=True)
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

### HeatmapChart

Heatmap for 2D matrix data visualization:

```python
from castella.chart import HeatmapChart, HeatmapChartData, ColormapType

# Create correlation matrix data
data = HeatmapChartData.from_2d_array(
    values=[
        [1.00, 0.85, 0.42, -0.15],
        [0.85, 1.00, 0.55, 0.08],
        [0.42, 0.55, 1.00, 0.67],
        [-0.15, 0.08, 0.67, 1.00],
    ],
    row_labels=["Price", "Volume", "Volatility", "Beta"],
    column_labels=["Price", "Volume", "Volatility", "Beta"],
    title="Correlation Matrix",
)

# Set fixed value range for color normalization
data.set_range(-1.0, 1.0)

chart = HeatmapChart(
    data,
    colormap=ColormapType.VIRIDIS,  # VIRIDIS, PLASMA, INFERNO, MAGMA
    show_values=True,       # Show value annotations in cells
    show_colorbar=True,     # Show color bar legend
    cell_gap=2.0,           # Gap between cells in pixels
)
```

#### Colormaps

Castella provides scientific colormaps that are perceptually uniform and colorblind-friendly:

```python
from castella.chart import viridis, plasma, inferno, magma, get_colormap

# Get colormap by type
cmap = get_colormap(ColormapType.VIRIDIS)

# Get color for a normalized value (0.0 to 1.0)
color = cmap(0.5)  # Returns "#26828e"

# Get N evenly spaced colors
colors = cmap.get_colors(5)  # ["#440154", "#3e4a89", "#26828e", "#35b779", "#fde725"]

# Reversed colormap
reversed_cmap = cmap.reversed()
```

#### Heatmap with DataTable

You can also apply heatmap coloring to DataTable cells using `HeatmapConfig`:

```python
from castella import DataTable, DataTableState, ColumnConfig, HeatmapConfig
from castella.chart import ColormapType

# Create table data
state = DataTableState(
    columns=[
        ColumnConfig(name="Region", width=120),
        ColumnConfig(name="Q1", width=80),
        ColumnConfig(name="Q2", width=80),
        ColumnConfig(name="Q3", width=80),
        ColumnConfig(name="Q4", width=80),
    ],
    rows=[
        ["North America", 145, 162, 178, 195],
        ["Europe", 122, 138, 155, 168],
        ["Asia Pacific", 198, 215, 242, 267],
    ],
)

# Apply heatmap coloring to numeric columns
heatmap = HeatmapConfig(colormap=ColormapType.VIRIDIS)
for i in range(1, 5):
    state.columns[i].cell_bg_color = heatmap.create_color_fn(col_idx=i, state=state)

table = DataTable(state)
```

Features:
- **Auto-contrast text**: Text color automatically adjusts for readability
- **Per-column ranges**: Each column can have its own value range
- **Custom colormaps**: Pass any `Colormap` instance

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
from castella import App, Component, Column, Row, Button
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
            ).fixed_height(200),
        )

    def _randomize(self, _):
        import random
        self._gauge_data.set_value(random.randint(0, 100))


App(Frame("Chart Demo", 1000, 700), ChartDemo()).run()
```

## Drill-Down Charts

Drill-down charts allow users to navigate through hierarchical data by clicking on data points to see more detailed breakdowns.

### Supported Chart Types

- **BarChart**: Click bars to drill down
- **PieChart**: Click slices to drill down
- **StackedBarChart**: Click stacked segments to drill down
- **HeatmapChart**: Click cells (row-based) to drill down

### Basic Usage

```python
from castella.chart import (
    DrillDownChart, HierarchicalChartData, HierarchicalNode,
    DataPoint, BarChart,
)

# Create hierarchical data: Region -> Country -> City
data = HierarchicalChartData(
    title="Global Sales",
    root=HierarchicalNode(
        id="world",
        label="World",
        level_name="Region",
        data=[
            DataPoint(category="North America", value=1500, label="North America"),
            DataPoint(category="Europe", value=1200, label="Europe"),
            DataPoint(category="Asia", value=1800, label="Asia"),
        ],
    ),
)

# Add child data for North America
na_node = HierarchicalNode(
    id="na",
    label="North America",
    level_name="Country",
    data=[
        DataPoint(category="USA", value=900, label="USA"),
        DataPoint(category="Canada", value=400, label="Canada"),
        DataPoint(category="Mexico", value=200, label="Mexico"),
    ],
)
data.root.add_child("North America", na_node)

# Create drill-down chart
chart = (
    DrillDownChart(data, chart_type=BarChart, show_values=True)
    .on_drill_down(lambda ev: print(f"Drilled into: {ev.clicked_key}"))
    .on_drill_up(lambda ev: print(f"Drilled up to: {ev.to_node_id}"))
)
```

### Navigation Controls

- **Click on data**: Drill down into child data
- **Back button**: Go up one level
- **Breadcrumb**: Navigate to any ancestor level

### Multi-Series Data (StackedBarChart / HeatmapChart)

For StackedBarChart and HeatmapChart, use `series_data` instead of `data`:

```python
from castella.chart import (
    DrillDownChart, HierarchicalChartData, HierarchicalNode,
    DataPoint, StackedBarChart, HeatmapChart,
)

def make_quarterly_data(categories, base_values):
    """Create quarterly breakdown for each category."""
    quarters = ["Q1", "Q2", "Q3", "Q4"]
    ratios = [0.2, 0.25, 0.25, 0.3]
    result = {}
    for q_idx, quarter in enumerate(quarters):
        points = []
        for cat, base in zip(categories, base_values):
            value = base * ratios[q_idx]
            points.append(DataPoint(category=cat, value=value, label=cat))
        result[quarter] = points
    return result

# Root level with quarterly breakdown
data = HierarchicalChartData(
    title="Quarterly Sales by Region",
    root=HierarchicalNode(
        id="world",
        label="World",
        level_name="Region",
        series_data=make_quarterly_data(
            ["North America", "Europe", "Asia"],
            [1500, 1200, 1800],
        ),
    ),
)

# StackedBarChart shows stacked bars with Q1-Q4 colors
stacked_chart = DrillDownChart(data, chart_type=StackedBarChart, show_values=True)

# HeatmapChart shows 2D matrix (rows=categories, columns=quarters)
heatmap_chart = DrillDownChart(data, chart_type=HeatmapChart, show_values=True)
```

### Time-Series Drill-Down

Helper function for Year → Month → Day hierarchy:

```python
from datetime import date
from castella.chart import (
    DrillDownChart, hierarchical_from_timeseries, BarChart,
)

# Sample data: (date, value) tuples
daily_sales = [
    (date(2023, 1, 1), 120.0),
    (date(2023, 1, 2), 145.0),
    # ... more data
]

# Create hierarchical structure automatically
data = hierarchical_from_timeseries(
    daily_sales,
    title="Daily Sales",
    aggregation="sum",      # sum, avg, count, min, max
    depth="day",            # year, month, or day
    short_month_names=True, # "Jan" vs "January"
    value_format=lambda v: f"${v:,.0f}",
)

chart = DrillDownChart(data, chart_type=BarChart, show_values=True)
```

### Programmatic Navigation

```python
chart = DrillDownChart(data, chart_type=BarChart)

# Access the drill-down state
state = chart.state

# Navigate programmatically
state.drill_down("North America")
state.drill_up()
state.navigate_to("world")  # Jump to specific node
state.reset()               # Reset to root

# Check navigation state
print(state.current_depth)   # 0 = root
print(state.can_drill_up)    # True if not at root
print(state.breadcrumbs)     # [(node_id, label), ...]
```

### Visual Indicators

Drillable data points show a small white dot indicator:

- **BarChart**: Bottom-right corner of the bar
- **PieChart**: Inside the slice at 60% radius
- **StackedBarChart**: Bottom-right of each segment
- **HeatmapChart**: Left edge of the first cell in each drillable row

### Example Application

```python
from castella import App, Column, Text
from castella.core import Component, Widget
from castella.frame import Frame
from castella.chart import (
    DrillDownChart, HierarchicalChartData, HierarchicalNode,
    DataPoint, BarChart,
)


class SalesDashboard(Component):
    def __init__(self):
        super().__init__()
        self._data = self._create_sales_data()

    def _create_sales_data(self):
        data = HierarchicalChartData(
            title="Sales by Region",
            root=HierarchicalNode(
                id="world",
                label="World",
                level_name="Region",
                data=[
                    DataPoint(category="Americas", value=2500),
                    DataPoint(category="EMEA", value=1800),
                    DataPoint(category="APAC", value=2200),
                ],
            ),
        )
        # Add children for Americas
        data.root.add_child("Americas", HierarchicalNode(
            id="americas",
            label="Americas",
            level_name="Country",
            data=[
                DataPoint(category="USA", value=1500),
                DataPoint(category="Canada", value=600),
                DataPoint(category="Brazil", value=400),
            ],
        ))
        return data

    def view(self) -> Widget:
        return Column(
            Text("Sales Dashboard", font_size=20).fixed_height(40),
            DrillDownChart(
                self._data,
                chart_type=BarChart,
                show_values=True,
            ),
        )


App(Frame("Sales Dashboard", 800, 600), SalesDashboard()).run()
```

## ASCII Charts (Terminal)

For terminal environments, Castella provides ASCII chart widgets that render using Unicode characters.

### ASCIIBarChart

```python
from castella.chart import ASCIIBarChart, ASCIIBarData

data = ASCIIBarData(
    title="Quarterly Sales",
    labels=["Q1", "Q2", "Q3", "Q4"],
    values=[120, 180, 150, 200],
)

chart = ASCIIBarChart(data, width=30, show_values=True)
```

Output:
```
Quarterly Sales

Q1 │██████████████████            │ 120.0
Q2 │███████████████████████████   │ 180.0
Q3 │██████████████████████▌       │ 150.0
Q4 │██████████████████████████████│ 200.0
```

### ASCIIPieChart

```python
from castella.chart import ASCIIPieChart, ASCIIPieData

data = ASCIIPieData(
    title="Market Share",
    labels=["Product A", "Product B", "Others"],
    values=[50, 30, 20],
)

chart = ASCIIPieChart(data)
```

Output:
```
Market Share

● Product A ██████████           50.0%
○ Product B ██████               30.0%
◐ Others    ████                 20.0%
```

### ASCIILineChart

```python
from castella.chart import ASCIILineChart

chart = ASCIILineChart(
    values=[10, 25, 15, 30, 20, 35],
    width=40,
    height=8,
    title="Trend",
)
```

### ASCIIGaugeChart

```python
from castella.chart import ASCIIGaugeChart

chart = ASCIIGaugeChart(
    value=67.5,
    max_value=100,
    width=25,
    title="CPU Usage",
)
```

Output:
```
CPU Usage
[████████████████▊        ] 67.5/100
```

### Running in Terminal Mode

To run your app in terminal mode:

```bash
CASTELLA_IS_TERMINAL_MODE=true uv run python your_app.py
```
