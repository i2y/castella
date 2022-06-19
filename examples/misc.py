from castella import (
    App,
    Box,
    Button,
    Column,
    Component,
    Image,
    Input,
    NetImage,
    Row,
    Spacer,
    State,
    StatefulComponent,
    Text,
)
from castella.frame import Frame


class Counter(Component):
    def __init__(self, count: State[int]):
        super().__init__()
        self.count = count

    def view(self):
        c = self.count
        return Row(
            Button("Up", font_size=50).on_click(lambda _: c.set(c() + 1)),
            Text(self.count),
            Button("Down", font_size=50).on_click(lambda _: c.set(c() - 1)),
        )


class NumList(StatefulComponent):
    def __init__(self, n: State[int]):
        super().__init__(n)
        self.num: State[int] = n

    def view(self):
        return Column(
            *(Text(i + 1).fixed_height(30) for i in range(self.num())), scrollable=True
        )


DOME_TENT_IMG = (
    "https://github.com/i2y/castella/blob/main/examples/camp_tent.png?raw=true"
)

c: State[int] = State(0)

App(
    Frame(title="Counter", width=800, height=600),
    Column(
        Counter(c),
        Spacer().fixed_height(20),
        Box(
            Row(
                Image(file_path="camp_tent_sankaku.png"), NetImage(url=DOME_TENT_IMG)
            ).fit_content()
        ),
        NumList(c),
        Input("fafa"),
    ),
).run()
