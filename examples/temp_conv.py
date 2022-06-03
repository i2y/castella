from cattt.core import (
    App,
    Input,
    Component,
    Row,
    InputState,
    Text,
    TextAlign,
)
from cattt.frame import Frame


class TempConv(Component):
    def __init__(self):
        super().__init__()
        self._c = InputState("0")
        self._f = InputState("32")

    def view(self):
        return Row(
            Input(self._c, font_size=80, align=TextAlign.RIGHT).on_change(self.to_f),
            Text("°C", font_size=80).fixed_width(100),
            Text("=", font_size=50).fixed_width(100),
            Input(self._f, font_size=80, align=TextAlign.RIGHT).on_change(self.to_c),
            Text("°F", font_size=80).fixed_width(100),
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


App(Frame("TempConv", 900, 100), TempConv()).run()
