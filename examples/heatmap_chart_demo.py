"""Heatmap Chart Demo - Demonstrates HeatmapChart widget with various colormaps."""

from castella import App, Column, Row, Text, Button
from castella.chart import HeatmapChart, HeatmapChartData, ColormapType
from castella.core import Component, State
from castella.frame import Frame


class HeatmapChartDemo(Component):
    """Demo component showcasing HeatmapChart features."""

    def __init__(self):
        super().__init__()
        self._colormap = State(ColormapType.VIRIDIS)
        self._colormap.attach(self)
        self._show_values = State(True)
        self._show_values.attach(self)

        # Create correlation matrix data
        self._data = HeatmapChartData.from_2d_array(
            values=[
                [1.00, 0.85, 0.42, -0.15, 0.23],
                [0.85, 1.00, 0.55, 0.08, 0.31],
                [0.42, 0.55, 1.00, 0.67, 0.45],
                [-0.15, 0.08, 0.67, 1.00, 0.72],
                [0.23, 0.31, 0.45, 0.72, 1.00],
            ],
            row_labels=["Price", "Volume", "Volatility", "Beta", "Momentum"],
            column_labels=["Price", "Volume", "Volatility", "Beta", "Momentum"],
            title="Correlation Matrix",
        )
        self._data.set_range(-1.0, 1.0)

    def _set_colormap(self, cmap: ColormapType):
        def handler(_):
            self._colormap.set(cmap)

        return handler

    def _toggle_values(self, _):
        self._show_values.set(not self._show_values())

    def view(self):
        colormap = self._colormap()
        show_values = self._show_values()

        # Colormap buttons
        colormap_buttons = Row(
            Text("Colormap: ").fixed_width(80),
            Button("Viridis").on_click(self._set_colormap(ColormapType.VIRIDIS)),
            Button("Plasma").on_click(self._set_colormap(ColormapType.PLASMA)),
            Button("Inferno").on_click(self._set_colormap(ColormapType.INFERNO)),
            Button("Magma").on_click(self._set_colormap(ColormapType.MAGMA)),
        ).fixed_height(40)

        # Options
        options = Row(
            Button(f"Values: {'ON' if show_values else 'OFF'}").on_click(
                self._toggle_values
            ),
        ).fixed_height(40)

        # Chart
        chart = (
            HeatmapChart(
                self._data,
                colormap=colormap,
                show_values=show_values,
                show_colorbar=True,
                cell_gap=2.0,
            )
            .on_hover(lambda ev: print(f"Hover: {ev.label} = {ev.value:.2f}"))
            .on_click(lambda ev: print(f"Click: {ev.label} = {ev.value:.2f}"))
        )

        return Column(
            Text("Heatmap Chart Demo").fixed_height(30),
            colormap_buttons,
            options,
            chart,
        )


def main():
    app = App(Frame("Heatmap Chart Demo", 800, 600), HeatmapChartDemo())
    app.run()


if __name__ == "__main__":
    main()
