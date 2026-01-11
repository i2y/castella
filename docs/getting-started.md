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

Castella for Desktop depends on either GLFW or SDL2. We recommend GLFW as it currently offers better performance.

### Quick Start with uv

```bash
# Create a new project
uv init my-castella-app
cd my-castella-app

# Add Castella with GLFW backend (recommended)
uv add "castella[glfw]"

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

#### Install from PyPI

```bash
uv add "castella[sdl]"
```

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

#### Additional SDL2 Installation (if needed)

You can download precompiled SDL2 from [SDL2 download page](https://www.libsdl.org/download-2.0.php).

After downloading, set the `PYSDL2_DLL_PATH` environment variable to the folder containing the SDL2 library.

For more details, see [PySDL2 integration guide](https://pysdl2.readthedocs.io/en/rel_0_9_7/integration.html).

### Alternative: Using pip

If you prefer traditional pip:

```bash
# With GLFW
pip install castella[glfw]

# With SDL2
pip install castella[sdl]

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

#### 2. Clone Castella repository

```bash
git clone https://github.com/i2y/castella.git
```

#### 3. Create your app files

Create `counter.html`:

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <title>Counter</title>
    <link rel="stylesheet" href="https://pyscript.net/releases/2025.11.2/core.css">
    <script type="module" src="https://pyscript.net/releases/2025.11.2/core.js"></script>
    <script type="text/javascript" src="https://unpkg.com/canvaskit-wasm@0.33.0/bin/canvaskit.js"></script>
</head>
<body>
<script type="py" src="counter.py" config="pyscript.toml"></script>
</body>
</html>
```

Create `pyscript.toml`:

```toml
packages = [ "./castella-0.11.1-py3-none-any.whl" ]
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

#### 4. Serve your app

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
