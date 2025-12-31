"""ASCII chart demo for terminal environments.

Run with TUI backend:
    CASTELLA_IS_TERMINAL_MODE=true uv run python examples/ascii_chart_demo.py

Or in a regular terminal with prompt_toolkit installed:
    uv sync --extra tui
    uv run python examples/ascii_chart_demo.py
"""

from castella import App, Component, Column, Row, Text
from castella.frame import Frame
from castella.chart import (
    ASCIIBarChart,
    ASCIIBarData,
    ASCIIPieChart,
    ASCIIPieData,
    ASCIILineChart,
    ASCIIGaugeChart,
)


class ASCIIChartDemo(Component):
    def __init__(self):
        super().__init__()

        # Bar chart data
        self._bar_data = ASCIIBarData(
            title="Quarterly Sales",
            labels=["Q1", "Q2", "Q3", "Q4"],
            values=[120, 180, 150, 200],
        )

        # Pie chart data
        self._pie_data = ASCIIPieData(
            title="Market Share",
            labels=["Product A", "Product B", "Product C", "Others"],
            values=[35, 28, 22, 15],
        )

        # Line chart values
        self._line_values = [10, 25, 15, 30, 22, 35, 28, 40, 32, 45]

        # Gauge value
        self._gauge_value = 67.5

    def view(self):
        return Column(
            Text("ASCII Chart Demo").fixed_height(30),
            Row(
                Column(
                    ASCIIBarChart(self._bar_data, width=30, show_values=True),
                    ASCIIPieChart(self._pie_data),
                ),
                Column(
                    ASCIILineChart(
                        self._line_values,
                        width=40,
                        height=8,
                        title="Trend",
                    ),
                    ASCIIGaugeChart(
                        value=self._gauge_value,
                        max_value=100,
                        width=25,
                        title="CPU Usage",
                    ),
                ),
            ),
        )


if __name__ == "__main__":
    App(Frame("ASCII Chart Demo", 1000, 600), ASCIIChartDemo()).run()
