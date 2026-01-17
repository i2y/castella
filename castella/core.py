"""Castella core module - widgets, layouts, and application framework."""

from __future__ import annotations

from abc import ABC, abstractmethod
from asyncio import Future
from collections.abc import Iterable
from copy import deepcopy
from dataclasses import replace
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Generator,
    Generic,
    Optional,
    Protocol,
    Self,
    TypeVar,
    runtime_checkable,
)

from pydantic import BaseModel, ConfigDict

if TYPE_CHECKING:
    from castella.chart.models.animation import EasingFunction
    from castella.events import EventManager
    from castella.render import LayoutRenderNode, RenderNode

# Re-exports for backward compatibility
from castella.models.font import EM, Font, FontMetrics, FontSizePolicy  # noqa: F401

# Import from new modules
from castella.models.geometry import Point, Size, Rect, Circle
from castella.models.style import (
    SizePolicy,
    PositionPolicy,
    FillStyle,
    StrokeStyle,
    Style,
    TextAlign,  # noqa: F401
)
from castella.models.events import (
    IMEPreeditEvent,
    KeyAction,  # noqa: F401
    KeyCode,  # noqa: F401
    MouseEvent,
    WheelEvent,
    InputCharEvent,
    InputKeyEvent,
    UpdateEvent,
)

try:
    import numpy as np
except ImportError:
    pass

from .theme import (
    Theme,
    ThemeManager,
    WidgetStyle,
    Kind,
    AppearanceState,
)


class Painter(Protocol):
    def clear_all(self, color: Optional[str] = None) -> None: ...

    def fill_rect(self, rect: Rect) -> None: ...

    def stroke_rect(self, rect: Rect) -> None: ...

    def fill_circle(self, circle: Circle) -> None: ...

    def stroke_circle(self, circle: Circle) -> None: ...

    def translate(self, pos: Point) -> None: ...

    def clip(self, rect: Rect) -> None: ...

    def fill_text(self, text: str, pos: Point, max_width: Optional[float]) -> None: ...

    def stroke_text(
        self, text: str, pos: Point, max_width: Optional[float]
    ) -> None: ...

    def measure_text(self, text: str) -> float: ...

    def get_font_metrics(self) -> FontMetrics: ...

    def draw_image(
        self, file_path: str, rect: Rect, use_cache: bool = True
    ) -> None: ...

    def measure_image(self, file_path: str, use_cache: bool = True) -> Size: ...

    def draw_net_image(self, url: str, rect: Rect, use_cache: bool = True) -> None: ...

    def measure_net_image(self, url: str, use_cache: bool = True) -> Size: ...

    def measure_np_array_as_an_image(self, array: "np.ndarray") -> Size: ...

    def get_net_image_async(self, name: str, url: str, callback): ...

    def get_numpy_image_async(self, array: "np.ndarray", callback): ...

    def draw_image_object(self, img, x: float, y: float) -> None: ...

    def draw_np_array_as_an_image(
        self, array: "np.ndarray", x: float, y: float
    ) -> None: ...

    def draw_np_array_as_an_image_rect(
        self, array: "np.ndarray", rect: Rect
    ) -> None: ...

    def save(self) -> None: ...

    def restore(self) -> None: ...

    def style(self, style: Style) -> None: ...

    def flush(self) -> None: ...


@runtime_checkable
class CaretDrawable(Protocol):
    def draw_caret(self, pos: Point, height: int) -> None: ...


class Frame(Protocol):
    def __init__(self, title: str, width: float = 0, height: float = 0) -> None: ...

    def on_mouse_down(self, handler: Callable[[MouseEvent], None]) -> None: ...

    def on_mouse_up(self, handler: Callable[[MouseEvent], None]) -> None: ...

    def on_mouse_wheel(self, handler: Callable[[WheelEvent], None]) -> None: ...

    def on_cursor_pos(self, handler: Callable[[MouseEvent], None]) -> None: ...

    def on_input_char(self, handler: Callable[[InputCharEvent], None]) -> None: ...

    def on_input_key(self, handler: Callable[[InputKeyEvent], None]) -> None: ...

    def on_redraw(self, handler: Callable[[Painter, bool], None]) -> None: ...

    def get_painter(self) -> Painter: ...

    def get_size(self) -> Size: ...

    def post_update(self, ev: "UpdateEvent") -> None: ...

    def flush(self) -> None: ...

    def clear(self) -> None: ...

    def run(self) -> None: ...

    def get_clipboard_text(self) -> str: ...

    def set_clipboard_text(self, text: str) -> None: ...

    def async_get_clipboard_text(
        self, callback: Callable[[Future[str]], None]
    ) -> None: ...

    def async_set_clipboard_text(
        self, text: str, callback: Callable[[Future], None]
    ) -> None: ...


class Observer(Protocol):
    def on_attach(self, o: "ObservableBase") -> None: ...

    def on_detach(self, o: "ObservableBase") -> None: ...

    def on_notify(self, event: Any = None) -> None: ...


class Observable(Protocol):
    def attach(self, observer: Observer) -> None: ...

    def detach(self, observer: Observer) -> None: ...

    def notify(self, event: Any = None) -> None: ...


class UpdateListener:
    __slots__ = ["_observable", "_callback"]

    def __init__(self, callback: Callable[[Any], None]):
        self._observable = None
        self._callback = callback

    def on_attach(self, o: "ObservableBase"):
        self._observable = o

    def on_detach(self, o: "ObservableBase"):
        del self._observable

    def on_notify(self, event: Any = None):
        self._callback(event)


class ObservableBase(ABC):
    def __init__(self) -> None:
        self._observers: list[Observer] = []

    def attach(self, observer: Observer) -> None:
        self._observers.append(observer)
        observer.on_attach(self)

    def detach(self, observer: Observer) -> None:
        if observer in self._observers:
            self._observers.remove(observer)
            observer.on_detach(self)

    def notify(self, event: Any = None) -> None:
        # Iterate over a copy to avoid issues if observers are modified during notification
        for o in list(self._observers):
            # Skip if observer was detached during iteration
            if o in self._observers:
                o.on_notify(event)

    def on_update(self, callback: Callable) -> None:
        self.attach(UpdateListener(callback))


V = TypeVar("V")


@runtime_checkable
class SimpleValue(Observable, Protocol[V]):
    def set(self, value: V): ...

    def value(self) -> V: ...


def get_zero_value(type_hint):
    if type_hint is int:
        return 0
    elif type_hint is float:
        return 0.0
    elif type_hint is bool:
        return False
    elif type_hint is str:
        return ""
    elif hasattr(type_hint, "__origin__") and type_hint.__origin__ is list:
        return []
    elif hasattr(type_hint, "__origin__") and type_hint.__origin__ is dict:
        return {}
    # 他の型のゼロ値を追加可能
    return None


class Model(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    def __init__(self, **data):
        super().__init__(**data)
        for name in self.model_fields:
            value = getattr(self, name)
            if not isinstance(value, State):
                wrapped_value = State(value)
                super().__setattr__(name, wrapped_value)

    def __setattr__(self, name, value):
        if name in self.model_fields:
            current_value = getattr(self, name, None)
            if isinstance(current_value, State):
                current_value.set(value)
            else:
                super().__setattr__(name, State(value))
        else:
            super().__setattr__(name, value)


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
        self._z_index: int = 1
        self._tab_index: int = 0
        self._dirty = True
        self._semantic_id_hint: str | None = None
        self._enable_to_detach = True
        self._parent: Self | None = None
        self._depth: int = 0  # Depth in widget tree (0 = root)
        self._mounted: bool = False  # Lifecycle: mounted to tree
        self._cached: bool = False  # Protected from unmount during rebuild
        self._render_node: "RenderNode | None" = None  # Lazy initialized
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
    ) -> Self:
        styles = self._widget_styles
        style_name = f"{kind.value}{state.value}".format(kind, state)
        styles[style_name] = new_style
        self._on_update_widget_styles()
        self.mark_paint_dirty()  # Style change only needs repaint
        return self

    def bg_color(self, rgb: str) -> Self:
        return self.change_style(
            Kind.NORMAL,
            AppearanceState.NORMAL,
            replace(
                self._get_widget_style(Kind.NORMAL, AppearanceState.NORMAL),
                bg_color=rgb,
            ),
        )

    def text_color(self, rgb: str) -> Self:
        return self.change_style(
            Kind.NORMAL,
            AppearanceState.NORMAL,
            replace(
                self._get_widget_style(Kind.NORMAL, AppearanceState.NORMAL),
                text_color=rgb,
            ),
        )

    def fg_color(self, rgb: str) -> Self:
        return self.text_color(rgb)

    def border_color(self, rgb: str) -> Self:
        return self.change_style(
            Kind.NORMAL,
            AppearanceState.NORMAL,
            replace(
                self._get_widget_style(Kind.NORMAL, AppearanceState.NORMAL),
                border_color=rgb,
            ),
        )

    def erase_border(self) -> Self:
        return self.border_color(
            self._get_widget_style(Kind.NORMAL, AppearanceState.NORMAL).bg_color
        )

    def show_border(self, color: str | None = None) -> Self:
        """Show border with specified or theme default color."""
        if color is None:
            color = self._get_widget_style(
                Kind.NORMAL, AppearanceState.NORMAL
            ).border_color
        return self.border_color(color)

    def _on_update_widget_styles(self) -> None:
        pass

    @staticmethod
    def _convert_widget_style_to_painter_styles(
        widget_style: "WidgetStyle",
    ) -> tuple[Style, Style]:
        return (
            Style(
                fill=FillStyle(color=widget_style.bg_color),
                stroke=StrokeStyle(color=widget_style.border_color),
                border_radius=widget_style.border_radius,
                shadow=widget_style.shadow,
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
            # Return position relative to this widget's origin
            local_p = Point(x=p.x - self._pos.x, y=p.y - self._pos.y)
            return self, local_p
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

    def on_notify(self, event: Any = None) -> None:
        self.dirty(True)
        self.update()

    def detach(self) -> None:
        # Call unmount lifecycle hook
        self._do_unmount()
        if self._enable_to_detach:
            # Create a copy to avoid modification during iteration
            # (on_detach removes from self._observable)
            for o in list(self._observable):
                o.detach(self)
        # Clear any App-level references to this widget to prevent
        # ghost redraws after the widget is removed from the tree
        app = App.get()
        if app is not None:
            if app._mouse_overed is self:
                app._mouse_overed = None
            if app._focused is self:
                app._focused = None
            if app._downed is self:
                app._downed = None

    # ========== Lifecycle Hooks ==========

    def on_mount(self) -> None:
        """Called when widget is mounted to the tree.

        Override this method to perform initialization that requires
        the widget to be in the tree (e.g., starting timers, subscriptions).
        """
        pass

    def on_unmount(self) -> None:
        """Called when widget is about to be unmounted from the tree.

        Override this method to perform cleanup (e.g., stopping timers,
        unsubscribing from events, releasing resources).
        """
        pass

    def _do_mount(self, parent: Self | None) -> None:
        """Internal: Perform mount operations."""
        if not self._mounted:
            self._mounted = True
            self._parent = parent
            self._depth = parent._depth + 1 if parent else 0
            self.on_mount()
        else:
            # Already mounted - just update parent (for cached widgets being re-parented)
            self._parent = parent
            self._depth = parent._depth + 1 if parent else 0

    def _do_unmount(self) -> None:
        """Internal: Perform unmount operations."""
        # Skip unmount for cached widgets (they're being reused in new layout)
        if self._cached:
            return
        if self._mounted:
            self.on_unmount()
            self._mounted = False

    def is_mounted(self) -> bool:
        """Check if widget is currently mounted to the tree."""
        return self._mounted

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

    def cursor_pos(self, ev: MouseEvent) -> None:
        """Called when cursor moves within the widget."""
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
    def redraw(self, p: Painter, completely: bool) -> None: ...

    def is_dirty(self) -> bool:
        """Check if widget needs repainting."""
        if self._render_node is not None:
            return self._render_node.is_paint_dirty()
        return self._dirty

    def is_layout_dirty(self) -> bool:
        """Check if widget needs layout recalculation."""
        if self._render_node is not None:
            return self._render_node.is_layout_dirty()
        return self._dirty

    def dirty(self, flag: bool) -> None:
        """Set dirty flag (for backward compatibility)."""
        self._dirty = flag
        if self._render_node is not None:
            if flag:
                self._render_node.mark_paint_dirty()
            else:
                self._render_node.clear_dirty()

    def mark_layout_dirty(self) -> None:
        """Mark layout as needing recalculation (implies paint dirty)."""
        self._dirty = True
        if self._render_node is not None:
            self._render_node.mark_layout_dirty()

    def mark_paint_dirty(self) -> None:
        """Mark as needing repaint without affecting layout."""
        self._dirty = True
        if self._render_node is not None:
            self._render_node.mark_paint_dirty()

    def move(self, p: Point) -> Self:
        if p != self._pos:
            self._pos = p
            self.mark_layout_dirty()
        return self

    def move_x(self, x: float) -> Self:
        if x != self._pos.x:
            self._pos.x = x
            self.mark_layout_dirty()
        return self

    def move_y(self, y: float) -> Self:
        if y != self._pos.y:
            self._pos.y = y
            self.mark_layout_dirty()
        return self

    def resize(self, s: Size) -> Self:
        if s != self._size:
            self._size = s
            self.mark_layout_dirty()
        return self

    def width(self, w: float) -> Self:
        if w != self._size.width:
            self._size.width = w
            self.mark_layout_dirty()
        return self

    def get_width(self) -> float:
        return self._size.width

    def height(self, h: float) -> Self:
        if h != self._size.height:
            self._size.height = h
            self.mark_layout_dirty()
        return self

    def get_height(self) -> float:
        return self._size.height

    def get_pos(self) -> Point:
        return self._pos

    def pos(self, pos: Point) -> Self:
        if pos != self._pos:
            self._pos = pos
            self.mark_layout_dirty()
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
            # Any scrollable parent or Box with multiple children needs complete redraw
            if parent.is_scrollable() or isinstance(parent, StatefulComponent):
                root = parent
            parent = parent._parent

        app = App.get()
        if app is None:
            return

        if root is None:
            App.get().post_update(
                self,
                completely
                or self.is_scrollable()
                or isinstance(self, StatefulComponent),
            )
        else:
            # Force complete redraw for proper z-index handling
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

    def width_policy(self, sp: SizePolicy) -> Self:
        self._width_policy = sp
        return self

    def get_height_policy(self) -> SizePolicy:
        return self._height_policy

    def height_policy(self, sp: SizePolicy) -> Self:
        self._height_policy = sp
        return self

    def get_flex(self) -> int:
        return self._flex

    def flex(self, flex: int) -> Self:
        self._flex = flex
        return self

    def get_z_index(self) -> int:
        """Get the z-index of this widget (default: 1)."""
        return self._z_index

    def z_index(self, z: int) -> Self:
        """Set the z-index of this widget. Must be a positive integer."""
        if z < 1:
            raise ValueError("z_index must be a positive integer (>= 1)")
        self._z_index = z
        # Invalidate parent's z-order cache if parent is a Layout
        if self._parent is not None:
            parent_node = self._parent._render_node
            if parent_node is not None and hasattr(parent_node, "invalidate_z_order"):
                parent_node.invalidate_z_order()
        return self

    def tab_index(self, value: int) -> Self:
        """Set the tab order for this widget (lower = earlier in Tab sequence).

        Widgets with a lower tab_index receive focus before widgets with
        a higher tab_index when the user presses Tab.

        Args:
            value: The tab order value (0 or greater).

        Returns:
            Self for method chaining.
        """
        self._tab_index = value
        return self

    def get_tab_index(self) -> int:
        """Get the tab order value."""
        return self._tab_index

    def get_semantic_id_hint(self) -> str | None:
        return self._semantic_id_hint

    def semantic_id(self, hint: str) -> Self:
        """Set a semantic ID hint for MCP accessibility.

        This hint is used by CastellaMCPServer to provide a stable,
        human-readable identifier for this widget that persists across
        view rebuilds.

        Args:
            hint: A short, descriptive identifier (e.g., "submit-btn", "email-input")

        Returns:
            Self for method chaining
        """
        self._semantic_id_hint = hint
        return self

    def parent(self, parent: Self) -> None:
        """Set parent and trigger mount lifecycle."""
        self._do_mount(parent)

    def get_depth(self) -> int:
        """Get the depth of this widget in the tree (0 = root)."""
        return self._depth

    @property
    def render_node(self) -> "RenderNode":
        """Get the render node for this widget (lazy initialized).

        The render node handles layout and paint operations.
        Override _create_render_node() to customize behavior.
        """
        if self._render_node is None:
            self._render_node = self._create_render_node()
        return self._render_node

    def _create_render_node(self) -> "RenderNode":
        """Create the render node for this widget.

        Override this method to provide a custom RenderNode.
        The default implementation returns a RenderNodeBase
        that delegates all operations to the widget.

        Returns:
            A RenderNode instance.
        """
        from castella.render import RenderNodeBase

        return RenderNodeBase(self)

    def get_parent(self) -> Self | None:
        return self._parent

    def delete_parent(self, parent: Self) -> None:
        if self._parent is parent:
            self._parent = None

    def ask_parent_to_render(self, completely: bool = False) -> None:
        if self._parent is not None:
            App.get().post_update(self._parent, completely)

    def fixed_width(self, width: float) -> Self:
        return self.width_policy(SizePolicy.FIXED).width(width)

    def fixed_height(self, height: float) -> Self:
        return self.height_policy(SizePolicy.FIXED).height(height)

    def fixed_size(self, width: float, height: float) -> Self:
        return (
            self.width_policy(SizePolicy.FIXED)
            .height_policy(SizePolicy.FIXED)
            .resize(Size(width=width, height=height))
        )

    def fit_parent(self) -> Self:
        return self.width_policy(SizePolicy.EXPANDING).height_policy(
            SizePolicy.EXPANDING
        )

    def fit_content(self) -> Self:
        return self.width_policy(SizePolicy.CONTENT).height_policy(SizePolicy.CONTENT)

    def fit_content_width(self) -> Self:
        return self.width_policy(SizePolicy.CONTENT)

    def fit_content_height(self) -> Self:
        return self.height_policy(SizePolicy.CONTENT)

    # Animation methods

    def animate_to(
        self,
        x: float | None = None,
        y: float | None = None,
        width: float | None = None,
        height: float | None = None,
        duration_ms: int = 300,
        easing: "EasingFunction | None" = None,
        on_complete: Callable[[], None] | None = None,
    ) -> Self:
        """Animate widget properties to target values.

        Args:
            x: Target x position (None = no change)
            y: Target y position (None = no change)
            width: Target width (None = no change)
            height: Target height (None = no change)
            duration_ms: Animation duration in milliseconds
            easing: Easing function (default: EASE_OUT_CUBIC)
            on_complete: Callback when all animations complete

        Returns:
            Self for method chaining

        Example:
            button.animate_to(x=200, y=100, duration_ms=400)
        """
        from castella.animation import AnimationScheduler, EasingFunction, Tween

        if easing is None:
            easing = EasingFunction.EASE_OUT_CUBIC

        scheduler = AnimationScheduler.get()
        animations_started = 0

        if x is not None:
            scheduler.add(Tween(self, "x", self._pos.x, x, duration_ms, easing))
            animations_started += 1

        if y is not None:
            scheduler.add(Tween(self, "y", self._pos.y, y, duration_ms, easing))
            animations_started += 1

        if width is not None:
            scheduler.add(
                Tween(self, "width", self._size.width, width, duration_ms, easing)
            )
            animations_started += 1

        if height is not None:
            # Last animation gets the on_complete callback
            scheduler.add(
                Tween(
                    self,
                    "height",
                    self._size.height,
                    height,
                    duration_ms,
                    easing,
                    on_complete=on_complete if animations_started == 0 else None,
                )
            )
            animations_started += 1

        # If on_complete is set and height wasn't animated, attach to last animation
        if on_complete is not None and animations_started > 0 and height is None:
            # For simplicity, on_complete only fires for height animation
            # A more sophisticated implementation would track all animations
            pass

        return self

    def slide_in(
        self,
        direction: str = "left",
        distance: float = 100,
        duration_ms: int = 300,
        easing: "EasingFunction | None" = None,
        on_complete: Callable[[], None] | None = None,
    ) -> Self:
        """Slide in from off-screen position.

        Args:
            direction: Direction to slide from ("left", "right", "top", "bottom")
            distance: Distance to slide in pixels
            duration_ms: Animation duration in milliseconds
            easing: Easing function (default: EASE_OUT_CUBIC)
            on_complete: Callback when animation completes

        Returns:
            Self for method chaining

        Example:
            panel.slide_in("left", distance=200)
        """
        from castella.animation import AnimationScheduler, EasingFunction, Tween

        if easing is None:
            easing = EasingFunction.EASE_OUT_CUBIC

        scheduler = AnimationScheduler.get()
        current_x = self._pos.x
        current_y = self._pos.y

        match direction:
            case "left":
                self._pos.x = current_x - distance
                scheduler.add(
                    Tween(
                        self,
                        "x",
                        current_x - distance,
                        current_x,
                        duration_ms,
                        easing,
                        on_complete,
                    )
                )
            case "right":
                self._pos.x = current_x + distance
                scheduler.add(
                    Tween(
                        self,
                        "x",
                        current_x + distance,
                        current_x,
                        duration_ms,
                        easing,
                        on_complete,
                    )
                )
            case "top":
                self._pos.y = current_y - distance
                scheduler.add(
                    Tween(
                        self,
                        "y",
                        current_y - distance,
                        current_y,
                        duration_ms,
                        easing,
                        on_complete,
                    )
                )
            case "bottom":
                self._pos.y = current_y + distance
                scheduler.add(
                    Tween(
                        self,
                        "y",
                        current_y + distance,
                        current_y,
                        duration_ms,
                        easing,
                        on_complete,
                    )
                )

        return self

    def slide_out(
        self,
        direction: str = "left",
        distance: float = 100,
        duration_ms: int = 300,
        easing: "EasingFunction | None" = None,
        on_complete: Callable[[], None] | None = None,
    ) -> Self:
        """Slide out to off-screen position.

        Args:
            direction: Direction to slide to ("left", "right", "top", "bottom")
            distance: Distance to slide in pixels
            duration_ms: Animation duration in milliseconds
            easing: Easing function (default: EASE_IN_CUBIC)
            on_complete: Callback when animation completes

        Returns:
            Self for method chaining

        Example:
            panel.slide_out("right", distance=200)
        """
        from castella.animation import AnimationScheduler, EasingFunction, Tween

        if easing is None:
            easing = EasingFunction.EASE_IN_CUBIC

        scheduler = AnimationScheduler.get()
        current_x = self._pos.x
        current_y = self._pos.y

        match direction:
            case "left":
                scheduler.add(
                    Tween(
                        self,
                        "x",
                        current_x,
                        current_x - distance,
                        duration_ms,
                        easing,
                        on_complete,
                    )
                )
            case "right":
                scheduler.add(
                    Tween(
                        self,
                        "x",
                        current_x,
                        current_x + distance,
                        duration_ms,
                        easing,
                        on_complete,
                    )
                )
            case "top":
                scheduler.add(
                    Tween(
                        self,
                        "y",
                        current_y,
                        current_y - distance,
                        duration_ms,
                        easing,
                        on_complete,
                    )
                )
            case "bottom":
                scheduler.add(
                    Tween(
                        self,
                        "y",
                        current_y,
                        current_y + distance,
                        duration_ms,
                        easing,
                        on_complete,
                    )
                )

        return self


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

    def __iadd__(self, value) -> Self:
        self._value += value
        self.notify()
        return self

    def __add__(self, value) -> T:
        return self._value + value

    def __isub__(self, value) -> Self:
        self._value -= value
        self.notify()
        return self

    def __imul__(self, value) -> Self:
        self._value *= value
        self.notify()
        return self

    def __itruediv__(self, value) -> Self:
        self._value /= value
        self.notify()
        return self


class ListState(list, State[T]):
    def __init__(self, items):
        super().__init__(items)
        ObservableBase.__init__(self)

    def __add__(self, rhs: Iterable[T]) -> "ListState":
        return ListState(super().__add__(list(rhs)))

    def __delattr__(self, name: str) -> None:
        super().__delattr__(name)
        self.notify()

    def __setattr__(self, name: str, value: Any) -> None:
        super().__setattr__(name, value)
        # Don't notify for internal attributes (e.g., _widget_cache, _observers)
        if not name.startswith("_"):
            self.notify()

    def __iadd__(self, rhs: Iterable[T]) -> Self:
        super().__iadd__(rhs)
        self.notify()
        return self

    def __imul__(self, rhs: int) -> Self:
        super().__imul__(rhs)
        self.notify()
        return self

    def __mul__(self, rhs: int) -> "ListState":
        return ListState(super().__mul__(rhs))

    def __rmul__(self, lhs: int) -> "ListState":
        return ListState(super().__rmul__(lhs))

    def __reversed__(self) -> Self:
        super().__reversed__()
        self.notify()
        return self

    def __setitem__(self, index: int, value: T) -> Self:
        super().__setitem__(index, value)
        self.notify()
        return self

    def __delitem__(self, index: int) -> Self:
        super().__delitem__(index)
        self.notify()
        return self

    def __iter__(self) -> Generator[T, None, None]:
        for item in super().__iter__():
            yield item

    def __next__(self) -> T:
        return next(super().__iter__())

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

    def set(self, items: Iterable[T]) -> None:
        """Replace all items at once (single notify).

        Use this instead of clear() + append() to avoid multiple rebuilds.
        """
        super().clear()
        super().extend(items)
        self.notify()

    def map_cached(
        self,
        factory: Callable[[T], "Widget"],
        key_fn: Callable[[T], Any] | None = None,
    ) -> list["Widget"]:
        """Map items to cached widget instances.

        This enables state preservation across view() rebuilds.
        Widgets are reused for the same items, preserving their internal state.
        Widgets for removed items are automatically cleaned up.

        Args:
            factory: Function that creates a widget from an item.
            key_fn: Optional function to extract a cache key from an item.
                    Defaults to using item.id, hash(item), or id(item).

        Returns:
            List of cached (or newly created) widgets.

        Example:
            def view(self):
                return Column(
                    *self._items.map_cached(
                        lambda item: TimerWidget(item.id, item.name)
                    )
                )
        """
        # Lazily initialize cache
        if not hasattr(self, "_widget_cache"):
            self._widget_cache: dict[Any, Widget] = {}

        cache = self._widget_cache
        result: list[Widget] = []
        seen_keys: set = set()

        for item in self:
            # Determine cache key
            if key_fn is not None:
                key = key_fn(item)
            elif hasattr(item, "id"):
                key = item.id
            else:
                try:
                    hash(item)
                    key = item
                except TypeError:
                    key = id(item)

            seen_keys.add(key)

            if key not in cache:
                cache[key] = factory(item)

            widget = cache[key]
            # Mark as cached to prevent unmount during rebuild
            widget._cached = True
            # Remove from old parent (if any) before adding to new layout
            if widget._parent is not None:
                old_parent = widget._parent
                if hasattr(old_parent, "_children") and widget in old_parent._children:
                    old_parent._children.remove(widget)
                    # Also remove from render node
                    if hasattr(old_parent, "_layout_render_node"):
                        old_parent._layout_render_node.remove_child(widget)
                widget._parent = None
            result.append(widget)

        # Cleanup removed items - unmount and remove from cache
        for key in list(cache.keys()):
            if key not in seen_keys:
                widget = cache[key]
                widget._cached = False  # Allow unmount
                widget._do_unmount()  # Actually unmount (stops timers, etc.)
                del cache[key]

        return result


class ScrollState(ObservableBase):
    """Observable scroll position state that persists across view rebuilds.

    Use this to preserve scroll position when a Component re-renders.

    Example:
        class MyComponent(Component):
            def __init__(self):
                super().__init__()
                self._items = ListState([...])
                self._items.attach(self)
                self._scroll = ScrollState()  # Survives re-renders

            def view(self):
                return Box(
                    Column(*[Text(item) for item in self._items]),
                    scroll_state=self._scroll,  # Pass to Box
                )
    """

    def __init__(self, x: int = 0, y: int = 0):
        super().__init__()
        self._x = x
        self._y = y

    @property
    def x(self) -> int:
        """Get horizontal scroll position."""
        return self._x

    @x.setter
    def x(self, value: int) -> None:
        """Set horizontal scroll position."""
        if self._x != value:
            self._x = value
            self.notify()

    @property
    def y(self) -> int:
        """Get vertical scroll position."""
        return self._y

    @y.setter
    def y(self, value: int) -> None:
        """Set vertical scroll position."""
        if self._y != value:
            self._y = value
            self.notify()

    def set(self, x: int | None = None, y: int | None = None) -> None:
        """Set scroll position (x and/or y)."""
        changed = False
        if x is not None and self._x != x:
            self._x = x
            changed = True
        if y is not None and self._y != y:
            self._y = y
            changed = True
        if changed:
            self.notify()


def get_theme() -> Theme:
    """Get the current theme from the ThemeManager."""
    return ThemeManager().current


def replace_font_size(style: Style, size: float, policy: FontSizePolicy) -> Style:
    new_font = style.font.model_copy(update={"size": int(size), "size_policy": policy})
    return style.model_copy(update={"font": new_font})


def determine_font(
    width: float, height: float, style: Style, text: str
) -> tuple[str, int]:
    size_of_text = len(text)
    if size_of_text == 0:
        size_of_text = 1  # to compute the height of caret

    if style.font.size_policy == FontSizePolicy.EXPANDING:
        # Clamp font size between 10 and 1000 (Font model constraint)
        font_size = max(
            min(
                int(height - 2 * style.padding),
                int((width - 2 * style.padding) / (size_of_text * 0.65)),
                1000,  # Font model max size
            ),
            10,
        )
        return style.font.family, font_size
    else:
        return style.font.family, style.font.size


SCROLL_BAR_SIZE = EM


class App:
    _instance: Self | None = None

    _default_font_family = get_theme().app.text_font.family

    def __new__(cls, _frame: Frame, _widget: Widget):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, frame: Frame, widget: Widget):
        from castella.events import EventManager

        self._frame = frame
        self._root_widget = widget
        self._event_manager = EventManager()
        self._event_manager.set_root(widget)

        # Legacy state - now delegated to EventManager internally
        # but kept for backward compatibility with widget.detach()
        self._downed: Widget | None = None
        self._focused: Widget | None = None
        self._mouse_overed: Widget | None = None
        self._style = Style(fill=FillStyle(color=get_theme().app.bg_color))

    @classmethod
    def get(cls) -> Self | None:
        return cls._instance

    @classmethod
    def default_font_family(cls, font_family: str) -> type[Self]:
        cls._default_font_family = font_family
        return cls

    @classmethod
    def get_default_font_family(cls) -> str:
        return cls._default_font_family

    @property
    def event_manager(self) -> "EventManager":
        """Access the event manager for advanced event handling.

        Provides access to:
        - focus: FocusManager for Tab navigation
        - pointer: PointerTracker for mouse state
        - gesture: GestureRecognizer for tap/drag detection
        - keyboard: KeyboardState for key tracking
        - shortcuts: ShortcutHandler for global shortcuts
        """

        return self._event_manager

    def mouse_down(self, ev: MouseEvent) -> None:
        target, p = self._root_widget.dispatch(ev.pos)
        if target is not None and p is not None:
            ev.target = target
            self._prev_abs_pos = ev.pos
            ev.pos = p  # p is already local coordinates from dispatch()
            self._prev_rel_pos = ev.pos
            target.mouse_down(ev)
            self._downed = target

    def mouse_up(self, ev: MouseEvent) -> None:
        if self._downed is None:
            return

        # Save reference before callbacks that may trigger view rebuild
        # and clear _downed via widget.detach()
        downed = self._downed
        try:
            # Use FocusManager to handle focus changes
            focus_mgr = self._event_manager.focus
            focus_mgr.set_focus(downed)
            self._focused = downed  # Sync legacy _focused

            ev.target = downed
            # Re-dispatch to get correct local coordinates for the target widget
            target, local_p = self._root_widget.dispatch(ev.pos)
            if local_p is not None and target is downed:
                # Mouse is still over the original target - use local coords
                ev.pos = local_p
            else:
                # Mouse moved away - use delta approach as fallback
                diff = ev.pos - self._prev_abs_pos
                ev.pos = self._prev_rel_pos + diff
            self._prev_abs_pos = ev.pos
            self._prev_rel_pos = ev.pos
            downed.mouse_up(ev)
        finally:
            self._downed = None

    def mouse_wheel(self, ev: WheelEvent) -> None:
        target, _ = self._root_widget.dispatch_to_scrollable(
            ev.pos, abs(ev.x_offset) > abs(ev.y_offset)
        )
        if target is not None:
            target.mouse_wheel(ev)

    def cursor_pos(self, ev: MouseEvent) -> None:
        target, p = self._root_widget.dispatch(ev.pos)
        if target is None:
            if self._mouse_overed is not None:
                self._mouse_overed.mouse_out()
                self._mouse_overed = None
        elif self._downed is None:
            if self._mouse_overed is None:
                self._mouse_overed = target
                target.mouse_over()
            elif self._mouse_overed is not target:
                self._mouse_overed.mouse_out()
                self._mouse_overed = target
                target.mouse_over()
            # Call cursor_pos on target widget with relative position
            if p is not None:
                rel_ev = MouseEvent(pos=p)
                target.cursor_pos(rel_ev)
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
        # Let FocusManager handle Tab/Shift+Tab navigation first
        focus_mgr = self._event_manager.focus
        if focus_mgr.handle_key_event(ev):
            # FocusManager handled Tab - sync legacy _focused
            self._focused = focus_mgr.focus
            return

        # Route other key events to the focused widget
        if self._focused is None:
            return
        self._focused.input_key(ev)

    def ime_preedit(self, ev: "IMEPreeditEvent") -> None:
        """Route IME preedit event to the focused widget."""
        if self._focused is None:
            return
        if hasattr(self._focused, "ime_preedit"):
            self._focused.ime_preedit(ev)

    def redraw(self, p: Painter, completely: bool) -> None:
        # Collect focusable widgets for Tab navigation
        self._event_manager.focus.collect_focusables(self._root_widget)

        # Clear entire canvas first to remove any remnants
        # Get current theme's canvas color for proper dark/light mode support
        bg_color = get_theme().app.bg_color
        self._style = Style(fill=FillStyle(color=bg_color))
        p.clear_all(bg_color)
        p.style(self._style)
        p.fill_rect(
            Rect(
                origin=Point(x=0, y=0),
                size=self._frame.get_size() + Size(width=1, height=1),
            )
        )
        self._relocate_layout(self._root_widget)
        if completely or self._root_widget.is_dirty():
            p.save()
            p.translate(self._root_widget.get_pos())
            p.clip(Rect(origin=Point(x=0, y=0), size=self._root_widget.get_size()))
            self._root_widget.redraw(p, completely)
            p.restore()
            self._root_widget.dirty(False)
        p.flush()

    def _relocate_layout(self, w: Widget) -> None:
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

        w.resize(Size(width=width, height=height))

    def post_update(self, w: Widget, completely: bool = False) -> None:
        self._frame.post_update(UpdateEvent(target=w, completely=completely))

    def run(self) -> None:
        self._frame.on_mouse_down(self.mouse_down)
        self._frame.on_mouse_up(self.mouse_up)
        self._frame.on_mouse_wheel(self.mouse_wheel)
        self._frame.on_cursor_pos(self.cursor_pos)
        self._frame.on_input_char(self.input_char)
        self._frame.on_input_key(self.input_key)
        self._frame.on_ime_preedit(self.ime_preedit)
        self._frame.on_redraw(self.redraw)
        self._frame.run()

    # supported platforms: desktop (glfw, sdl2)
    def get_clipboard_text(self) -> str:
        return self._frame.get_clipboard_text()

    # supported platforms: desktop (glfw, sdl2)
    def set_clipboard_text(self, text: str) -> None:
        self._frame.set_clipboard_text(text)

    # supported platforms: web
    def async_get_clipboard_text(self, callback: Callable[[Future[str]], None]) -> None:
        self._frame.async_get_clipboard_text(callback)

    # supported platforms: web
    def async_set_clipboard_text(
        self, text: str, callback: Callable[[Future], None]
    ) -> None:
        return self._frame.async_set_clipboard_text(text, callback)


class Container(Protocol):
    def get_children(self) -> Generator[Widget, None, None]: ...

    def detach(self) -> None: ...


class Layout(Widget, ABC):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._children: list[Widget] = []
        # _widget_styles is initialized in Widget.__init__()
        # _on_update_widget_styles() is called in Widget.__init__()

    def _create_render_node(self) -> "RenderNode":
        """Create a LayoutRenderNode for z-order caching."""
        from castella.render import LayoutRenderNode

        return LayoutRenderNode(self)

    @property
    def _layout_render_node(self) -> "LayoutRenderNode":
        """Get the layout render node (type-safe access)."""
        return self.render_node  # type: ignore

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

        # If widget already has a parent, remove from old parent first
        # This is important for frozen widgets that are reused across rebuilds
        old_parent = w.get_parent()
        if old_parent is not None and old_parent is not self:
            if w in old_parent._children:
                old_parent._children.remove(w)
            # Also remove from old parent's render node
            if hasattr(old_parent, "_layout_render_node"):
                old_parent._layout_render_node.remove_child(w)

        self._children.append(w)
        w.parent(self)
        # Sync with render node for z-order caching
        self._layout_render_node.add_child(w)

    def detach(self) -> None:
        super().detach()
        # If frozen (e.g., AudioPlayer), don't detach children
        # They will be reused when this widget is re-added to the tree
        if self._enable_to_detach:
            for c in self.get_children():
                c.detach()

    def remove(self, w: Widget) -> None:
        self._children.remove(w)
        # Trigger unmount lifecycle before removing
        w._do_unmount()
        w.delete_parent(self)
        # Sync with render node
        self._layout_render_node.remove_child(w)

    def dispatch(self, p: Point) -> tuple[Widget | None, Point | None]:
        if self.contain_in_content_area(p):
            p = self._adjust_pos(p)
            # Use cached z-order (higher z_index receives events first)
            for c in self._layout_render_node.iter_hit_test_order():
                target, adjusted_p = c.dispatch(p)
                if target is not None:
                    return target, adjusted_p
            # Return position relative to this widget's origin
            local_p = Point(x=p.x - self._pos.x, y=p.y - self._pos.y)
            return self, local_p
        elif self.contain(p):
            # Return position relative to this widget's origin
            local_p = Point(x=p.x - self._pos.x, y=p.y - self._pos.y)
            return self, local_p
        else:
            return None, None

    def dispatch_to_scrollable(
        self, p: Point, is_direction_x: bool
    ) -> tuple[Widget | None, Point | None]:
        if self.contain_in_content_area(p):
            p = self._adjust_pos(p)
            # Use cached z-order (higher z_index receives events first)
            for c in self._layout_render_node.iter_hit_test_order():
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
    def has_scrollbar(self, is_direction_x: bool) -> bool: ...

    def _adjust_pos(self, p: Point) -> Point:
        return p + Point(x=0, y=0)

    def contain_in_content_area(self, p: Point) -> bool:
        return (self._pos.x < p.x < self._pos.x + self._size.width) and (
            self._pos.y < p.y < self._pos.y + self._size.height
        )

    def _on_update_widget_styles(self) -> None:
        """Update instance style from widget_styles (called after bg_color() etc.)."""
        widget_style = self._get_widget_style(Kind.NORMAL, AppearanceState.NORMAL)
        self._style = Style(
            fill=FillStyle(color=widget_style.bg_color),
            border_radius=widget_style.border_radius,
            shadow=widget_style.shadow,
        )

    def redraw(self, p: Painter, completely: bool) -> None:
        p.style(self._style)
        if completely or self.is_dirty():
            p.fill_rect(
                Rect(
                    origin=Point(x=0, y=0),
                    size=self.get_size() + Size(width=1, height=1),
                )
            )
        self._relocate_children(p)
        self._redraw_children(p, completely)

    @abstractmethod
    def _relocate_children(self, p: Painter) -> None: ...

    def _redraw_children(self, p: Painter, completely: bool) -> None:
        # Use cached z-order (lower z_index first, higher on top)
        for c in self._layout_render_node.iter_paint_order():
            if completely or c.is_dirty():
                p.save()
                p.translate((c.get_pos() - self.get_pos()))
                p.clip(Rect(origin=Point(x=0, y=0), size=c.get_size()))
                c.redraw(p, completely)
                p.restore()
                c.dirty(False)

    def width_policy(self, sp: SizePolicy) -> Self:
        if sp is SizePolicy.CONTENT and self.has_width_expandable_children():
            raise RuntimeError(
                "Layout with CONTENT size policy cannot have an size expandable child widget"
            )

        self._width_policy = sp
        return self

    def height_policy(self, sp: SizePolicy) -> Self:
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
            pos=Point(x=0, y=0),
            pos_policy=None,
            size=Size(width=0, height=0),
            width_policy=SizePolicy.EXPANDING,
            height_policy=SizePolicy.EXPANDING,
        )
        self._child: Widget | None = None
        self._pending_rebuild: bool = False  # Thread-safe flag for deferred rebuild
        self._widget_cache: dict[tuple, dict] = {}  # Widget instance cache for view()

    def _relocate_children(self, p: Painter) -> None:
        self._resize_children(p)
        self._move_children()

    def _resize_children(self, p: Painter) -> None:
        if len(self._children) == 0:
            return

        child = self._children[0]
        child.resize(self.get_size().model_copy())

    def _move_children(self):
        if len(self._children) == 0:
            return
        child = self._children[0]
        child.move(self.get_pos())

    def has_scrollbar(self, is_direction_x: bool) -> bool:
        return False

    @abstractmethod
    def view(self) -> Widget: ...

    def cache(
        self,
        items: Iterable[Any],
        factory: Callable[[Any], "Widget"],
    ) -> list["Widget"]:
        """Cache widget instances for items across view() rebuilds.

        This enables state preservation without key-based reconciliation.
        Widgets are reused for the same items, preserving their internal state.
        Widgets for removed items are automatically cleaned up.

        The cache is identified by the source code location (file + line number),
        so multiple cache() calls in the same view() work correctly.

        Args:
            items: Iterable of items to create widgets for.
            factory: Function that creates a widget from an item.

        Returns:
            List of cached (or newly created) widgets.

        Example:
            def view(self):
                return Column(
                    *self.cache(
                        self._items,
                        lambda item: TimerWidget(item.id, item.name)
                    )
                )
        """
        import inspect

        # Identify cache by call site (file + line number)
        frame = inspect.currentframe()
        if frame is not None and frame.f_back is not None:
            caller = frame.f_back
            cache_id = (caller.f_code.co_filename, caller.f_lineno)
        else:
            cache_id = (id(factory),)

        if cache_id not in self._widget_cache:
            self._widget_cache[cache_id] = {}

        cache = self._widget_cache[cache_id]
        items_list = list(items)

        result: list[Widget] = []
        seen_keys: set = set()

        for item in items_list:
            key = self._get_cache_key(item)
            seen_keys.add(key)

            if key not in cache:
                cache[key] = factory(item)

            widget = cache[key]
            # Mark as cached to prevent unmount during rebuild
            widget._cached = True
            # Remove from old parent (if any) before adding to new layout
            if widget._parent is not None:
                old_parent = widget._parent
                if hasattr(old_parent, "_children") and widget in old_parent._children:
                    old_parent._children.remove(widget)
                    # Also remove from render node
                    if hasattr(old_parent, "_layout_render_node"):
                        old_parent._layout_render_node.remove_child(widget)
                widget._parent = None
            result.append(widget)

        # Cleanup removed items - unmount and remove from cache
        for key in list(cache.keys()):
            if key not in seen_keys:
                widget = cache[key]
                widget._cached = False  # Allow unmount
                widget._do_unmount()  # Actually unmount (stops timers, etc.)
                del cache[key]

        return result

    def _get_cache_key(self, item: Any) -> Any:
        """Extract a cache key from an item.

        Priority:
        1. item.id if available
        2. item itself if hashable
        3. id(item) as fallback
        """
        if hasattr(item, "id"):
            return item.id
        try:
            hash(item)
            return item
        except TypeError:
            return id(item)

    def on_notify(self, event: Any = None) -> None:
        """Handle state change notification.

        Uses BuildOwner for batched rebuilds when in a build scope,
        otherwise falls back to immediate rebuild (backward compatibility).
        """
        from castella.build_owner import BuildOwner

        owner = BuildOwner.get()
        if owner.is_in_build_scope():
            # Batched mode: schedule for rebuild when scope exits
            owner.schedule_build_for(self)
        else:
            # Immediate mode (backward compatibility)
            self._pending_rebuild = True
            self.dirty(True)
            app = App.get()
            if app is not None:
                app._root_widget.dirty(True)
                app._frame.post_update(UpdateEvent(target=app, completely=True))

    def _do_rebuild(self) -> None:
        """Perform the actual view rebuild.

        Called by BuildOwner during batched rebuilds.
        """
        self._pending_rebuild = True
        self.dirty(True)
        app = App.get()
        if app is not None:
            app._root_widget.dirty(True)
            app._frame.post_update(UpdateEvent(target=app, completely=True))

    def redraw(self, p: Painter, completely: bool) -> None:
        # Handle pending rebuild (triggered by on_notify from any thread)
        if self._pending_rebuild:
            self._pending_rebuild = False
            if self._child is not None:
                self.remove(self._child)
                self._child.detach()
                self._child = None

        if self._child is None:
            self._child = self.view()
            self.add(self._child)
            completely = True
        super().redraw(p, completely)

    def measure(self, p: Painter) -> Size:
        if self._child is None:
            return Size(width=0, height=0)
        return self._child.measure(p)


class StatefulComponent(Component, ABC):
    def __init__(self, state: Observable):
        super().__init__()
        self.model(state)
