from castella import (
    App,
    show_popup,
    hide_popup,
    Button,
    Column,
    Row,
    Spacer,
    MultilineText,
    Text,
    Kind,
)
from castella.frame import Frame


App(
    Frame("Demo", width=600, height=400),
    Column(
        Row(Spacer(), Text("Text 1")).fixed_size(300, 100),
        Button("Button 1").on_click(
            lambda _: show_popup(
                Column(
                    MultilineText(
                        "BBBB BBB BB BBBB BBB BBBBB BB BBB",
                        font_size=30,
                        wrap=True,
                        kind=Kind.DANGER,
                    ).fixed_height(200),
                    Button("Close").on_click(lambda _: hide_popup()).fixed_height(50),
                ).fixed_size(300, 250)
            )
        ),
        Row(
            Button("Button 2").flex(2),
            Column(Button("Button 3"), Button("Button 4")),
        ).fixed_height(200),
    ),
).run()
