## Prerequisites

Castella requires Python >= `3.11`.

We recommend using [uv](https://docs.astral.sh/uv/) for package management. uv is a fast Python package manager that simplifies dependency management.

## Installing uv

If you don't have uv installed:

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

## For Desktop

Castella for Desktop supports three backends: GLFW, SDL2, and SDL3. The recommended choice depends on your platform:

| Platform | Easy Setup | Better Performance |
|----------|------------|------------------|
| **Windows** | `castella[sdl3]` or `castella[sdl]` | `castella[glfw]` (requires [GLFW install](https://www.glfw.org/download.html)) |
| **Linux** | `castella[sdl3]` or `castella[sdl]` | `castella[glfw]` (requires `apt install libglfw3-dev`) |
| **macOS** | All backends work without extra install | `castella[glfw]` |

All backends support IME (Japanese/Chinese/Korean input) on all platforms. On macOS, GLFW provides better IME integration via native Cocoa APIs.

### Quick Start with uv

```bash
# Create a new project
uv init my-castella-app
cd my-castella-app

# Add Castella (choose your backend)
uv add "castella[sdl3]"  # For easy setup (all platforms, no extra install)
uv add "castella[sdl]"   # For easy setup (SDL2 stable alternative)
uv add "castella[glfw]"  # For better performance

# Run your app
uv run python your_app.py
```

### Using GLFW Backend

#### Install from PyPI

```bash
uv add "castella[glfw]"
```

#### Install from GitHub (latest source)

```bash
uv add "castella[glfw] @ git+https://github.com/i2y/castella.git"
```

#### Development from Source

```bash
git clone https://github.com/i2y/castella.git
cd castella
uv sync --extra glfw
uv run python examples/counter.py
```

#### Additional GLFW Installation (if needed)

The GLFW shared library is typically installed automatically. If you encounter GLFW-related errors, you can install it manually:

**macOS:**
```bash
brew install glfw3
```

**Linux (Debian/Ubuntu):**
```bash
sudo apt-get install -y libglfw3-dev
```

**Linux (RHEL/CentOS):**
```bash
sudo yum install -y libglfw3-dev
```

**Windows:**
Download from [GLFW download page](https://www.glfw.org/download.html).

### Using SDL2 Backend

The SDL2 backend includes all necessary binaries via the `pysdl2-dll` package. **No additional installation is required** on Windows, Linux, or macOS.

#### Install from PyPI

```bash
uv add "castella[sdl]"
```

This automatically installs:

- `pysdl2-dll` - Pre-built SDL2 binaries for Windows, Linux (x86_64, ARM64), and macOS
- `castella-skia` - Pre-built Skia rendering engine for all platforms
- `PySDL2` - Python bindings for SDL2
- `PyOpenGL` - OpenGL bindings

#### Install from GitHub (latest source)

```bash
uv add "castella[sdl] @ git+https://github.com/i2y/castella.git"
```

#### Development from Source

```bash
git clone https://github.com/i2y/castella.git
cd castella
uv sync --extra sdl
uv run python examples/counter.py
```

#### Using Custom SDL2 (Advanced)

By default, the bundled SDL2 from `pysdl2-dll` is used automatically. If you need to use a custom SDL2 installation:

```bash
# Use system SDL2 instead of bundled
export PYSDL2_DLL_PATH=system

# Or specify a custom path
export PYSDL2_DLL_PATH=/path/to/sdl2/lib
```

For more details, see [PySDL2 integration guide](https://pysdl2.readthedocs.io/en/rel_0_9_7/integration.html).

### Using SDL3 Backend

The SDL3 backend uses [PySDL3](https://github.com/Aermoss/PySDL3), the official Python bindings for SDL3. **No additional installation is required** - SDL3 binaries are automatically downloaded on first run.

#### Install from PyPI

```bash
uv add "castella[sdl3]"
```

This automatically installs:

- `PySDL3` - Python bindings for SDL3 (auto-downloads SDL3 binaries)
- `castella-skia` - Pre-built Skia rendering engine for all platforms
- `PyOpenGL` - OpenGL bindings

#### Install from GitHub (latest source)

```bash
uv add "castella[sdl3] @ git+https://github.com/i2y/castella.git"
```

#### Development from Source

```bash
git clone https://github.com/i2y/castella.git
cd castella
uv sync --extra sdl3
uv run python examples/counter.py
```

### Alternative: Using pip

If you prefer traditional pip:

```bash
# With GLFW
pip install castella[glfw]

# With SDL2
pip install castella[sdl]

# With SDL3
pip install castella[sdl3]

# From GitHub
pip install "git+https://github.com/i2y/castella.git#egg=castella[glfw]"
```

### Verify Installation

If installation was successful, the examples should work:

```bash
# With uv
uv run python examples/hello_world.py

# With pip
python examples/hello_world.py
```

See the [examples folder](https://github.com/i2y/castella/tree/main/examples) for more sample applications.


## For Web Browsers

Here we explain how to use Castella in a PyScript app.

For more information on PyScript, see the [official documentation](https://pyscript.net/).

To use Castella on an HTML page:

- Load the PyScript JS file and CanvasKit JS file
- Specify Castella modules in the PyScript config file (`pyscript.toml`)
- Serve the HTML page with any web server

### Example Setup

#### 1. Create your app folder

```bash
mkdir counter
cd counter
```

#### 2. Create your app files

Create `counter.html`:

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <title>Counter</title>
    <link rel="stylesheet" href="https://pyscript.net/releases/2025.11.2/core.css">
    <script type="text/javascript" src="https://unpkg.com/canvaskit-wasm@0.39.1/bin/canvaskit.js"></script>
    <script type="text/javascript">
        const loadFont = fetch('https://fonts.gstatic.com/s/roboto/v30/KFOmCnqEu92Fr1Mu4mxP.ttf')
            .then((response) => response.arrayBuffer());

        const ckLoaded = CanvasKitInit();
        Promise.all([ckLoaded, loadFont]).then(([CanvasKit, robotoData]) => {
            window.CK = CanvasKit;
            window.fontMgr = CanvasKit.FontMgr.FromData([robotoData]);
            window.typeface = CanvasKit.Typeface.MakeFreeTypeFaceFromData(robotoData);
            // Load PyScript after CanvasKit is ready
            const script = document.createElement('script');
            script.type = 'module';
            script.src = 'https://pyscript.net/releases/2025.11.2/core.js';
            document.head.appendChild(script);
        });
    </script>
</head>
<body>
<script type="py" src="counter.py" config="pyscript.toml"></script>
</body>
</html>
```

Create `pyscript.toml`:

```toml
packages = [ "pydantic", "castella" ]
```

Create `counter.py`:

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


if __name__ == "__main__":
    App(Frame("Counter", 800, 600), Counter()).run()
```

#### 3. Serve your app

```bash
# With uv
uv run python -m http.server 3000

# With Python directly
python -m http.server 3000
```

Open [http://127.0.0.1:3000/counter.html](http://127.0.0.1:3000/counter.html) in your browser.

<style type="text/css">
    div.demo {
        margin: 8px;
        border: solid 1px #ccc;
        resize: both;
        overflow: hidden;
        width: 300px;
        height: 300px;
    }
</style>

<div class="demo">
    <iframe width="100%" height="100%" src="../examples/counter.html"></iframe>
</div>

The above counter app is embedded in an iframe.

## For Terminals

### Install with uv

```bash
uv add "castella[tui]"
```

### Alternative: Using pip

```bash
pip install castella[tui]
```

### Running in Terminal Mode

If you have other platform-specific packages installed, set the environment variable:

```bash
# macOS / Linux
CASTELLA_IS_TERMINAL_MODE=true uv run python your_script.py

# Windows (PowerShell)
$env:CASTELLA_IS_TERMINAL_MODE="true"; uv run python your_script.py
```

If you only have the TUI package installed, terminal mode is enabled automatically.

## Optional Features

Castella provides several optional extras for additional functionality:

### AI Agent Support

For A2A (Agent-to-Agent) and A2UI (Agent-to-User Interface) protocols:

```bash
uv add "castella[agent,glfw]"
```

See the [Agent UI documentation](agent.md) for details.

### MCP (Model Context Protocol) Support

For AI agents to introspect and control UIs programmatically:

```bash
uv add "castella[mcp,glfw]"
```

See the [MCP documentation](mcp.md) for details.

### Combined Installation

You can combine multiple extras:

```bash
# Desktop with agent and MCP support
uv add "castella[glfw,agent,mcp]"
```
