from castella import App, Column, SizePolicy, Text
from castella.frame import Frame

App(
    Frame("Layouts", 800, 600),
    Column(
        Text("abc"),
        Text("abc").width_policy(SizePolicy.FIXED).width(200),
        Text("abc").height_policy(SizePolicy.FIXED).height(200),
        Text("abc")
        .width_policy(SizePolicy.FIXED)
        .height_policy(SizePolicy.FIXED)
        .width(200)
        .height(100),
        Text("abc", font_size=40).width_policy(SizePolicy.CONTENT),
        Text("abc", font_size=40).height_policy(SizePolicy.CONTENT),
        Text("abc", font_size=40)
        .width_policy(SizePolicy.CONTENT)
        .height_policy(SizePolicy.CONTENT),
    ).spacing(10),
).run()
