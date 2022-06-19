import threading
import time
from datetime import datetime

from castella import App, Component, State, Text
from castella.frame import Frame


class Clock(Component):
    def __init__(self):
        super().__init__()
        self._state = State(datetime.now().time().strftime("%X"))
        self._thread = threading.Thread(target=self.run, args=())
        self._thread.daemon = True
        self._thread.start()

    def run(self):
        while True:
            time.sleep(1)
            self._state.set(datetime.now().time().strftime("%X"))

    def view(self):
        return Text(self._state)


App(Frame("Clock", 600, 200), Clock()).run()
