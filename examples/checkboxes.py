from castella import App, CheckBox, Text, TextAlign, Column, Row
from castella.frame import Frame

App(
    Frame("Checkboxes", 480, 300),
    Column(
        Row(
            Text("Foo", align=TextAlign.RIGHT).erase_border(),
            CheckBox().fixed_width(40),
        )
        .fixed_height(40)
        .spacing(10),
        Row(
            Text("Bar", align=TextAlign.RIGHT).erase_border(),
            CheckBox().fixed_width(40),
        )
        .fixed_height(40)
        .spacing(10),
        scrollable=True,
    ).spacing(10),
).run()
