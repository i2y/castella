from cattt.core import App, Button, Column, Component, Row, State, Text
from cattt.frame import Frame


class Counter(Component):
    def __init__(self, count: int):
        super().__init__()
        self._count = State(count)

    def view(self):
        return Column(
            Text(self._count),
            Row(Button("Up").on_click(self.up), Button("Down").on_click(self.down)),
            Button("Init").on_click(self.init),
        )

    def up(self, _):
        self._count += 1

    def down(self, _):
        self._count -= 1

    def init(self, _):
        self._count.set(0)


App(
    Frame("Counter", width=1200, height=600),
    Column(
        Row(
            Counter(0).fixed_width(300),
            Counter(0),
        ).flex(3).spacing(10),
        Row(Counter(100).flex(1)).spacing(10),
    ).spacing(20),
).run()
