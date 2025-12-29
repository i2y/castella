"""Test ASCII chart rendering output directly in terminal.

This script prints the ASCII chart output without needing the full UI framework.
"""

from castella.chart import (
    ASCIIBarChart,
    ASCIIBarData,
    ASCIIPieChart,
    ASCIIPieData,
    ASCIILineChart,
    ASCIIGaugeChart,
)


def main():
    print("=" * 60)
    print("ASCII Bar Chart")
    print("=" * 60)

    bar_data = ASCIIBarData(
        title="Quarterly Sales",
        labels=["Q1", "Q2", "Q3", "Q4"],
        values=[120, 180, 150, 200],
    )
    bar_chart = ASCIIBarChart(bar_data, width=30, show_values=True)
    for line in bar_chart._render_lines():
        print(line)

    print()
    print("=" * 60)
    print("ASCII Pie Chart")
    print("=" * 60)

    pie_data = ASCIIPieData(
        title="Market Share",
        labels=["Product A", "Product B", "Product C", "Others"],
        values=[35, 28, 22, 15],
    )
    pie_chart = ASCIIPieChart(pie_data)
    for line in pie_chart._render_lines():
        print(line)

    print()
    print("=" * 60)
    print("ASCII Line Chart")
    print("=" * 60)

    line_values = [10, 25, 15, 30, 22, 35, 28, 40, 32, 45]
    line_chart = ASCIILineChart(line_values, width=50, height=10, title="Trend Over Time")
    for line in line_chart._render_lines():
        print(line)

    print()
    print("=" * 60)
    print("ASCII Gauge Chart")
    print("=" * 60)

    gauge_chart = ASCIIGaugeChart(value=67.5, max_value=100, width=30, title="CPU Usage")
    for line in gauge_chart._render_lines():
        print(line)

    print()
    print("=" * 60)
    print("Multiple Gauges")
    print("=" * 60)

    for name, value in [("CPU", 67), ("Memory", 45), ("Disk", 82), ("Network", 23)]:
        gauge = ASCIIGaugeChart(value=value, max_value=100, width=25, title=name)
        for line in gauge._render_lines():
            print(line)


if __name__ == "__main__":
    main()
