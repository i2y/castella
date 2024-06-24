from castella import App, Row, Button, Column, TextAlign
from castella.frame import Frame

App(
    Frame("Button"),
    Row(
        Column(
            Button("First"),
            Button("Second", align=TextAlign.CENTER),
            Button("Third", align=TextAlign.RIGHT),
            Button("Fourth", align=TextAlign.LEFT),
        ).spacing(10)
    ).spacing(10),
).run()
