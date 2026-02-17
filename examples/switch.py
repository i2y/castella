from castella import App, Switch
from castella.frame import Frame

App(
    Frame("Switch"),
    Switch(True),
).run()
