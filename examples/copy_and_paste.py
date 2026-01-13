from castella import (
    App,
    Column,
    Component,
    Row,
    Text,
    Button,
    State,
)
from castella.frame import Frame


class CopyAndPaste(Component):
    def __init__(self):
        super().__init__()
        self._text_1 = State("foo")
        self._text_2 = State("")

    def view(self):
        return Column(
            Row(
                Text(self._text_1, font_size=80).erase_border(),
                Button("Copy").on_click(
                    lambda _: App.get().set_clipboard_text(str(self._text_1))
                ),
            ).spacing(8),
            Row(
                Text(self._text_2, font_size=80).erase_border(),
                Button("Paste").on_click(
                    lambda _: self._text_2.set(App.get().get_clipboard_text())
                ),
            ).spacing(8),
        ).spacing(8)


App(Frame("Copy and Paste", 400, 200), CopyAndPaste()).run()
