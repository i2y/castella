# Charts

Castella provides chart widgets powered by Matplotlib for data visualization.

!!! note "Requirements"
    Charts require `matplotlib` and `numpy`:
    ```bash
    # With uv (recommended)
    uv add matplotlib numpy

    # With pip
    pip install matplotlib numpy
    ```

## BarChart

Bar charts display categorical data with rectangular bars.

```python
from castella.bar_chart import BarChart, BarChartState

# Create chart state with labels and values
data = BarChartState(
    label=["A", "B", "C", "D"],
    value=[10, 25, 15, 30]
)

# Use in your view
BarChart(data)
```

### Updating Data

```python
# Update the chart data (triggers automatic re-render)
data.set(
    label=["X", "Y", "Z"],
    value=[5, 10, 20]
)
```

## LineChart

Line charts display data points connected by lines, useful for showing trends.

```python
from castella.line_chart import LineChart, LineChartState

# Create chart state with values
data = LineChartState(value=[1, 4, 2, 5, 3, 6])

# Use in your view
LineChart(data)
```

### Updating Data

```python
# Update the chart data
data.set(value=[10, 8, 12, 9, 15])
```

## PieChart

Pie charts display proportional data as slices of a circle.

```python
from castella.pie_chart import PieChart, PieChartState

# Create chart state with labels and values
data = PieChartState(
    label=["Category A", "Category B", "Category C"],
    value=[30, 45, 25]
)

# Use in your view
PieChart(data)
```

### Updating Data

```python
# Update the chart data
data.set(
    label=["New A", "New B"],
    value=[60, 40]
)
```

## Complete Example

```python
from castella import App, Column, Row, Button, Text
from castella.frame import Frame
from castella.bar_chart import BarChart, BarChartState
from castella.pie_chart import PieChart, PieChartState
from castella.line_chart import LineChart, LineChartState


# Create chart data
bar_data = BarChartState(label=["Foo", "Bar", "Baz"], value=[50, 100, 75])
pie_data = PieChartState(label=["Foo", "Bar", "Baz"], value=[50, 100, 75])
line_data = LineChartState(value=[10, 25, 15, 30, 20])

App(
    Frame("Charts Demo", 1200, 400),
    Row(
        BarChart(bar_data),
        PieChart(pie_data),
        LineChart(line_data),
    ),
).run()
```

## Reactive Charts

Charts automatically update when their state changes:

```python
from castella import App, Column, Row, Button, Component, State
from castella.frame import Frame
from castella.bar_chart import BarChart, BarChartState
import random


class ReactiveChartDemo(Component):
    def __init__(self):
        super().__init__()
        self._chart_data = BarChartState(
            label=["A", "B", "C"],
            value=[10, 20, 30]
        )
        self.model(self._chart_data)

    def _randomize(self, _):
        self._chart_data.set(
            label=["A", "B", "C"],
            value=[random.randint(5, 50) for _ in range(3)]
        )

    def view(self):
        return Column(
            BarChart(self._chart_data),
            Button("Randomize Data").on_click(self._randomize),
        )


App(Frame("Reactive Chart", 600, 500), ReactiveChartDemo()).run()
```

## Notes

- Charts default to `SizePolicy.CONTENT` for both width and height
- Charts are rendered as images using Matplotlib's figure canvas
- Matplotlib must be installed for chart widgets to work
- Performance depends on Matplotlib rendering speed
