from typing import TYPE_CHECKING, Optional, List, Dict, TypeAlias
from math import ceil

from castella.core import Circle, FontMetrics, Point, Rect, Size, Style

if TYPE_CHECKING:
    import numpy as np
from castella.font import FontSlant, FontWeight


FONT_SIZE = 12
LINE_HEIGHT = FONT_SIZE

# TypeAlias
PTStyle: TypeAlias = str
Text: TypeAlias = str
Cell: TypeAlias = tuple[PTStyle, Text]
Row: TypeAlias = List[Cell]


class Canvas:
    def __init__(self, width: int, height: int):
        self._width = width
        self._height = height
        self._rows = [[("", " ") for _ in range(width)] for _ in range(height)]

    def draw_rect(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        style: str,
        clip_rect: Optional[Rect] = None,
    ):
        x0 = x
        y0 = y
        x1 = x + width
        y1 = y + height

        if clip_rect is not None:
            x0 = max(x0, int(clip_rect.origin.x))
            y0 = max(y0, int(clip_rect.origin.y))
            x1 = min(x1, int(clip_rect.origin.x + clip_rect.size.width))
            y1 = min(y1, int(clip_rect.origin.y + clip_rect.size.height))

        for i in range(max(0, y0), min(y1, self._height)):
            for j in range(max(0, x0), min(x1, self._width)):
                self._rows[i][j] = (style, " ")  # self._rows[i][j][1])

    def draw_text(
        self,
        x: int,
        y: int,
        text: str,
        style: str,
        clip_rect: Optional[Rect] = None,
    ):
        if y < 0 or y >= self._height:
            return

        if (
            clip_rect
            and not clip_rect.origin.y <= y < clip_rect.origin.y + clip_rect.size.height
        ):
            return

        for i, char in enumerate(text):
            j = x + i
            if j < 0 or j >= self._width:
                continue

            if (
                clip_rect
                and not clip_rect.origin.x
                <= j
                < clip_rect.origin.x + clip_rect.size.width
            ):
                continue

            # The background colour is specified in the form "bg:colour", so search with "bg:" and use that colour if found.
            orig_style, _ = self._rows[y][j]
            orig_bg_color = (
                orig_style.split("bg:")[1].split()[0] if "bg:" in orig_style else None
            )
            if orig_bg_color is None:
                new_style = style
            else:
                new_style = f"bg:{orig_bg_color} {style}"

            self._rows[y][j] = (new_style, char)

    def draw_caret(self, x: int, y: int, height: int = 1):
        if 0 <= x < self._width:
            for i in range(0, height + 1):
                if y + i <= self._height:
                    self._rows[y + i][x] = ("reverse", self._rows[y + i][x][1])

    def draw_stroke_rect(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        style: str,
        clip_rect: Optional[Rect] = None,
    ):
        # top and bottom lines
        for j in range(x + 1, x + width - 1):
            for i in [y, y + height - 1]:
                if 0 <= i < self._height and 0 <= j < self._width:
                    if clip_rect and not clip_rect.contain(Point(x=j, y=i)):
                        continue
                    self._rows[i][j] = (style, "─")

        # left and right lines
        for i in range(y + 1, y + height - 1):
            for j in [x, x + width - 1]:
                if 0 <= i < self._height and 0 <= j < self._width:
                    if clip_rect and not clip_rect.contain(Point(x=j, y=i)):
                        continue
                    self._rows[i][j] = (style, "│")

        # corners
        corners = [
            (x, y, "┌"),  # 左上
            (x + width - 1, y, "┐"),  # 右上
            (x, y + height - 1, "└"),  # 左下
            (x + width - 1, y + height - 1, "┘"),  # 右下
        ]
        for j, i, char in corners:
            if 0 <= i < self._height and 0 <= j < self._width:
                if clip_rect and not clip_rect.contain(Point(x=j, y=i)):
                    continue
                self._rows[i][j] = (style, char)

    def render(self) -> List[Row]:
        return self._rows


def to_pt_rect(rect: Optional[Rect]) -> Optional[Rect]:
    if rect is not None:
        return Rect(
            origin=Point(
                x=ceil(rect.origin.x / FONT_SIZE), y=ceil(rect.origin.y / LINE_HEIGHT)
            ),
            size=Size(
                width=ceil(rect.size.width / FONT_SIZE),
                height=ceil(rect.size.height / LINE_HEIGHT),
            ),
        )
    else:
        return None


class PTPainter:
    def __init__(self, canvas: Canvas):
        self.canvas = canvas
        self.current_style = Style()
        self.translation = Point(x=0, y=0)
        self.clip_rect: Optional[Rect] = None
        self.state_stack: List[Dict] = []

    def clear_all(self, color: Optional[str] = None) -> None:
        size = self.canvas._width, self.canvas._height
        self.canvas = Canvas(*size)

    def fill_circle(self, circle: Circle) -> None:
        raise NotImplementedError

    def stroke_circle(self, circle: Circle) -> None:
        raise NotImplementedError

    def get_font_metrics(self) -> FontMetrics:
        return FontMetrics(cap_height=LINE_HEIGHT)

    def fill_rect(self, rect: Rect) -> None:
        rect = Rect(origin=rect.origin + self.translation, size=rect.size)
        x = div2(rect.origin.x, FONT_SIZE)
        y = ceil(rect.origin.y / LINE_HEIGHT)
        width = ceil(rect.size.width / FONT_SIZE)
        height = ceil(rect.size.height / LINE_HEIGHT)
        pt_style = convert_castella_style_to_pt_style_for_rect(self.current_style)
        self.canvas.draw_rect(x, y, width, height, pt_style, to_pt_rect(self.clip_rect))

    def stroke_rect(self, rect: Rect) -> None:
        rect = Rect(origin=rect.origin + self.translation, size=rect.size)
        x = ceil(rect.origin.x / FONT_SIZE)
        y = ceil(rect.origin.y / LINE_HEIGHT)
        width = ceil(rect.size.width / FONT_SIZE)
        height = ceil(rect.size.height / LINE_HEIGHT)
        pt_style = convert_castella_style_to_pt_style_for_rect(self.current_style)
        self.canvas.draw_stroke_rect(
            x, y, width, height, pt_style, to_pt_rect(self.clip_rect)
        )

    def fill_text(self, text: str, pos: Point, max_width: Optional[float]) -> None:
        pos = pos + self.translation
        if self.clip_rect and not self.clip_rect.contain(pos):
            return
        x = div2(pos.x, FONT_SIZE)
        y = div(pos.y, LINE_HEIGHT)
        if max_width:
            text = text[: div(max_width, FONT_SIZE)]

        pt_style = convert_castella_style_to_pt_style_for_text(self.current_style)
        self.canvas.draw_text(x, y, text, pt_style, to_pt_rect(self.clip_rect))

    def stroke_text(self, text: str, pos: Point, max_width: Optional[float]) -> None:
        # for now, stroke_text is the same as fill_text
        return self.fill_text(text, pos, max_width)

    def draw_caret(self, pos: Point, height: int) -> None:
        pos = pos + self.translation
        if self.clip_rect and not self.clip_rect.contain(pos):
            return
        x = div2(pos.x, FONT_SIZE)
        y = div(pos.y, LINE_HEIGHT)
        h = div(height, LINE_HEIGHT)
        self.canvas.draw_caret(x, y + 1, h)

    def measure_image(self, file_path: str, use_cache: bool = True) -> Size:
        raise NotImplementedError

    def draw_image(self, file_path: str, rect: Rect, use_cache: bool = True) -> None:
        raise NotImplementedError

    def draw_net_image(self, url: str, rect: Rect, use_cache: bool = True) -> None:
        raise NotImplementedError

    def measure_net_image(self, url: str, use_cache: bool = True) -> Size:
        raise NotImplementedError

    def measure_np_array_as_an_image(self, array: "np.ndarray") -> Size:  # type: ignore
        raise NotImplementedError

    def get_net_image_async(self, name: str, url: str, callback) -> None:
        raise NotImplementedError

    def get_numpy_image_async(self, array: "np.ndarray", callback) -> None:  # type: ignore
        raise NotImplementedError

    def draw_image_object(self, img, x: float, y: float) -> None:
        raise NotImplementedError

    def draw_np_array_as_an_image(
        self,
        array: "np.ndarray",  # type: ignore
        x: float,
        y: float,
    ) -> None:
        raise NotImplementedError

    def draw_np_array_as_an_image_rect(self, array: "np.ndarray", rect: Rect) -> None:  # type: ignore
        raise NotImplementedError

    def measure_text(self, text: str) -> float:
        return len(text) * FONT_SIZE

    def style(self, style: Style) -> None:
        self.current_style = style

    def flush(self) -> None:
        pass

    def _get_renderable(self) -> List[List[tuple[str, str]]]:
        return self.canvas.render()

    def clip(self, rect: Optional[Rect]) -> None:
        if rect is not None:
            if self.clip_rect is None:
                self.clip_rect = Rect(
                    origin=rect.origin + self.translation, size=rect.size
                )
            else:
                self.clip_rect = self.clip_rect.intersect(
                    Rect(origin=rect.origin + self.translation, size=rect.size)
                )

    def translate(self, pos: Point) -> None:
        self.translation = self.translation + pos

    def save(self) -> None:
        state = {
            "current_style": self.current_style,
            "translation": self.translation,
            "clip_rect": self.clip_rect,
        }
        self.state_stack.append(state)

    def restore(self) -> None:
        if self.state_stack is not None:
            state = self.state_stack.pop()
            self.current_style = state["current_style"]
            self.translation = state["translation"]
            self.clip_rect = state["clip_rect"]


def convert_castella_style_to_pt_style_for_rect(c_style: Style) -> str:
    style_str = ""
    # Background color
    if c_style.fill.color is not None:
        style_str += f"bg:{c_style.fill.color} "
    #     # c_style.fill.
    # Foreground color (text color)
    if c_style.stroke.color is not None:
        style_str += f"fg:{c_style.stroke.color} "
        # style_str += f"bg:{c_style.stroke.color} "
    # Bold or normal
    if c_style.font.weight == FontWeight.BOLD:
        style_str += "bold "
    # Italic or upright
    if c_style.font.slant == FontSlant.ITALIC:
        style_str += "italic "

    return style_str.strip()


def convert_castella_style_to_pt_style_for_text(c_style: Style) -> str:
    style_str = ""
    # Background color
    if c_style.fill.color is not None:
        style_str += f"fg:{c_style.fill.color} "

    # Bold or normal
    if c_style.font.weight == FontWeight.BOLD:
        style_str += "bold "
    # Italic or upright
    if c_style.font.slant == FontSlant.ITALIC:
        style_str += "italic "

    return style_str.strip()


def div(a: float, b: float) -> int:
    quotient, remainder = divmod(a, b)

    if remainder == 0:
        quotient -= 1

    return int(quotient)


def div2(a: float, b: float) -> int:
    quotient, remainder = divmod(a, b)

    return int(quotient)
