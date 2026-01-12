"""Time-series drill-down chart example.

This example demonstrates the time-series drill-down functionality:
- Drill down from Year → Month → Day
- Automatic aggregation of values
- Support for multiple aggregation methods (sum, avg, count, min, max)

Run with:
    uv run python examples/drilldown_timeseries.py
"""

from datetime import date
import random

from castella import App, Column, Row, Text, Button, SizePolicy
from castella.core import Component, State, Widget
from castella.frame import Frame
from castella.chart import (
    DrillDownChart,
    hierarchical_from_timeseries,
    BarChart,
)


def generate_sales_data() -> list[tuple[date, float]]:
    """Generate sample daily sales data for 2023-2024."""
    data = []
    random.seed(42)  # For reproducibility

    # Generate data for 2023
    for month in range(1, 13):
        days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1]
        for day in range(1, days_in_month + 1):
            # Base value with seasonal variation
            base = 100 + 50 * (month / 12)  # Increase throughout year
            variation = random.uniform(-30, 30)
            value = max(10, base + variation)
            data.append((date(2023, month, day), value))

    # Generate data for 2024 (partial year)
    for month in range(1, 7):
        days_in_month = [31, 29, 31, 30, 31, 30][month - 1]  # 2024 is leap year
        for day in range(1, days_in_month + 1):
            base = 120 + 60 * (month / 12)  # Higher base for 2024
            variation = random.uniform(-30, 30)
            value = max(10, base + variation)
            data.append((date(2024, month, day), value))

    return data


class TimeSeriesDrillDownDemo(Component):
    """Demo component for time-series drill-down."""

    def __init__(self):
        super().__init__()
        self._aggregation = State("sum")
        self._aggregation.attach(self)

        # Generate sample data
        self._raw_data = generate_sales_data()

    def view(self) -> Widget:
        aggregation = self._aggregation()

        # Aggregation buttons
        agg_bar = Row(
            Button("Sum", font_size=12)
            .on_click(lambda _: self._aggregation.set("sum"))
            .bg_color("#3b82f6" if aggregation == "sum" else "#333333")
            .fixed_height(32)
            .width_policy(SizePolicy.CONTENT),
            Button("Average", font_size=12)
            .on_click(lambda _: self._aggregation.set("avg"))
            .bg_color("#3b82f6" if aggregation == "avg" else "#333333")
            .fixed_height(32)
            .width_policy(SizePolicy.CONTENT),
            Button("Count", font_size=12)
            .on_click(lambda _: self._aggregation.set("count"))
            .bg_color("#3b82f6" if aggregation == "count" else "#333333")
            .fixed_height(32)
            .width_policy(SizePolicy.CONTENT),
            Button("Max", font_size=12)
            .on_click(lambda _: self._aggregation.set("max"))
            .bg_color("#3b82f6" if aggregation == "max" else "#333333")
            .fixed_height(32)
            .width_policy(SizePolicy.CONTENT),
        ).fixed_height(40)

        # Create hierarchical data from time-series
        chart_data = hierarchical_from_timeseries(
            self._raw_data,
            title=f"Daily Sales ({aggregation.upper()})",
            aggregation=aggregation,  # type: ignore
            depth="day",
            short_month_names=True,
            value_format=lambda v: f"${v:,.0f}",
        )

        chart = (
            DrillDownChart(
                chart_data,
                chart_type=BarChart,
                show_values=True,
            )
            .on_drill_down(lambda ev: print(f"Drilled into: {ev.clicked_key}"))
        )

        return Column(
            Text("Time-Series Drill-Down Demo", font_size=18)
            .text_color("#ffffff")
            .fixed_height(30),
            Text("Click on a bar to drill down: Year → Month → Day", font_size=12)
            .text_color("#888888")
            .fixed_height(24),
            agg_bar,
            chart,
        )


def main() -> None:
    """Run the time-series drill-down example."""
    App(Frame("Time-Series Drill-Down", 900, 600), TimeSeriesDrillDownDemo()).run()


if __name__ == "__main__":
    main()
