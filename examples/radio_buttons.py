from castella import App, RadioButtons, RadioButtonsState
from castella.frame import Frame

App(
    Frame("Checkboxes", 320, 160),
    RadioButtons(RadioButtonsState(("Foo", "Bar", "Hoge"), 1))
    .button_width(28)
    .fixed_width(200),
).run()
