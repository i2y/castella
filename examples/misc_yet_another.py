from pydantic import BaseModel, Field
from castella import (
    App,
    Button,
    Column,
    Component,
    ScrollState,
    StatefulComponent,
    Input,
    Row,
    Spacer,
    State,
    Text,
    DataTable,
    TableModel,
)

from castella.frame import Frame
from castella import EM


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
        self._scroll = ScrollState()  # Preserves scroll position across re-renders

    def view(self):
        return Column(
            *(Text(i + 1).fixed_height(3 * EM) for i in range(self.num())),
            scrollable=True,
            scroll_state=self._scroll,
        )


class Person(BaseModel):
    name: str = Field(..., title="Name")
    age: int = Field(..., title="Age")
    country: str = Field(..., title="Country")


persons = [
    Person(name="Alice", age=25, country="USA"),
    Person(name="Bob", age=30, country="UK"),
    Person(name="Charlie", age=35, country="Japan"),
    Person(name="David", age=40, country="China"),
    Person(name="Eve", age=45, country="Russia"),
    Person(name="Frank", age=50, country="India"),
    Person(name="Grace", age=55, country="Brazil"),
    Person(name="Helen", age=60, country="France"),
    Person(name="Ivy", age=65, country="Germany"),
    Person(name="Jack", age=70, country="Italy"),
    Person(name="Kelly", age=75, country="Canada"),
    Person(name="Larry", age=80, country="Australia"),
    Person(name="Mary", age=85, country="Spain"),
    Person(name="Nancy", age=90, country="Mexico"),
    Person(name="Olivia", age=95, country="Argentina"),
    Person(name="Peter", age=100, country="Chile"),
    Person(name="Queen", age=105, country="Peru"),
    Person(name="Roger", age=110, country="Cuba"),
    Person(name="Sally", age=115, country="Egypt"),
    Person(name="Tom", age=120, country="Greece"),
    Person(name="Ursula", age=125, country="Turkey"),
    Person(name="Victor", age=130, country="India"),
    Person(name="Wendy", age=135, country="Brazil"),
    Person(name="Xavier", age=140, country="France"),
    Person(name="Yvonne", age=145, country="Germany"),
    Person(name="Zack", age=150, country="Italy"),
    Person(name="Alpha", age=155, country="Canada"),
]

model = TableModel.from_pydantic_model(persons)
table = DataTable(model)


DOME_TENT_IMG = (
    "https://github.com/i2y/castella/blob/main/examples/camp_tent.png?raw=true"
)


c: State[int] = State(10)

App(
    Frame(title="Counter", width=800, height=600),
    Column(
        Counter(c),
        Spacer().fixed_height(EM),
        NumList(c),
        Spacer().fixed_height(EM),
        table,
        Spacer().fixed_height(EM),
        Input("fafa"),
        Spacer().fixed_height(EM),
    ),
).run()
