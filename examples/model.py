from castella import App, Box, Column, Button, Text, Model
from castella.frame import Frame


class User(Model):
    name: str = "Bob"
    age: int
    balance: float
    is_active: bool


user = User(age=25, balance=100.0, is_active=True)

App(
    Frame("Box"),
    Column(
        Text(user.name, font_size=24),
        Button("Change Name").on_click(lambda _: setattr(user, "name", "Alice")),
    ),
).run()
