from castella import App, Button, Column, Component, Row, State, Text
from castella.frame import Frame


class Count(State[int]):
    def __str__(self):
        return f"count: {self._value}"


class Counter(Component):
    def __init__(self):
        super().__init__()
        self._count = Count(0)

    def view(self):
        return Column(
            Text(self._count),
            Row(
                Button("Up", font_size=50).on_click(self.up),
                Button("Down", font_size=50).on_click(self.down),
            ),
            Button("Init", font_size=50).on_click(self.init),
        )

    def up(self, _):
        self._count += 1

    def down(self, _):
        self._count -= 1

    def init(self, _):
        self._count.set(0)


App(
    Frame("Counter", width=800, height=600),
    Counter(),
).run()
