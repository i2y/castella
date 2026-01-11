# castella-skia - Unified Rust Skia Backend

castella-skia is a Rust-based Skia rendering backend that provides GPU-accelerated graphics for Castella on Desktop and iOS platforms.

## Overview

- **Single codebase** for Desktop (OpenGL) and iOS (Metal)
- **High performance** GPU-accelerated rendering via skia-safe
- **Automatic font fallback** for emoji, CJK, and mixed scripts using Skia Paragraph API
- **Thread-local caching** for FontCollection and DirectContext

## Why castella-skia?

| Benefit | Description |
|---------|-------------|
| Unified rendering | Same Skia version and behavior across platforms |
| Simplified dependencies | No need for skia-python on Desktop |
| iOS support | Metal backend enables native iOS rendering |
| Full control | Owned crate with version management |
| Maintainability | Bug fixes apply to all platforms |

## Platform Backends

| Platform | Graphics API | Notes |
|----------|--------------|-------|
| Desktop macOS | OpenGL 3.2 Core | Core Profile for shader compatibility |
| Desktop Linux | OpenGL / Vulkan | Environment dependent |
| Desktop Windows | OpenGL / Vulkan | Environment dependent |
| iOS | Metal | Native iOS GPU API |
| Android | Vulkan | Planned |

## Usage

### Desktop

castella-skia is the rendering backend for Desktop (GLFW/SDL). No configuration needed:

```bash
uv run python examples/counter.py
```

### iOS

iOS always uses castella-skia with the Metal backend. No configuration needed.

## Building from Source

### Prerequisites

- Rust toolchain (stable)
- Python 3.10+
- maturin (`pip install maturin`)

### Development Build

```bash
cd bindings/python
source ../../.venv/bin/activate  # If using venv
maturin develop --release
```

### iOS Cross-Compilation

```bash
# Add iOS targets
rustup target add aarch64-apple-ios-sim  # M1/M2 Simulator
rustup target add aarch64-apple-ios      # Physical device

# Build for iOS Simulator
cd bindings/python
./build_ios.sh
```

## Architecture

```
castella/
├── Cargo.toml                    # Workspace configuration
├── castella-skia-core/           # Pure Rust core library
│   ├── Cargo.toml
│   └── src/
│       ├── lib.rs                # Public API
│       ├── painter.rs            # SkiaPainter implementation
│       ├── surface.rs            # GPU surface management
│       ├── font.rs               # Font management and fallback
│       ├── image.rs              # Image loading and caching
│       └── types.rs              # Type definitions
└── bindings/python/              # Python bindings (PyO3)
    ├── Cargo.toml
    ├── pyproject.toml
    ├── src/lib.rs                # PyO3 wrapper
    └── python/castella_skia/     # Python package
```

### Key Components

#### Surface

Manages GPU context and rendering surface:

```python
from castella_skia import Surface

# Desktop (OpenGL)
surface = Surface(width, height)

# iOS (Metal)
surface = Surface.from_metal(device, queue, width, height)
```

#### SkiaPainter

Implements BasePainter protocol:

```python
from castella_skia import Surface, SkiaPainter

surface = Surface(800, 600)
painter = SkiaPainter(surface)

# Drawing operations
painter.fill_rect(0, 0, 100, 50, style)
painter.fill_text("Hello", 10, 30, style)
painter.fill_circle(50, 50, 25, style)
```

### Supported Operations

| Method | Description |
|--------|-------------|
| `fill_rect` | Fill a rectangle |
| `stroke_rect` | Stroke a rectangle outline |
| `fill_circle` | Fill a circle |
| `stroke_circle` | Stroke a circle outline |
| `fill_rounded_rect` | Fill a rounded rectangle |
| `stroke_rounded_rect` | Stroke a rounded rectangle outline |
| `fill_text` | Draw filled text |
| `measure_text` | Measure text dimensions |
| `clip` | Set clipping rectangle |
| `translate` | Translate coordinate system |
| `save` / `restore` | Save/restore canvas state |
| `draw_image` | Draw an image |

## Font Fallback

castella-skia uses Skia's Paragraph API for automatic font fallback:

- **Emoji**: Automatically uses system emoji font
- **CJK**: Falls back to appropriate CJK fonts (Hiragino, PingFang, etc.)
- **Mixed scripts**: Seamlessly handles mixed language text

```python
# This "just works" - emoji and Japanese rendered correctly
painter.fill_text("Hello 👋 こんにちは", 10, 30, style)
```

## Integration with Castella

castella-skia integrates via `rust_skia_painter.py`:

```python
# castella/rust_skia_painter.py
from castella_skia import Surface, SkiaPainter

class RustSkiaPainter(BasePainter):
    def __init__(self, frame):
        self._surface = Surface(frame.width, frame.height)
        self._painter = SkiaPainter(self._surface)

    def fill_rect(self, x, y, w, h, style):
        self._painter.fill_rect(x, y, w, h, self._convert_style(style))
```

## Performance

### Caching

- **FontCollection**: Thread-local caching avoids recreation
- **DirectContext**: GPU context cached per thread
- **Typeface**: Font faces cached by family name

### Best Practices

1. Reuse Surface objects when possible
2. Batch drawing operations
3. Use `save()`/`restore()` instead of recreating painters

## Troubleshooting

### OpenGL Context Issues (Desktop)

If you see OpenGL errors on macOS:

```bash
# Ensure OpenGL 3.2 Core Profile is available
# Check system_profiler for GPU capabilities
system_profiler SPDisplaysDataType
```

### Metal Not Available (iOS Simulator)

Ensure you're using an M1/M2 Mac or a compatible Simulator version.

### Font Rendering Issues

If fonts appear incorrect:

1. Check that system fonts are available
2. Verify the font family name is correct
3. Test with a known-good font like "Arial" or "Helvetica"

## See Also

- [iOS Documentation](ios.md) - iOS-specific usage
- [Environment Variables](environment.md) - Configuration options
