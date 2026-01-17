"""Drill-down chart example.

This example demonstrates the drill-down chart functionality:
- Click on a bar/slice/cell to drill down into child data
- Use the Back button or breadcrumb navigation to go back
- The chart automatically updates to show the current level
- Switch between BarChart, PieChart, StackedBarChart, and HeatmapChart using tabs

Run with:
    uv run python examples/drilldown_chart.py
"""

from castella import App, Column, Row, Text, Button, SizePolicy
from castella.core import State, StatefulComponent, Widget
from castella.frame import Frame
from castella.chart import (
    DrillDownChart,
    HierarchicalChartData,
    HierarchicalNode,
    DataPoint,
    BarChart,
    PieChart,
    StackedBarChart,
    HeatmapChart,
)


def create_sales_data() -> HierarchicalChartData:
    """Create hierarchical sales data: Region -> Country -> City."""

    # Root level: Regions
    data = HierarchicalChartData(
        title="Global Sales (Click to drill down)",
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

    # North America -> Countries
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

    # USA -> Cities
    usa_node = HierarchicalNode(
        id="usa",
        label="USA",
        level_name="City",
        data=[
            DataPoint(category="New York", value=350, label="New York"),
            DataPoint(category="Los Angeles", value=280, label="Los Angeles"),
            DataPoint(category="Chicago", value=170, label="Chicago"),
            DataPoint(category="Houston", value=100, label="Houston"),
        ],
    )
    na_node.add_child("USA", usa_node)

    # Canada -> Cities
    canada_node = HierarchicalNode(
        id="canada",
        label="Canada",
        level_name="City",
        data=[
            DataPoint(category="Toronto", value=180, label="Toronto"),
            DataPoint(category="Vancouver", value=120, label="Vancouver"),
            DataPoint(category="Montreal", value=100, label="Montreal"),
        ],
    )
    na_node.add_child("Canada", canada_node)

    # Europe -> Countries
    europe_node = HierarchicalNode(
        id="europe",
        label="Europe",
        level_name="Country",
        data=[
            DataPoint(category="UK", value=450, label="UK"),
            DataPoint(category="Germany", value=400, label="Germany"),
            DataPoint(category="France", value=350, label="France"),
        ],
    )
    data.root.add_child("Europe", europe_node)

    # UK -> Cities
    uk_node = HierarchicalNode(
        id="uk",
        label="UK",
        level_name="City",
        data=[
            DataPoint(category="London", value=250, label="London"),
            DataPoint(category="Manchester", value=120, label="Manchester"),
            DataPoint(category="Birmingham", value=80, label="Birmingham"),
        ],
    )
    europe_node.add_child("UK", uk_node)

    # Asia -> Countries
    asia_node = HierarchicalNode(
        id="asia",
        label="Asia",
        level_name="Country",
        data=[
            DataPoint(category="Japan", value=800, label="Japan"),
            DataPoint(category="China", value=600, label="China"),
            DataPoint(category="South Korea", value=400, label="South Korea"),
        ],
    )
    data.root.add_child("Asia", asia_node)

    # Japan -> Cities
    japan_node = HierarchicalNode(
        id="japan",
        label="Japan",
        level_name="City",
        data=[
            DataPoint(category="Tokyo", value=400, label="Tokyo"),
            DataPoint(category="Osaka", value=250, label="Osaka"),
            DataPoint(category="Nagoya", value=150, label="Nagoya"),
        ],
    )
    asia_node.add_child("Japan", japan_node)

    return data


def create_stacked_sales_data() -> HierarchicalChartData:
    """Create hierarchical multi-series sales data for StackedBarChart.

    Each level has quarterly breakdown (Q1, Q2, Q3, Q4).
    Region -> Country -> City with quarterly data.
    """

    def make_quarterly_data(
        categories: list[str], base_values: list[float]
    ) -> dict[str, list[DataPoint]]:
        """Create quarterly series data for given categories."""
        quarters = ["Q1", "Q2", "Q3", "Q4"]
        # Quarterly ratios (Q4 is typically highest)
        ratios = [0.2, 0.25, 0.25, 0.3]
        result: dict[str, list[DataPoint]] = {}
        for q_idx, quarter in enumerate(quarters):
            points = []
            for cat, base in zip(categories, base_values):
                value = base * ratios[q_idx]
                points.append(DataPoint(category=cat, value=value, label=cat))
            result[quarter] = points
        return result

    # Root level: Regions with quarterly breakdown
    data = HierarchicalChartData(
        title="Quarterly Sales by Region (Click to drill down)",
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

    # North America -> Countries
    na_node = HierarchicalNode(
        id="na",
        label="North America",
        level_name="Country",
        series_data=make_quarterly_data(
            ["USA", "Canada", "Mexico"],
            [900, 400, 200],
        ),
    )
    data.root.add_child("North America", na_node)

    # USA -> Cities
    usa_node = HierarchicalNode(
        id="usa",
        label="USA",
        level_name="City",
        series_data=make_quarterly_data(
            ["New York", "Los Angeles", "Chicago", "Houston"],
            [350, 280, 170, 100],
        ),
    )
    na_node.add_child("USA", usa_node)

    # Canada -> Cities
    canada_node = HierarchicalNode(
        id="canada",
        label="Canada",
        level_name="City",
        series_data=make_quarterly_data(
            ["Toronto", "Vancouver", "Montreal"],
            [180, 120, 100],
        ),
    )
    na_node.add_child("Canada", canada_node)

    # Europe -> Countries
    europe_node = HierarchicalNode(
        id="europe",
        label="Europe",
        level_name="Country",
        series_data=make_quarterly_data(
            ["UK", "Germany", "France"],
            [450, 400, 350],
        ),
    )
    data.root.add_child("Europe", europe_node)

    # UK -> Cities
    uk_node = HierarchicalNode(
        id="uk",
        label="UK",
        level_name="City",
        series_data=make_quarterly_data(
            ["London", "Manchester", "Birmingham"],
            [250, 120, 80],
        ),
    )
    europe_node.add_child("UK", uk_node)

    # Asia -> Countries
    asia_node = HierarchicalNode(
        id="asia",
        label="Asia",
        level_name="Country",
        series_data=make_quarterly_data(
            ["Japan", "China", "South Korea"],
            [800, 600, 400],
        ),
    )
    data.root.add_child("Asia", asia_node)

    # Japan -> Cities
    japan_node = HierarchicalNode(
        id="japan",
        label="Japan",
        level_name="City",
        series_data=make_quarterly_data(
            ["Tokyo", "Osaka", "Nagoya"],
            [400, 250, 150],
        ),
    )
    asia_node.add_child("Japan", japan_node)

    return data


class DrillDownDemo(StatefulComponent):
    """Demo with tabs for BarChart, PieChart, StackedBarChart, and HeatmapChart."""

    def __init__(self):
        self._chart_type = State("bar")
        super().__init__(self._chart_type)

        # Create separate data for each chart type
        # (each needs its own DrillDownState)
        self._bar_data = create_sales_data()
        self._pie_data = create_sales_data()
        self._stacked_data = create_stacked_sales_data()  # Multi-series for stacking
        self._heatmap_data = create_stacked_sales_data()  # Reuse multi-series for heatmap

    def view(self) -> Widget:
        chart_type = self._chart_type()

        # Tab buttons
        tab_bar = Row(
            Button("BarChart", font_size=12)
            .on_click(lambda _: self._chart_type.set("bar"))
            .bg_color("#3b82f6" if chart_type == "bar" else "#333333")
            .fixed_height(32)
            .width_policy(SizePolicy.CONTENT),
            Button("PieChart", font_size=12)
            .on_click(lambda _: self._chart_type.set("pie"))
            .bg_color("#3b82f6" if chart_type == "pie" else "#333333")
            .fixed_height(32)
            .width_policy(SizePolicy.CONTENT),
            Button("StackedBarChart", font_size=12)
            .on_click(lambda _: self._chart_type.set("stacked"))
            .bg_color("#3b82f6" if chart_type == "stacked" else "#333333")
            .fixed_height(32)
            .width_policy(SizePolicy.CONTENT),
            Button("HeatmapChart", font_size=12)
            .on_click(lambda _: self._chart_type.set("heatmap"))
            .bg_color("#3b82f6" if chart_type == "heatmap" else "#333333")
            .fixed_height(32)
            .width_policy(SizePolicy.CONTENT),
        ).fixed_height(40)

        # Create the appropriate chart
        if chart_type == "bar":
            chart = (
                DrillDownChart(
                    self._bar_data,
                    chart_type=BarChart,
                    show_values=True,
                )
                .on_drill_down(lambda ev: print(f"[Bar] Drilled: {ev.clicked_key}"))
            )
        elif chart_type == "pie":
            chart = (
                DrillDownChart(
                    self._pie_data,
                    chart_type=PieChart,
                    donut=True,
                )
                .on_drill_down(lambda ev: print(f"[Pie] Drilled: {ev.clicked_key}"))
            )
        elif chart_type == "stacked":
            chart = (
                DrillDownChart(
                    self._stacked_data,
                    chart_type=StackedBarChart,
                    show_values=True,
                )
                .on_drill_down(lambda ev: print(f"[Stacked] Drilled: {ev.clicked_key}"))
            )
        else:  # heatmap
            chart = (
                DrillDownChart(
                    self._heatmap_data,
                    chart_type=HeatmapChart,
                    show_values=True,
                )
                .on_drill_down(lambda ev: print(f"[Heatmap] Drilled: {ev.clicked_key}"))
            )

        return Column(
            Text("Drill-Down Chart Demo", font_size=18)
            .text_color("#ffffff")
            .fixed_height(30),
            Text("Click on a bar/slice/cell to drill down, use Back or breadcrumbs to go up", font_size=12)
            .text_color("#888888")
            .fixed_height(24),
            tab_bar,
            chart,
        )


def main() -> None:
    """Run the drill-down chart example."""
    App(Frame("Drill-Down Chart", 900, 600), DrillDownDemo()).run()


if __name__ == "__main__":
    main()
