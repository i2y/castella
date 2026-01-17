# Castella
Castella is a pure Python cross-platform UI framework.

<img src="https://user-images.githubusercontent.com/6240399/174487936-8484be0e-b2b5-433c-9416-594c0fd57f3a.png" style="height: 1em;"></img> [Documentation Site](https://i2y.github.io/castella) <img src="https://user-images.githubusercontent.com/6240399/174487787-7099167f-a8ad-42e8-9362-c19c84dc81be.png" style="height: 1em;"></img> [Examples](examples) <img src="https://user-images.githubusercontent.com/6240399/174487787-7099167f-a8ad-42e8-9362-c19c84dc81be.png" style="height: 1em;"></img> [Slides](https://speakerdeck.com/i2y/a-cross-platform-pure-python-declarative-ui-framework)

## Goals
The primary final goal of Castella is to provide features for Python programmers easy to create a UI application for several OS platforms and web browsers in a single most same code as possible as. The second goal is to provide a UI framework that Python programmers can easily understand, modify, and extend as needed.

## Features
- The core part as a UI framework of Castella is written in only Python. It's not a wrapper for existing something written in other programing languages. "pure Python cross-platform UI framework" specifies things like the above.
- Castella allows pythonista to define UI declaratively in Python.
- Castella provides hot-reloading or hot-restarting on development.
- **Deep Pydantic v2 integration** - 70+ Pydantic models power the entire framework:
  - Core types: geometry (`Point`, `Size`, `Rect`), fonts, styles with immutable patterns
  - Chart data models with observable patterns and automatic UI updates
  - A2UI/A2A/MCP protocol types with validation and serialization
  - Theme system with design tokens (`ColorPalette`, `Typography`, `Spacing`)
  - DataTable: `from_pydantic()` extracts `Field.title`, `Field.description` (tooltips), and type annotations (column width inference)
- Comprehensive theme system with design tokens (colors, typography, spacing).
- Built-in themes: Tokyo Night (default), Cupertino, Material Design 3, and classic Castella themes.
- Dark/light mode with automatic system detection and runtime switching.
- Rounded corners and shadows support for modern UI aesthetics.
- Custom themes via `Theme.derive()` for partial overrides or full `ColorPalette` customization.
- Rich markdown rendering with syntax highlighting and LaTeX math support.
- Multi-line text editor with scrolling, cursor positioning, text selection, and clipboard support (copy/cut/paste).
- Native interactive charts (Bar, Line, Pie, Scatter, Area, Stacked Bar, Gauge, Heatmap) with tooltips, hover, click events, and smooth curves.
- **Heatmap support** - Both chart (`HeatmapChart`) and table (`HeatmapConfig`) variants with Viridis, Plasma, Inferno, Magma colormaps.
- ASCII charts for terminal environments (Bar, Pie, Line, Gauge).
- **Animation system** - Smooth property animations with `ValueTween`, `AnimatedState`, and easing functions.
- **Audio playback** - Cross-platform audio support with `AudioPlayer` widget and `AudioManager` API (MP3, OGG, WAV).
- **ProgressBar widget** - Animated progress indicator with customizable colors.
- **Widget lifecycle hooks** - `on_mount`/`on_unmount` for resource management (timers, subscriptions).
- **State preservation** - `ListState.map_cached()` and `Component.cache()` preserve widget state across view rebuilds.
- Castella utilizes GPU via dependent libraries.
- Z-index support enables layered UIs with modals, popups, and overlays.
- **A2A Protocol support** - Connect to AI agents via Google's Agent-to-Agent protocol with `A2AClient`.
- **A2UI Protocol support** - Render agent-generated UIs with 17 standard components, tested with Google's sample agents.
- **MCP (Model Context Protocol) support** - AI agents can introspect and control UIs programmatically via MCP.
- **AgentChat** - Build chat interfaces with AI agents in just 3 lines of code.
- **Agent Skills** - AI coding agents can learn Castella via 5 built-in skills.
- **Workflow Studio Samples** - Demo applications showcasing visual development environments for AI workflow frameworks.
- **Internationalization (i18n)** - Runtime locale switching with YAML translations, reactive `LocaleString`, and pluralization support.

## Workflow Studio Samples

Castella includes sample applications demonstrating visual development environments for popular AI workflow frameworks. These are located in `examples/` and serve as references for building your own workflow visualization tools.

| Sample | Framework | Features |
|--------|-----------|----------|
| `langgraph_studio/` | [LangGraph](https://github.com/langchain-ai/langgraph) | Graph visualization, step execution, state inspection |
| `llamaindex_studio/` | [LlamaIndex Workflows](https://docs.llamaindex.ai/en/stable/module_guides/workflow/) | Workflow visualization, breakpoints, execution history |
| `pydantic_graph_studio/` | [pydantic-graph](https://ai.pydantic.dev/pydantic-graph/) | Graph structure visualization, step-by-step execution |
| `edda_workflow_manager/` | [Edda](https://github.com/i2y/edda) + [LlamaIndex Workflows](https://docs.llamaindex.ai/en/stable/module_guides/workflow/) | Workflow management, execution history, live monitoring |

```bash
# Run LangGraph Studio sample
uv run python -m examples.langgraph_studio.main

# Run LlamaIndex Workflow Studio sample
uv run python examples/llamaindex_studio/main.py

# Run pydantic-graph Studio sample
uv run python -m examples.pydantic_graph_studio.main

# Run Edda Workflow Manager sample
uv run python examples/edda_workflow_manager/main.py --db sqlite+aiosqlite:///path/to/edda.db
```

## Agent Skills

Castella includes [Agent Skills](https://agentskills.io/) to help AI coding agents effectively use the framework. Located in `skills/`:

| Skill | Description |
|-------|-------------|
| `castella-core` | Core UI development - widgets, components, state, layouts, themes |
| `castella-a2ui` | A2UI JSON rendering - parse messages, data binding, progressive rendering |
| `castella-a2a` | A2A protocol - connect to agents, agent cards, streaming responses |
| `castella-mcp` | MCP integration - servers, resources, tools, semantic IDs |
| `castella-agent-ui` | Agent UI components - AgentChat, MultiAgentChat, AgentHub |

Each skill follows the [agentskills.io specification](https://agentskills.io/specification) with:
- `SKILL.md` - Main skill document with quick start and patterns
- `references/` - Detailed API documentation
- `scripts/` - Executable examples

## Dependencies
- For desktop platforms, Castella is standing on existing excellent python bindings for window management library (GLFW, SDL2, or SDL3) and 2D graphics library (Skia).
- For web browsers, Castella is standing on awesome Pyodide/PyScript and CanvasKit (Wasm version of Skia).
- For terminals, Castella is standing on prompt_toolkit.

## Quick Start

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create a new project
uv init my-app && cd my-app

# Add Castella (choose your backend)
uv add "castella[sdl3]"  # For easy setup (all platforms, no extra install)
uv add "castella[sdl]"   # For easy setup (SDL2 stable alternative)
uv add "castella[glfw]"  # For better performance

# Run your app
uv run python your_app.py
```

### Platform Recommendations

| Platform | Easy Setup | Better Performance |
|----------|------------|------------------|
| **Windows** | `castella[sdl3]` or `castella[sdl]` | `castella[glfw]` (requires [GLFW install](https://www.glfw.org/download.html)) |
| **Linux** | `castella[sdl3]` or `castella[sdl]` | `castella[glfw]` (requires `apt install libglfw3-dev`) |
| **macOS** | All backends work without extra install | `castella[glfw]` |

### IME Support (Japanese/Chinese/Korean Input)

All backends support IME on all platforms. On macOS, GLFW provides better IME integration via native Cocoa APIs.

For detailed installation instructions (TUI, web), see the [Getting Started Guide](https://i2y.github.io/castella/getting-started/).

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

## Animation Example

Animate values with easing functions:

```python
from castella import App, Column, Component, Button, ProgressBar, ProgressBarState
from castella.animation import ValueTween, AnimationScheduler, EasingFunction
from castella.frame import Frame


class AnimationDemo(Component):
    def __init__(self):
        super().__init__()
        self._progress = ProgressBarState(0, min_val=0, max_val=100)
        self._progress.attach(self)

    def view(self):
        return Column(
            ProgressBar(self._progress).fixed_height(24),
            Button("Animate").on_click(self._animate),
        )

    def _animate(self, _):
        self._progress.set(0)
        AnimationScheduler.get().add(
            ValueTween(
                from_value=0,
                to_value=100,
                duration_ms=1000,
                easing=EasingFunction.EASE_OUT_CUBIC,
                on_update=lambda v: self._progress.set(v),
            )
        )


App(Frame("Animation", 400, 200), AnimationDemo()).run()
```

## Audio Player Example

Play audio files with the built-in `AudioPlayer` widget:

```python
from castella import App
from castella.audio import AudioPlayer
from castella.frame import Frame

# Simple audio player with full controls
player = AudioPlayer("music.mp3")
player.on_ended(lambda: print("Playback finished!"))

App(Frame("Audio Player", 500, 200), player).run()
```

Or use the low-level `AudioManager` API for custom audio handling:

```python
from castella.audio import AudioManager

manager = AudioManager.get()
handle, state = manager.load("sound.wav")

manager.play(handle)
manager.set_volume(handle, 0.5)  # 50% volume
manager.seek(handle, 5000)      # Seek to 5 seconds
```

Installation: `uv add "castella[audio]"` (or included with `castella[sdl]`/`castella[sdl3]`)

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

## A2UI Example

Render AI-generated UIs from [A2UI](https://a2ui.org/) compatible agents:

```python
from castella import App
from castella.a2ui import A2UIClient, A2UIComponent
from castella.frame import Frame

# Connect to an A2UI-enabled agent
client = A2UIClient("http://localhost:10002")

# Send a message and get UI
surface = client.send("Find me restaurants in Tokyo")

# Render in Castella
if surface:
    App(Frame("A2UI Demo", 800, 600), A2UIComponent(surface)).run()
```

## MCP Example

Enable AI agents to control your UI via [MCP (Model Context Protocol)](https://modelcontextprotocol.github.io/):

```python
from castella import App, Column, Button, Input, Text
from castella.frame import Frame
from castella.mcp import CastellaMCPServer

def build_ui():
    return Column(
        Text("Hello MCP!"),
        Input("").semantic_id("name-input"),
        Button("Submit").semantic_id("submit-btn"),
    )

app = App(Frame("MCP Demo", 800, 600), build_ui())
mcp = CastellaMCPServer(app, name="my-app")

# Run SSE server for HTTP clients
mcp.run_sse_in_background(host="localhost", port=8765)

app.run()
```

AI agents can then introspect the UI tree and control widgets:
```python
# Client example (AI agent)
call_tool("type_text", element_id="name-input", text="Hello")
call_tool("click", element_id="submit-btn")
```

## Pydantic Integration Example

Leverage Pydantic's `Field` metadata for automatic DataTable configuration:

```python
from pydantic import BaseModel, Field
from castella import App, DataTable, DataTableState
from castella.frame import Frame


class Employee(BaseModel):
    id: int = Field(..., title="ID", description="Unique identifier")
    name: str = Field(..., title="Name", description="Full name")
    salary: float = Field(..., title="Salary", description="Annual salary")


employees = [
    Employee(id=1, name="Alice", salary=75000.0),
    Employee(id=2, name="Bob", salary=85000.0),
]

# Field.title → column name, Field.description → tooltip, type → column width
state = DataTableState.from_pydantic(employees)

# Fluent API for per-table styling
table = (
    DataTable(state)
    .header_bg_color("#3d5a80")
    .header_text_color("#ffffff")
    .selected_bg_color("#ee6c4d")
)

App(Frame("Employee Table", 600, 400), table).run()
```

You can see some other examples in [examples](examples) directory.

## I18n Example

Add multi-language support to your app:

```python
from castella import App, Button, Column, Component, Text
from castella.frame import Frame
from castella.i18n import I18nManager, load_yaml_catalog

# Load translations
manager = I18nManager()
manager.load_catalog("en", load_yaml_catalog("locales/en.yaml"))
manager.load_catalog("ja", load_yaml_catalog("locales/ja.yaml"))
manager.set_locale("en")


class MyApp(Component):
    def view(self):
        return Column(
            Text(manager.t("greeting")),
            Button(manager.t("button.save")).on_click(self._save),
            Button("日本語").on_click(lambda _: manager.set_locale("ja")),
            Button("English").on_click(lambda _: manager.set_locale("en")),
        )

    def _save(self, _):
        print("Saved!")


App(Frame("I18n Demo", 400, 300), MyApp()).run()
```

```yaml
# locales/en.yaml
locale: en
greeting: "Hello, World!"
button:
  save: "Save"
```

```yaml
# locales/ja.yaml
locale: ja
greeting: "こんにちは！"
button:
  save: "保存"
```

## Supported Platforms
Currently, Castella supports the following platforms:

- Windows 10/11
- Mac OS X
- Linux
- **iOS** (Simulator and Device)
- Web browsers
- Terminals

### iOS Support

Castella runs on iOS with full widget support including charts, data tables, and keyboard/IME input. Uses the castella-skia Metal backend for GPU-accelerated rendering.

```bash
# Build and run iOS demo (auto-downloads dependencies)
AUTO_DOWNLOAD_DEPS=1 ./tools/build_ios.sh examples/ios_all_widgets_demo
```

**Building iOS dependencies locally:**

```bash
# Build pydantic-core for iOS
./tools/build_pydantic_core_ios.sh

# Build castella-skia for iOS
cd bindings/python && ./build_ios.sh

# Then build iOS app
./tools/build_ios.sh examples/ios_all_widgets_demo
```

See the [iOS Documentation](https://i2y.github.io/castella/ios/) for details.

## castella-skia (Rust Backend)

Castella uses a Rust-based Skia backend for GPU-accelerated rendering across all platforms:

```
castella/
├── castella-skia-core/    # Pure Rust core library (crates.io)
└── bindings/
    ├── python/            # Python bindings (PyPI: castella-skia)
    ├── ruby/              # Ruby bindings (planned)
    └── node/              # Node.js bindings (planned)
```

The architecture separates the core rendering logic from language-specific bindings, enabling multi-language support.

```bash
# Build Python bindings
cd bindings/python && maturin develop --release

# Run Castella app
uv run python examples/counter.py
```

## License
MIT License

Copyright (c) 2022 Yasushi Itoh

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NON-INFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
