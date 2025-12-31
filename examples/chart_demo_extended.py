"""Extended chart demo - showcasing all chart types including new ones."""

from castella import App, Component, Column, Row, Text, Button
from castella.frame import Frame
from castella.chart import (
    # Basic charts
    ScatterChart,
    PointShape,
    AreaChart,
    StackedBarChart,
    GaugeChart,
    GaugeStyle,
    GaugeChartData,
    # Data models
    CategoricalChartData,
    NumericChartData,
    CategoricalSeries,
    NumericSeries,
    SeriesStyle,
)


class ExtendedChartDemo(Component):
    """Demo component showcasing all chart types."""

    def __init__(self):
        super().__init__()

        # Scatter chart data
        self._scatter_data = NumericChartData(title="Height vs Weight")
        self._scatter_data.add_series(
            NumericSeries.from_values(
                name="Male",
                x_values=[165, 170, 175, 180, 185, 168, 172, 178],
                y_values=[65, 72, 78, 85, 90, 68, 75, 82],
                style=SeriesStyle(color="#3b82f6"),
            )
        )
        self._scatter_data.add_series(
            NumericSeries.from_values(
                name="Female",
                x_values=[155, 160, 165, 170, 158, 162, 168],
                y_values=[50, 55, 60, 65, 52, 58, 62],
                style=SeriesStyle(color="#ec4899"),
            )
        )
        self._scatter_data.attach(self)

        # Area chart data
        self._area_data = NumericChartData(title="Website Traffic")
        self._area_data.add_series(
            NumericSeries.from_y_values(
                name="Visitors",
                y_values=[1200, 1500, 1300, 1800, 2100, 1900, 2400],
                style=SeriesStyle(color="#22c55e"),
            )
        )
        self._area_data.add_series(
            NumericSeries.from_y_values(
                name="Page Views",
                y_values=[3500, 4200, 3800, 5200, 6100, 5500, 7000],
                style=SeriesStyle(color="#3b82f6"),
            )
        )
        self._area_data.attach(self)

        # Stacked bar chart data
        self._stacked_data = CategoricalChartData(title="Revenue by Region")
        self._stacked_data.add_series(
            CategoricalSeries.from_values(
                name="North",
                categories=["Q1", "Q2", "Q3", "Q4"],
                values=[100, 120, 90, 150],
                style=SeriesStyle(color="#3b82f6"),
            )
        )
        self._stacked_data.add_series(
            CategoricalSeries.from_values(
                name="South",
                categories=["Q1", "Q2", "Q3", "Q4"],
                values=[80, 100, 110, 95],
                style=SeriesStyle(color="#22c55e"),
            )
        )
        self._stacked_data.add_series(
            CategoricalSeries.from_values(
                name="East",
                categories=["Q1", "Q2", "Q3", "Q4"],
                values=[60, 75, 85, 70],
                style=SeriesStyle(color="#f59e0b"),
            )
        )
        self._stacked_data.attach(self)

        # Gauge chart data
        self._gauge_data = GaugeChartData(
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
        self._gauge_data.attach(self)

        # Second gauge (memory)
        self._gauge_data2 = GaugeChartData(
            title="Memory",
            value=45,
            min_value=0,
            max_value=100,
            value_format="{:.0f}%",
        )
        self._gauge_data2.attach(self)

    def view(self):
        return Column(
            Text("Extended Chart Demo", font_size=24)
            .fixed_height(40),
            # Row 1: Scatter and Area charts
            Row(
                ScatterChart(
                    self._scatter_data,
                    point_radius=6,
                    point_shape=PointShape.CIRCLE,
                    show_grid=True,
                )
                .on_click(lambda ev: print(f"Point clicked: {ev.label}"))
                .on_hover(lambda ev: print(f"Point hover: {ev.label}")),
                AreaChart(
                    self._area_data,
                    show_points=True,
                    fill_opacity=0.3,
                )
                .on_click(lambda ev: print(f"Area point clicked: {ev.value}"))
                .on_hover(lambda ev: print(f"Area hover: {ev.value}")),
            ),
            # Row 2: Stacked bar and Gauges
            Row(
                StackedBarChart(
                    self._stacked_data,
                    show_values=False,
                )
                .on_click(lambda ev: print(f"Stack clicked: {ev.label} = {ev.value}"))
                .on_hover(lambda ev: print(f"Stack hover: {ev.label}")),
                Column(
                    GaugeChart(
                        self._gauge_data,
                        style=GaugeStyle.HALF_CIRCLE,
                        show_ticks=True,
                        arc_width=25,
                    )
                    .on_click(lambda ev: print(f"Gauge clicked: {ev.value}")),
                    GaugeChart(
                        self._gauge_data2,
                        style=GaugeStyle.HALF_CIRCLE,
                        show_ticks=True,
                        arc_width=25,
                    ),
                ),
            ),
            # Controls
            Row(
                Button("Update Gauges").on_click(self._update_gauges),
                Button("Randomize Scatter").on_click(self._randomize_scatter),
                Button("Toggle Stacked").on_click(self._toggle_stacked),
            ).fixed_height(40),
        )

    def _update_gauges(self, _):
        """Update gauge values."""
        import random

        self._gauge_data.set_value(random.randint(0, 100))
        self._gauge_data2.set_value(random.randint(0, 100))

    def _randomize_scatter(self, _):
        """Randomize scatter data."""
        import random

        x_vals = [random.uniform(155, 190) for _ in range(8)]
        y_vals = [random.uniform(50, 95) for _ in range(8)]

        self._scatter_data.update_series(
            0,
            NumericSeries.from_values(
                name="Male",
                x_values=x_vals,
                y_values=y_vals,
                style=SeriesStyle(color="#3b82f6"),
            ),
        )

    def _toggle_stacked(self, _):
        """Toggle stacked bar series visibility."""
        self._stacked_data.toggle_series_visibility(2)


if __name__ == "__main__":
    App(Frame("Extended Chart Demo", 1200, 800), ExtendedChartDemo()).run()
