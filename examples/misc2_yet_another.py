import numpy as np
from castella import (
    App,
    Box,
    Button,
    Column,
    Component,
    Input,
    Kind,
    MultilineText,
    Row,
    ScrollState,
    State,
    StatefulComponent,
    Text,
    EM,
)
from castella.frame import Frame

array = np.zeros((200, 400, 4), dtype=np.uint8)
array[:, :, 3] = 255


class Counter(Component):
    def __init__(self, count: State[int]):
        super().__init__()
        self.count = count

    def view(self):
        c = self.count
        return Row(
            Button("Up", font_size=4 * EM).on_click(lambda _: c.set(c() + 1)),
            Text(self.count),
            Button("Down", font_size=4 * EM).on_click(lambda _: c.set(c() - 1)),
        )


class NumList(StatefulComponent):
    def __init__(self, n: State[int]):
        super().__init__(n)
        self.num = n
        self._scroll = ScrollState()

    def view(self):
        return Column(
            *(Text(i + 1).fixed_height(4) for i in range(self.num())),
            scrollable=True,
            scroll_state=self._scroll,
        )


TENT_IMG = "./camp_tent.png"

c: State[int] = State(0)

App(
    Frame(title="Misc", width=50 * EM, height=50 * EM),
    Row(
        Column(
            Counter(c).flex(2),
            Text("hoge", kind=Kind.INFO, font_size=EM),
            Text("hoge", kind=Kind.SUCCESS, font_size=EM),
            Text("hoge", kind=Kind.WARNING, font_size=EM),
            Box(
                MultilineText(
                    "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.",
                    font_size=EM,
                    kind=Kind.DANGER,
                    wrap=True,
                    padding=EM,
                    line_spacing=0,
                ),
            ),
            # Row(Switch(True).fixed_width(50), Switch(False)).fixed_height(25),
            # Box(Image(TENT_IMG).fixed_size(500, 300)).flex(4),
            # Row(NumList(c), Box(NumpyImage(array).fixed_size(400, 200))),
            Input("fafa", font_size=EM),
        )
    ),
).run()
