"""Tween animation for interpolating widget properties."""

from __future__ import annotations

from typing import TYPE_CHECKING, Callable, Literal

from castella.chart.models.animation import EasingFunction

from .animation import Animation
from .easing import apply_easing, lerp

if TYPE_CHECKING:
    from castella.core import Widget


PropertyName = Literal["x", "y", "width", "height"]


class Tween(Animation):
    """Property interpolation animation.

    Animates a widget property from one value to another over time,
    using an easing function to control the rate of change.

    Example:
        tween = Tween(
            target=my_button,
            property_name="x",
            from_value=0,
            to_value=200,
            duration_ms=500,
            easing=EasingFunction.EASE_OUT_CUBIC,
        )
        AnimationScheduler.get().add(tween)
    """

    def __init__(
        self,
        target: Widget,
        property_name: PropertyName,
        from_value: float,
        to_value: float,
        duration_ms: int = 300,
        easing: EasingFunction = EasingFunction.EASE_OUT_CUBIC,
        on_complete: Callable[[], None] | None = None,
        on_update: Callable[[float], None] | None = None,
    ) -> None:
        """Initialize tween animation.

        Args:
            target: Widget to animate
            property_name: Property to animate ("x", "y", "width", "height")
            from_value: Starting value
            to_value: Target value
            duration_ms: Animation duration in milliseconds
            easing: Easing function to use
            on_complete: Callback when animation completes
            on_update: Callback on each update with current value
        """
        super().__init__(on_complete=on_complete, on_update=on_update)
        self._target = target
        self._property_name = property_name
        self._from_value = from_value
        self._to_value = to_value
        self._duration_ms = max(1, duration_ms)
        self._easing = easing
        self._elapsed: float = 0.0

    def tick(self, dt: float) -> bool:
        """Update animation state.

        Args:
            dt: Delta time in seconds since last tick

        Returns:
            True if animation is complete, False otherwise
        """
        if self._cancelled:
            return True

        self._elapsed += dt * 1000  # Convert to milliseconds
        progress = min(1.0, self._elapsed / self._duration_ms)
        eased = apply_easing(progress, self._easing)

        value = lerp(self._from_value, self._to_value, eased)
        self._set_property(value)

        if self._on_update is not None:
            self._on_update(value)

        return progress >= 1.0

    def _set_property(self, value: float) -> None:
        """Set the target property value and trigger update."""
        match self._property_name:
            case "x":
                self._target.move_x(value)
            case "y":
                self._target.move_y(value)
            case "width":
                self._target.width(value)
            case "height":
                self._target.height(value)

        # Trigger redraw
        self._target.update()

    @property
    def target(self) -> Widget:
        """Get the animation target widget."""
        return self._target

    @property
    def property_name(self) -> PropertyName:
        """Get the animated property name."""
        return self._property_name

    @property
    def progress(self) -> float:
        """Get the current animation progress (0.0 to 1.0)."""
        return min(1.0, self._elapsed / self._duration_ms)


class ValueTween(Animation):
    """Generic value interpolation animation.

    Animates between two numeric values without targeting a specific widget.
    Useful for custom animations where you handle the value update yourself.

    Example:
        def on_value_change(value):
            my_widget._pos.x = value
            my_widget.update()

        tween = ValueTween(
            from_value=0,
            to_value=100,
            duration_ms=300,
            on_update=on_value_change,
        )
        AnimationScheduler.get().add(tween)
    """

    def __init__(
        self,
        from_value: float,
        to_value: float,
        duration_ms: int = 300,
        easing: EasingFunction = EasingFunction.EASE_OUT_CUBIC,
        on_complete: Callable[[], None] | None = None,
        on_update: Callable[[float], None] | None = None,
    ) -> None:
        """Initialize value tween.

        Args:
            from_value: Starting value
            to_value: Target value
            duration_ms: Animation duration in milliseconds
            easing: Easing function to use
            on_complete: Callback when animation completes
            on_update: Callback on each update with current value (required for effect)
        """
        super().__init__(on_complete=on_complete, on_update=on_update)
        self._from_value = from_value
        self._to_value = to_value
        self._duration_ms = max(1, duration_ms)
        self._easing = easing
        self._elapsed: float = 0.0
        self._current_value: float = from_value

    def tick(self, dt: float) -> bool:
        """Update animation state.

        Args:
            dt: Delta time in seconds since last tick

        Returns:
            True if animation is complete, False otherwise
        """
        if self._cancelled:
            return True

        self._elapsed += dt * 1000
        progress = min(1.0, self._elapsed / self._duration_ms)
        eased = apply_easing(progress, self._easing)

        self._current_value = lerp(self._from_value, self._to_value, eased)

        if self._on_update is not None:
            self._on_update(self._current_value)

        return progress >= 1.0

    @property
    def current_value(self) -> float:
        """Get the current interpolated value."""
        return self._current_value

    @property
    def progress(self) -> float:
        """Get the current animation progress (0.0 to 1.0)."""
        return min(1.0, self._elapsed / self._duration_ms)
