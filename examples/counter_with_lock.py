from castella import (
    App,
    Button,
    Column,
    Component,
    Row,
    Spacer,
    State,
    Switch,
    Text,
    TextAlign,
)
from castella.frame import Frame

is_locked = State(False)


class Counter(Component):
    def __init__(self, lock):
        super().__init__()
        self._is_locked = lock

    def view(self):
        count = State(0)
        up = lambda _: count.set(count() + 1) if not self._is_locked() else ...
        down = lambda _: count.set(count() - 1) if not self._is_locked() else ...

        return Column(
            Text(count),
            Row(
                Button("+", font_size=50).on_click(up),
                Button("-", font_size=50).on_click(down),
            ),
        )


App(
    Frame("Counter", 800, 600),
    Column(
        Row(
            Spacer(),
            Text("Lock", align=TextAlign.RIGHT).fixed_width(80).erase_border(),
            Switch(is_locked)
            .fixed_width(80)
            .on_change(lambda v: print("locked") if v else print("unlocked")),
        ).fixed_height(40),
        Counter(is_locked),
    ),
).run()
