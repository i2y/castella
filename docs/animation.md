# Animation

Castella provides a built-in animation system for smooth property animations with easing functions.

## Overview

The animation system consists of:

- **AnimationScheduler** - Background thread ticker (60 FPS for desktop, 10 FPS for TUI)
- **ValueTween** - Animate numeric values over time
- **AnimatedState** - State wrapper that automatically animates value changes
- **EasingFunction** - Built-in easing functions (linear, ease-out, bounce, etc.)

## ValueTween

`ValueTween` animates a value from one number to another over a specified duration.

```python
from castella.animation import ValueTween, AnimationScheduler, EasingFunction

# Animate from 0 to 100 over 1 second
AnimationScheduler.get().add(
    ValueTween(
        from_value=0,
        to_value=100,
        duration_ms=1000,
        easing=EasingFunction.EASE_OUT_CUBIC,
        on_update=lambda v: print(f"Value: {v}"),
        on_complete=lambda: print("Done!"),
    )
)
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `from_value` | float | Starting value |
| `to_value` | float | Target value |
| `duration_ms` | int | Animation duration in milliseconds |
| `easing` | EasingFunction | Easing function (default: LINEAR) |
| `on_update` | Callable[[float], None] | Callback for each frame |
| `on_complete` | Callable[[], None] | Callback when animation completes |

## AnimatedState

`AnimatedState` is a state wrapper that automatically animates when values change.

```python
from castella import AnimatedState, StatefulComponent, Text, Button, Column

class Counter(StatefulComponent):
    def __init__(self):
        # Values animate automatically when set
        self._value = AnimatedState(0, duration_ms=300)
        super().__init__(self._value)

    def view(self):
        return Column(
            Text(f"Value: {self._value()}"),
            Button("+10").on_click(lambda _: self._value.set(self._value() + 10)),
        )
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `initial` | T | required | Initial value |
| `duration_ms` | int | 300 | Animation duration |
| `easing` | EasingFunction | EASE_OUT_CUBIC | Easing function |

### Methods

| Method | Description |
|--------|-------------|
| `set(value, animate=True)` | Set value with optional animation |
| `set_immediate(value)` | Set value without animation |
| `__call__()` | Get current (animated) value |

## Easing Functions

Available easing functions in `EasingFunction`:

| Function | Description |
|----------|-------------|
| `LINEAR` | Constant speed |
| `EASE_IN_QUAD` | Accelerate from zero |
| `EASE_OUT_QUAD` | Decelerate to zero |
| `EASE_IN_OUT_QUAD` | Accelerate then decelerate |
| `EASE_IN_CUBIC` | Cubic acceleration |
| `EASE_OUT_CUBIC` | Cubic deceleration |
| `EASE_IN_OUT_CUBIC` | Cubic acceleration/deceleration |
| `BOUNCE` | Bounce effect |

## Widget Animation Methods

Widgets have built-in animation methods for position and size:

```python
# Animate to position/size
widget.animate_to(x=200, y=100, duration_ms=400)

# Slide in from off-screen
widget.slide_in("left", distance=200, duration_ms=300)

# Slide out to off-screen
widget.slide_out("right", distance=200, duration_ms=300)
```

### animate_to()

```python
widget.animate_to(
    x=200,           # Target x position
    y=100,           # Target y position
    width=300,       # Target width
    height=150,      # Target height
    duration_ms=400, # Duration
    easing=EasingFunction.EASE_OUT_CUBIC,
    on_complete=lambda: print("Done"),
)
```

### slide_in() / slide_out()

```python
# Directions: "left", "right", "top", "bottom"
widget.slide_in("left", distance=200)
widget.slide_out("right", distance=200, on_complete=lambda: print("Hidden"))
```

## Complete Example

```python
from castella import (
    App, Component, Column, Button, Text,
    ProgressBar, ProgressBarState, AnimatedState,
)
from castella.animation import ValueTween, AnimationScheduler, EasingFunction
from castella.frame import Frame


class AnimationDemo(Component):
    def __init__(self):
        super().__init__()
        # ProgressBar for ValueTween demo
        self._progress = ProgressBarState(0, min_val=0, max_val=100)
        self._progress.attach(self)

        # AnimatedState for automatic animation
        self._counter = AnimatedState(0, duration_ms=300)
        self._counter.attach(self)

    def view(self):
        return Column(
            Text("ValueTween Demo"),
            ProgressBar(self._progress).fixed_height(24),
            Button("Animate").on_click(self._animate),

            Text(f"Counter: {self._counter()}"),
            Button("+10").on_click(lambda _: self._counter.set(self._counter() + 10)),
        )

    def _animate(self, _):
        self._progress.set(0)
        AnimationScheduler.get().add(
            ValueTween(
                from_value=0,
                to_value=100,
                duration_ms=1500,
                easing=EasingFunction.BOUNCE,
                on_update=lambda v: self._progress.set(v),
            )
        )


App(Frame("Animation Demo", 400, 300), AnimationDemo()).run()
```

## TUI Support

In terminal mode, animations run at a lower frame rate (10 FPS) for better performance. The animation system automatically detects terminal mode via the `CASTELLA_IS_TERMINAL_MODE` environment variable.
