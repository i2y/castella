from castella import (
    App,
    CheckBox,
    Text,
    TextAlign,
    Column,
    Row,
    Spacer,
    State,
)
from castella.bar_chart import BarChart, BarChartState
from castella.pie_chart import PieChart, PieChartState
from castella.frame import Frame


bar_chart_state = BarChartState(label=[], value=[])
pie_chart_state = PieChartState(label=[], value=[])

foo = State(True)
bar = State(True)


def update_chart_state() -> None:
    label = []
    value = []
    if foo.value():
        label.append("Foo")
        value.append(50)
    if bar.value():
        label.append("Bar")
        value.append(100)
    bar_chart_state.set(label, value)
    pie_chart_state.set(label, value)


foo.on_update(update_chart_state)
bar.on_update(update_chart_state)

update_chart_state()

App(
    Frame("Chart", 1500, 500),
    Column(
        Spacer().fixed_height(10),
        Row(
            Column(
                Row(
                    Text("Foo", align=TextAlign.RIGHT).erase_border(),
                    CheckBox(foo).fixed_width(40),
                    Spacer().fixed_width(10),
                ).fixed_height(40),
                Row(
                    Text("Bar", align=TextAlign.RIGHT).erase_border(),
                    CheckBox(bar).fixed_width(40),
                    Spacer().fixed_width(10),
                ).fixed_height(40),
            )
            .fixed_width(100)
            .spacing(10),
            BarChart(bar_chart_state),
            Spacer().fixed_width(10),
            PieChart(pie_chart_state),
        ).fixed_width(1400),
    ),
).run()
