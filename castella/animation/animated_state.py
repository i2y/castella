"""AnimatedState - a State wrapper that animates value transitions."""

from __future__ import annotations

from typing import Generic, TypeVar

from castella.chart.models.animation import EasingFunction
from castella.core import ObservableBase

from .animation import Animation
from .easing import apply_easing, lerp
from .interpolators import is_interpolatable
from .scheduler import AnimationScheduler

T = TypeVar("T", int, float)


class AnimatedState(ObservableBase, Generic[T]):
    """A state wrapper that smoothly animates between values.

    When set() is called, instead of immediately changing to the new value,
    it animates from the current value to the target over the specified duration.

    Example:
        class Counter(Component):
            def __init__(self):
                super().__init__()
                self._value = AnimatedState(0, duration_ms=200)
                self._value.attach(self)

            def view(self):
                return Column(
                    Text(f"Value: {self._value():.1f}"),
                    Button("Add").on_click(lambda _: self._value.set(self._value() + 10)),
                )
    """

    def __init__(
        self,
        initial: T,
        duration_ms: int = 300,
        easing: EasingFunction = EasingFunction.EASE_OUT_CUBIC,
    ) -> None:
        """Initialize animated state.

        Args:
            initial: Initial value
            duration_ms: Default animation duration
            easing: Default easing function
        """
        super().__init__()
        self._current: T = initial
        self._target: T = initial
        self._duration_ms = duration_ms
        self._easing = easing
        self._animation: _StateAnimation[T] | None = None

    def __call__(self) -> T:
        """Get the current animated value."""
        return self._current

    def value(self) -> T:
        """Get the current animated value."""
        return self._current

    def target(self) -> T:
        """Get the target value (may differ from current if animating)."""
        return self._target

    def set(
        self,
        value: T,
        animate: bool = True,
        duration_ms: int | None = None,
        easing: EasingFunction | None = None,
    ) -> None:
        """Set the target value, optionally animating.

        Args:
            value: New target value
            animate: Whether to animate the transition
            duration_ms: Override default duration (None uses default)
            easing: Override default easing (None uses default)
        """
        if not animate or not is_interpolatable(value):
            self._stop_animation()
            self._current = value
            self._target = value
            self.notify()
            return

        # If same as target, do nothing
        if value == self._target:
            return

        self._target = value
        self._start_animation(
            duration_ms if duration_ms is not None else self._duration_ms,
            easing if easing is not None else self._easing,
        )

    def set_immediate(self, value: T) -> None:
        """Set value without animation."""
        self.set(value, animate=False)

    def is_animating(self) -> bool:
        """Check if currently animating."""
        return self._animation is not None and not self._animation.is_cancelled()

    def stop(self) -> None:
        """Stop any running animation at current value."""
        self._stop_animation()

    def finish(self) -> None:
        """Immediately jump to target value and stop animation."""
        self._stop_animation()
        self._current = self._target
        self.notify()

    def _start_animation(self, duration_ms: int, easing: EasingFunction) -> None:
        """Start a new animation from current to target."""
        self._stop_animation()

        self._animation = _StateAnimation(
            state=self,
            from_value=self._current,
            to_value=self._target,
            duration_ms=duration_ms,
            easing=easing,
        )
        AnimationScheduler.get().add(self._animation)

    def _stop_animation(self) -> None:
        """Stop current animation if any."""
        if self._animation is not None:
            self._animation.cancel()
            AnimationScheduler.get().remove(self._animation)
            self._animation = None

    def _update_current(self, value: T) -> None:
        """Update current value during animation. Called by _StateAnimation."""
        self._current = value
        self.notify()

    def _on_animation_complete(self) -> None:
        """Called when animation completes."""
        self._animation = None


class _StateAnimation(Animation, Generic[T]):
    """Internal animation class for AnimatedState."""

    def __init__(
        self,
        state: AnimatedState[T],
        from_value: T,
        to_value: T,
        duration_ms: int,
        easing: EasingFunction,
    ) -> None:
        super().__init__()
        self._state = state
        self._from_value = float(from_value)
        self._to_value = float(to_value)
        self._duration_ms = max(1, duration_ms)
        self._easing = easing
        self._elapsed: float = 0.0

    def tick(self, dt: float) -> bool:
        """Update animation state."""
        if self._cancelled:
            return True

        self._elapsed += dt * 1000
        progress = min(1.0, self._elapsed / self._duration_ms)
        eased = apply_easing(progress, self._easing)

        value = lerp(self._from_value, self._to_value, eased)

        # Cast back to original type
        if isinstance(self._state._current, int):
            self._state._update_current(round(value))  # type: ignore
        else:
            self._state._update_current(value)  # type: ignore

        if progress >= 1.0:
            self._state._on_animation_complete()
            return True
        return False
