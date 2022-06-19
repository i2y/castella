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
    runtime_checkable,
)

import numpy as np

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
        return (self.origin.x <= p.x <= self.origin.x + self.size.width) and (
            self.origin.y <= p.y <= self.origin.y + self.size.height
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


def replace_font_size(style: Style, size: float, policy: FontSizePolicy) -> Style:
    return replace(style, font=replace(style.font, size=size, size_policy=policy))


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


SCROLL_BAR_SIZE = 20


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
