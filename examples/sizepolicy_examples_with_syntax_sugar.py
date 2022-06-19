from castella import App, Column, Text
from castella.frame import Frame

App(
    Frame("Layouts", 800, 600),
    Column(
        Text("abc").fit_parent(),
        Text("abc").fixed_width(200),
        Text("abc").fixed_height(200),
        Text("abc").fixed_size(200, 100),
        Text("abc", font_size=40).fit_content_width(),
        Text("abc", font_size=40).fit_content_height(),
        Text("abc", font_size=40).fit_content(),
    ).spacing(10),
).run()
