from castella import App, Row, Text
from castella.frame import Frame

App(
    Frame("Row"),
    Row(
        Text("First", font_size=24),
        Text("Second", font_size=24),
        Text("Third", font_size=24),
    ),
).run()
