from castella import App, Column, Row, Text
from castella.frame import Frame

App(
    Frame("Layouts", 800, 600),
    Column(
        Row(Text("r1-1").flex(2), Text("r1-2"), Text("r1-3")),
        Row(Text("r2-1"), Text("r2-2").flex(2), Text("r2-3")).flex(2),
        Column(Text("c1-1"), Text("c1-2"), Text("c1-3").flex(2)).flex(3),
    ).spacing(10),
).run()
