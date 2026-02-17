from castella import App, Row, Text
from castella.frame import Frame

App(
    Frame("Row"),
    Row(
        Text("First", font_size=24).fixed_size(100, 50),
        Text("Second", font_size=24).flex(2),
        Text("Third", font_size=24).flex(1),
    ),
).run()
