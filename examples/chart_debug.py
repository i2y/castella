"""Debug script for chart hover/click issues."""

from castella import App, Component, Column, Row, Text, SizePolicy
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
from castella.chart.hit_testing import hit_test


class DebugBarChart(BarChart):
    """Bar chart with debug output."""

    def cursor_pos(self, ev):
        print(f"[BarChart] cursor_pos called at ({ev.pos.x:.1f}, {ev.pos.y:.1f})")
        print(f"  Elements count: {len(self._elements)}")
        if self._elements:
            for i, el in enumerate(self._elements):
                print(f"    Element {i}: rect=({el.rect.origin.x:.1f}, {el.rect.origin.y:.1f}, {el.rect.size.width:.1f}x{el.rect.size.height:.1f})")
        element = hit_test(self._elements, ev.pos)
        print(f"  Hit test result: {element.label if element else None}")
        super().cursor_pos(ev)

    def mouse_up(self, ev):
        print(f"[BarChart] mouse_up called at ({ev.pos.x:.1f}, {ev.pos.y:.1f})")
        super().mouse_up(ev)


class DebugLineChart(LineChart):
    """Line chart with debug output."""

    def cursor_pos(self, ev):
        print(f"[LineChart] cursor_pos called at ({ev.pos.x:.1f}, {ev.pos.y:.1f})")
        print(f"  Elements count: {len(self._elements)}")
        if self._elements:
            for i, el in enumerate(self._elements[:3]):  # First 3 only
                print(f"    Element {i}: center=({el.center.x:.1f}, {el.center.y:.1f}), r={el.radius:.1f}")
        element = hit_test(self._elements, ev.pos)
        print(f"  Hit test result: {element.label if element else None}")
        super().cursor_pos(ev)

    def mouse_up(self, ev):
        print(f"[LineChart] mouse_up called at ({ev.pos.x:.1f}, {ev.pos.y:.1f})")
        super().mouse_up(ev)


class DebugPieChart(PieChart):
    """Pie chart with debug output."""

    def cursor_pos(self, ev):
        print(f"[PieChart] cursor_pos called at ({ev.pos.x:.1f}, {ev.pos.y:.1f})")
        print(f"  Elements count: {len(self._elements)}")
        element = hit_test(self._elements, ev.pos)
        print(f"  Hit test result: {element.label if element else None}")
        super().cursor_pos(ev)

    def mouse_up(self, ev):
        print(f"[PieChart] mouse_up called at ({ev.pos.x:.1f}, {ev.pos.y:.1f})")
        super().mouse_up(ev)


class ChartDebugDemo(Component):
    """Debug demo for chart events."""

    def __init__(self):
        super().__init__()

        # Bar chart data
        self._bar_data = CategoricalChartData(title="Bar Test")
        self._bar_data.add_series(
            CategoricalSeries.from_values(
                name="Test",
                categories=["A", "B", "C"],
                values=[100, 150, 80],
                style=SeriesStyle(color="#3b82f6"),
            )
        )
        self._bar_data.attach(self)

        # Line chart data
        self._line_data = NumericChartData(title="Line Test")
        self._line_data.add_series(
            NumericSeries.from_y_values(
                name="Test",
                y_values=[20, 25, 22, 28, 24],
                style=SeriesStyle(color="#f59e0b"),
            )
        )
        self._line_data.attach(self)

        # Pie chart data
        self._pie_data = CategoricalChartData(title="Pie Test")
        self._pie_data.add_series(
            CategoricalSeries.from_values(
                name="Test",
                categories=["X", "Y", "Z"],
                values=[40, 35, 25],
            )
        )
        self._pie_data.attach(self)

    def view(self):
        return Column(
            Text("Chart Debug Demo", font_size=20)
            .height(40)
            .height_policy(SizePolicy.FIXED),
            Row(
                DebugBarChart(self._bar_data, show_values=True)
                .on_click(lambda ev: print(f">>> BAR CLICK: {ev.label}"))
                .on_hover(lambda ev: print(f">>> BAR HOVER: {ev.label}")),
                DebugLineChart(self._line_data, show_points=True)
                .on_click(lambda ev: print(f">>> LINE CLICK: {ev.label}"))
                .on_hover(lambda ev: print(f">>> LINE HOVER: {ev.value:.1f}")),
            ),
            Row(
                DebugPieChart(self._pie_data, show_labels=True)
                .on_click(lambda ev: print(f">>> PIE CLICK: {ev.label}"))
                .on_hover(lambda ev: print(f">>> PIE HOVER: {ev.label}")),
            ).height(300).height_policy(SizePolicy.FIXED),
        )


if __name__ == "__main__":
    print("Starting chart debug demo...")
    print("Move mouse over charts and click to see debug output")
    print("=" * 50)
    App(Frame("Chart Debug", 900, 500), ChartDebugDemo()).run()
