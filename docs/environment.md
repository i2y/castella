# Environment Variables

Castella can be configured using environment variables for platform selection, appearance, and locale settings.

## Platform Selection

### CASTELLA_FRAME

Select the desktop frame backend.

| Value | Description |
|-------|-------------|
| `glfw` | Use GLFW backend |
| `sdl` | Use SDL2 backend |
| `sdl3` | Use SDL3 backend |
| `tui` | Use terminal UI mode |
| `auto` | Auto-detect (default): GLFW → SDL3 → SDL2 → TUI |

```bash
# Use SDL3 backend
CASTELLA_FRAME=sdl3 uv run python examples/counter.py

# Use GLFW backend
CASTELLA_FRAME=glfw uv run python examples/counter.py
```

### CASTELLA_IS_TERMINAL_MODE

Force terminal UI mode (using prompt-toolkit) instead of graphical mode. (Deprecated: use `CASTELLA_FRAME=tui` instead)

| Value | Description |
|-------|-------------|
| `true` | Force terminal mode |
| (unset) | Auto-detect based on environment |

```bash
CASTELLA_IS_TERMINAL_MODE=true uv run python examples/counter.py
```

## Appearance

### CASTELLA_DARK_MODE

Force dark or light mode, overriding system detection.

| Value | Description |
|-------|-------------|
| `true` | Force dark mode |
| `false` | Force light mode |
| (unset) | Auto-detect from system (default) |

```bash
# Force dark mode
CASTELLA_DARK_MODE=true uv run python examples/counter.py

# Force light mode
CASTELLA_DARK_MODE=false uv run python examples/counter.py
```

### CASTELLA_FONT_SIZE

Override the default base font size.

| Value | Description |
|-------|-------------|
| Integer | Font size in points (e.g., `14`, `16`) |
| (unset) | Use theme default |

```bash
CASTELLA_FONT_SIZE=16 uv run python examples/counter.py
```

## Internationalization

### CASTELLA_LOCALE

Force a specific locale, overriding system detection.

| Value | Description |
|-------|-------------|
| `en` | English |
| `ja` | Japanese |
| `zh` | Chinese |
| `fr` | French |
| `de` | German |
| `ru` | Russian |
| (unset) | Auto-detect from system |

```bash
CASTELLA_LOCALE=ja uv run python examples/i18n_demo.py
```

## Platform-Specific

### PYSDL2_DLL_PATH (Windows)

Path to SDL2 DLL files on Windows when using the SDL2 backend.

```bash
# Windows PowerShell
$env:PYSDL2_DLL_PATH = "C:\SDL2\lib\x64"
python examples/counter.py
```

### CASTELLA_IOS_DEPS

Base directory for iOS pre-built dependencies (pydantic-core, castella-skia).

| Value | Description |
|-------|-------------|
| Path | Directory containing iOS dependencies |
| (unset) | Defaults to `~/castella-ios-deps` |

```bash
CASTELLA_IOS_DEPS=/path/to/deps ./tools/build_ios.sh examples/ios_test_app
```

## Examples

### Development Setup

```bash
# Dark mode with larger fonts
export CASTELLA_DARK_MODE=true
export CASTELLA_FONT_SIZE=16
uv run python examples/counter.py
```

### Testing Different Backends

```bash
# SDL3 backend
CASTELLA_FRAME=sdl3 uv run python examples/counter.py

# SDL2 backend
CASTELLA_FRAME=sdl uv run python examples/counter.py

# GLFW backend
CASTELLA_FRAME=glfw uv run python examples/counter.py

# Terminal mode
CASTELLA_FRAME=tui uv run python examples/counter.py
```

### Internationalization Testing

```bash
# Test Japanese locale
CASTELLA_LOCALE=ja uv run python examples/i18n_demo.py

# Test with Japanese locale and dark mode
CASTELLA_LOCALE=ja CASTELLA_DARK_MODE=true uv run python examples/i18n_demo.py
```

## See Also

- [castella-skia](castella-skia.md) - Rust Skia backend details
- [Internationalization](i18n.md) - I18n system documentation
- [iOS](ios.md) - iOS platform configuration
