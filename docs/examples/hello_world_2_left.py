from castella import App, Text, TextAlign
from castella.frame import Frame

App(
    Frame("Hello world", 480, 300),
    Text("Hello World!", font_size=20, align=TextAlign.LEFT),
).run()
