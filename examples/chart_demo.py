"""Chart demo - showcasing the new native chart widgets."""

from castella import App, Component, Column, Row, Text, Button
from castella.frame import Frame
from castella.chart import (
    BarChart,
    LineChart,
    PieChart,
    CategoricalChartData,
    NumericChartData,
    CategoricalSeries,
    NumericSeries,
    SeriesStyle,
)


class ChartDemo(Component):
    """Demo component showcasing various chart types."""

    def __init__(self):
        super().__init__()

        # Bar chart data
        self._bar_data = CategoricalChartData(title="Quarterly Sales")
        self._bar_data.add_series(
            CategoricalSeries.from_values(
                name="2024",
                categories=["Q1", "Q2", "Q3", "Q4"],
                values=[120, 150, 90, 180],
                style=SeriesStyle(color="#3b82f6"),
            )
        )
        self._bar_data.add_series(
            CategoricalSeries.from_values(
                name="2023",
                categories=["Q1", "Q2", "Q3", "Q4"],
                values=[100, 130, 85, 150],
                style=SeriesStyle(color="#22c55e"),
            )
        )
        self._bar_data.attach(self)

        # Line chart data
        self._line_data = NumericChartData(title="Temperature (Normal)")
        self._line_data.add_series(
            NumericSeries.from_y_values(
                name="Sensor A",
                y_values=[20.5, 22.3, 21.1, 23.4, 22.8, 24.1, 23.5],
                style=SeriesStyle(color="#f59e0b"),
            )
        )
        self._line_data.add_series(
            NumericSeries.from_y_values(
                name="Sensor B",
                y_values=[18.2, 19.5, 20.3, 21.1, 20.8, 22.0, 21.5],
                style=SeriesStyle(color="#8b5cf6"),
            )
        )
        self._line_data.attach(self)

        # Smooth line chart data
        self._smooth_data = NumericChartData(title="Temperature (Smooth)")
        self._smooth_data.add_series(
            NumericSeries.from_y_values(
                name="Sensor A",
                y_values=[20.5, 22.3, 21.1, 23.4, 22.8, 24.1, 23.5],
                style=SeriesStyle(color="#f59e0b"),
            )
        )
        self._smooth_data.add_series(
            NumericSeries.from_y_values(
                name="Sensor B",
                y_values=[18.2, 19.5, 20.3, 21.1, 20.8, 22.0, 21.5],
                style=SeriesStyle(color="#8b5cf6"),
            )
        )
        self._smooth_data.attach(self)

        # Pie chart data
        self._pie_data = CategoricalChartData(title="Market Share")
        self._pie_data.add_series(
            CategoricalSeries.from_values(
                name="Browsers",
                categories=["Chrome", "Safari", "Firefox", "Edge", "Other"],
                values=[65, 18, 8, 5, 4],
            )
        )
        self._pie_data.attach(self)

    def view(self):
        return Column(
            Text("Native Chart Demo", font_size=24)
            .fixed_height(40),
            Row(
                # Bar Chart
                BarChart(
                    self._bar_data,
                    show_values=True,
                    enable_tooltip=True,
                )
                .on_click(lambda ev: print(f"Bar clicked: {ev.label} = {ev.value}"))
                .on_hover(lambda ev: print(f"Bar hover: {ev.label}")),
                # Line Chart (Normal)
                LineChart(
                    self._line_data,
                    show_points=True,
                    enable_tooltip=True,
                )
                .on_click(lambda ev: print(f"Point clicked: {ev.label}"))
                .on_hover(lambda ev: print(f"Point hover: {ev.value:.1f}")),
                # Line Chart (Smooth - Catmull-Rom splines)
                LineChart(
                    self._smooth_data,
                    show_points=True,
                    smooth=True,  # Enable smooth curves
                    enable_tooltip=True,
                ),
            ),
            Row(
                # Pie Chart
                PieChart(
                    self._pie_data,
                    donut=False,
                    show_labels=True,
                    show_percentages=True,
                    enable_tooltip=True,
                ).on_click(
                    lambda ev: print(f"Slice clicked: {ev.label} = {ev.value}%")
                ),
                # Donut Chart
                PieChart(
                    self._pie_data,
                    donut=True,
                    inner_radius_ratio=0.6,
                    show_labels=True,
                    enable_tooltip=True,
                ).with_title("Donut Variant"),
            ),
            Row(
                Button("Add Random Data").on_click(self._add_random_data),
                Button("Toggle Series").on_click(self._toggle_series),
                Button("Reset").on_click(self._reset_data),
            )
            .fixed_height(40),
        )

    def _add_random_data(self, _):
        """Add random data to charts."""
        import random

        # Update bar chart
        new_values = [random.randint(50, 200) for _ in range(4)]
        self._bar_data.update_series(
            0,
            CategoricalSeries.from_values(
                name="2024",
                categories=["Q1", "Q2", "Q3", "Q4"],
                values=new_values,
                style=SeriesStyle(color="#3b82f6"),
            ),
        )

        # Update line charts (both normal and smooth)
        new_y = [random.uniform(18, 25) for _ in range(7)]
        new_series = [
            NumericSeries.from_y_values(
                name="Sensor A",
                y_values=new_y,
                style=SeriesStyle(color="#f59e0b"),
            ),
            self._line_data.series[1],  # Keep second series
        ]
        self._line_data.set_series(new_series)
        self._smooth_data.set_series(new_series)

    def _toggle_series(self, _):
        """Toggle visibility of second series."""
        self._bar_data.toggle_series_visibility(1)
        self._line_data.toggle_series_visibility(1)
        self._smooth_data.toggle_series_visibility(1)

    def _reset_data(self, _):
        """Reset to original data."""
        self._bar_data.set_series(
            [
                CategoricalSeries.from_values(
                    name="2024",
                    categories=["Q1", "Q2", "Q3", "Q4"],
                    values=[120, 150, 90, 180],
                    style=SeriesStyle(color="#3b82f6"),
                ),
                CategoricalSeries.from_values(
                    name="2023",
                    categories=["Q1", "Q2", "Q3", "Q4"],
                    values=[100, 130, 85, 150],
                    style=SeriesStyle(color="#22c55e"),
                ),
            ]
        )

        line_series = [
            NumericSeries.from_y_values(
                name="Sensor A",
                y_values=[20.5, 22.3, 21.1, 23.4, 22.8, 24.1, 23.5],
                style=SeriesStyle(color="#f59e0b"),
            ),
            NumericSeries.from_y_values(
                name="Sensor B",
                y_values=[18.2, 19.5, 20.3, 21.1, 20.8, 22.0, 21.5],
                style=SeriesStyle(color="#8b5cf6"),
            ),
        ]
        self._line_data.set_series(line_series)
        self._smooth_data.set_series(line_series)

        # Reset visibility
        self._bar_data.set_series_visibility(1, True)
        self._line_data.set_series_visibility(1, True)
        self._smooth_data.set_series_visibility(1, True)


if __name__ == "__main__":
    App(Frame("Chart Demo", 1200, 800), ChartDemo()).run()
