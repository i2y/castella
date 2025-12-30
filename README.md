# Castella
Castella is a pure Python cross-platform UI framework.

<img src="https://user-images.githubusercontent.com/6240399/174487936-8484be0e-b2b5-433c-9416-594c0fd57f3a.png" style="height: 1em;"></img> [Documentation Site](https://i2y.github.io/castella) <img src="https://user-images.githubusercontent.com/6240399/174487787-7099167f-a8ad-42e8-9362-c19c84dc81be.png" style="height: 1em;"></img> [Examples](examples) <img src="https://user-images.githubusercontent.com/6240399/174487787-7099167f-a8ad-42e8-9362-c19c84dc81be.png" style="height: 1em;"></img> [Slides](https://speakerdeck.com/i2y/a-cross-platform-pure-python-declarative-ui-framework)

## Goals
The primary final goal of Castella is to provide features for Python programmers easy to create a UI application for several OS platforms and web browsers in a single most same code as possible as. The second goal is to provide a UI framework that Python programmers can easily understand, modify, and extend as needed.

## Features
- The core part as a UI framework of Castella is written in only Python. It's not a wrapper for existing something written in other programing languages. "pure Python cross-platform UI framework" specifies things like the above.
- Castella allows pythonista to define UI declaratively in Python.
- Castella provides hot-reloading or hot-restarting on development.
- Comprehensive theme system with design tokens (colors, typography, spacing).
- Built-in themes: Tokyo Night (default), Cupertino, Material Design 3, and classic Castella themes.
- Dark/light mode with automatic system detection and runtime switching.
- Rounded corners and shadows support for modern UI aesthetics.
- Custom themes via `Theme.derive()` for partial overrides or full `ColorPalette` customization.
- Rich markdown rendering with syntax highlighting and LaTeX math support.
- Multi-line text editor with scrolling and cursor positioning.
- Native interactive charts (Bar, Line, Pie, Scatter, Area, Stacked Bar, Gauge) with tooltips, hover, click events, and smooth curves.
- ASCII charts for terminal environments (Bar, Pie, Line, Gauge).
- Castella utilizes GPU via dependent libraries.
- Z-index support enables layered UIs with modals, popups, and overlays.
- **A2A Protocol support** - Connect to AI agents via Google's Agent-to-Agent protocol with `A2AClient`.
- **A2UI Protocol support** - Render agent-generated UIs with 17 standard components, tested with Google's sample agents.
- **AgentChat** - Build chat interfaces with AI agents in just 3 lines of code.

## Dependencies
- For desktop platforms, Castella is standing on existing excellent python bindings for window management library (GLFW or SDL2) and 2D graphics library (Skia).
- For web browsers, Castella is standing on awesome Pyodide/PyScript and CanvasKit (Wasm version of Skia).
- For terminals, Castella is standing on prompt_toolkit.

## Quick Start

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create a new project
uv init my-app && cd my-app

# Add Castella with GLFW backend
uv add "castella[glfw]"

# Run your app
uv run python your_app.py
```

For detailed installation instructions (SDL2, TUI, web), see the [Getting Started Guide](https://i2y.github.io/castella/getting-started/).

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
[Watch a very short demo video](docs/videos/demo.mp4)

## Agent Chat Example

Build a chat UI for AI agents in just 3 lines:

```python
from castella.agent import AgentChat

# Connect to an A2A-compatible agent
chat = AgentChat.from_a2a("http://localhost:8080")
chat.run()

# Or use a custom handler
chat = AgentChat(
    handler=lambda msg: f"You said: {msg}",
    title="My Bot",
)
chat.run()
```

You can see some other examples in [examples](examples) directory.

## Supported Platforms
Currently, Castella theoretically should support not-too-old versions of the following platforms.

- Windows 10/11
- Mac OS X
- Linux
- Web browsers
- Terminals

## License
MIT License

Copyright (c) 2022 Yasushi Itoh

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NON-INFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
