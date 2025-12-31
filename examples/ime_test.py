"""IME (Input Method Editor) Test Application.

This example tests Japanese/Chinese IME input.
"""

from castella import App, Column, Input, Text, Component
from castella.core import State
from castella.frame import Frame


class IMETestApp(Component):
    def __init__(self):
        super().__init__()
        self._text1 = State("")
        self._text2 = State("")
        # DON'T attach Input states - causes focus loss on every keystroke
        # self._text1.attach(self)
        # self._text2.attach(self)

    def view(self):
        return Column(
            Text("IME Input Test").height(40),
            Text("Type Japanese/Chinese text below:").height(30),
            Input(self._text1()).on_change(lambda t: self._text1.set(t)).height(40),
            Text("Second input field:").height(30),
            Input(self._text2()).on_change(lambda t: self._text2.set(t)).height(40),
        )


if __name__ == "__main__":
    App(Frame("IME Test", 500, 300), IMETestApp()).run()
