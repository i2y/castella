from castella import App, Button, Column, Component, Row, State, Text
from castella.frame import Frame


class Counter(Component):
    def view(self):
        count = State(0)
        up = lambda _: count.set(count() + 1)
        down = lambda _: count.set(count() - 1)

        return Column(
            Text(count),
            Row(
                Button("+", font_size=50).on_click(up),
                Button("-", font_size=50).on_click(down),
            ),
        )


App(Frame("Counter", 800, 600), Counter()).run()
