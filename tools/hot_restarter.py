import sys
import time
from subprocess import Popen

from watchdog.events import PatternMatchingEventHandler
from watchdog.observers import Observer


class Monitor:
    def __init__(self, filename):
        self.filename = filename
        self.proc = None

    def start_proc(self):
        self.proc = Popen([sys.executable, self.filename])

    def restart_proc(self):
        if self.proc is not None:
            self.proc.kill()
        self.start_proc()

    def run(self):
        self.start_proc()
        try:
            while True:
                time.sleep(0.5)
                if not (self.proc is None or self.proc.poll() is None):
                    self.restart_proc()
        except KeyboardInterrupt:
            if self.proc is not None:
                self.proc.kill()


class FileChangeHandler(PatternMatchingEventHandler):
    def __init__(self, m: Monitor):
        super().__init__(
            patterns=["*.py"],
            ignore_patterns=[],
            ignore_directories=True,
            case_sensitive=True,
        )
        self._monitor = m

    def on_modified(self, _):
        self._monitor.restart_proc()


if __name__ == "__main__":
    filename = sys.argv[1]
    monitor = Monitor(filename)
    observer = Observer()
    observer.schedule(FileChangeHandler(monitor), path=".", recursive=True)
    observer.start()
    monitor.run()
