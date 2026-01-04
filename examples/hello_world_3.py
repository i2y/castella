from castella import App, Text
from castella.frame import Frame

App(Frame("Hello world", 480, 300), Text("Hello World!").fixed_size(100, 200)).run()
