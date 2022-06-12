from cattt.core import App, Button, Column, PositionPolicy, Row, Spacer, Text
from cattt.frame import Frame

App(
    Frame("Demo", width=600, height=400),
    Column(
        Row(Spacer(), Text("Text 1")).fixed_size(300, 100),
        Button("Button 1").width(399).on_click(lambda ev: print(ev)),
        Row(
            Button("Button 2").flex(2),
            Column(Button("Button 3"), Button("Button 4")),
        ).fixed_height(200),
    ),
).push_layer(
    Column(Button("Button X").on_click(lambda ev: App.get().pop_layer())).fixed_size(
        300, 300
    ),
    PositionPolicy.CENTER,
).run()
