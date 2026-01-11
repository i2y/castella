"""castella-skia - Unified Skia rendering backend for Castella UI framework.

This package provides GPU-accelerated 2D rendering for Castella across all platforms:
- Desktop (macOS, Linux, Windows) via OpenGL
- iOS via Metal
- Android via Vulkan (TODO)
"""

from .castella_skia import (
    # Types
    Point,
    Size,
    Rect,
    Circle,
    Shadow,
    FontMetrics,
    Style,
    # Core classes
    Surface,
    SkiaPainter,
    # Functions
    clear_image_cache,
    debug_font_for_char,
    debug_text_segments,
    # Version
    __version__,
)

__all__ = [
    # Types
    "Point",
    "Size",
    "Rect",
    "Circle",
    "Shadow",
    "FontMetrics",
    "Style",
    # Core classes
    "Surface",
    "SkiaPainter",
    # Functions
    "clear_image_cache",
    "debug_font_for_char",
    "debug_text_segments",
    # Version
    "__version__",
]
