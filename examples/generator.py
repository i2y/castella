from castella import (
    App,
    Column,
    Kind,
    Row,
    Spacer,
    State,
    StatefulComponent,
    Switch,
    Text,
    TextAlign,
)
from castella.frame import Frame


class ExampleUsingGenerator(StatefulComponent):
    def __init__(self):
        self._mode = State(True)
        super().__init__(self._mode)

    def view(self):
        return Column(
            switch(self._mode),
            *main_component(self._mode),
        )


def switch(mode: State[bool]):
    return Row(
        Spacer(),
        Text("Column", align=TextAlign.RIGHT).fixed_width(80).erase_border(),
        Switch(mode).fixed_width(80),
    ).fixed_height(40)


def main_component(mode: State[bool]):
    if mode.value():
        yield Column(*children())
    else:
        yield Row(*children())


def children():
    yield Text("aaaaaaaaaa", kind=Kind.INFO)
    yield Text("bbbbbbbbbb", kind=Kind.DANGER)
    yield Text("cccccccccc", kind=Kind.WARNING)


App(Frame("ExampleUsingGenerator", 800, 600), ExampleUsingGenerator()).run()
