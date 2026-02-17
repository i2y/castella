from castella import App, Box, Text
from castella.frame import Frame


App(
    Frame("Box", 0, 0),
    Box(
        Text("Content", font_size=24).fixed_size(400, 400),
    ),
).run()
