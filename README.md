# Castella
Castella is a pure Python cross-platform UI framework.

<img src="https://user-images.githubusercontent.com/6240399/174487936-8484be0e-b2b5-433c-9416-594c0fd57f3a.png" style="height: 1em;"></img> [Documentation Site](https://i2y.github.io/castella) <img src="https://user-images.githubusercontent.com/6240399/174487787-7099167f-a8ad-42e8-9362-c19c84dc81be.png" style="height: 1em;"></img> [Examples](examples)

## Goals

The primary final goal of Castella is to provide features for Python programmers easy to create a GUI application for several OS platforms and web browsers in a single most same code as possible as. The second goal is to provide a UI framework that Python programmers can easily understand, modify, and extend as needed.
(Stated on May 25, 2022: This goal is the final goal. Currently this framework is in the super early stage, so this goal is far away. I hope to get much closer to the goal in a few months or a year by improving the implementation or documentation a little bit every day as much as possible.)

## Features
- The core part as a UI framework of Castella is written in only Python. It's not a wrapper for existing something written in other programing languages.
- Castella allows human to define UI declaratively in Python.
- Castella provides hot-reloading or hot-restarting on development.
- Dark mode is supported. If the runtime environment is in dark mode, Castella app's UI appearance will automatically be styled in dark mode.
- Castella utilizes GPU via dependent libraries.

## Dependencies
- For desktop platforms, Castella is standing on existing excellent python bindings for window management library (GLFW or SDL2) and 2D graphics library (Skia).
- For web browsers, Castella is standing on awesome Pyodide/PyScript and CanvasKit (Wasm version of Skia).

## Installation
https://i2y.github.io/castella/getting-started/

## An example of code using Castella

```python
from castella import App, Button, Column, Component, Row, State, Text
from castella.frame import Frame


class Counter(Component):
    def __init__(self):
        super().__init__()
        self._count = State(0)

    def view(self):
        return Column(
            Text(self._count),
            Row(
                Button("Up", font_size=50).on_click(self.up),
                Button("Down", font_size=50).on_click(self.down),
            ),
        )

    def up(self, _):
        self._count += 1

    def down(self, _):
        self._count -= 1


App(Frame("Counter", 800, 600), Counter()).run()
```

https://user-images.githubusercontent.com/6240399/171010621-8c0068d2-eb90-4332-8a1b-115291053d42.mp4

You can see some other examples in [examples](examples) directory.

## Supported Platforms
Currently, Castella theoretically should support not-too-old versions of the following platforms.

- Windows 10/11
- Mac OS X
- Linux
- Web browsers

Unfortunately, however, I could not actually confirm this at all on Linux, as I don't have a Linux machine these days. I want it..
Also, currently I have a only windows machine and it had already been updated to Windows 11, so I now confirm only it on Windows 11.
So, If anyone have an environment other than Windows 11, it would be helpful if you could try it and report back to me if you have any problems. If you find any problems, it would be more helpul if you could fix it.

## License
MIT License

Copyright (c) 2022 Yasushi Itoh

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NON-INFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
