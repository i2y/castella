from castella import (
    App,
    Box,
    Button,
    Column,
    Component,
    Row,
    Spacer,
    MultilineText,
    State,
    Text,
    Kind,
)
from castella.frame import Frame


class PopupDemo(Component):
    def __init__(self):
        super().__init__()
        self._show_popup = State(False)
        self.model(self._show_popup)

    def view(self):
        main_content = Column(
            Row(Spacer(), Text("Text 1")).fixed_size(300, 100),
            Button("Button 1").on_click(lambda _: self._show_popup.set(True)),
            Row(
                Button("Button 2").flex(2),
                Column(Button("Button 3"), Button("Button 4")),
            ).fixed_height(200),
        ).z_index(1)

        if self._show_popup():
            popup = Column(
                MultilineText(
                    "BBBB BBB BB BBBB BBB BBBBB BB BBB",
                    font_size=30,
                    wrap=True,
                    kind=Kind.DANGER,
                ).fixed_height(200),
                Button("Close").on_click(
                    lambda _: self._show_popup.set(False)
                ).fixed_height(50),
            ).fixed_size(300, 250).z_index(10)

            return Box(main_content, popup)

        return main_content


App(
    Frame("Demo", width=600, height=400),
    PopupDemo(),
).run()
