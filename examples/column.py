from castella import App, Column, Text
from castella.frame import Frame

App(
    Frame("Column"),
    Column(
        Text("First", font_size=24),
        Text("Second", font_size=24),
        Text("Third", font_size=24),
    ),
).run()
