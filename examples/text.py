from castella import App, Row, Column, Text, TextAlign, Kind
from castella.frame import Frame

App(
    Frame("Button"),
    Row(
        Column(
            Text("First", kind=Kind.NORMAL),
            Text("Second", kind=Kind.INFO, align=TextAlign.CENTER),
            Text("Third", kind=Kind.SUCCESS, align=TextAlign.RIGHT),
            Text("Fourth", kind=Kind.WARNING, align=TextAlign.LEFT),
            Text("Fifth", kind=Kind.DANGER, align=TextAlign.LEFT),
        ).spacing(10)
    ).spacing(10),
).run()
