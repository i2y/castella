"""Basic DataTable example with live updates using the new DataTableState API."""

from pydantic import BaseModel, Field
from castella import App, DataTable, DataTableState
from castella.frame import Frame


class Person(BaseModel):
    name: str = Field(..., title="Name", description="Full name of the person")
    age: int = Field(..., title="Age", description="Age in years (0-200)")
    country: str = Field(..., title="Country", description="Country of residence")


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
    Person(name="Beta", age=160, country="Australia"),
    Person(name="Gamma", age=165, country="Spain"),
    Person(name="Delta", age=170, country="Mexico"),
]

# Create table state from Pydantic models
state = DataTableState.from_pydantic(persons)

# Create table
table = DataTable(state)


# Update model in background thread
def update_model():
    import time

    age_offset = 0
    while True:
        time.sleep(5)
        age_offset += 1
        # Update rows using the new API
        new_rows = [
            [p.name, p.age + age_offset, p.country]
            for p in persons
        ]
        state.set_rows(new_rows)


import threading

threading.Thread(target=update_model, daemon=True).start()


App(
    Frame("Table"),
    table,
).run()
