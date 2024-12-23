from castella import App, Button, Column, StatefulComponent, State, Text
from castella.frame import Frame


class NumList(StatefulComponent):
    def __init__(self, n: State[int]):
        super().__init__(n)
        self._num: State[int] = n

    def view(self):
        return Column(
            Button("Add")
            .fixed_height(40)
            .on_click(lambda _: self._num.set(self._num() + 1)),
            *(Text(i + 1).fixed_height(40) for i in range(self._num())),
            scrollable=True,
        )


App(Frame("NumList"), NumList(State(1))).run()
