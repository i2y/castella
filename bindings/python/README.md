# castella-skia

Python bindings for castella-skia-core, providing GPU-accelerated 2D rendering for the Castella UI framework.

## Platforms

- **Desktop** (macOS, Linux, Windows) - OpenGL backend
- **iOS** - Metal backend
- **Android** - Vulkan backend (planned)

## Installation

```bash
pip install castella-skia
```

## Usage

```python
import castella_skia

# Create a surface from OpenGL context
surface = castella_skia.Surface.from_gl_context(800, 600)

# Create a painter
painter = castella_skia.SkiaPainter(surface)

# Set style and draw
style = castella_skia.Style(fill_color="#ff0000")
painter.style(style)
painter.fill_rect(10, 10, 100, 50)

# Flush to screen
painter.flush()
surface.flush_and_submit()
```

## License

MIT
