import functools
import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass, replace
from enum import Enum, IntEnum, auto
from typing import (Any, Callable, Generator, Generic, List, Optional,
                    Protocol, TypeVar, Union, cast, runtime_checkable)

import numpy as np
if "pyodide" in sys.modules:
    import color
else:
    from . import color


@dataclass(slots=True)
class Point:
    x: float
    y: float

    def __add__(self, other: "Point") -> "Point":
        return Point(self.x + other.x, self.y + other.y)

    def __sub__(self, other: "Point") -> "Point":
        return Point(self.x - other.x, self.y - other.y)


@dataclass(slots=True)
class Size:
    width: float
    height: float

    def __add__(self, other):
        return Size(self.width + other.width, self.height + other.height)

    def __sub__(self, other):
        return Size(self.width - other.width, self.height - other.height)


@dataclass(slots=True, frozen=True)
class Rect:
    origin: Point
    size: Size

    def contain(self, p: Point) -> bool:
        return ((p.x >= self.origin.x and
                 p.x <= self.origin.x + self.size.width) and
                (p.y >= self.origin.y and
                 p.y <= self.origin.y + self.size.height))


class SizePolicy(Enum):
    FIXED = auto()
    FIXED_HEIGHT = auto()
    FIXED_WIDTH = auto()
    EXPANDING = auto()
    CONTENT = auto()


class PositionPolicy(Enum):
    FIXED = auto()
    CENTER = auto()


class FontSizePolicy(Enum):
    FIXED = auto()
    EXPANDING = auto()


class FontWeight(Enum):
    NORMAL = auto()
    BOLD = auto()


class FontSlant(Enum):
    UPRIGHT = auto()
    ITALIC = auto()


@dataclass(slots=True, frozen=True)
class FillStyle:
    color: str = "black"


@dataclass(slots=True, frozen=True)
class StrokeStyle:
    color: str = "black"


class LineCap(Enum):
    BUTT = auto()
    ROUND = auto()
    SQUARE = auto()


@dataclass(slots=True, frozen=True)
class LineStyle:
    width: float = 1.0
    cap: LineCap = LineCap.BUTT


class FontSize(IntEnum):
    TWO_X_SMALL = 10
    X_SMALL = 12
    SMALL = 14
    MEDIUM = 16
    LARGE = 20
    X_LARGE = 24
    TWO_X_LARGE = 36
    THREE_X_LARGE = 48
    FOUR_X_LARGE = 72


@dataclass(slots=True, frozen=True)
class Font:
    family: str = "sans-serif"
    size: int = FontSize.MEDIUM
    size_policy: FontSizePolicy = FontSizePolicy.EXPANDING
    weight: FontWeight = FontWeight.NORMAL
    slant: FontSlant = FontSlant.UPRIGHT


@dataclass(slots=True, frozen=True)
class FontMetrics:
    cap_height: float


@dataclass(slots=True, frozen=True)
class Style:
    fill: FillStyle = FillStyle()
    stroke: StrokeStyle = StrokeStyle()
    line: LineStyle = LineStyle()
    font: Font = Font()
    padding: int = 8 # currently this value has the meaning only for Text and Button


@dataclass(slots=True, frozen=True)
class TextStyle:
    color: str
    fontFamilies: List[str]
    fontSize: float


class TextAlign(Enum):
    LEFT = auto()
    CENTER = auto()
    RIGHT = auto()


@dataclass(slots=True, frozen=True)
class ParagraphStyle:
    text_style: TextStyle
    text_align: TextAlign


class Paragraph(Protocol):
    def layout(self, width: float) -> None:
        ...

    def get_height(self) -> float:
        ...

    def get_max_width(self) -> float:
        ...


class ParagraphBuilder(Protocol):
    def __init__(self, style: ParagraphStyle):
        ...

    def add_text(self, text: str) -> None:
        ...

    def build(self) -> Paragraph:
        ...


class Painter(Protocol):
    def clear_all(self) -> None:
        ...

    def fill_rect(self, rect: Rect) -> None:
        ...

    def stroke_rect(self, rect: Rect) -> None:
        ...

    def translate(self, pos: Point) -> None:
        ...

    def clip(self, rect: Rect) -> None:
        ...

    def fill_text(
        self, text: str, pos: Point, max_width: Optional[float]
    ) -> None:
        ...

    def stroke_text(
        self, text: str, pos: Point, max_width: Optional[float]
    ) -> None:
        ...

    def measure_text(self, text: str) -> float:
        ...

    def get_font_metrics(self) -> FontMetrics:
        ...

    # High level API
    def draw_paragraph(self, paragraph: Paragraph, pos: Point) -> None:
        ...

    def draw_image(self, file_path: str, rect: Rect, use_cache: bool=True) -> None:
        ...

    def measure_image(self, file_path: str, use_cache: bool=True) -> Size:
        ...

    def draw_net_image(self, url: str, rect: Rect, use_cache: bool=True) -> None:
        ...

    def measure_net_image(self, url: str, use_cache: bool=True) -> Size:
        ...

    def measure_np_array_as_an_image(self, array: np.ndarray) -> Size:
        ...

    def get_net_image_async(self, name: str, url: str, callback):
        ...

    def get_numpy_image_async(self, array: np.ndarray, callback):
        ...

    def draw_image_object(self, img, x: float, y: float) -> None:
        ...

    def draw_np_array_as_an_image(self, array: np.ndarray, x: float, y: float) -> None:
        ...

    def draw_np_array_as_an_image_rect(self, array: np.ndarray, rect: Rect) -> None:
        ...

    def save(self) -> None:
        ...

    def restore(self) -> None:
        ...

    def style(self, style: Style) -> None:
        ...

    def flush(self) -> None:
        ...


W = TypeVar("W", bound="Widget")


@dataclass(slots=True)
class MouseEvent(Generic[W]):
    pos: Point = Point(0, 0)
    target: Optional[W] = None

    def translate(self, p: Point) -> "MouseEvent":
        return MouseEvent(self.pos - p, self.target)


@dataclass(slots=True)
class InputCharEvent:
    char: str


class KeyCode(Enum):
    BACKSPACE = auto()
    LEFT = auto()
    RIGHT = auto()
    UP = auto()
    DOWN = auto()
    PAGE_UP = auto()
    PAGE_DOWN = auto()
    UNKNOWN = auto()


class KeyAction(Enum):
    PRESS = auto()
    REPEAT = auto()
    RELEASE = auto()
    UNKNOWN = auto()


@dataclass(slots=True, frozen=True)
class InputKeyEvent:
    key: KeyCode
    scancode: int
    action: KeyAction
    mods: int


class Frame(Protocol):
    def __init__(self, title: str, width: float=0, height: float = 0) -> None:
        ...

    def on_mouse_down(self, handler: Callable[[MouseEvent], None]) -> None:
        ...

    def on_mouse_up(self, handler: Callable[[MouseEvent], None]) -> None:
        ...

    def on_cursor_pos(self, handler: Callable[[MouseEvent], None]) -> None:
        ...

    def on_input_char(self, handler: Callable[[InputCharEvent], None]) -> None:
        ...

    def on_input_key(self, handler: Callable[[InputKeyEvent], None]) -> None:
        ...

    def on_redraw(self, handler: Callable[[Painter, bool], None]) -> None:
        ...

    def get_painter(self) -> Painter:
        ...

    def get_size(self) -> Size:
        ...

    def post_update(self, ev: "UpdateEvent") -> None:
        ...

    def flush(self) -> None:
        ...

    def clear(self) -> None:
        ...

    def run(self) -> None:
        ...


class Observer(Protocol):
    def on_attach(self, o: "ObservableBase"):
        ...

    def on_detach(self, o: "ObservableBase"):
        ...

    def on_notify(self):
        ...


class Observable(Protocol):
    def attach(self, observer: Observer) -> None:
        ...

    def detach(self, observer: Observer) -> None:
        ...

    def notify(self) -> None:
        ...


class ObservableBase(ABC):
    def __init__(self) -> None:
        self._observers: list[Observer] = []

    def attach(self, observer: Observer) -> None:
        self._observers.append(observer)
        observer.on_attach(self)

    def detach(self, observer: Observer) -> None:
        self._observers.remove(observer)
        observer.on_detach(self)

    def notify(self) -> None:
        for o in self._observers:
            o.on_notify()


V = TypeVar("V")

@runtime_checkable
class SimpleValue(Observable, Protocol[V]):
   def set(self, value: V):
       ...

   def value(self) -> V:
       ...


class Widget(ABC):
    def __init__(
        self,
        state: Optional[Observable],
        pos: Point,
        pos_policy: Optional[PositionPolicy],
        size: Size,
        size_policy: Optional[SizePolicy],
    ) -> None:
        self._id = id(self)
        self._observable: list[Observable] = []
        self._state = state
        if state is not None:
            state.attach(self)
        self._pos = pos
        self._pos_policy = pos_policy
        self._size = size
        self._size_policy = size_policy
        self._flex = 1
        self._dirty = True
        self._enable_to_detach = True
        self._parent = None


    def contain(self, p: Point) -> tuple[Optional["Widget"], Point|None]:
        if (p.x > self._pos.x and p.x < self._pos.x + self._size.width) and (
            p.y > self._pos.y and p.y < self._pos.y + self._size.height
        ):
            return self, p
        else:
            return None, None

    def on_attach(self, o: Observable) -> None:
        self._observable.append(o)

    def on_detach(self, o: Observable) -> None:
        self._observable.remove(o)

    def on_notify(self) -> None:
        self.dirty(True)
        self.update()

    def detach(self) -> None:
        if self._enable_to_detach:
            for o in self._observable:
                o.detach(self)

    def freeze(self) -> None:
        self._enable_to_detach = False

    def mouse_down(self, ev: MouseEvent) -> None:
        pass

    def mouse_up(self, ev: MouseEvent) -> None:
        pass

    def mouse_drag(self, ev: MouseEvent) -> None:
        pass

    def mouse_over(self) -> None:
        pass

    def mouse_out(self) -> None:
        pass

    def input_char(self, ev: InputCharEvent) -> None:
        pass

    def input_key(self, ev: InputKeyEvent) -> None:
        pass

    def focused(self) -> None:
        pass

    def unfocused(self) -> None:
        pass

    @abstractmethod
    def redraw(self, p: Painter, completely: bool) -> None:
        ...

    def is_dirty(self) -> bool:
        return self._dirty

    def dirty(self, flag: bool) -> None:
        self._dirty = flag

    def move(self, p: Point): # -> Self:
        if p != self._pos:
            self._pos = p
            self._dirty = True
        return self

    def move_x(self, x: float): # -> Self:
        if x != self._pos.x:
            self._pos.x = x
            self._dirty = True
        return self

    def move_y(self, y: float): # -> Self:
        if y != self._pos.y:
            self._pos.y = y
            self._dirty = True
        return self

    def resize(self, s: Size): # -> Self:
        if s != self._size:
            self._size = s
            self._dirty = True
        return self

    def width(self, w: float): # -> Self:
        if w != self._size.width:
            self._dirty = True
            self._size.width = w
        return self

    def get_width(self) -> float:
        return self._size.width

    def height(self, h: float): # -> Self:
        if h != self._size.height:
            self._size.height = h
            self._dirty = True
        return self

    def get_height(self) -> float:
        return self._size.height

    def get_pos(self) -> Point:
        return self._pos

    def pos(self, pos: Point): # -> Self:
        if pos != self._pos:
            self._pos = pos
            self._dirty = True
        return self

    def get_size(self) -> Size:
        return self._size

    def measure(self, p: Painter) -> Size:
        return self._size

    def is_scrollable(self) -> bool:
        return False

    def update(self, completely: bool = False) -> None:
        parent = self._parent
        root = None
        while parent is not None:
            if parent.is_scrollable() or isinstance(parent, StatefulComponent):
                root = parent
            parent = parent._parent

        if root is None:
            App.get().post_update(self, completely or self.is_scrollable() or isinstance(self, StatefulComponent))
        else:
            App.get().post_update(root, True)

    def model(self, state: Observable) -> None:
        if self._state is not None:
            self._state.detach(self)
        self._state = state
        state.attach(self)

    def state(self) -> Observable | None:
        return self._state

    def size_policy(self, sp: SizePolicy): # -> Self:
        self._size_policy = sp
        return self

    def get_flex(self) -> int:
        return self._flex

    def flex(self, flex: int): # -> Self:
        self._flex = flex
        return self

    def is_width_expanding(self) -> bool:
        return (
            self._size_policy is SizePolicy.FIXED_HEIGHT
            or self._size_policy is SizePolicy.EXPANDING
        )

    def is_height_fixed(self) -> bool:
        return (
            self._size_policy is SizePolicy.FIXED
            or self._size_policy is SizePolicy.FIXED_HEIGHT
            or self._size_policy is SizePolicy.CONTENT
        )

    def is_height_expanding(self) -> bool:
        return (
            self._size_policy is SizePolicy.FIXED_WIDTH
            or self._size_policy is SizePolicy.EXPANDING
        )

    def is_width_fixed(self) -> bool:
        return (
            self._size_policy is SizePolicy.FIXED
            or self._size_policy is SizePolicy.FIXED_WIDTH
            or self._size_policy is SizePolicy.CONTENT
        )

    def parent(self, parent: "Widget") -> None:
        self._parent = parent

    def get_parent(self): # -> Self:
        return self._parent

    def delete_parent(self, parent: "Widget") -> None:
        if self._parent is parent:
            self._parent = None

    def ask_parent_to_render(self, completely: bool = False) -> None:
        if self._parent is not None:
            App.get().post_update(self._parent, completely)

    def fixed_height(self, height: float): # -> Self:
        return self.size_policy(SizePolicy.FIXED_HEIGHT).height(height)

    def fixed_width(self, width: float): # -> Self:
        return self.size_policy(SizePolicy.FIXED_WIDTH).width(width)

    def fixed_size(self, width: float, height: float): # -> Self:
        return self.size_policy(SizePolicy.FIXED).resize(Size(width, height))

    def fit(self): # -> Self:
        return self.size_policy(SizePolicy.EXPANDING)


T = TypeVar("T")


class State(ObservableBase, Generic[T]):
    def __init__(self, value: T):
        super().__init__()
        self._value: T = value

    def value(self) -> T:
        return self._value

    def __call__(self) -> T:
        return self._value

    def set(self, value: T) -> None:
        self._value = value
        self.notify()

    def __str__(self) -> str:
        return str(self._value)

    def __iadd__(self, value): # -> Self:
        self._value += value
        self.notify()
        return self

    def __add__(self, value) -> T:
        return self._value + value

    def __isub__(self, value): # -> Self:
        self._value -= value
        self.notify()
        return self

    def __imul__(self, value): # -> Self:
        self._value *= value
        self.notify()
        return self

    def __itruediv__(self, value): # -> Self:
        self._value /= value
        self.notify()
        return self


from collections.abc import Iterable


class ListState(list, ObservableBase, Generic[T]):
    def __init__(self, items):
        super().__init__(items)
        ObservableBase.__init__(self)

    def __add__(self, rhs: Iterable[T]): # -> Self:
        return ListState(super().__add__(list(rhs)))

    def __delattr__(self, name: str) -> None:
        super().__delattr__(name)
        self.notify()

    def __setattr__(self, name: str, value: Any) -> None:
        super().__setattr__(name, value)
        self.notify()

    def __iadd__(self, rhs: Iterable[T]): # -> Self:
        super().__iadd__(rhs)
        self.notify()
        return self

    def __imul__(self, rhs: int): # -> Self:
        super().__imul__(rhs)
        self.notify()
        return self

    def __mul__(self, rhs: int): # -> Self:
        return ListState(super().__mul__(rhs))

    def __rmul__(self, lhs: int): # -> Self:
        return ListState(super().__rmul__(lhs))

    def __reversed__(self): # -> Self:
        super().__reversed__()
        self.notify()
        return self

    def __setitem__(self, index: int, value: T): # -> Self:
        super().__setitem__(index, value)
        self.notify()
        return self

    def __delitem__(self, index: int): # -> Self:
        super().__delitem__(index)
        self.notify()
        return self

    def append(self, value: T) -> None:
        super().append(value)
        self.notify()

    def extend(self, it: Iterable[T]) -> None:
        super().extend(it)
        self.notify()

    def clear(self) -> None:
        super().clear()
        self.notify()

    def insert(self, index: int, value: T) -> None:
        super().insert(index, value)
        self.notify()

    def pop(self) -> T:
        retval = super().pop()
        self.notify()
        return retval

    def remove(self, value: T) -> None:
        super().remove(value)
        self.notify()

    def sort(self) -> None:
        super().sort()
        self.notify()


class ButtonState(ObservableBase):
    def __init__(self, text: str) -> None:
        super().__init__()
        self._text = text
        self._pushed = False

    def pushed(self, flag: bool) -> None:
        self._pushed = flag
        self.notify()


class TextInputState(ObservableBase):
    def __init__(self, text: str):
        super().__init__()
        self._text = text
        self._editing = False
        self._caret = len(text)

    def set(self, value: str) -> None:
        self._text = value
        self.notify()

    def value(self) -> str:
        if self._editing:
            return self._text[:self._caret] + "|" + self._text[self._caret:]
        else:
            return self._text

    def __str__(self) -> str:
        return self.value()

    def start_editing(self) -> None:
        if self._editing:
            return
        self._editing = True
        self._caret = len(self._text)
        self.notify()

    def finish_editing(self) -> None:
        if not self._editing:
            return
        self._editing = False
        self.notify()

    def insert(self, text: str) -> None:
        if not self._editing:
            return
        self._text = self._text[:self._caret] + text + self._text[self._caret:]
        self._caret += len(text)
        self.notify()

    def delete_prev(self) -> None:
        if not self._editing:
            return
        if self._caret == 0:
            return
        self._text = self._text[:self._caret-1] + self._text[self._caret:]
        self._caret -= 1
        self.notify()

    def delete_next(self) -> None:
        if not self._editing:
            return
        if len(self._text[self._caret+1:]) == 0:
            return
        self._text = self._text[:self._caret] + self._text[self._caret+1:]
        self.notify()

    def move_to_prev(self) -> None:
        if not self._editing:
            return
        if self._caret > 0:
            self._caret -= 1
            self.notify()

    def move_to_next(self) -> None:
        if not self._editing:
            return
        if len(self._text) > self._caret:
            self._caret += 1
            self.notify()


def _is_darkmode() -> bool:
    if "pyodide" in sys.modules:
        import js
        return js.window.matchMedia('(prefers-color-scheme: dark)').matches

    import darkdetect

    if darkdetect.isDark() is True:
        return True
    else:
        return False


def _get_color_schema() -> dict[str, str]:
    if _is_darkmode():
        return color.COLOR_SCHEMA[color.DARK_MODE]
    else:
        return color.COLOR_SCHEMA[color.LIGHT_MODE]


@dataclass(slots=True, frozen=True)
class WidgetStyle:
    bg_color: str = "#000000"
    border_color: str = "#FFFFFF"
    text_color: str = "#FFFFFF"
    text_font: Font = Font()


class Kind(Enum):
    NORMAL = "_normal"
    INFO = "_info"
    SUCCESS = "_success"
    WARNING = "_warning"
    DANGER = "_danger"


class AppearanceState(Enum):
    NORMAL = ""
    HOVER = "_hover"
    SELECTED = "_selected"
    DISABLED = "_disabled"
    PUSHED = "_pushed"


@dataclass(slots=True, frozen=True)
class Theme:
    app: WidgetStyle
    text_normal: WidgetStyle
    text_info: WidgetStyle
    text_success: WidgetStyle
    text_warning: WidgetStyle
    text_danger: WidgetStyle
    button_normal: WidgetStyle
    button_normal_hover: WidgetStyle
    button_normal_pushed: WidgetStyle
    layout: WidgetStyle
    scrollbar: WidgetStyle
    scrollbox: WidgetStyle

    def _get_widget_style(self,
                          widget: str,
                          kind: Kind = Kind.NORMAL,
                          state: AppearanceState = AppearanceState.NORMAL) -> WidgetStyle:
        style_name = f"{widget}{kind.value}{state.value}".format(widget, kind, state)
        if hasattr(self, style_name):
            return getattr(self, style_name)
        else:
            raise RuntimeError(f"Unknown style: {style_name}".format(style_name))

    def _convert_widget_style_to_painter_styles(self, widget_style: WidgetStyle) -> tuple[Style, Style]:
        return (Style(FillStyle(color=widget_style.bg_color),
                      StrokeStyle(color=widget_style.border_color)),
                Style(fill=FillStyle(color=widget_style.text_color),
                                      font=widget_style.text_font))

    def get_styles(self, widget: str, kind: Kind, state: AppearanceState) -> tuple[Style, Style]:
        return self._convert_widget_style_to_painter_styles(self._get_widget_style(widget, kind, state))


def _get_theme() -> Theme:
    color_schema = _get_color_schema()
    color_mode = color.DARK_MODE if _is_darkmode() else color.LIGHT_MODE
    return Theme(
        app=WidgetStyle(
            bg_color=color_schema["bg-canvas"],
        ),
        text_normal=WidgetStyle(
            bg_color=color_schema["bg-primary"],
            border_color=color_schema["border-primary"],
            text_color=color_schema["text-primary"],
        ),
        text_info=WidgetStyle(
            bg_color=color_schema["bg-info"],
            border_color=color_schema["border-primary"],
            text_color=color_schema["text-primary"],
        ),
        text_success=WidgetStyle(
            bg_color=color_schema["bg-success"],
            border_color=color_schema["border-success"],
            text_color=color_schema["text-primary"],
            text_font=Font(size=50, size_policy=FontSizePolicy.FIXED)
        ),
        text_warning=WidgetStyle(
            bg_color=color_schema["bg-warning"],
            border_color=color_schema["border-warning"],
            text_color=color_schema["text-warning"],
            text_font=Font(size=50, size_policy=FontSizePolicy.FIXED)
        ),
        text_danger=WidgetStyle(
            bg_color=color_schema["bg-danger"],
            border_color=color_schema["border-danger"],
            text_color=color_schema["text-danger"],
            text_font=Font(size=50, size_policy=FontSizePolicy.FIXED)
        ),
        button_normal=WidgetStyle(
            bg_color=color_schema["bg-tertiary"],
            border_color=color_schema["border-primary"],
            text_color=color_schema["text-primary"],
            text_font=Font(size=50, size_policy=FontSizePolicy.FIXED)
        ),
        button_normal_hover=WidgetStyle(
            bg_color=color_schema["bg-overlay"],
            border_color=color_schema["border-primary"],
            text_color=color_schema["text-primary"],
            text_font=Font(size=50, size_policy=FontSizePolicy.FIXED)
        ),
        button_normal_pushed=WidgetStyle(
            bg_color=color.COLOR_SCALE_GRAY[6 if _is_darkmode() else 2][color_mode],
            border_color=color_schema["border-secondary"],
            text_color=color_schema["text-primary"],
            text_font=Font(size=50, size_policy=FontSizePolicy.FIXED)
        ),
        layout=WidgetStyle(
            bg_color=color_schema["bg-primary"],
        ),
        scrollbar=WidgetStyle(
            bg_color=color_schema["bg-secondary"],
            border_color=color_schema["border-secondary"],
        ),
        scrollbox=WidgetStyle(
            bg_color=color_schema["border-secondary"],
        ),
    )


_theme = None

def get_theme() -> Theme:
    global _theme
    if _theme is None:
        _theme = _get_theme()
    return _theme


def set_theme(theme: Theme) -> None:
    global _theme
    _theme = theme


class Spacer(Widget):
    def __init__(self):
        super().__init__(
            state=None,
            size=Size(0, 0),
            pos=Point(0, 0),
            pos_policy=None,
            size_policy=SizePolicy.EXPANDING,
        )

    def mouse_down(self, _: MouseEvent) -> None:
        pass

    def mouse_up(self, _: MouseEvent) -> None:
        pass

    def redraw(self, _: Painter, completely: bool) -> None:
        pass

    def size_policy(self, sp: SizePolicy): # -> Self:
        if sp is SizePolicy.CONTENT:
            raise RuntimeError("Spacer doesn't accept SizePolicy.CONTENT")
        return super().size_policy(sp)


def replace_font_size(style: Style, size: float, policy: FontSizePolicy) -> Style:
    return replace(style, font=replace(style.font,
                                       size=size,
                                       size_policy=policy))


class Text(Widget):
    def __init__(self,
                 text: Any,
                 kind: Kind = Kind.NORMAL,
                 align: TextAlign = TextAlign.CENTER,
                 font_size: int | None = None):
        if isinstance(text, SimpleValue):
            state = text
        else:
            state = State(str(text))

        super().__init__(
            state=state,
            size=Size(0, 0),
            pos=Point(0, 0),
            pos_policy=None,
            size_policy=SizePolicy.EXPANDING,
        )

        self._align = align
        self._rect_style, self._text_style = get_theme().get_styles("text", kind, AppearanceState.NORMAL)
        if font_size is not None:
            self._text_style = replace_font_size(self._text_style, font_size, FontSizePolicy.FIXED)

    def mouse_down(self, ev: MouseEvent) -> None:
        pass

    def mouse_up(self, ev: MouseEvent) -> None:
        pass

    def redraw(self, p: Painter, _: bool) -> None:
        state: State = cast(State, self._state)
        p.style(self._rect_style)
        rect = Rect(origin=Point(0, 0), size=self.get_size())
        p.fill_rect(rect)
        p.stroke_rect(rect)

        width = self.get_width()
        height = self.get_height()
        font_family, font_size = determine_font(
            width,
            height,
            self._text_style,
            str(state),
        )
        p.style(
            replace(
                self._text_style,
                font=Font(
                    font_family,
                    font_size,
                ),
            ),
        )

        if self._align is TextAlign.CENTER:
            pos = Point(
                width / 2 - p.measure_text(str(state)) / 2,
                height / 2 + p.get_font_metrics().cap_height / 2,
            )
        elif self._align is TextAlign.RIGHT:
            pos = Point(
                width
                - p.measure_text(str(state))
                - self._rect_style.padding,
                height / 2 + p.get_font_metrics().cap_height / 2,
            )
        else:
            pos = Point(
                self._rect_style.padding,
                height / 2 + p.get_font_metrics().cap_height / 2,
            )

        p.fill_text(
            text=str(state),
            pos=pos,
            max_width=width,
        )

    def size_policy(self, sp: SizePolicy): # -> Self:
        if sp is SizePolicy.CONTENT and self._text_style.font.size_policy is not FontSizePolicy.FIXED:
            raise RuntimeError("Text doesn't accept SizePolicy.CONTENT because the font size policy is not FIXED")
        return super().size_policy(sp)

    def measure(self, p: Painter) -> Size:
        p.save()
        p.style(self._text_style)
        state: State = cast(State, self._state)
        s = Size(p.measure_text(str(state)), self._text_style.font.size)
        p.restore()
        return s


class Input(Text):
    def __init__(self, text: str, align: TextAlign = TextAlign.LEFT, font_size: int | None = None):
        super().__init__(TextInputState(text), Kind.NORMAL, align, font_size)

    def focused(self) -> None:
        state = cast(TextInputState, self._state)
        state.start_editing()

    def unfocused(self) -> None:
        state = cast(TextInputState, self._state)
        state.finish_editing()

    def input_char(self, ev: InputCharEvent) -> None:
        state = cast(TextInputState, self._state)
        state.insert(ev.char)

    def input_key(self, ev: InputKeyEvent) -> None:
        if ev.action is KeyAction.RELEASE:
            return

        state = cast(TextInputState, self._state)
        if ev.key is KeyCode.BACKSPACE:
            state.delete_prev()
        elif ev.key is KeyCode.LEFT:
            state.move_to_prev()
        elif ev.key is KeyCode.RIGHT:
            state.move_to_next()


def determine_font(
    width: float, height: float, style: Style, text: str
) -> tuple[str, int]:
    size_of_text = len(text)
    if size_of_text == 0:
        return style.font.family, style.font.size
    elif style.font.size_policy == FontSizePolicy.EXPANDING:
        return style.font.family, max(
            min(
                int(height - 2 * style.padding),
                int((width - 2 * style.padding) / (size_of_text * 0.65)),
            ),
            10,
        )
    else:
        return style.font.family, style.font.size


class Button(Widget):
    def __init__(self,
                 text: str,
                 align: TextAlign = TextAlign.CENTER,
                 font_size: int | None = None):
        super().__init__(
            state=ButtonState(text),
            size=Size(0, 0),
            pos=Point(0, 0),
            pos_policy=None,
            size_policy=SizePolicy.EXPANDING,
        )
        self._on_click = lambda ev: ...
        self._align = align
        kind = Kind.NORMAL
        theme = get_theme()
        self._style, self._text_style = theme.get_styles("button", kind, AppearanceState.NORMAL)
        self._kind = kind
        self._pushed_style, self._pushed_text_style = theme.get_styles("button", kind, AppearanceState.PUSHED)
        if font_size is not None:
            self._text_style = replace_font_size(self._text_style, font_size, FontSizePolicy.FIXED)

    def mouse_down(self, ev: MouseEvent) -> None:
        state: ButtonState = cast(ButtonState, self._state)
        state.pushed(True)

    def mouse_up(self, ev: MouseEvent) -> None:
        state: ButtonState = cast(ButtonState, self._state)
        state.pushed(False)
        self._on_click(ev)

    def mouse_over(self) -> None:
        self._style, self._text_style = get_theme().get_styles("button", self._kind, AppearanceState.HOVER)
        self.update()

    def mouse_out(self) -> None:
        self._style, self._text_style = get_theme().get_styles("button", self._kind, AppearanceState.NORMAL)
        self.update()

    def on_click(self, callback: Callable[[MouseEvent], Any]): # -> Self:
        self._on_click = callback
        return self

    def get_label(self) -> str:
        state: ButtonState = cast(ButtonState, self._state)
        return state._text

    def redraw(self, p: Painter, _: bool) -> None:
        state: ButtonState = cast(ButtonState, self._state)

        rect = Rect(origin=Point(0, 0), size=self.get_size())
        if state._pushed:
            p.style(self._pushed_style)
            p.fill_rect(rect)
            p.stroke_rect(rect)
        else:
            p.style(self._style)
            p.fill_rect(rect)
            p.stroke_rect(rect)

        width = self.get_width()
        height = self.get_height()
        font_family, font_size = determine_font(
            width, height, self._text_style, state._text
        )
        p.style(
            replace(
                self._pushed_text_style,
                font=Font(
                    font_family,
                    font_size,
                ),
            ),
        )

        if self._align is TextAlign.CENTER:
            pos = Point(
                width / 2 - p.measure_text(str(state._text)) / 2,
                height / 2 + p.get_font_metrics().cap_height / 2,
            )
        elif self._align is TextAlign.RIGHT:
            pos = Point(
                width
                - p.measure_text(str(state._text))
                - self._style.padding,
                height / 2 + p.get_font_metrics().cap_height / 2,
            )
        else:
            pos = Point(
                self._style.padding,
                height / 2 + p.get_font_metrics().cap_height / 2,
            )

        p.fill_text(
            text=state._text,
            pos=pos,
            max_width=width - 2 * self._style.padding,
        )

    def size_policy(self, sp: SizePolicy): # -> Self:
        if sp is SizePolicy.CONTENT and self._text_style.font.size_policy is not FontSizePolicy.FIXED:
            raise RuntimeError("The button doesn't accept SizePolicy.CONTENT because the font size policy is not FIXED")
        return super().size_policy(sp)

    def measure(self, p: Painter) -> Size:
        p.save()
        p.style(self._text_style)
        state: State = cast(State, self._state)
        s = Size(p.measure_text(str(state)) + 2 * self._style.padding, self._text_style.font.size)
        p.restore()
        return s


class Image(Widget):
    def __init__(self, file_path: str | SimpleValue[str], use_cache: bool=True):
        if isinstance(file_path, SimpleValue):
            state = file_path
        else:
            state = State(file_path)

        super().__init__(
            state=state,
            size=Size(0, 0),
            pos=Point(0, 0),
            pos_policy=None,
            size_policy=SizePolicy.CONTENT,
        )

        self._use_cache = use_cache

    def redraw(self, p: Painter, _: bool) -> None:
        state: SimpleValue[str] = cast(SimpleValue[str], self._state)
        p.draw_image(state.value(), Rect(Point(0, 0), self.get_size()), self._use_cache)

    def measure(self, p: Painter) -> Size:
        state: SimpleValue[str] = cast(SimpleValue[str], self._state)
        return p.measure_image(state.value())


class NetImage(Widget):
    def __init__(self, url: str | SimpleValue[str], use_cache: bool=True):
        if isinstance(url, SimpleValue):
            state = url
        else:
            state = State(url)

        super().__init__(
            state=state,
            size=Size(0, 0),
            pos=Point(0, 0),
            pos_policy=None,
            size_policy=SizePolicy.CONTENT,
        )

        self._use_cache = use_cache

    def redraw(self, p: Painter, _: bool) -> None:
        state: SimpleValue[str] = cast(SimpleValue[str], self._state)
        p.draw_net_image(state.value(), Rect(Point(0, 0), self.get_size()), self._use_cache)

    def measure(self, p: Painter) -> Size:
        state: SimpleValue[str] = cast(SimpleValue[str], self._state)
        return p.measure_net_image(state.value())


class AsyncNetImage(Widget):
    def __init__(self, url: str | SimpleValue[str]):
        if isinstance(url, SimpleValue):
            state = url
        else:
            state = State(url)

        super().__init__(
            state=state,
            size=Size(0, 0),
            pos=Point(0, 0),
            pos_policy=None,
            size_policy=SizePolicy.FIXED,
        )

    def redraw(self, p: Painter, _: bool) -> None:
        state: SimpleValue[str] = cast(SimpleValue[str], self._state)
        url = state.value()
        img = p.get_net_image_async(url, url, self.callback)
        if img is None:
            return
        p.draw_image_object(img, 0, 0)

    def callback(self) -> None:
        if self.get_parent() is None:
            self.update()
        else:
            self.ask_parent_to_render(True)

    def size_policy(self, sp: SizePolicy): # -> Self:
        if sp is SizePolicy.CONTENT:
            raise RuntimeError("AsyncNetImage doesn't accept SizePolicy.CONTENT")
        return super().size_policy(sp)


if "pyodide" in sys.modules:
    class NumpyImage(Widget):
        def __init__(self, array: np.ndarray | SimpleValue[np.ndarray]):
            if isinstance(array, SimpleValue):
                state = array
            else:
                state = State(array)

            super().__init__(
                state=state,
                size=Size(0, 0),
                pos=Point(0, 0),
                pos_policy=None,
                size_policy=SizePolicy.FIXED
            )

        def redraw(self, p: Painter, _: bool) -> None:
            state: SimpleValue[np.ndarray] = cast(SimpleValue[np.ndarray], self._state)
            array = state.value()
            img = p.get_numpy_image_async(array, self.callback)
            if img is None:
                return
            p.draw_image_object(img, 0, 0)

        def callback(self):
            self.dirty(True)
            if self.get_parent() is None:
                self.update()
            else:
                self.ask_parent_to_render(True)

        def size_policy(self, sp: SizePolicy):
            if sp is SizePolicy.CONTENT:
                raise RuntimeError("NumpyImage doesn't accept SizePolicy.CONTENT")
            return super().size_policy(sp)
else:
    class NumpyImage(Widget):
        def __init__(self, array: np.ndarray | SimpleValue[np.ndarray]):
            if isinstance(array, SimpleValue):
                state = array
            else:
                state = State(array)

            super().__init__(
                state=state,
                size=Size(0, 0),
                pos=Point(0, 0),
                pos_policy=None,
                size_policy=SizePolicy.CONTENT,
            )

        def redraw(self, p: Painter, _: bool) -> None:
            state: SimpleValue[np.ndarray] = cast(SimpleValue[np.ndarray], self._state)
            p.draw_np_array_as_an_image_rect(state.value(), Rect(Point(0, 0), self.get_size()))

        def measure(self, p: Painter) -> Size:
            state: SimpleValue[np.ndarray] = cast(SimpleValue[np.ndarray], self._state)
            return p.measure_np_array_as_an_image(state.value())


class Container(Protocol):
    def get_children(self) -> Generator[Widget, None, None]:
        ...

    def detach(self) -> None:
        ...


class Layout(Widget, ABC):
    _widget_style: WidgetStyle
    _style: Style

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._children: list[Widget] = []
        if not hasattr(Layout, "_widget_style"):
            Layout._widget_style = get_theme().layout
            Layout._style = Style(fill=FillStyle(color=Layout._widget_style.bg_color))

    def get_children(self) -> Generator[Widget, None, None]:
        yield from self._children

    def add(self, w: Widget) -> None:
        if (self._size_policy is SizePolicy.CONTENT
            and (self.is_height_expanding() or self.is_width_expanding())):
            raise RuntimeError("Layout with CONTENT size policy cannot have an size expandable child widget")

        self._children.append(w)
        w.parent(self)

    def detach(self) -> None:
        super().detach()
        for c in self.get_children():
            c.detach()

    def remove(self, w: Widget) -> None:
        self._children.remove(w)
        w.delete_parent(self)

    def contain(self, p: Point) -> tuple[Widget|None, Point|None]:
        if self.contain_in_content_area(p):
            p = self._adjust_pos(p)
            for c in self._children:
                target, adjusted_p = c.contain(p)
                if target is not None:
                    return target, adjusted_p
            return self, p
        elif self.contain_in_my_area(p):
            return self, p
        else:
            return None, None

    def _adjust_pos(self, p: Point) -> Point:
        return p + Point(0, 0)

    def contain_in_content_area(self, p: Point) -> bool:
        return (p.x > self._pos.x and p.x < self._pos.x + self._size.width) and (
                p.y > self._pos.y and p.y < self._pos.y + self._size.height)

    def contain_in_my_area(self, p: Point) -> bool:
        return False

    def mouse_down(self, _: MouseEvent) -> None:
        pass

    def mouse_up(self, _: MouseEvent) -> None:
        pass

    def redraw(self, p: Painter, completely: bool) -> None:
        p.style(self._style)
        if completely or self.is_dirty():
            p.fill_rect(Rect(origin=Point(0, 0), size=self.get_size()))
        self._relocattte_children(p)
        self._redraw_children(p, completely)

    @abstractmethod
    def _relocattte_children(self, p: Painter) -> None:
        ...

    def _redraw_children(self, p: Painter, completely: bool) -> None:
        for c in self._children:
            if completely or c.is_dirty():
                p.save()
                p.translate((c.get_pos() - self.get_pos()))
                p.clip(Rect(Point(0, 0), c.get_size())) # TODO orig self.get_size()))
                c.redraw(p, completely)
                p.restore()
                c.dirty(False)

    def size_policy(self, sp: SizePolicy): # -> Self:
        if sp is SizePolicy.CONTENT and self.has_size_expandable_children():
            raise RuntimeError("Layout with CONTENT size policy cannot have an size expandable child widget")

        self._size_policy = sp
        return self

    def has_size_expandable_children(self) -> bool:
        for c in self._children:
            if c.is_width_expanding() or c.is_height_expanding():
                return True

        return False


SCROLL_BAR_SIZE = 20


class Column(Layout):
    _scrollbar_widget_style = get_theme().scrollbar
    _scrollbox_widget_style = get_theme().scrollbox
    _scrollbar_style = Style(FillStyle(color=_scrollbar_widget_style.bg_color),
                             StrokeStyle(color=_scrollbar_widget_style.border_color))
    _scrollbox_style = Style(FillStyle(color=_scrollbox_widget_style.bg_color))

    def __init__(self, *children: Widget, scrollable: bool=False):
        super().__init__(
            state=None,
            pos=Point(0, 0),
            pos_policy=None,
            size=Size(0, 0),
            size_policy=SizePolicy.EXPANDING,
        )
        self._spacing = 0
        self._scroll_y = 0
        self._scrollable = scrollable
        self._scroll_box = None
        self._under_dragging = False
        self._last_drag_pos = None
        for c in children:
            self.add(c)

    def add(self, w: Widget) -> None:
        if self._scrollable and w.is_height_expanding():
            raise RuntimeError("Scrollable Column cannot have an hight expandable child widget")
        super().add(w)

    def get_children(self) -> Generator[Widget, None, None]:
        if self._spacing < 1:
            yield from self._children
            return

        for c in self._children:
            yield self._spacer
            yield c
        yield self._spacer

    def spacing(self, size: int): # -> Self:
        self._spacing = size
        self._spacer = (
            Spacer().size_policy(SizePolicy.FIXED_HEIGHT).height(size)
        )
        return self

    def redraw(self, p: Painter, completely: bool) -> None:
        if not self._scrollable:
            self._scroll_box = None
            self._scroll_y = 0
            self._last_drag_pos = None
            self._under_dragging = False
            return super().redraw(p, completely)

        content_height = self.content_height()
        if content_height <= self.get_height():
            self._scroll_box = None
            self._scroll_y = 0
            self._last_drag_pos = None
            self._under_dragging = False
            return super().redraw(p, completely)

        scroll_bar_width = SCROLL_BAR_SIZE
        p.save()
        p.style(self._style)
        if completely or self.is_dirty():
            p.fill_rect(Rect(origin=Point(0, 0), size=self.get_size()))
        p.translate(Point(0, -self._scroll_y))

        orig_width = self.get_width()
        self._size.width -= scroll_bar_width
        self._relocattte_children(p)
        self._redraw_children(p, completely)
        self._size.width = orig_width
        p.restore()

        p.save()
        p.style(Column._scrollbar_style)
        p.fill_rect(Rect(origin=Point(orig_width - scroll_bar_width, 0), size=Size(scroll_bar_width, self.get_height())))
        p.stroke_rect(Rect(origin=Point(orig_width - scroll_bar_width, -1), size=Size(scroll_bar_width, self.get_height()+2)))
        p.style(Column._scrollbox_style)
        if content_height != 0 and self.get_height() != 0:
            scroll_box_height = self.get_height() * self.get_height()/content_height
            scroll_box = Rect(origin=Point(orig_width - scroll_bar_width,
                                           (self._scroll_y/content_height)*self.get_height()),
                              size=Size(scroll_bar_width, scroll_box_height))
            self._scroll_box = scroll_box
            p.fill_rect(scroll_box)
        p.restore()

    def is_scrollable(self) -> bool:
        return self._scrollable

    def mouse_down(self, ev: MouseEvent) -> None:
        if self._scroll_box is not None:
            self._under_dragging = self._scroll_box.contain(ev.pos)
            self._last_drag_pos = ev.pos

    def mouse_up(self, _: MouseEvent) -> None:
        self._under_dragging = False

    def mouse_drag(self, ev: MouseEvent) -> None:
        last_drag_pos = self._last_drag_pos
        self._last_drag_pos = ev.pos
        if self._under_dragging and last_drag_pos is not None:
            self.scroll_y(int((ev.pos.y - last_drag_pos.y)*(self.content_height()/self.get_height())))

    def scroll_y(self, y: int): # -> Self:
        if y > 0:
            max_scroll_y = self.content_height() - self.get_height()
            if self._scroll_y == max_scroll_y:
                return self
            self._scroll_y += y
            self._scroll_y = min(max_scroll_y, self._scroll_y)
            if self._parent is not None:
                self._dirty = True
                self.ask_parent_to_render(True)
            else:
                self.update(True)
            return self
        else:
            if self._scroll_y == 0:
                return self
            self._scroll_y += y
            self._scroll_y = max(0, self._scroll_y)
            if self._parent is not None:
                self._dirty = True
                self.ask_parent_to_render(True)
            else:
                self.update(True)
            return self

    def measure(self, p: Painter) -> Size:
        width = max((0, *map(lambda c: c.measure(p).width, self.get_children())))
        height = functools.reduce(lambda total, child: total + child.measure(p).height, self.get_children(), 0)
        return Size(width, height)

    def content_height(self) -> float:
        return functools.reduce(lambda total, child: total + child.get_height(), self.get_children(), 0)

    def _adjust_pos(self, p: Point) -> Point:
        return p + Point(0, self._scroll_y)

    def contain_in_content_area(self, p: Point) -> bool:
        if self._scrollable and self.content_height() > self.get_height():
            return (p.x > self._pos.x and p.x < self._pos.x + self._size.width - SCROLL_BAR_SIZE) and (
                    p.y > self._pos.y and p.y < self._pos.y + self._size.height)
        return self.contain_in_my_area(p)

    def contain_in_my_area(self, p: Point) -> bool:
        return (p.x > self._pos.x and p.x < self._pos.x + self._size.width) and (
                p.y > self._pos.y and p.y < self._pos.y + self._size.height)

    def _relocattte_children(self, p: Painter) -> None:
        self._resize_children(p)
        self._move_children()

    def _resize_children(self, p: Painter) -> None:
        if len(self._children) == 0:
            return

        remaining_height = self.get_height()
        remaining_children: list[Widget] = []
        total_flex = 0

        for c in self.get_children():
            if c._size_policy is SizePolicy.CONTENT:
                c.resize(c.measure(p))

            if c.is_height_fixed():
                remaining_height = remaining_height - c.get_height()
            else:
                remaining_children.append(c)
                total_flex = total_flex + c.get_flex()

        fraction = remaining_height % total_flex if remaining_height > 0 and total_flex > 0 else 0
        for rc in remaining_children:
            flex = rc.get_flex()
            height = (remaining_height * flex) / total_flex
            if fraction > 0:
                height += flex
                fraction -= flex
            rc.height(int(height))

        for c in self.get_children():
            if c.is_width_expanding():
                c.width(self.get_width())

    def _move_children(self) -> None:
        acc_y = self.get_pos().y
        for c in self.get_children():
            c.move_y(acc_y)
            acc_y += c.get_height()
            c.move_x(self.get_pos().x)


class Row(Layout):
    _scrollbar_widget_style = get_theme().scrollbar
    _scrollbox_widget_style = get_theme().scrollbox
    _scrollbar_style = Style(FillStyle(color=_scrollbar_widget_style.bg_color),
                             StrokeStyle(color=_scrollbar_widget_style.border_color))
    _scrollbox_style = Style(FillStyle(color=_scrollbox_widget_style.bg_color))

    def __init__(self, *children: Widget, scrollable: bool=False):
        super().__init__(
            state=None,
            pos=Point(0, 0),
            pos_policy=None,
            size=Size(0, 0),
            size_policy=SizePolicy.EXPANDING,
        )
        self._spacing = 0
        self._scroll_x = 0
        self._scrollable = scrollable
        self._scroll_box = None
        self._under_dragging = False
        self._last_drag_pos = None
        for c in children:
            self.add(c)

    def add(self, w: Widget) -> None:
        if self._scrollable and w.is_width_expanding():
            raise RuntimeError("Scrollable Row cannot have an width expandable child widget")
        super().add(w)

    def get_children(self) -> Generator[Widget, None, None]:
        if self._spacing < 1:
            yield from self._children
            return

        for c in self._children:
            yield self._spacer
            yield c
        yield self._spacer

    def spacing(self, size: int): # -> Self:
        self._spacing = size
        self._spacer = Spacer().size_policy(SizePolicy.FIXED_WIDTH).width(size)
        return self

    def redraw(self, p: Painter, completely: bool) -> None:
        if not self._scrollable:
            self._scroll_box = None
            self._scroll_x = 0
            self._last_drag_pos = None
            self._under_dragging = False
            return super().redraw(p, completely)

        for c in self.get_children():
            if c._size_policy is SizePolicy.CONTENT:
                c.resize(c.measure(p))
        content_width = self.content_width()
        if content_width <= self.get_width():
            self._scroll_box = None
            self._scroll_x = 0
            self._last_drag_pos = None
            self._under_dragging = False
            return super().redraw(p, completely)

        scroll_bar_height = SCROLL_BAR_SIZE
        p.save()
        p.style(self._style)
        if completely or self.is_dirty():
            p.fill_rect(Rect(origin=Point(0, 0), size=self.get_size()))
        p.translate(Point(-self._scroll_x, 0))

        orig_height = self.get_height()
        self._size.height -= scroll_bar_height
        self._relocattte_children(p)
        self._redraw_children(p, completely)
        self._size.height = orig_height
        p.restore()

        p.save()
        p.style(Row._scrollbar_style)
        p.fill_rect(Rect(origin=Point(0, orig_height - scroll_bar_height), size=Size(self.get_width(), scroll_bar_height)))
        p.stroke_rect(Rect(origin=Point(-1, orig_height - scroll_bar_height), size=Size(self.get_width()+2, scroll_bar_height)))
        p.style(Row._scrollbox_style)
        if content_width != 0 and self.get_width() != 0:
            scroll_box_width = self.get_width() * self.get_width()/content_width
            scroll_box = Rect(origin=Point((self._scroll_x/content_width)*self.get_width(),
                                           orig_height - scroll_bar_height),
                              size=Size(scroll_box_width, scroll_bar_height))
            self._scroll_box = scroll_box
            p.fill_rect(scroll_box)
        p.restore()

    def mouse_down(self, ev: MouseEvent) -> None:
        if self._scroll_box is not None:
            self._under_dragging = self._scroll_box.contain(ev.pos)
            self._last_drag_pos = ev.pos

    def mouse_up(self, _: MouseEvent) -> None:
        self._under_dragging = False

    def mouse_drag(self, ev: MouseEvent) -> None:
        last_drag_pos = self._last_drag_pos
        self._last_drag_pos = ev.pos
        if self._under_dragging and last_drag_pos is not None:
            self.scroll_x(int((ev.pos.x - last_drag_pos.x)*(self.content_width()/self.get_width())))

    def scroll_x(self, x: int): # -> Self:
        if x > 0:
            max_scroll_x = self.content_width() - self.get_width()
            if self._scroll_x == max_scroll_x:
                return self
            self._scroll_x += x
            self._scroll_x = min(max_scroll_x, self._scroll_x)
            if self._parent is not None:
                self._dirty = True
                self.ask_parent_to_render(True)
            else:
                self.update(True)
            return self
        else:
            if self._scroll_x == 0:
                return self
            self._scroll_x += x
            self._scroll_x = max(0, self._scroll_x)
            if self._parent is not None:
                self._dirty = True
                self.ask_parent_to_render(True)
            else:
                self.update(True)
            return self

    def is_scrollable(self) -> bool:
        return self._scrollable

    def measure(self, p: Painter) -> Size:
        width = functools.reduce(lambda total, child: total + child.measure(p).width, self.get_children(), 0)
        height= max((0, *map(lambda c: c.measure(p).height, self.get_children())))
        return Size(width, height)

    def content_width(self) -> float:
        return functools.reduce(lambda total, child: total + child.get_width(), self.get_children(), 0)

    def _adjust_pos(self, p: Point) -> Point:
        return p + Point(self._scroll_x, 0)

    def contain_in_content_area(self, p: Point) -> bool:
        if self._scrollable and self.content_width() > self.get_width():
            return (p.x > self._pos.x and p.x < self._pos.x + self._size.width) and (
                    p.y > self._pos.y and p.y < self._pos.y + self._size.height - SCROLL_BAR_SIZE)
        return self.contain_in_my_area(p)

    def contain_in_my_area(self, p: Point) -> bool:
        return (p.x > self._pos.x and p.x < self._pos.x + self._size.width) and (
                p.y > self._pos.y and p.y < self._pos.y + self._size.height)

    def _relocattte_children(self, p: Painter) -> None:
        self._resize_children(p)
        self._move_children()

    def _resize_children(self, p: Painter) -> None:
        if len(self._children) == 0:
            return

        remaining_width = self.get_width()
        remaining_children: list[Widget] = []
        total_flex = 0

        for c in self.get_children():
            if c._size_policy is SizePolicy.CONTENT:
                c.resize(c.measure(p))

            if c.is_width_fixed():
                remaining_width = remaining_width - c.get_width()
            else:
                remaining_children.append(c)
                total_flex = total_flex + c.get_flex()

        fraction = remaining_width % total_flex if remaining_width > 0 and total_flex > 0 else 0
        for rc in remaining_children:
            flex = rc.get_flex()
            width = (remaining_width * flex) / total_flex
            if fraction > 0:
                width += flex
                fraction -= flex
            rc.width(int(width))

        for c in self.get_children():
            if c.is_height_expanding():
                c.height(self.get_height())

    def _move_children(self) -> None:
        acc_x = self.get_pos().x
        for c in self.get_children():
            c.move_x(acc_x)
            acc_x += c.get_width()
            c.move_y(self.get_pos().y)


class Box(Layout):
    _scrollbar_widget_style = get_theme().scrollbar
    _scrollbox_widget_style = get_theme().scrollbox
    _scrollbar_style = Style(FillStyle(color=_scrollbar_widget_style.bg_color),
                             StrokeStyle(color=_scrollbar_widget_style.border_color))
    _scrollbox_style = Style(FillStyle(color=_scrollbox_widget_style.bg_color))

    def __init__(self, child: Widget):
        super().__init__(
            state=None,
            pos=Point(0, 0),
            pos_policy=None,
            size=Size(0, 0),
            size_policy=SizePolicy.EXPANDING,
            # size_constraint=None,
        )
        self.add(child)
        self._child = child
        self._under_dragging_x = False
        self._under_dragging_y = False
        self._last_drag_pos = None
        self._scroll_x = 0
        self._scroll_box_x = None
        self._scroll_y = 0
        self._scroll_box_y = None

    def redraw(self, p: Painter, completely: bool) -> None:
        for c in self.get_children():
            if c._size_policy is SizePolicy.CONTENT:
                c.resize(c.measure(p))
        content_width, content_height = self.content_size()

        orig_height = self.get_height()
        orig_width = self.get_width()
        x_scroll_bar_height = 0
        y_scroll_bar_width = 0

        if content_width > self.get_width():
            x_scroll_bar_height = SCROLL_BAR_SIZE
        else:
            self._scroll_x = 0
            self._scroll_box_x = None

        if content_height > self.get_height():
            y_scroll_bar_width = SCROLL_BAR_SIZE
        else:
            self._scroll_y = 0
            self._scroll_box_y = None

        p.save()
        p.style(self._style)
        if completely or self.is_dirty():
            p.fill_rect(Rect(origin=Point(0, 0), size=self.get_size()))
        p.translate(Point(-self._scroll_x, -self._scroll_y))
        self._size.height -= x_scroll_bar_height
        self._size.width -= y_scroll_bar_width
        self._relocattte_children(p)
        self._redraw_children(p, completely)
        self._size.height = orig_height
        self._size.width = orig_width
        p.restore()

        p.save()
        p.style(Box._scrollbar_style)
        p.fill_rect(Rect(origin=Point(0, orig_height - x_scroll_bar_height), size=Size(self.get_width() - y_scroll_bar_width, x_scroll_bar_height)))
        p.stroke_rect(Rect(origin=Point(-1, orig_height - x_scroll_bar_height), size=Size(self.get_width()+2 - y_scroll_bar_width, x_scroll_bar_height)))
        p.style(Box._scrollbox_style)
        if content_width != 0 and self.get_width() != 0:
            scroll_box_width = (self.get_width() - y_scroll_bar_width) * self.get_width()/content_width
            scroll_box = Rect(origin=Point((self._scroll_x/content_width)*self.get_width(),
                                           orig_height - x_scroll_bar_height),
                              size=Size(scroll_box_width, x_scroll_bar_height))
            self._scroll_box_x = scroll_box
            p.fill_rect(scroll_box)

        p.style(Box._scrollbar_style)
        p.fill_rect(Rect(origin=Point(orig_width - y_scroll_bar_width, 0), size=Size(y_scroll_bar_width, self.get_height() - x_scroll_bar_height)))
        p.stroke_rect(Rect(origin=Point(orig_width - y_scroll_bar_width, -1), size=Size(y_scroll_bar_width, self.get_height()+2 - x_scroll_bar_height)))
        p.style(Box._scrollbox_style)
        if content_height != 0 and self.get_height() != 0:
            scroll_box_height = (self.get_height() - x_scroll_bar_height) * self.get_height()/content_height
            scroll_box = Rect(origin=Point(orig_width - y_scroll_bar_width,
                                           (self._scroll_y/content_height)*self.get_height()),
                              size=Size(y_scroll_bar_width, scroll_box_height))
            self._scroll_box_y = scroll_box
            p.fill_rect(scroll_box)
        p.restore()

    def is_scrollable(self) -> bool:
        return True

    def mouse_down(self, ev: MouseEvent) -> None:
        if self._scroll_box_x is not None:
            self._under_dragging_x = self._scroll_box_x.contain(ev.pos)
            self._last_drag_pos = ev.pos
        if not self._under_dragging_x and self._scroll_box_y is not None:
            self._under_dragging_y = self._scroll_box_y.contain(ev.pos)
            self._last_drag_pos = ev.pos

    def mouse_up(self, _: MouseEvent) -> None:
        self._under_dragging_x = False
        self._under_dragging_y = False

    def mouse_drag(self, ev: MouseEvent) -> None:
        w, h = self.content_size()
        last_drag_pos = self._last_drag_pos
        self._last_drag_pos = ev.pos
        if last_drag_pos is None:
            return

        if self._under_dragging_x:
            self.scroll_x(w, int((ev.pos.x - last_drag_pos.x)*(w/self.get_width())))
        elif self._under_dragging_y:
            self.scroll_y(h, int((ev.pos.y - last_drag_pos.y)*(h/self.get_height())))

    def scroll_x(self, w: float, x: int): # -> Self:
        if x > 0:
            max_scroll_x = w - self.get_width()
            if self._scroll_x == max_scroll_x:
                return self
            self._scroll_x += x
            self._scroll_x = min(max_scroll_x, self._scroll_x)
            if self._parent is not None:
                self._dirty = True
                self.ask_parent_to_render(True)
            else:
                self.update(True)
            return self
        else:
            if self._scroll_x == 0:
                return self
            self._scroll_x += x
            self._scroll_x = max(0, self._scroll_x)
            if self._parent is not None:
                self._dirty = True
                self.ask_parent_to_render(True)
            else:
                self.update(True)
            return self

    def scroll_y(self, h: float, y: int): # -> Self:
        if y > 0:
            max_scroll_y = h - self.get_height()
            if self._scroll_y == max_scroll_y:
                return self
            self._scroll_y += y
            self._scroll_y = min(max_scroll_y, self._scroll_y)
            if self._parent is not None:
                self._dirty = True
                self.ask_parent_to_render(True)
            else:
                self.update(True)
            return self
        else:
            if self._scroll_y == 0:
                return self
            self._scroll_y += y
            self._scroll_y = max(0, self._scroll_y)
            if self._parent is not None:
                self._dirty = True
                self.ask_parent_to_render(True)
            else:
                self.update(True)
            return self

    def measure(self, p: Painter) -> Size:
        return self._child.measure(p)

    def content_size(self) -> tuple[float, float]:
        return functools.reduce(lambda total, child: (total[0] + child.get_width(), total[1] + child.get_height()),
                                self.get_children(),
                                (0, 0))

    def _adjust_pos(self, p: Point) -> Point:
        return p + Point(self._scroll_x, self._scroll_y)

    def contain_in_content_area(self, p: Point) -> bool:
        w, h = self.content_size()
        return (p.x > self._pos.x and p.x < self._pos.x + self._size.width - SCROLL_BAR_SIZE * (h > self.get_height())) and (
                p.y > self._pos.y and p.y < self._pos.y + self._size.height - SCROLL_BAR_SIZE * (w > self.get_width()))

    def contain_in_my_area(self, p: Point) -> bool:
        return (p.x > self._pos.x and p.x < self._pos.x + self._size.width) and (
                p.y > self._pos.y and p.y < self._pos.y + self._size.height)

    def _relocattte_children(self, p: Painter) -> None:
        self._resize_children(p)
        self._move_children()

    def _resize_children(self, p: Painter) -> None:
        if len(self._children) == 0:
            return

        remaining_width = self.get_width()
        remaining_children: list[Widget] = []
        total_flex = 0

        for c in self.get_children():
            if c._size_policy is SizePolicy.CONTENT:
                c.resize(c.measure(p))

            if c.is_width_fixed():
                remaining_width = remaining_width - c.get_width()
            else:
                remaining_children.append(c)
                total_flex = total_flex + c.get_flex()

        fraction = remaining_width % total_flex if remaining_width > 0 and total_flex > 0 else 0
        for rc in remaining_children:
            flex = rc.get_flex()
            width = (remaining_width * flex) / total_flex
            if fraction > 0:
                width += flex
                fraction -= flex
            rc.width(int(width))

        for c in self.get_children():
            if c.is_height_expanding():
                c.height(self.get_height())

    def _move_children(self) -> None:
        acc_x = self.get_pos().x
        for c in self.get_children():
            c.move_x(acc_x)
            acc_x += c.get_width()
            c.move_y(self.get_pos().y)


class Component(Layout, ABC):
    def __init__(self):
        super().__init__(
            state=None,
            pos=Point(0, 0),
            pos_policy=None,
            size=Size(0, 0),
            size_policy=SizePolicy.EXPANDING,
        )
        self._child = None

    def _relocattte_children(self, p: Painter) -> None:
        self._resize_children(p)
        self._move_children()

    def _resize_children(self, p: Painter) -> None:
        if len(self._children) == 0:
            return

        child = self._children[0]
        child.resize(replace(self.get_size()))

    def _move_children(self):
        child = self._children[0]
        child.move(self.get_pos())

    @abstractmethod
    def view(self) -> Widget:
        ...

    def on_notify(self) -> None:
        if self._child is not None:
            self.remove(self._child)
            self._child.detach()
            self._child = None
        super().on_notify()

    def redraw(self, p: Painter, completely: bool) -> None:
        if self._child is None:
            self._child = self.view()
            self.add(self._child)
        super().redraw(p, completely)

    def measure(self, p: Painter) -> Size:
        if self._child is None:
            return Size(0, 0)
        return self._child.measure(p)


class StatefulComponent(Component):
    def __init__(self, state: Observable):
        super().__init__()
        self.model(state)


@dataclass(slots=True, frozen=True)
class UpdateEvent:
    target: Union[Widget, "App"]
    completely: bool = False


class App:
    _instance: "App"

    def __new__(cls, _frame: Frame, _widget: Widget):
        if not hasattr(cls, "_instance"):
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, frame: Frame, widget: Widget):
        self._frame = frame
        self._downed: Optional[Widget] = None
        self._focused: Optional[Widget] = None
        self._mouse_overed: Optional[Widget] = None
        self._layers: list[Widget] = []
        self._layerPositions: list[PositionPolicy] = []
        self._style = Style(fill=FillStyle(color=get_theme().app.bg_color))
        self.push_layer(widget, PositionPolicy.FIXED)

    @classmethod
    def get(cls): # -> Self:
        return cls._instance

    def push_layer(self, l: Widget, p: PositionPolicy): # -> Self:
        self._layers.append(l)
        self._layerPositions.append(p)
        self._frame.post_update(UpdateEvent(self, True))
        return self

    def pop_layer(self): # -> Self:
        self._layers.pop()
        self._layerPositions.pop()
        self._frame.post_update(UpdateEvent(self, True))
        return self

    def peek_layer(self) -> tuple[Widget, PositionPolicy]:
        return self._layers[-1], self._layerPositions[-1]

    def mouse_down(self, ev: MouseEvent) -> None:
        target, p = self.peek_layer()[0].contain(ev.pos)
        if target is not None and p is not None:
            ev.target = target
            self._prev_abs_pos = ev.pos
            ev.pos = p - target.get_pos()
            self._prev_rel_pos = ev.pos
            target.mouse_down(ev)
            self._downed = target
        else:
            if len(self._layers) > 1:
                self.pop_layer()

    def mouse_up(self, ev: MouseEvent) -> None:
        if self._downed is None:
            return

        try:
            if self._focused is not None:
                self._focused.unfocused()

            self._focused = self._downed
            self._focused.focused()

            ev.target = self._downed
            diff = ev.pos - self._prev_abs_pos
            self._prev_abs_pos = ev.pos
            ev.pos =  self._prev_rel_pos + diff
            self._prev_rel_pos = ev.pos
            self._downed.mouse_up(ev)
        finally:
            self._downed = None

    def cursor_pos(self, ev: MouseEvent) -> None:
        layer = self.peek_layer()[0]
        target, p = layer.contain(ev.pos)
        if target is None:
            return
        elif self._downed is None:
            if self._mouse_overed is None:
                self._mouse_overed = target
                self._mouse_overed_layer = layer
                target.mouse_over()
            elif self._mouse_overed is not target:
                if self._mouse_overed_layer is layer:
                    self._mouse_overed.mouse_out()
                self._mouse_overed = target
                self._mouse_overed_layer = layer
                target.mouse_over()
            return
        elif (target is self._downed or self._downed.contain(ev.pos)[0] is not None) and p is not None:
            diff = ev.pos - self._prev_abs_pos
            self._prev_abs_pos = ev.pos
            ev.pos =  self._prev_rel_pos + diff
            self._prev_rel_pos = ev.pos
            self._downed.mouse_drag(ev)

    def input_char(self, ev: InputCharEvent) -> None:
        if self._focused is None:
            return
        self._focused.input_char(ev)

    def input_key(self, ev: InputKeyEvent) -> None:
        if self._focused is None:
            return
        self._focused.input_key(ev)

    def redraw(self, p: Painter, completely: bool) -> None:
        p.style(self._style)
        p.fill_rect(Rect(origin=Point(0, 0), size=self._frame.get_size()))
        for i in range(len(self._layers)):
            l = self._layers[i]
            pos = self._layerPositions[i]
            self._relocattte_layout(l, pos)
            if completely or l.is_dirty():
                p.save()
                p.translate(l.get_pos())
                p.clip(Rect(Point(0, 0), l.get_size()))
                l.redraw(p, completely)
                p.restore()
                l.dirty(False)
        p.flush()

    def _relocattte_layout(self, w: Widget, p: PositionPolicy) -> None:
        if w is None:
            return

        frame_size = self._frame.get_size()
        latest_size = w.get_size()
        size_policy = w._size_policy

        if size_policy in (SizePolicy.EXPANDING, SizePolicy.FIXED_WIDTH, None):
            height = frame_size.height
        else:
            height = latest_size.height

        if size_policy in (SizePolicy.EXPANDING, SizePolicy.FIXED_HEIGHT, None):
            width = frame_size.width
        else:
            width = latest_size.width

        if p is PositionPolicy.FIXED:
            pass
        else:
            w.move(
                Point(
                    int(self._frame.get_size().width / 2 - w.get_size().width / 2),
                    int(self._frame.get_size().height / 2 - w.get_size().height / 2),
                )
            )
        w.resize(Size(width=width, height=height))

    def post_update(self, w: Widget, completely: bool= False) -> None:
        self._frame.post_update(UpdateEvent(w, completely))

    def run(self) -> None:
        self._frame.on_mouse_down(self.mouse_down)
        self._frame.on_mouse_up(self.mouse_up)
        self._frame.on_cursor_pos(self.cursor_pos)
        self._frame.on_input_char(self.input_char)
        self._frame.on_input_key(self.input_key)
        self._frame.on_redraw(self.redraw)
        self._frame.run()
