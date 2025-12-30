"""Slider widget for range input with drag interaction."""

from typing import Callable, Self, cast

from castella.core import (
    AppearanceState,
    Circle,
    FillStyle,
    Kind,
    MouseEvent,
    ObservableBase,
    Painter,
    Point,
    Rect,
    Size,
    SizePolicy,
    Style,
    Widget,
    get_theme,
)


class SliderState(ObservableBase):
    """Observable state for Slider widget.

    Attributes:
        value: Current value (clamped between min and max)
        min_val: Minimum value
        max_val: Maximum value
    """

    def __init__(
        self,
        value: float = 0.0,
        min_val: float = 0.0,
        max_val: float = 100.0,
    ):
        super().__init__()
        self._min = min_val
        self._max = max_val
        self._value = self._clamp(value)
        self._dragging = False

    def _clamp(self, value: float) -> float:
        """Clamp value to [min, max] range."""
        return max(self._min, min(self._max, value))

    def value(self) -> float:
        """Get current value."""
        return self._value

    def set(self, value: float) -> None:
        """Set value (clamped to range)."""
        new_value = self._clamp(value)
        if new_value != self._value:
            self._value = new_value
            self.notify()

    def min_val(self) -> float:
        """Get minimum value."""
        return self._min

    def max_val(self) -> float:
        """Get maximum value."""
        return self._max

    def set_range(self, min_val: float, max_val: float) -> None:
        """Set min and max values."""
        self._min = min_val
        self._max = max_val
        self._value = self._clamp(self._value)
        self.notify()

    def ratio(self) -> float:
        """Get value as ratio (0.0 to 1.0)."""
        range_val = self._max - self._min
        if range_val == 0:
            return 0.0
        return (self._value - self._min) / range_val

    def set_from_ratio(self, ratio: float) -> None:
        """Set value from ratio (0.0 to 1.0)."""
        ratio = max(0.0, min(1.0, ratio))
        new_value = self._min + ratio * (self._max - self._min)
        self.set(new_value)

    def is_dragging(self) -> bool:
        """Check if slider is being dragged."""
        return self._dragging

    def set_dragging(self, dragging: bool) -> None:
        """Set dragging state."""
        self._dragging = dragging


class Slider(Widget):
    """Slider widget for selecting numeric values within a range.

    The slider consists of:
    - Track: Background bar showing the full range
    - Fill: Colored portion showing progress from min to current value
    - Thumb: Draggable knob at current position

    Example:
        slider = Slider(value=50, min_val=0, max_val=100)
        slider.on_change(lambda v: print(f"Value: {v}"))

    With state:
        state = SliderState(value=25, min_val=0, max_val=100)
        slider = Slider(state)
    """

    def __init__(
        self,
        value: float | SliderState = 0.0,
        min_val: float = 0.0,
        max_val: float = 100.0,
        kind: Kind = Kind.NORMAL,
    ):
        """Initialize Slider.

        Args:
            value: Initial value or SliderState
            min_val: Minimum value (ignored if value is SliderState)
            max_val: Maximum value (ignored if value is SliderState)
            kind: Visual style kind
        """
        self._kind = kind
        self._callback: Callable[[float], None] = lambda _: None

        if isinstance(value, SliderState):
            state = value
        else:
            state = SliderState(value, min_val, max_val)

        super().__init__(
            state=state,
            size=Size(width=0, height=30),
            pos=Point(x=0, y=0),
            pos_policy=None,
            width_policy=SizePolicy.EXPANDING,
            height_policy=SizePolicy.FIXED,
        )

    def _on_update_widget_styles(self) -> None:
        """Update styles based on theme."""
        # Track style (background bar)
        self._track_style, _ = self._get_painter_styles(
            self._kind, AppearanceState.NORMAL
        )
        # Fill style (filled portion)
        self._fill_style, _ = self._get_painter_styles(
            self._kind, AppearanceState.SELECTED
        )
        # Thumb style (draggable knob)
        self._thumb_style, _ = self._get_painter_styles(
            self._kind, AppearanceState.HOVER
        )

    def redraw(self, p: Painter, completely: bool) -> None:
        """Draw the slider."""
        state = cast(SliderState, self._state)
        size = self.get_size()

        # Skip drawing if size is not yet set (widget not in tree)
        if size.width == 0 or size.height == 0:
            return

        # Clear background to prevent thumb afterimages
        if completely or self.is_dirty():
            widget_style = get_theme().layout["normal"]
            clear_style = Style(
                fill=FillStyle(color=widget_style.bg_color),
            )
            p.style(clear_style)
            p.fill_rect(
                Rect(
                    origin=Point(x=0, y=0),
                    size=size + Size(width=1, height=1),
                )
            )

        # Calculate dimensions
        track_height = max(4, size.height * 0.2)
        track_y = (size.height - track_height) / 2
        thumb_radius = min(size.height / 2 - 2, 12)
        padding = thumb_radius  # Leave room for thumb at edges

        # Track width (excluding thumb padding)
        track_width = size.width - padding * 2

        # Draw track (background bar)
        track_rect = Rect(
            origin=Point(x=padding, y=track_y),
            size=Size(width=track_width, height=track_height),
        )
        p.style(self._track_style)
        p.fill_rect(track_rect)

        # Draw fill (progress)
        ratio = state.ratio()
        fill_width = track_width * ratio
        if fill_width > 0:
            fill_rect = Rect(
                origin=Point(x=padding, y=track_y),
                size=Size(width=fill_width, height=track_height),
            )
            p.style(self._fill_style)
            p.fill_rect(fill_rect)

        # Draw thumb (circle)
        thumb_x = padding + fill_width
        thumb_y = size.height / 2
        thumb_circle = Circle(
            center=Point(x=thumb_x, y=thumb_y),
            radius=thumb_radius,
        )
        p.style(self._thumb_style)
        p.fill_circle(thumb_circle)

    def mouse_down(self, ev: MouseEvent) -> None:
        """Handle mouse down - start dragging."""
        state = cast(SliderState, self._state)
        state.set_dragging(True)
        self._update_value_from_position(ev.pos.x)

    def mouse_up(self, ev: MouseEvent) -> None:
        """Handle mouse up - stop dragging."""
        state = cast(SliderState, self._state)
        state.set_dragging(False)

    def mouse_drag(self, ev: MouseEvent) -> None:
        """Handle mouse drag - update value while dragging."""
        state = cast(SliderState, self._state)
        if state.is_dragging():
            self._update_value_from_position(ev.pos.x)

    def _update_value_from_position(self, x: float) -> None:
        """Update slider value based on mouse x position."""
        state = cast(SliderState, self._state)
        size = self.get_size()

        # Account for thumb padding
        thumb_radius = min(size.height / 2 - 2, 12)
        padding = thumb_radius
        track_width = size.width - padding * 2

        # Calculate ratio from position
        adjusted_x = x - padding
        ratio = adjusted_x / track_width if track_width > 0 else 0

        old_value = state.value()
        state.set_from_ratio(ratio)

        if old_value != state.value():
            self._callback(state.value())

    def on_change(self, callback: Callable[[float], None]) -> Self:
        """Set callback for value changes.

        Args:
            callback: Function called with new value when slider changes

        Returns:
            Self for method chaining
        """
        self._callback = callback
        return self

    def kind(self, kind: Kind) -> Self:
        """Set visual style kind.

        Args:
            kind: Visual style (NORMAL, INFO, SUCCESS, WARNING, DANGER)

        Returns:
            Self for method chaining
        """
        self._kind = kind
        self._on_update_widget_styles()
        return self

    def width_policy(self, sp: SizePolicy) -> Self:
        """Set width sizing policy."""
        if sp is SizePolicy.CONTENT:
            raise RuntimeError("Slider doesn't accept SizePolicy.CONTENT for width")
        return super().width_policy(sp)

    def height_policy(self, sp: SizePolicy) -> Self:
        """Set height sizing policy."""
        if sp is SizePolicy.CONTENT:
            raise RuntimeError("Slider doesn't accept SizePolicy.CONTENT for height")
        return super().height_policy(sp)
