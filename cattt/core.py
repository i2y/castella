import functools
import re
import sys
from abc import ABC, abstractmethod
from collections.abc import Iterable
from copy import deepcopy
from dataclasses import dataclass, replace
from enum import Enum, IntEnum, auto
from typing import (
    Any,
    Callable,
    Generator,
    Generic,
    List,
    Optional,
    Protocol,
    TypeAlias,
    TypeVar,
    Union,
    cast,
    runtime_checkable,
)

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
        return (p.x >= self.origin.x and p.x <= self.origin.x + self.size.width) and (
            p.y >= self.origin.y and p.y <= self.origin.y + self.size.height
        )


@dataclass(slots=True, frozen=True)
class Circle:
    center: Point
    radius: float

    def contain(self, p: Point) -> bool:
        c = self.center
        return ((p.x - c.x) ** 2 + (p.y - c.y) ** 2) < self.radius**2


class SizePolicy(Enum):
    FIXED = auto()
    EXPANDING = auto()
    CONTENT = auto()


@dataclass(slots=True, frozen=True)
class NewSizePolicy:
    width: SizePolicy
    height: SizePolicy


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
    padding: int = 8  # currently this value has the meaning only for Text and Button


@dataclass(slots=True, frozen=True)
class TextStyle:
    color: str
    fontFamilies: List[str]
    fontSize: float


class TextAlign(Enum):
    LEFT = auto()
    CENTER = auto()
    RIGHT = auto()


class Painter(Protocol):
    def clear_all(self) -> None:
        ...

    def fill_rect(self, rect: Rect) -> None:
        ...

    def stroke_rect(self, rect: Rect) -> None:
        ...

    def fill_circle(self, circle: Circle) -> None:
        ...

    def stroke_circle(self, circle: Circle) -> None:
        ...

    def translate(self, pos: Point) -> None:
        ...

    def clip(self, rect: Rect) -> None:
        ...

    def fill_text(self, text: str, pos: Point, max_width: Optional[float]) -> None:
        ...

    def stroke_text(self, text: str, pos: Point, max_width: Optional[float]) -> None:
        ...

    def measure_text(self, text: str) -> float:
        ...

    def get_font_metrics(self) -> FontMetrics:
        ...

    def draw_image(self, file_path: str, rect: Rect, use_cache: bool = True) -> None:
        ...

    def measure_image(self, file_path: str, use_cache: bool = True) -> Size:
        ...

    def draw_net_image(self, url: str, rect: Rect, use_cache: bool = True) -> None:
        ...

    def measure_net_image(self, url: str, use_cache: bool = True) -> Size:
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


@dataclass(slots=True, frozen=True)
class WheelEvent:
    pos: Point
    x_offset: float
    y_offset: float


@dataclass(slots=True, frozen=True)
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
    DELETE = auto()
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
    def __init__(self, title: str, width: float = 0, height: float = 0) -> None:
        ...

    def on_mouse_down(self, handler: Callable[[MouseEvent], None]) -> None:
        ...

    def on_mouse_up(self, handler: Callable[[MouseEvent], None]) -> None:
        ...

    def on_mouse_wheel(self, handler: Callable[[WheelEvent], None]) -> None:
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


class UpdateListener:
    __slots__ = ["_observable", "_callback"]

    def __init__(self, callback: Callable[[], None]):
        self._observable = None
        self._callback = callback

    def on_attach(self, o: "ObservableBase"):
        self._observable = o

    def on_detach(self, o: "ObservableBase"):
        del self._observable

    def on_notify(self):
        self._callback()


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

    def on_update(self, callback: Callable) -> None:
        self.attach(UpdateListener(callback))


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
        state: Observable | None,
        pos: Point,
        pos_policy: PositionPolicy | None,
        size: Size,
        width_policy: SizePolicy = SizePolicy.EXPANDING,
        height_policy: SizePolicy = SizePolicy.EXPANDING,
    ) -> None:
        self._id = id(self)
        self._observable: list[Observable] = []
        self._state = state
        if state is not None:
            state.attach(self)
        self._pos = pos
        self._pos_policy = pos_policy
        self._size = size
        self._width_policy = width_policy
        self._height_policy = height_policy
        self._flex = 1
        self._dirty = True
        self._enable_to_detach = True
        self._parent = None
        self._widget_styles = get_theme().get_widget_styles(self)
        self._on_update_widget_styles()

    def _get_widget_style(
        self, kind: "Kind", state: "AppearanceState"
    ) -> "WidgetStyle":
        style_name = f"{kind.value}{state.value}".format(kind, state)
        styles = self._widget_styles

        if style_name in styles:
            s = styles[style_name]
            return s
        else:
            widget = self.__class__.__name__.lower()
            raise RuntimeError(
                f"Unknown style: {widget}.{kind.value}{state.value}".format(kind, state)
            )

    def change_style(
        self, kind: "Kind", state: "AppearanceState", new_style: "WidgetStyle"
    ):  # -> Self:
        styles = self._widget_styles
        style_name = f"{kind.value}{state.value}".format(kind, state)
        styles[style_name] = new_style
        self._on_update_widget_styles()
        return self

    def bg_color(self, rgb: str):  # -> Self:
        return self.change_style(
            Kind.NORMAL,
            AppearanceState.NORMAL,
            replace(
                self._get_widget_style(Kind.NORMAL, AppearanceState.NORMAL),
                bg_color=rgb,
            ),
        )

    def text_color(self, rgb: str):  # -> Self:
        return self.change_style(
            Kind.NORMAL,
            AppearanceState.NORMAL,
            replace(
                self._get_widget_style(Kind.NORMAL, AppearanceState.NORMAL),
                text_color=rgb,
            ),
        )

    def fg_color(self, rgb: str):  # -> Self:
        return self.text_color(rgb)

    def border_color(self, rgb: str):  # -> Self:
        return self.change_style(
            Kind.NORMAL,
            AppearanceState.NORMAL,
            replace(
                self._get_widget_style(Kind.NORMAL, AppearanceState.NORMAL),
                border_color=rgb,
            ),
        )

    def erase_border(self):  # -> Self:
        return self.border_color(
            self._get_widget_style(Kind.NORMAL, AppearanceState.NORMAL).bg_color
        )

    def _on_update_widget_styles(self) -> None:
        pass

    @staticmethod
    def _convert_widget_style_to_painter_styles(
        widget_style: "WidgetStyle",
    ) -> tuple[Style, Style]:
        return (
            Style(
                FillStyle(color=widget_style.bg_color),
                StrokeStyle(color=widget_style.border_color),
            ),
            Style(
                fill=FillStyle(color=widget_style.text_color),
                font=deepcopy(widget_style.text_font),
            ),
        )

    def _get_painter_styles(
        self, kind: "Kind", appearance_state: "AppearanceState"
    ) -> tuple[Style, Style]:
        return Widget._convert_widget_style_to_painter_styles(
            self._get_widget_style(kind, appearance_state)
        )

    def dispatch(self, p: Point) -> tuple[Optional["Widget"], Point | None]:
        if self.contain(p):
            return self, p
        else:
            return None, None

    def dispatch_to_scrollable(
        self,
        p: Point,
        is_direction_x: bool,
    ) -> tuple[Optional["Widget"], Point | None]:
        return None, None

    def contain(self, p: Point) -> bool:
        return (self._pos.x < p.x < self._pos.x + self._size.width) and (
            self._pos.y < p.y < self._pos.y + self._size.height
        )

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

    def mouse_wheel(self, ev: WheelEvent) -> None:
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

    def move(self, p: Point):  # -> Self:
        if p != self._pos:
            self._pos = p
            self._dirty = True
        return self

    def move_x(self, x: float):  # -> Self:
        if x != self._pos.x:
            self._pos.x = x
            self._dirty = True
        return self

    def move_y(self, y: float):  # -> Self:
        if y != self._pos.y:
            self._pos.y = y
            self._dirty = True
        return self

    def resize(self, s: Size):  # -> Self:
        if s != self._size:
            self._size = s
            self._dirty = True
        return self

    def width(self, w: float):  # -> Self:
        if w != self._size.width:
            self._dirty = True
            self._size.width = w
        return self

    def get_width(self) -> float:
        return self._size.width

    def height(self, h: float):  # -> Self:
        if h != self._size.height:
            self._size.height = h
            self._dirty = True
        return self

    def get_height(self) -> float:
        return self._size.height

    def get_pos(self) -> Point:
        return self._pos

    def pos(self, pos: Point):  # -> Self:
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
            App.get().post_update(
                self,
                completely
                or self.is_scrollable()
                or isinstance(self, StatefulComponent),
            )
        else:
            App.get().post_update(root, True)

    def model(self, state: Observable) -> None:
        if self._state is not None:
            self._state.detach(self)
        self._state = state
        state.attach(self)

    def state(self) -> Observable | None:
        return self._state

    def get_width_policy(self) -> SizePolicy:
        return self._width_policy

    def width_policy(self, sp: SizePolicy):  # -> Self:
        self._width_policy = sp
        return self

    def get_height_policy(self) -> SizePolicy:
        return self._height_policy

    def height_policy(self, sp: SizePolicy):  # -> Self:
        self._height_policy = sp
        return self

    def get_flex(self) -> int:
        return self._flex

    def flex(self, flex: int):  # -> Self:
        self._flex = flex
        return self

    def parent(self, parent: "Widget") -> None:
        self._parent = parent

    def get_parent(self):  # -> Self:
        return self._parent

    def delete_parent(self, parent: "Widget") -> None:
        if self._parent is parent:
            self._parent = None

    def ask_parent_to_render(self, completely: bool = False) -> None:
        if self._parent is not None:
            App.get().post_update(self._parent, completely)

    def fixed_width(self, width: float):  # -> Self:
        return self.width_policy(SizePolicy.FIXED).width(width)

    def fixed_height(self, height: float):  # -> Self:
        return self.height_policy(SizePolicy.FIXED).height(height)

    def fixed_size(self, width: float, height: float):  # -> Self:
        return (
            self.width_policy(SizePolicy.FIXED)
            .height_policy(SizePolicy.FIXED)
            .resize(Size(width, height))
        )

    def fit_parent(self):  # -> Self:
        return self.width_policy(SizePolicy.EXPANDING).height_policy(
            SizePolicy.EXPANDING
        )

    def fit_content(self):  # -> Self:
        return self.width_policy(SizePolicy.CONTENT).height_policy(SizePolicy.CONTENT)

    def fit_content_width(self):  # -> Self:
        return self.width_policy(SizePolicy.CONTENT)

    def fit_content_height(self):  # -> Self:
        return self.height_policy(SizePolicy.CONTENT)


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

    def __iadd__(self, value):  # -> Self:
        self._value += value
        self.notify()
        return self

    def __add__(self, value) -> T:
        return self._value + value

    def __isub__(self, value):  # -> Self:
        self._value -= value
        self.notify()
        return self

    def __imul__(self, value):  # -> Self:
        self._value *= value
        self.notify()
        return self

    def __itruediv__(self, value):  # -> Self:
        self._value /= value
        self.notify()
        return self


class ListState(list, ObservableBase, Generic[T]):
    def __init__(self, items):
        super().__init__(items)
        ObservableBase.__init__(self)

    def __add__(self, rhs: Iterable[T]):  # -> Self:
        return ListState(super().__add__(list(rhs)))

    def __delattr__(self, name: str) -> None:
        super().__delattr__(name)
        self.notify()

    def __setattr__(self, name: str, value: Any) -> None:
        super().__setattr__(name, value)
        self.notify()

    def __iadd__(self, rhs: Iterable[T]):  # -> Self:
        super().__iadd__(rhs)
        self.notify()
        return self

    def __imul__(self, rhs: int):  # -> Self:
        super().__imul__(rhs)
        self.notify()
        return self

    def __mul__(self, rhs: int):  # -> Self:
        return ListState(super().__mul__(rhs))

    def __rmul__(self, lhs: int):  # -> Self:
        return ListState(super().__rmul__(lhs))

    def __reversed__(self):  # -> Self:
        super().__reversed__()
        self.notify()
        return self

    def __setitem__(self, index: int, value: T):  # -> Self:
        super().__setitem__(index, value)
        self.notify()
        return self

    def __delitem__(self, index: int):  # -> Self:
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

    def is_pushed(self) -> bool:
        return self._pushed

    def get_text(self) -> str:
        return self._text


class InputState(ObservableBase):
    def __init__(self, text: str):
        super().__init__()
        self._text = text
        self._editing = False
        self._caret = len(text)

    def set(self, value: str) -> None:
        self._text = value
        self.notify()

    def value(self) -> str:
        return self._text

    def raw_value(self) -> str:
        return self._text

    def __str__(self) -> str:
        return self.value()

    def get_caret_pos(self) -> int:
        return self._caret

    def is_in_editing(self) -> bool:
        return self._editing

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
        self._text = self._text[: self._caret] + text + self._text[self._caret :]
        self._caret += len(text)
        self.notify()

    def delete_prev(self) -> None:
        if not self._editing:
            return
        if self._caret == 0:
            return
        self._text = self._text[: self._caret - 1] + self._text[self._caret :]
        self._caret -= 1
        self.notify()

    def delete_next(self) -> None:
        if not self._editing:
            return
        if len(self._text[self._caret :]) == 0:
            return
        self._text = self._text[: self._caret] + self._text[self._caret + 1 :]
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

        return js.window.matchMedia("(prefers-color-scheme: dark)").matches

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


# WidgetStyles = NewType('WidgetStyles', Mapping[str, WidgetStyle])
WidgetStyles: TypeAlias = dict[str, WidgetStyle]


class Kind(Enum):
    NORMAL = "normal"
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    DANGER = "danger"


class AppearanceState(Enum):
    NORMAL = ""
    HOVER = "_hover"
    SELECTED = "_selected"
    DISABLED = "_disabled"
    PUSHED = "_pushed"


@dataclass(slots=True, frozen=True)
class Theme:
    app: WidgetStyle
    scrollbar: WidgetStyle
    scrollbox: WidgetStyle
    layout: WidgetStyle
    text: WidgetStyles
    multilinetext: WidgetStyles
    input: WidgetStyles
    button: WidgetStyles
    switch: WidgetStyles

    def get_widget_styles(self, widget: Widget) -> WidgetStyles:
        class_name = widget.__class__.__name__.lower()
        return deepcopy(getattr(self, class_name)) if hasattr(self, class_name) else {}


def _get_theme() -> Theme:
    color_schema = _get_color_schema()
    return Theme(
        app=WidgetStyle(
            bg_color=color_schema["bg-canvas"],
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
        text={
            "normal": WidgetStyle(
                bg_color=color_schema["bg-primary"],
                border_color=color_schema["border-primary"],
                text_color=color_schema["text-primary"],
            ),
            "info": WidgetStyle(
                bg_color=color_schema["bg-info"],
                border_color=color_schema["border-info"],
                text_color=color_schema["text-info"],
            ),
            "success": WidgetStyle(
                bg_color=color_schema["bg-success"],
                border_color=color_schema["border-success"],
                text_color=color_schema["text-success"],
            ),
            "warning": WidgetStyle(
                bg_color=color_schema["bg-warning"],
                border_color=color_schema["border-warning"],
                text_color=color_schema["text-warning"],
            ),
            "danger": WidgetStyle(
                bg_color=color_schema["bg-danger"],
                border_color=color_schema["border-danger"],
                text_color=color_schema["text-danger"],
            ),
        },
        multilinetext={
            "normal": WidgetStyle(
                bg_color=color_schema["bg-primary"],
                border_color=color_schema["bg-primary"],
                text_color=color_schema["text-primary"],
            ),
            "info": WidgetStyle(
                bg_color=color_schema["bg-info"],
                border_color=color_schema["border-info"],
                text_color=color_schema["text-info"],
            ),
            "success": WidgetStyle(
                bg_color=color_schema["bg-success"],
                border_color=color_schema["border-success"],
                text_color=color_schema["text-success"],
            ),
            "warning": WidgetStyle(
                bg_color=color_schema["bg-warning"],
                border_color=color_schema["border-warning"],
                text_color=color_schema["text-warning"],
            ),
            "danger": WidgetStyle(
                bg_color=color_schema["bg-danger"],
                border_color=color_schema["border-danger"],
                text_color=color_schema["text-danger"],
            ),
        },
        input={
            "normal": WidgetStyle(
                bg_color=color_schema["bg-secondary"],
                border_color=color_schema["border-primary"],
                text_color=color_schema["text-primary"],
            ),
            "info": WidgetStyle(
                bg_color=color_schema["bg-info"],
                border_color=color_schema["border-info"],
                text_color=color_schema["text-info"],
            ),
            "success": WidgetStyle(
                bg_color=color_schema["bg-success"],
                border_color=color_schema["border-success"],
                text_color=color_schema["text-success"],
            ),
            "warning": WidgetStyle(
                bg_color=color_schema["bg-warning"],
                border_color=color_schema["border-warning"],
                text_color=color_schema["text-warning"],
            ),
            "danger": WidgetStyle(
                bg_color=color_schema["bg-danger"],
                border_color=color_schema["border-danger"],
                text_color=color_schema["text-danger"],
            ),
        },
        button={
            "normal": WidgetStyle(
                bg_color=color_schema["bg-tertiary"],
                border_color=color_schema["border-primary"],
                text_color=color_schema["text-primary"],
            ),
            "normal_hover": WidgetStyle(
                bg_color=color_schema["bg-overlay"],
                border_color=color_schema["border-primary"],
                text_color=color_schema["text-primary"],
            ),
            "normal_pushed": WidgetStyle(
                bg_color=color_schema["bg-pushed"],
                border_color=color_schema["border-secondary"],
                text_color=color_schema["text-primary"],
            ),
        },
        switch={
            "normal": WidgetStyle(
                bg_color=color_schema["bg-tertiary"],
                text_color=color_schema["fg"],
            ),
            "normal_selected": WidgetStyle(
                bg_color=color_schema["bg-selected"],
                text_color=color_schema["fg"],
            ),
        },
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
            width_policy=SizePolicy.EXPANDING,
            height_policy=SizePolicy.EXPANDING,
        )

    def mouse_down(self, _: MouseEvent) -> None:
        pass

    def mouse_up(self, _: MouseEvent) -> None:
        pass

    def redraw(self, _: Painter, completely: bool) -> None:
        pass

    def width_policy(self, sp: SizePolicy):  # -> Self:
        if sp is SizePolicy.CONTENT:
            raise RuntimeError("Spacer doesn't accept SizePolicy.CONTENT")
        return super().width_policy(sp)

    def height_policy(self, sp: SizePolicy):  # -> Self:
        if sp is SizePolicy.CONTENT:
            raise RuntimeError("Spacer doesn't accept SizePolicy.CONTENT")
        return super().height_policy(sp)


def replace_font_size(style: Style, size: float, policy: FontSizePolicy) -> Style:
    return replace(style, font=replace(style.font, size=size, size_policy=policy))


class Text(Widget):
    def __init__(
        self,
        text: Any,
        kind: Kind = Kind.NORMAL,
        align: TextAlign = TextAlign.CENTER,
        font_size: int | None = None,
    ):
        if isinstance(text, SimpleValue):
            state = text
        else:
            state = State(str(text))

        self._kind = kind
        self._font_size = font_size
        self._align = align

        super().__init__(
            state=state,
            size=Size(0, 0),
            pos=Point(0, 0),
            pos_policy=None,
            width_policy=SizePolicy.EXPANDING,
            height_policy=SizePolicy.EXPANDING,
        )

    def _on_update_widget_styles(self) -> None:
        self._rect_style, self._text_style = self._get_painter_styles(
            self._kind, AppearanceState.NORMAL
        )
        if self._font_size is not None:
            self._text_style = replace_font_size(
                self._text_style, self._font_size, FontSizePolicy.FIXED
            )

    def redraw(self, p: Painter, _: bool) -> None:
        state: State = cast(State, self._state)

        p.style(self._rect_style)
        size = self.get_size()
        rect = Rect(origin=Point(0, 0), size=size)
        p.fill_rect(rect)
        p.stroke_rect(rect)

        width = size.width
        height = size.height
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
                width - p.measure_text(str(state)) - self._rect_style.padding,
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

    def width_policy(self, sp: SizePolicy):  # -> Self:
        if (
            sp is SizePolicy.CONTENT
            and self._text_style.font.size_policy is not FontSizePolicy.FIXED
        ):
            raise RuntimeError(
                "Text doesn't accept SizePolicy.CONTENT because the font size policy is not FIXED"
            )
        return super().width_policy(sp)

    def height_policy(self, sp: SizePolicy):  # -> Self:
        if (
            sp is SizePolicy.CONTENT
            and self._text_style.font.size_policy is not FontSizePolicy.FIXED
        ):
            raise RuntimeError(
                "Text doesn't accept SizePolicy.CONTENT because the font size policy is not FIXED"
            )
        return super().height_policy(sp)

    def measure(self, p: Painter) -> Size:
        p.save()
        p.style(self._text_style)
        state: State = cast(State, self._state)
        s = Size(p.measure_text(str(state)), self._text_style.font.size)
        p.restore()
        return s


class MultilineText(Widget):
    def __init__(
        self,
        text: str | SimpleValue[str],
        font_size: int,
        padding: int = 8,
        line_spacing: int = 4,
        kind: Kind = Kind.NORMAL,
        wrap: bool = False,  # only works if the size policy of width is not SizePolicy.CONTENT
    ):
        if isinstance(text, SimpleValue):
            state = text
        else:
            state = State(text)

        self._kind = kind
        self._font_size = font_size
        self._padding = padding
        self._border_width = 1  # currently this is fixed value, probably this will become variable later.
        self._line_spacing = line_spacing
        self._wrap = wrap

        super().__init__(
            state=state,
            size=Size(0, 0),
            pos=Point(0, 0),
            pos_policy=None,
            width_policy=SizePolicy.EXPANDING,
            height_policy=SizePolicy.CONTENT,
        )

    def _on_update_widget_styles(self) -> None:
        self._rect_style, self._text_style = self._get_painter_styles(
            self._kind, AppearanceState.NORMAL
        )
        self._text_style = replace_font_size(
            self._text_style, self._font_size, FontSizePolicy.FIXED
        )

    def redraw(self, p: Painter, _: bool) -> None:
        padding = self._padding
        line_spacing = self._line_spacing

        p.style(self._rect_style)
        rect = Rect(origin=Point(0, 0), size=self.get_size())
        p.fill_rect(rect)
        p.stroke_rect(rect)

        p.style(self._text_style)
        h = self._text_style.font.size
        y = h + padding
        for line in self._get_lines(p):
            p.fill_text(line, Point(padding, y), None)
            y += h + line_spacing

    def _get_lines(self, p: Painter) -> Generator[str, None, None]:
        state: SimpleValue[str] = cast(SimpleValue[str], self._state)
        text = state.value()

        if self._size.width == 0:
            yield from []

        if self._wrap and self._width_policy is not SizePolicy.CONTENT:
            # for now, support only languages like English.
            # later a little, I will add other languages support.
            line_width = self._size.width - (self._padding + self._border_width) * 2
            for line in text.splitlines():
                retval_words = []
                words_width = 0
                for word in re.split(r"(?<=\s)", line):
                    word_width = p.measure_text(word)
                    words_width += word_width
                    if words_width > line_width:
                        yield "".join(retval_words)
                        retval_words = [word]
                        words_width = word_width
                    else:
                        retval_words.append(word)
                yield "".join(retval_words)
        else:
            yield from text.splitlines()

    def measure(self, p: Painter) -> Size:
        padding = self._padding
        border_width = self._border_width
        line_spacing = self._line_spacing

        w, h = 0, 0
        p.save()
        p.style(self._text_style)
        lines = list(self._get_lines(p))
        w = max(p.measure_text(line) for line in lines) + (padding + border_width) * 2
        h = (
            self._text_style.font.size * len(lines)
            + line_spacing * (len(lines) - 1)
            + padding * 2
            + border_width * 2
        )
        p.restore()
        return Size(w, h)


class Input(Text):
    def __init__(
        self,
        text: str | InputState,
        align: TextAlign = TextAlign.LEFT,
        font_size: int | None = None,
    ):
        if isinstance(text, InputState):
            super().__init__(text, Kind.NORMAL, align, font_size)
        else:
            super().__init__(InputState(text), Kind.NORMAL, align, font_size)
        self._callback = lambda v: ...

    def redraw(self, p: Painter, _: bool) -> None:
        state: InputState = cast(InputState, self._state)

        p.style(self._rect_style)
        size = self.get_size()
        rect = Rect(origin=Point(0, 0), size=size)
        p.fill_rect(rect)
        p.stroke_rect(rect)

        width = size.width
        height = size.height
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

        cap_height = p.get_font_metrics().cap_height
        if self._align is TextAlign.CENTER:
            pos = Point(
                width / 2 - p.measure_text(str(state)) / 2,
                height / 2 + cap_height / 2,
            )
        elif self._align is TextAlign.RIGHT:
            pos = Point(
                width - p.measure_text(str(state)) - self._rect_style.padding,
                height / 2 + cap_height / 2,
            )
        else:
            pos = Point(
                self._rect_style.padding,
                height / 2 + cap_height / 2,
            )

        p.fill_text(
            text=str(state),
            pos=pos,
            max_width=width,
        )

        if state.is_in_editing():
            # fill_rect caret using get_caret_pos etc.
            caret_pos_x = p.measure_text(str(state)[: state.get_caret_pos()])
            p.style(Style(FillStyle(color="#AAAAAA")))
            p.fill_rect(
                Rect(
                    Point(
                        pos.x + caret_pos_x,
                        pos.y - cap_height - (font_size - cap_height) / 2,
                    ),
                    Size(5, font_size),
                )
            )

    def focused(self) -> None:
        state = cast(InputState, self._state)
        state.start_editing()

    def unfocused(self) -> None:
        state = cast(InputState, self._state)
        state.finish_editing()

    def input_char(self, ev: InputCharEvent) -> None:
        state = cast(InputState, self._state)
        state.insert(ev.char)
        self._callback(state.raw_value())

    def input_key(self, ev: InputKeyEvent) -> None:
        if ev.action is KeyAction.RELEASE:
            return

        state = cast(InputState, self._state)
        if ev.key is KeyCode.BACKSPACE:
            state.delete_prev()
            self._callback(state.raw_value())
        elif ev.key is KeyCode.DELETE:
            state.delete_next()
            self._callback(state.raw_value())
        elif ev.key is KeyCode.LEFT:
            state.move_to_prev()
        elif ev.key is KeyCode.RIGHT:
            state.move_to_next()

    def on_change(self, callback: Callable[[str], None]):  # -> Self:
        self._callback = callback
        return self


def determine_font(
    width: float, height: float, style: Style, text: str
) -> tuple[str, int]:
    size_of_text = len(text)
    if size_of_text == 0:
        size_of_text = 1  # to compute the height of caret

    if style.font.size_policy == FontSizePolicy.EXPANDING:
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
    def __init__(
        self,
        text: str,
        align: TextAlign = TextAlign.CENTER,
        font_size: int | None = None,
    ):
        self._on_click = lambda _: ...
        self._align = align
        self._kind = Kind.NORMAL
        self._appearance_state = AppearanceState.NORMAL
        if font_size is None:
            self._font_size = 0
            self._font_size_policy = FontSizePolicy.EXPANDING
        else:
            self._font_size = font_size
            self._font_size_policy = FontSizePolicy.FIXED
        super().__init__(
            state=ButtonState(text),
            size=Size(0, 0),
            pos=Point(0, 0),
            pos_policy=None,
            width_policy=SizePolicy.EXPANDING,
            height_policy=SizePolicy.EXPANDING,
        )

    def _on_update_widget_styles(self) -> None:
        self._style, self._text_style = self._get_painter_styles(
            self._kind, self._appearance_state
        )
        self._pushed_style, self._pushed_text_style = self._get_painter_styles(
            self._kind, AppearanceState.PUSHED
        )

        if self._font_size != 0:
            self._text_style = replace_font_size(
                self._text_style, self._font_size, FontSizePolicy.FIXED
            )
            self._pushed_text_style = replace_font_size(
                self._pushed_text_style, self._font_size, FontSizePolicy.FIXED
            )

    def mouse_down(self, ev: MouseEvent) -> None:
        state: ButtonState = cast(ButtonState, self._state)
        state.pushed(True)

    def mouse_up(self, ev: MouseEvent) -> None:
        state: ButtonState = cast(ButtonState, self._state)
        state.pushed(False)
        self._on_click(ev)

    def mouse_over(self) -> None:
        self._style, self._text_style = self._get_painter_styles(
            self._kind, AppearanceState.HOVER
        )
        self._text_style = replace_font_size(
            self._text_style, self._font_size, self._font_size_policy
        )
        self.update()

    def mouse_out(self) -> None:
        self._style, self._text_style = self._get_painter_styles(
            self._kind, AppearanceState.NORMAL
        )
        self._text_style = replace_font_size(
            self._text_style, self._font_size, self._font_size_policy
        )
        self.update()

    def on_click(self, callback: Callable[[MouseEvent], Any]):  # -> Self:
        self._on_click = callback
        return self

    def get_label(self) -> str:
        state: ButtonState = cast(ButtonState, self._state)
        return state._text

    def redraw(self, p: Painter, _: bool) -> None:
        state: ButtonState = cast(ButtonState, self._state)

        rect = Rect(origin=Point(0, 0), size=self.get_size())
        if state.is_pushed():
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
            width,
            height,
            replace(
                self._text_style,
                font=Font(
                    self._text_style.font.family,
                    self._text_style.font.size,
                    self._font_size_policy,
                ),
            ),
            state.get_text(),
        )
        p.style(
            replace(
                self._text_style,
                font=Font(
                    font_family,
                    font_size,
                    self._font_size_policy,
                ),
            ),
        )

        if self._align is TextAlign.CENTER:
            pos = Point(
                width / 2 - p.measure_text(str(state.get_text())) / 2,
                height / 2 + p.get_font_metrics().cap_height / 2,
            )
        elif self._align is TextAlign.RIGHT:
            pos = Point(
                width - p.measure_text(str(state.get_text())) - self._style.padding,
                height / 2 + p.get_font_metrics().cap_height / 2,
            )
        else:
            pos = Point(
                self._style.padding,
                height / 2 + p.get_font_metrics().cap_height / 2,
            )

        p.fill_text(
            text=state.get_text(),
            pos=pos,
            max_width=width - 2 * self._style.padding,
        )

    def width_policy(self, sp: SizePolicy):  # -> Self:
        if (
            sp is SizePolicy.CONTENT
            and self._text_style.font.size_policy is not FontSizePolicy.FIXED
        ):
            raise RuntimeError(
                "The button doesn't accept SizePolicy.CONTENT because the font size policy is not FIXED"
            )
        return super().width_policy(sp)

    def height_policy(self, sp: SizePolicy):  # -> Self:
        if (
            sp is SizePolicy.CONTENT
            and self._text_style.font.size_policy is not FontSizePolicy.FIXED
        ):
            raise RuntimeError(
                "The button doesn't accept SizePolicy.CONTENT because the font size policy is not FIXED"
            )
        return super().height_policy(sp)

    def measure(self, p: Painter) -> Size:
        p.save()
        p.style(self._text_style)
        state: State = cast(State, self._state)
        s = Size(
            p.measure_text(str(state)) + 2 * self._style.padding,
            self._text_style.font.size,
        )
        p.restore()
        return s


class Switch(Widget):
    def __init__(self, selected: bool | SimpleValue[bool]):
        self._kind = Kind.NORMAL
        self._callback = lambda _: ...
        super().__init__(
            state=selected if isinstance(selected, SimpleValue) else State(selected),
            size=Size(0, 0),
            pos=Point(0, 0),
            pos_policy=None,
            width_policy=SizePolicy.EXPANDING,
            height_policy=SizePolicy.EXPANDING,
        )

    def mouse_up(self, ev: MouseEvent) -> None:
        state = cast(SimpleValue[bool], self._state)
        new_value = not state.value()
        state.set(new_value)
        self._callback(new_value)

    def _on_update_widget_styles(self) -> None:
        self._bg_style, self._fg_style = self._get_painter_styles(
            self._kind, AppearanceState.NORMAL
        )
        self._selected_bg_style, _ = self._get_painter_styles(
            self._kind, AppearanceState.SELECTED
        )

    def redraw(self, p: Painter, _: bool) -> None:
        self._draw_background(p)
        self._draw_knob(p)

    def _draw_background(self, p: Painter) -> None:
        s = self.get_size()
        r = s.height / 2 - 0.5
        left_circle = Circle(center=Point(r, r), radius=r)
        center_rect = Rect(origin=Point(r, 0), size=s - Size(r * 2, 0))
        right_circle = Circle(center=Point(s.width - r, r), radius=r)

        state = cast(SimpleValue[bool], self._state)
        if state.value():
            p.style(self._selected_bg_style)
        else:
            p.style(self._bg_style)
        p.fill_circle(left_circle)
        p.fill_rect(center_rect)
        p.fill_circle(right_circle)

    def _draw_knob(self, p: Painter) -> None:
        s = self.get_size()
        r = s.height / 2 - 0.5
        inner_r = s.height * 0.75 / 2 - 0.5
        w = s.width
        state = cast(SimpleValue[bool], self._state)
        p.style(self._fg_style)
        if state.value():
            knob = Circle(center=Point(w - r, r), radius=inner_r)
        else:
            knob = Circle(center=Point(r, r), radius=inner_r)
        p.fill_circle(knob)

    def width_policy(self, sp: SizePolicy):  # -> Self:
        if sp is SizePolicy.CONTENT:
            raise RuntimeError("The switch doesn't accept SizePolicy.CONTENT")
        return super().width_policy(sp)

    def height_policy(self, sp: SizePolicy):  # -> Self:
        if sp is SizePolicy.CONTENT:
            raise RuntimeError("The switch doesn't accept SizePolicy.CONTENT")
        return super().height_policy(sp)

    def on_change(self, callback: Callable[[bool], None]):  # -> Self:
        self._callback = callback
        return self


class Image(Widget):
    def __init__(self, file_path: str | SimpleValue[str], use_cache: bool = True):
        if isinstance(file_path, SimpleValue):
            state = file_path
        else:
            state = State(file_path)

        self._use_cache = use_cache

        super().__init__(
            state=state,
            size=Size(0, 0),
            pos=Point(0, 0),
            pos_policy=None,
            width_policy=SizePolicy.CONTENT,
            height_policy=SizePolicy.CONTENT,
        )

    def redraw(self, p: Painter, _: bool) -> None:
        state: SimpleValue[str] = cast(SimpleValue[str], self._state)
        p.draw_image(state.value(), Rect(Point(0, 0), self.get_size()), self._use_cache)

    def measure(self, p: Painter) -> Size:
        state: SimpleValue[str] = cast(SimpleValue[str], self._state)
        return p.measure_image(state.value())


class NetImage(Widget):
    def __init__(self, url: str | SimpleValue[str], use_cache: bool = True):
        if isinstance(url, SimpleValue):
            state = url
        else:
            state = State(url)

        self._use_cache = use_cache

        super().__init__(
            state=state,
            size=Size(0, 0),
            pos=Point(0, 0),
            pos_policy=None,
            width_policy=SizePolicy.CONTENT,
            height_policy=SizePolicy.CONTENT,
        )

    def redraw(self, p: Painter, _: bool) -> None:
        state: SimpleValue[str] = cast(SimpleValue[str], self._state)
        p.draw_net_image(
            state.value(), Rect(Point(0, 0), self.get_size()), self._use_cache
        )

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
            width_policy=SizePolicy.FIXED,
            height_policy=SizePolicy.FIXED,
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

    def width_policy(self, sp: SizePolicy):  # -> Self:
        if sp is SizePolicy.CONTENT:
            raise RuntimeError("AsyncNetImage doesn't accept SizePolicy.CONTENT")
        return super().width_policy(sp)

    def height_policy(self, sp: SizePolicy):  # -> Self:
        if sp is SizePolicy.CONTENT:
            raise RuntimeError("AsyncNetImage doesn't accept SizePolicy.CONTENT")
        return super().height_policy(sp)


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
                width_policy=SizePolicy.FIXED,
                height_policy=SizePolicy.FIXED,
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

        def width_policy(self, sp: SizePolicy):
            if sp is SizePolicy.CONTENT:
                raise RuntimeError("NumpyImage doesn't accept SizePolicy.CONTENT")
            return super().width_policy(sp)

        def height_policy(self, sp: SizePolicy):
            if sp is SizePolicy.CONTENT:
                raise RuntimeError("NumpyImage doesn't accept SizePolicy.CONTENT")
            return super().height_policy(sp)

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
                width_policy=SizePolicy.CONTENT,
                height_policy=SizePolicy.CONTENT,
            )

        def redraw(self, p: Painter, _: bool) -> None:
            state: SimpleValue[np.ndarray] = cast(SimpleValue[np.ndarray], self._state)
            p.draw_np_array_as_an_image_rect(
                state.value(), Rect(Point(0, 0), self.get_size())
            )

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
        if (
            self._width_policy is SizePolicy.CONTENT
            and w.get_width_policy() is SizePolicy.EXPANDING
        ) or (
            self._height_policy is SizePolicy.CONTENT
            and w.get_height_policy() is SizePolicy.EXPANDING
        ):
            raise RuntimeError(
                "Layout with CONTENT size policy cannot have an size expandable child widget"
            )

        self._children.append(w)
        w.parent(self)

    def detach(self) -> None:
        super().detach()
        for c in self.get_children():
            c.detach()

    def remove(self, w: Widget) -> None:
        self._children.remove(w)
        w.delete_parent(self)

    def dispatch(self, p: Point) -> tuple[Widget | None, Point | None]:
        if self.contain_in_content_area(p):
            p = self._adjust_pos(p)
            for c in self._children:
                target, adjusted_p = c.dispatch(p)
                if target is not None:
                    return target, adjusted_p
            return self, p
        elif self.contain(p):
            return self, p
        else:
            return None, None

    def dispatch_to_scrollable(
        self, p: Point, is_direction_x: bool
    ) -> tuple[Widget | None, Point | None]:
        if self.contain_in_content_area(p):
            p = self._adjust_pos(p)
            for c in self._children:
                target, adjusted_p = c.dispatch_to_scrollable(p, is_direction_x)
                if target is not None:
                    return target, adjusted_p

            if self.has_scrollbar(is_direction_x):
                return self, p
            else:
                return None, None
        elif self.contain(p) and self.has_scrollbar(is_direction_x):
            return self, p
        else:
            return None, None

    @abstractmethod
    def has_scrollbar(self, is_direction_x: bool) -> bool:
        ...

    def _adjust_pos(self, p: Point) -> Point:
        return p + Point(0, 0)

    def contain_in_content_area(self, p: Point) -> bool:
        return (self._pos.x < p.x < self._pos.x + self._size.width) and (
            self._pos.y < p.y < self._pos.y + self._size.height
        )

    def redraw(self, p: Painter, completely: bool) -> None:
        p.style(self._style)
        if completely or self.is_dirty():
            p.fill_rect(Rect(origin=Point(0, 0), size=self.get_size() + Size(1, 1)))
        self._relocate_children(p)
        self._redraw_children(p, completely)

    @abstractmethod
    def _relocate_children(self, p: Painter) -> None:
        ...

    def _redraw_children(self, p: Painter, completely: bool) -> None:
        for c in self._children:
            if completely or c.is_dirty():
                p.save()
                p.translate((c.get_pos() - self.get_pos()))
                p.clip(Rect(Point(0, 0), c.get_size()))
                c.redraw(p, completely)
                p.restore()
                c.dirty(False)

    def width_policy(self, sp: SizePolicy):  # -> Self:
        if sp is SizePolicy.CONTENT and self.has_width_expandable_children():
            raise RuntimeError(
                "Layout with CONTENT size policy cannot have an size expandable child widget"
            )

        self._width_policy = sp
        return self

    def height_policy(self, sp: SizePolicy):  # -> Self:
        if sp is SizePolicy.CONTENT and self.has_height_expandable_children():
            raise RuntimeError(
                "Layout with CONTENT size policy cannot have an size expandable child widget"
            )

        self._height_policy = sp
        return self

    def has_width_expandable_children(self) -> bool:
        for c in self._children:
            if c.get_width_policy() is SizePolicy.EXPANDING:
                return True

        return False

    def has_height_expandable_children(self) -> bool:
        for c in self._children:
            if c.get_height_policy() is SizePolicy.EXPANDING:
                return True

        return False


SCROLL_BAR_SIZE = 20


class Column(Layout):
    _scrollbar_widget_style = get_theme().scrollbar
    _scrollbox_widget_style = get_theme().scrollbox
    _scrollbar_style = Style(
        FillStyle(color=_scrollbar_widget_style.bg_color),
        StrokeStyle(color=_scrollbar_widget_style.border_color),
    )
    _scrollbox_style = Style(FillStyle(color=_scrollbox_widget_style.bg_color))

    def __init__(self, *children: Widget, scrollable: bool = False):
        super().__init__(
            state=None,
            pos=Point(0, 0),
            pos_policy=None,
            size=Size(0, 0),
            height_policy=SizePolicy.EXPANDING,
            width_policy=SizePolicy.EXPANDING,
        )
        self._spacer = None
        self._spacing = 0
        self._scroll_y = 0
        self._scrollable = scrollable
        self._scroll_box = None
        self._under_dragging = False
        self._last_drag_pos = None
        for c in children:
            self.add(c)

    def add(self, w: Widget) -> None:
        if self._scrollable and w.get_height_policy() is SizePolicy.EXPANDING:
            raise RuntimeError(
                "Scrollable Column cannot have an hight expandable child widget"
            )
        super().add(w)

    def get_children(self) -> Generator[Widget, None, None]:
        if self._spacer is None:
            yield from self._children
            return

        for c in self._children:
            yield self._spacer
            yield c
        yield self._spacer

    def spacing(self, size: int):  # -> Self:
        self._spacing = size
        self._spacer = Spacer().fixed_height(size)
        return self

    def redraw(self, p: Painter, completely: bool) -> None:
        if not self._scrollable:
            self._scroll_box = None
            self._scroll_y = 0
            self._last_drag_pos = None
            self._under_dragging = False
            return super().redraw(p, completely)

        self._resize_children(p)
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
            p.fill_rect(Rect(origin=Point(0, 0), size=self.get_size() + Size(1, 1)))
        p.translate(Point(0, -self._scroll_y))

        orig_width = self.get_width()
        self._size.width -= scroll_bar_width
        self._relocate_children(p)
        self._redraw_children(p, completely)
        self._size.width = orig_width
        p.restore()

        p.save()
        p.style(Column._scrollbar_style)
        p.fill_rect(
            Rect(
                origin=Point(orig_width - scroll_bar_width, 0),
                size=Size(scroll_bar_width, self.get_height()),
            )
        )
        p.stroke_rect(
            Rect(
                origin=Point(orig_width - scroll_bar_width, -1),
                size=Size(scroll_bar_width, self.get_height() + 2),
            )
        )
        p.style(Column._scrollbox_style)
        if content_height != 0 and self.get_height() != 0:
            scroll_box_height = self.get_height() * self.get_height() / content_height
            scroll_box = Rect(
                origin=Point(
                    orig_width - scroll_bar_width,
                    (self._scroll_y / content_height) * self.get_height(),
                ),
                size=Size(scroll_bar_width, scroll_box_height),
            )
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
            self.scroll_y(
                int(
                    (ev.pos.y - last_drag_pos.y)
                    * (self.content_height() / self.get_height())
                )
            )

    def mouse_wheel(self, ev: WheelEvent) -> None:
        self.scroll_y(int(ev.y_offset))

    def has_scrollbar(self, is_direction_x: bool) -> bool:
        return (not is_direction_x) and self._scroll_box is not None

    def scroll_y(self, y: int):  # -> Self:
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
        height = functools.reduce(
            lambda total, child: total + child.measure(p).height, self.get_children(), 0
        )
        return Size(width, height)

    def content_height(self) -> float:
        return functools.reduce(
            lambda total, child: total + child.get_height(), self.get_children(), 0
        )

    def _adjust_pos(self, p: Point) -> Point:
        return p + Point(0, self._scroll_y)

    def contain_in_content_area(self, p: Point) -> bool:
        if self._scrollable and self.content_height() > self.get_height():
            return (
                self._pos.x < p.x < self._pos.x + self._size.width - SCROLL_BAR_SIZE
            ) and (self._pos.y < p.y < self._pos.y + self._size.height)
        return self.contain_in_my_area(p)

    def contain_in_my_area(self, p: Point) -> bool:
        return (self._pos.x < p.x < self._pos.x + self._size.width) and (
            self._pos.y < p.y < self._pos.y + self._size.height
        )

    def _relocate_children(self, p: Painter) -> None:
        self._resize_children(p)
        self._move_children()

    def _resize_children(self, p: Painter) -> None:
        if len(self._children) == 0:
            return

        remaining_height = self.get_height()
        remaining_children: list[Widget] = []
        total_flex = 0

        for c in self.get_children():
            hp = c.get_height_policy()
            if hp is SizePolicy.CONTENT:
                c.height(c.measure(p).height)

            if hp is SizePolicy.EXPANDING:
                remaining_children.append(c)
                total_flex = total_flex + c.get_flex()
            else:
                remaining_height = remaining_height - c.get_height()

        fraction = (
            remaining_height % total_flex
            if remaining_height > 0 and total_flex > 0
            else 0
        )
        for rc in remaining_children:
            flex = rc.get_flex()
            height = (remaining_height * flex) / total_flex
            if fraction > 0:
                height += flex
                fraction -= flex
            rc.height(int(height))

        for c in self.get_children():
            match c.get_width_policy():
                case SizePolicy.EXPANDING:
                    c.width(self.get_width())
                case SizePolicy.CONTENT:
                    c.width(c.measure(p).width)

    def _move_children(self) -> None:
        acc_y = self.get_pos().y
        for c in self.get_children():
            c.move_y(acc_y)
            acc_y += c.get_height()
            c.move_x(self.get_pos().x)


class Row(Layout):
    _scrollbar_widget_style = get_theme().scrollbar
    _scrollbox_widget_style = get_theme().scrollbox
    _scrollbar_style = Style(
        FillStyle(color=_scrollbar_widget_style.bg_color),
        StrokeStyle(color=_scrollbar_widget_style.border_color),
    )
    _scrollbox_style = Style(FillStyle(color=_scrollbox_widget_style.bg_color))

    def __init__(self, *children: Widget, scrollable: bool = False):
        super().__init__(
            state=None,
            pos=Point(0, 0),
            pos_policy=None,
            size=Size(0, 0),
            width_policy=SizePolicy.EXPANDING,
            height_policy=SizePolicy.EXPANDING,
        )
        self._spacer = None
        self._spacing = 0
        self._scroll_x = 0
        self._scrollable = scrollable
        self._scroll_box = None
        self._under_dragging = False
        self._last_drag_pos = None
        for c in children:
            self.add(c)

    def add(self, w: Widget) -> None:
        if self._scrollable and w.get_width_policy() is SizePolicy.EXPANDING:
            raise RuntimeError(
                "Scrollable Row cannot have an width expandable child widget"
            )
        super().add(w)

    def get_children(self) -> Generator[Widget, None, None]:
        if self._spacer is None:
            yield from self._children
            return

        for c in self._children:
            yield self._spacer
            yield c
        yield self._spacer

    def spacing(self, size: int):  # -> Self:
        self._spacing = size
        self._spacer = Spacer().fixed_width(size)
        return self

    def redraw(self, p: Painter, completely: bool) -> None:
        if not self._scrollable:
            self._scroll_box = None
            self._scroll_x = 0
            self._last_drag_pos = None
            self._under_dragging = False
            return super().redraw(p, completely)

        self._resize_children(p)
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
            p.fill_rect(Rect(origin=Point(0, 0), size=self.get_size() + Size(1, 1)))
        p.translate(Point(-self._scroll_x, 0))

        orig_height = self.get_height()
        self._size.height -= scroll_bar_height
        self._relocate_children(p)
        self._redraw_children(p, completely)
        self._size.height = orig_height
        p.restore()

        p.save()
        p.style(Row._scrollbar_style)
        p.fill_rect(
            Rect(
                origin=Point(0, orig_height - scroll_bar_height),
                size=Size(self.get_width(), scroll_bar_height),
            )
        )
        p.stroke_rect(
            Rect(
                origin=Point(-1, orig_height - scroll_bar_height),
                size=Size(self.get_width() + 2, scroll_bar_height),
            )
        )
        p.style(Row._scrollbox_style)
        if content_width != 0 and self.get_width() != 0:
            scroll_box_width = self.get_width() * self.get_width() / content_width
            scroll_box = Rect(
                origin=Point(
                    (self._scroll_x / content_width) * self.get_width(),
                    orig_height - scroll_bar_height,
                ),
                size=Size(scroll_box_width, scroll_bar_height),
            )
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
            self.scroll_x(
                int(
                    (ev.pos.x - last_drag_pos.x)
                    * (self.content_width() / self.get_width())
                )
            )

    def mouse_wheel(self, ev: WheelEvent) -> None:
        self.scroll_x(int(ev.x_offset))

    def has_scrollbar(self, is_direction_x: bool) -> bool:
        return is_direction_x and self._scroll_box is not None

    def scroll_x(self, x: int):  # -> Self:
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
        width = functools.reduce(
            lambda total, child: total + child.measure(p).width, self.get_children(), 0
        )
        height = max((0, *map(lambda c: c.measure(p).height, self.get_children())))
        return Size(width, height)

    def content_width(self) -> float:
        return functools.reduce(
            lambda total, child: total + child.get_width(), self.get_children(), 0
        )

    def _adjust_pos(self, p: Point) -> Point:
        return p + Point(self._scroll_x, 0)

    def contain_in_content_area(self, p: Point) -> bool:
        if self._scrollable and self.content_width() > self.get_width():
            return (self._pos.x < p.x < self._pos.x + self._size.width) and (
                self._pos.y < p.y < self._pos.y + self._size.height - SCROLL_BAR_SIZE
            )
        return self.contain_in_my_area(p)

    def contain_in_my_area(self, p: Point) -> bool:
        return (self._pos.x < p.x < self._pos.x + self._size.width) and (
            self._pos.y < p.y < self._pos.y + self._size.height
        )

    def _relocate_children(self, p: Painter) -> None:
        self._resize_children(p)
        self._move_children()

    def _resize_children(self, p: Painter) -> None:
        if len(self._children) == 0:
            return

        remaining_width = self.get_width()
        remaining_children: list[Widget] = []
        total_flex = 0

        for c in self.get_children():
            wp = c.get_width_policy()
            if wp is SizePolicy.CONTENT:
                c.width(c.measure(p).width)

            if wp is SizePolicy.EXPANDING:
                remaining_children.append(c)
                total_flex = total_flex + c.get_flex()
            else:
                remaining_width = remaining_width - c.get_width()

        fraction = (
            remaining_width % total_flex
            if remaining_width > 0 and total_flex > 0
            else 0
        )
        for rc in remaining_children:
            flex = rc.get_flex()
            width = (remaining_width * flex) / total_flex
            if fraction > 0:
                width += flex
                fraction -= flex
            rc.width(int(width))

        for c in self.get_children():
            match c.get_height_policy():
                case SizePolicy.EXPANDING:
                    c.height(self.get_height())
                case SizePolicy.CONTENT:
                    c.height(c.measure(p).height)

    def _move_children(self) -> None:
        acc_x = self.get_pos().x
        for c in self.get_children():
            c.move_x(acc_x)
            acc_x += c.get_width()
            c.move_y(self.get_pos().y)


class Box(Layout):
    _scrollbar_widget_style = get_theme().scrollbar
    _scrollbox_widget_style = get_theme().scrollbox
    _scrollbar_style = Style(
        FillStyle(color=_scrollbar_widget_style.bg_color),
        StrokeStyle(color=_scrollbar_widget_style.border_color),
    )
    _scrollbox_style = Style(FillStyle(color=_scrollbox_widget_style.bg_color))

    def __init__(self, child: Widget):
        super().__init__(
            state=None,
            pos=Point(0, 0),
            pos_policy=None,
            size=Size(0, 0),
            width_policy=SizePolicy.EXPANDING,
            height_policy=SizePolicy.EXPANDING,
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

    def add(self, w: Widget) -> None:
        if len(self._children) > 0:
            raise RuntimeError("Box cannot have more than 1 child widget")
        super().add(w)

    def redraw(self, p: Painter, completely: bool) -> None:
        self_size = self._size
        self_height = self_size.height
        self_width = self_size.width
        if self_width == 0 or self_height == 0:
            return

        c = self._child
        self._resize_children(p)
        content_width, content_height = self.content_size()
        x_scroll_bar_height = 0
        y_scroll_bar_width = 0

        if content_width > self_width - y_scroll_bar_width:
            x_scroll_bar_height = SCROLL_BAR_SIZE

        if content_height > self_height - x_scroll_bar_height:
            y_scroll_bar_width = SCROLL_BAR_SIZE

        if content_width > self_width - y_scroll_bar_width:
            x_scroll_bar_height = SCROLL_BAR_SIZE

        if c.get_width_policy() is SizePolicy.EXPANDING or x_scroll_bar_height == 0:
            self._scroll_x = 0
            self._scroll_box_x = None
            x_scroll_bar_height = 0

        if c.get_height_policy() is SizePolicy.EXPANDING or y_scroll_bar_width == 0:
            self._scroll_y = 0
            self._scroll_box_y = None
            y_scroll_bar_width = 0

        p.save()
        p.style(self._style)
        if completely or self.is_dirty():
            p.fill_rect(Rect(origin=Point(0, 0), size=self_size + Size(1, 1)))

        p.translate(
            Point(
                -self._scroll_x * (self_width + y_scroll_bar_width) / self_size.width,
                -self._scroll_y
                * (self_height + x_scroll_bar_height)
                / self_size.height,
            )
        )
        self._size.height -= x_scroll_bar_height
        self._size.width -= y_scroll_bar_width
        self._relocate_children(p)
        self._redraw_children(p, completely)
        self._size.height = self_height
        self._size.width = self_width
        p.restore()

        p.save()
        if x_scroll_bar_height > 0:
            p.style(Box._scrollbar_style)
            p.fill_rect(
                Rect(
                    origin=Point(0, self_height - x_scroll_bar_height),
                    size=Size(self_width - y_scroll_bar_width, x_scroll_bar_height),
                )
            )
            p.stroke_rect(
                Rect(
                    origin=Point(0, self_height - x_scroll_bar_height),
                    size=Size(self_width - y_scroll_bar_width, x_scroll_bar_height),
                )
            )
            p.style(Box._scrollbox_style)
            if content_width != 0 and self_width != 0:
                scroll_box_width = (
                    self_width - y_scroll_bar_width
                ) ** 2 / content_width
                scroll_box = Rect(
                    origin=Point(
                        (self._scroll_x / content_width)
                        * (self_width - y_scroll_bar_width),
                        self_height - x_scroll_bar_height,
                    ),
                    size=Size(scroll_box_width, x_scroll_bar_height),
                )
                self._scroll_box_x = scroll_box
                p.fill_rect(scroll_box)

        if y_scroll_bar_width > 0:
            p.style(Box._scrollbar_style)
            p.fill_rect(
                Rect(
                    origin=Point(self_width - y_scroll_bar_width, 0),
                    size=Size(y_scroll_bar_width, self_height - x_scroll_bar_height),
                )
            )
            p.stroke_rect(
                Rect(
                    origin=Point(self_width - y_scroll_bar_width, 0),
                    size=Size(y_scroll_bar_width, self_height - x_scroll_bar_height),
                )
            )
            p.style(Box._scrollbox_style)
            if content_height != 0 and self_height != 0:
                scroll_box_height = (
                    self_height - x_scroll_bar_height
                ) ** 2 / content_height
                scroll_box = Rect(
                    origin=Point(
                        self_width - y_scroll_bar_width,
                        (self._scroll_y / content_height)
                        * (self_height - x_scroll_bar_height),
                    ),
                    size=Size(y_scroll_bar_width, scroll_box_height),
                )
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
            self.scroll_x(w, int((ev.pos.x - last_drag_pos.x) * (w / self.get_width())))
        elif self._under_dragging_y:
            self.scroll_y(
                h, int((ev.pos.y - last_drag_pos.y) * (h / self.get_height()))
            )

    def mouse_wheel(self, ev: WheelEvent) -> None:
        w, h = self.content_size()
        if ev.x_offset != 0:
            self.scroll_x(w, int(ev.x_offset))
        if ev.y_offset != 0:
            self.scroll_y(h, int(ev.y_offset))

    def has_scrollbar(self, is_direction_x: bool) -> bool:
        if is_direction_x:
            return self._scroll_box_x is not None
        else:
            return self._scroll_box_y is not None

    def scroll_x(self, w: float, x: int):  # -> Self:
        if x > 0:
            max_scroll_x = (
                w
                - self.get_width()
                + (0 if self._scroll_box_y is None else SCROLL_BAR_SIZE)
            )
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

    def scroll_y(self, h: float, y: int):  # -> Self:
        if y > 0:
            max_scroll_y = (
                h
                - self.get_height()
                + (0 if self._scroll_box_x is None else SCROLL_BAR_SIZE)
            )
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
        return functools.reduce(
            lambda total, child: (
                total[0] + child.get_width(),
                total[1] + child.get_height(),
            ),
            self.get_children(),
            (0, 0),
        )

    def _adjust_pos(self, p: Point) -> Point:
        return p + Point(self._scroll_x, self._scroll_y)

    def contain_in_content_area(self, p: Point) -> bool:
        w, h = self.content_size()
        return (
            self._pos.x
            < p.x
            < self._pos.x
            + self._size.width
            - (0 if self._scroll_box_y is None else SCROLL_BAR_SIZE)
        ) and (
            self._pos.y
            < p.y
            < self._pos.y
            + self._size.height
            - (0 if self._scroll_box_x is None else SCROLL_BAR_SIZE)
        )

    def contain_in_my_area(self, p: Point) -> bool:
        return (self._pos.x < p.x < self._pos.x + self._size.width) and (
            self._pos.y < p.y < self._pos.y + self._size.height
        )

    def _relocate_children(self, p: Painter) -> None:
        self._resize_children(p)
        self._move_children()

    def _resize_children(self, p: Painter) -> None:
        if len(self._children) == 0:
            return

        c = self._child
        match c.get_width_policy():
            case SizePolicy.CONTENT:
                c.width(c.measure(p).width)
            case SizePolicy.EXPANDING:
                c.width(self.get_width())

        match c.get_height_policy():
            case SizePolicy.CONTENT:
                c.height(c.measure(p).height)
            case SizePolicy.EXPANDING:
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
            width_policy=SizePolicy.EXPANDING,
            height_policy=SizePolicy.EXPANDING,
        )
        self._child = None

    def _relocate_children(self, p: Painter) -> None:
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

    def has_scrollbar(self, is_direction_x: bool) -> bool:
        return False

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


class StatefulComponent(Component, ABC):
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
        self._mouse_overed_layer = None
        self._prev_rel_pos = None
        self._prev_abs_pos = None
        self._frame = frame
        self._downed: Optional[Widget] = None
        self._focused: Optional[Widget] = None
        self._mouse_overed: Optional[Widget] = None
        self._layers: list[Widget] = []
        self._layerPositions: list[PositionPolicy] = []
        self._style = Style(fill=FillStyle(color=get_theme().app.bg_color))
        self.push_layer(widget, PositionPolicy.FIXED)

    @classmethod
    def get(cls):  # -> Self:
        return cls._instance

    def push_layer(self, l: Widget, p: PositionPolicy):  # -> Self:
        self._layers.append(l)
        self._layerPositions.append(p)
        self._frame.post_update(UpdateEvent(self, True))
        return self

    def pop_layer(self):  # -> Self:
        self._layers.pop()
        self._layerPositions.pop()
        self._frame.post_update(UpdateEvent(self, True))
        return self

    def peek_layer(self) -> tuple[Widget, PositionPolicy]:
        return self._layers[-1], self._layerPositions[-1]

    def mouse_down(self, ev: MouseEvent) -> None:
        target, p = self.peek_layer()[0].dispatch(ev.pos)
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
            ev.pos = self._prev_rel_pos + diff
            self._prev_rel_pos = ev.pos
            self._downed.mouse_up(ev)
        finally:
            self._downed = None

    def mouse_wheel(self, ev: WheelEvent) -> None:
        target, _ = self.peek_layer()[0].dispatch_to_scrollable(
            ev.pos, abs(ev.x_offset) > abs(ev.y_offset)
        )
        if target is not None:
            target.mouse_wheel(ev)

    def cursor_pos(self, ev: MouseEvent) -> None:
        layer = self.peek_layer()[0]
        target, p = layer.dispatch(ev.pos)
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
        elif (
            target is self._downed or self._downed.dispatch(ev.pos)[0] is not None
        ) and p is not None:
            diff = ev.pos - self._prev_abs_pos
            self._prev_abs_pos = ev.pos
            ev.pos = self._prev_rel_pos + diff
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
        p.fill_rect(Rect(origin=Point(0, 0), size=self._frame.get_size() + Size(1, 1)))
        for i in range(len(self._layers)):
            l = self._layers[i]
            pos = self._layerPositions[i]
            self._relocate_layout(l, pos)
            if completely or l.is_dirty():
                p.save()
                p.translate(l.get_pos())
                p.clip(Rect(Point(0, 0), l.get_size()))
                l.redraw(p, completely)
                p.restore()
                l.dirty(False)
        p.flush()

    def _relocate_layout(self, w: Widget, p: PositionPolicy) -> None:
        if w is None:
            return

        frame_size = self._frame.get_size()
        latest_size = w.get_size()
        width_policy = w.get_width_policy()
        height_policy = w.get_height_policy()

        if height_policy is SizePolicy.EXPANDING:
            height = frame_size.height
        else:
            height = latest_size.height

        if width_policy is SizePolicy.EXPANDING:
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

    def post_update(self, w: Widget, completely: bool = False) -> None:
        self._frame.post_update(UpdateEvent(w, completely))

    def run(self) -> None:
        self._frame.on_mouse_down(self.mouse_down)
        self._frame.on_mouse_up(self.mouse_up)
        self._frame.on_mouse_wheel(self.mouse_wheel)
        self._frame.on_cursor_pos(self.cursor_pos)
        self._frame.on_input_char(self.input_char)
        self._frame.on_input_key(self.input_key)
        self._frame.on_redraw(self.redraw)
        self._frame.run()
