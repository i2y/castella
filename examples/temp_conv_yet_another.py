from typing import Callable

from castella import (
    App,
    Column,
    Component,
    Input,
    InputState,
    Row,
    Text,
    TextAlign,
    EM,
)
from castella.frame import Frame


class TempConv(Component):
    def __init__(self):
        super().__init__()
        self._c = InputState("0")
        self._f = InputState("32")

    def view(self):
        return Column(
            Row(
                value(self._c, self.to_f),
                text("°C"),
                text("="),
                value(self._f, self.to_c),
                text("°F"),
            ).fixed_height(3 * EM)
        )

    def to_f(self, v: str):
        try:
            c = 0 if v == "" else float(v)
            self._f.set(str(round(c * 1.8 + 32, 2)))
        except:
            self._f.set("")

    def to_c(self, v: str):
        try:
            f = 0 if v == "" else float(v)
            self._c.set(str(round((f - 32) / 1.8, 2)))
        except:
            self._c.set("")


def text(s: str) -> Text:
    return Text(s, font_size=EM).fixed_width(4 * EM).erase_border()


def value(s: InputState, callback: Callable[[str], None]) -> Input:
    return Input(s, font_size=EM, align=TextAlign.RIGHT).on_change(callback)


App(Frame("TempConv", 90 * EM, 10 * EM), TempConv()).run()
