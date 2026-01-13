"""Basic charts example using native chart widgets."""

from castella import (
    App,
    CheckBox,
    Text,
    TextAlign,
    Column,
    Row,
    Spacer,
    State,
    Component,
)
from castella.frame import Frame
from castella.chart import (
    BarChart,
    PieChart,
    CategoricalChartData,
    CategoricalSeries,
    SeriesStyle,
)


class ChartsDemo(Component):
    def __init__(self):
        super().__init__()
        self._foo = State(True)
        self._bar = State(True)
        self._foo.attach(self)
        self._bar.attach(self)

        self._bar_data = CategoricalChartData(title="Bar Chart")
        self._pie_data = CategoricalChartData(title="Pie Chart")
        self._bar_data.attach(self)
        self._pie_data.attach(self)

        self._update_chart_data()

    def _update_chart_data(self):
        categories = []
        values = []
        if self._foo():
            categories.append("Foo")
            values.append(50)
        if self._bar():
            categories.append("Bar")
            values.append(100)

        if categories:
            series = CategoricalSeries.from_values(
                name="Data",
                categories=categories,
                values=values,
                style=SeriesStyle(color="#3b82f6"),
            )
            self._bar_data.set_series([series])
            self._pie_data.set_series([series])
        else:
            self._bar_data.set_series([])
            self._pie_data.set_series([])

    def _on_foo_change(self, checked):
        self._foo.set(checked)
        self._update_chart_data()

    def _on_bar_change(self, checked):
        self._bar.set(checked)
        self._update_chart_data()

    def view(self):
        return Column(
            Spacer().fixed_height(10),
            Row(
                Column(
                    Row(
                        Text("Foo", align=TextAlign.RIGHT).erase_border(),
                        CheckBox(self._foo).on_change(self._on_foo_change).fixed_width(40),
                        Spacer().fixed_width(10),
                    ).fixed_height(40),
                    Row(
                        Text("Bar", align=TextAlign.RIGHT).erase_border(),
                        CheckBox(self._bar).on_change(self._on_bar_change).fixed_width(40),
                        Spacer().fixed_width(10),
                    ).fixed_height(40),
                )
                .fixed_width(100)
                .spacing(10),
                BarChart(self._bar_data, show_values=True),
                Spacer().fixed_width(10),
                PieChart(self._pie_data, show_labels=True),
            ).fixed_width(1400),
        )


App(Frame("Chart", 1500, 500), ChartsDemo()).run()
