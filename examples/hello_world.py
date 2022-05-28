from cattt.core import App, Text, TextAlign
from cattt.frame import Frame


App(Frame("Hello world", 480, 300),
    Text("Hello World!")).run()
