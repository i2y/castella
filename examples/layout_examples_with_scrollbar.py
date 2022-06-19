from castella import App, Box, Column, Row, Text
from castella.frame import Frame

App(
    Frame("Layouts", 800, 600),
    Column(
        Box(Row(Text("r1-1"), Text("r1-2"), Text("r1-3")).fixed_size(900, 300)),
        Row(
            Text("r2-1").fixed_width(300),
            Text("r2-2").fixed_width(300),
            Text("r2-3").fixed_width(300),
            scrollable=True,
        ),
        Column(
            Text("c1-1").fixed_height(100),
            Text("c1-2").fixed_height(100),
            Text("c1-3").fixed_height(100),
            scrollable=True,
        ),
    ).spacing(10),
).run()
