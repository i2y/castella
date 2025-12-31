"""Animation system for Castella UI framework.

This module provides animation primitives for smooth property transitions:

- AnimationScheduler: Manages the animation tick loop (singleton)
- Tween: Animates widget properties (x, y, width, height)
- ValueTween: Generic value interpolation
- AnimatedState: State wrapper with animated transitions
- Easing functions: Linear, ease-in/out, cubic, bounce

Basic usage:

    # Tween animation
    from castella.animation import Tween, AnimationScheduler, EasingFunction

    tween = Tween(
        target=my_button,
        property_name="x",
        from_value=0,
        to_value=200,
        duration_ms=500,
        easing=EasingFunction.EASE_OUT_CUBIC,
    )
    AnimationScheduler.get().add(tween)

    # AnimatedState
    from castella.animation import AnimatedState

    class Counter(Component):
        def __init__(self):
            super().__init__()
            self._value = AnimatedState(0, duration_ms=200)
            self._value.attach(self)

        def view(self):
            return Text(f"Value: {self._value():.1f}")
"""

from castella.chart.models.animation import AnimationConfig, EasingFunction

from .animated_state import AnimatedState
from .animation import Animation
from .easing import apply_easing, lerp
from .interpolators import (
    interpolate,
    interpolate_float,
    interpolate_int,
    interpolate_point,
    interpolate_size,
    is_interpolatable,
)
from .scheduler import AnimationScheduler
from .tween import PropertyName, Tween, ValueTween

__all__ = [
    # Core classes
    "Animation",
    "AnimationScheduler",
    "Tween",
    "ValueTween",
    "AnimatedState",
    # Configuration
    "AnimationConfig",
    "EasingFunction",
    "PropertyName",
    # Easing
    "apply_easing",
    "lerp",
    # Interpolation
    "interpolate",
    "interpolate_float",
    "interpolate_int",
    "interpolate_point",
    "interpolate_size",
    "is_interpolatable",
]
