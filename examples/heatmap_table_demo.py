"""Heatmap Table Demo - Demonstrates DataTable with heatmap cell coloring."""

from castella import (
    App,
    Column,
    Row,
    Text,
    Button,
    DataTable,
    DataTableState,
    ColumnConfig,
    HeatmapConfig,
)
from castella.chart import ColormapType
from castella.core import Component, State
from castella.frame import Frame


class HeatmapTableDemo(Component):
    """Demo component showcasing DataTable heatmap features."""

    def __init__(self):
        super().__init__()
        self._colormap = State(ColormapType.VIRIDIS)
        self._colormap.attach(self)

        # Sales data by region and quarter
        self._columns = [
            ColumnConfig(name="Region", width=120),
            ColumnConfig(name="Q1", width=80),
            ColumnConfig(name="Q2", width=80),
            ColumnConfig(name="Q3", width=80),
            ColumnConfig(name="Q4", width=80),
            ColumnConfig(name="Total", width=100),
        ]

        self._rows = [
            ["North America", 145, 162, 178, 195, 680],
            ["Europe", 122, 138, 155, 168, 583],
            ["Asia Pacific", 198, 215, 242, 267, 922],
            ["Latin America", 67, 78, 92, 105, 342],
            ["Middle East", 45, 52, 61, 73, 231],
            ["Africa", 32, 38, 45, 56, 171],
        ]

        self._state = DataTableState(columns=self._columns, rows=self._rows)
        self._apply_heatmap()

    def _apply_heatmap(self):
        """Apply heatmap coloring to numeric columns."""
        colormap = self._colormap()
        heatmap = HeatmapConfig(colormap=colormap)

        # Apply heatmap to Q1-Q4 columns (indices 1-4)
        for i in range(1, 5):
            self._state.columns[i].cell_bg_color = heatmap.create_color_fn(
                col_idx=i, state=self._state
            )

        # Apply heatmap to Total column with separate range
        total_heatmap = HeatmapConfig(colormap=colormap)
        self._state.columns[5].cell_bg_color = total_heatmap.create_color_fn(
            col_idx=5, state=self._state
        )

    def _set_colormap(self, cmap: ColormapType):
        def handler(_):
            self._colormap.set(cmap)
            self._apply_heatmap()
            # Trigger redraw
            self._state.notify()

        return handler

    def view(self):
        # Colormap buttons
        colormap_buttons = Row(
            Text("Colormap: ").fixed_width(80),
            Button("Viridis").on_click(self._set_colormap(ColormapType.VIRIDIS)),
            Button("Plasma").on_click(self._set_colormap(ColormapType.PLASMA)),
            Button("Inferno").on_click(self._set_colormap(ColormapType.INFERNO)),
            Button("Magma").on_click(self._set_colormap(ColormapType.MAGMA)),
        ).fixed_height(40)

        # Table
        table = DataTable(self._state).on_cell_click(
            lambda ev: print(f"Click: row={ev.row}, col={ev.column}, value={ev.value}")
        )

        return Column(
            Text("Heatmap Table Demo - Sales by Region and Quarter").fixed_height(30),
            colormap_buttons,
            table,
        )


def main():
    app = App(Frame("Heatmap Table Demo", 700, 400), HeatmapTableDemo())
    app.run()


if __name__ == "__main__":
    main()
