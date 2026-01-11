"""Type stubs for castella-skia."""

from typing import Optional, Tuple, List

__version__: str

class Point:
    x: float
    y: float
    def __init__(self, x: float = 0.0, y: float = 0.0) -> None: ...

class Size:
    width: float
    height: float
    def __init__(self, width: float = 0.0, height: float = 0.0) -> None: ...

class Rect:
    x: float
    y: float
    width: float
    height: float
    def __init__(
        self,
        x: float = 0.0,
        y: float = 0.0,
        width: float = 0.0,
        height: float = 0.0,
    ) -> None: ...

class Circle:
    cx: float
    cy: float
    radius: float
    def __init__(
        self, cx: float = 0.0, cy: float = 0.0, radius: float = 0.0
    ) -> None: ...

class FontMetrics:
    ascent: float
    descent: float
    leading: float
    height: float
    def __init__(
        self, ascent: float = 0.0, descent: float = 0.0, leading: float = 0.0
    ) -> None: ...

class Style:
    fill_color: Optional[str]
    stroke_color: Optional[str]
    stroke_width: float
    font_family: Optional[str]
    font_size: float
    border_radius: float
    def __init__(
        self,
        fill_color: Optional[str] = None,
        stroke_color: Optional[str] = None,
        stroke_width: float = 1.0,
        font_family: Optional[str] = None,
        font_size: float = 14.0,
        border_radius: float = 0.0,
    ) -> None: ...

class Surface:
    @property
    def width(self) -> int: ...
    @property
    def height(self) -> int: ...
    @staticmethod
    def new_raster(width: int, height: int) -> Surface: ...
    @staticmethod
    def from_gl_context(
        width: int,
        height: int,
        sample_count: int = 0,
        stencil_bits: int = 0,
        framebuffer_id: int = 0,
    ) -> Surface: ...
    @staticmethod
    def from_metal(
        device_ptr: int, queue_ptr: int, width: int, height: int
    ) -> Surface: ...
    def resize(
        self,
        width: int,
        height: int,
        sample_count: int = 0,
        stencil_bits: int = 0,
        framebuffer_id: int = 0,
    ) -> None: ...
    def resize_metal(self, width: int, height: int) -> None: ...
    def flush_and_submit(self) -> None: ...
    def save_png(self, path: str) -> None: ...
    def get_rgba_data(self) -> bytes: ...
    def get_png_data(self) -> bytes: ...

class SkiaPainter:
    def __init__(self, surface: Surface) -> None: ...
    def clear_all(self) -> None: ...
    def fill_rect(self, x: float, y: float, width: float, height: float) -> None: ...
    def stroke_rect(self, x: float, y: float, width: float, height: float) -> None: ...
    def translate(self, x: float, y: float) -> None: ...
    def scale(self, sx: float, sy: float) -> None: ...
    def clip(self, x: float, y: float, width: float, height: float) -> None: ...
    def fill_text(
        self, text: str, x: float, y: float, max_width: Optional[float] = None
    ) -> None: ...
    def stroke_text(
        self, text: str, x: float, y: float, max_width: Optional[float] = None
    ) -> None: ...
    def measure_text(self, text: str) -> float: ...
    def get_font_metrics(self) -> FontMetrics: ...
    def save(self) -> None: ...
    def restore(self) -> None: ...
    def style(self, style: Style) -> None: ...
    def flush(self) -> None: ...
    def fill_circle(self, cx: float, cy: float, radius: float) -> None: ...
    def stroke_circle(self, cx: float, cy: float, radius: float) -> None: ...
    def draw_image(
        self,
        file_path: str,
        x: float,
        y: float,
        width: float,
        height: float,
        use_cache: bool = True,
    ) -> None: ...
    def measure_image(
        self, file_path: str, use_cache: bool = True
    ) -> Tuple[int, int]: ...

def clear_image_cache() -> None: ...
def debug_font_for_char(ch: str, primary_family: str) -> Tuple[str, int, bool, str]: ...
def debug_text_segments(text: str, primary_family: str) -> List[Tuple[str, str]]: ...
