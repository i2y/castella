from cattt.core import App, Button, Column, Component, Row, State, Text
from cattt.frame import Frame


class Counter(Component):
    def view(self):
        count = State(0)
        up = lambda _: count.set(count() + 1)
        down = lambda _: count.set(count() - 1)

        return Column(
            Text(count), Row(Button("+").on_click(up), Button("-").on_click(down))
        )


App(Frame("Counter", 800, 600), Counter()).run()
