from castella import App, CheckBox, Text, TextAlign, Column, Row, Button
from castella.frame import Frame


App.default_font_family("Yu Gothic UI")

App(
    Frame("Checkboxes", 480, 300),
    Column(
        Row(
            Text("あいうえお", align=TextAlign.RIGHT).erase_border(),
            CheckBox(True).fixed_width(40),
        )
        .fixed_height(40)
        .spacing(10),
        Row(
            Text("かきくけこ", align=TextAlign.RIGHT).erase_border(),
            CheckBox().fixed_width(40),
        )
        .fixed_height(40)
        .spacing(10),
        scrollable=True,
    ).spacing(10),
).run()
