# Castella Animation System

Smooth property animations with easing functions and reactive state transitions.

## AnimationScheduler

Singleton managing the animation tick loop (60 FPS desktop, 10 FPS TUI):

```python
from castella.animation import AnimationScheduler

scheduler = AnimationScheduler.get()
scheduler.add(tween)     # Add animation
```

## Easing Functions

Available easing functions:

```python
from castella.animation import EasingFunction

EasingFunction.LINEAR           # Constant speed
EasingFunction.EASE_IN          # Slow start
EasingFunction.EASE_OUT         # Slow end
EasingFunction.EASE_IN_OUT      # Slow start and end
EasingFunction.EASE_IN_CUBIC    # Cubic slow start
EasingFunction.EASE_OUT_CUBIC   # Cubic slow end
EasingFunction.EASE_IN_OUT_CUBIC  # Cubic slow start and end
EasingFunction.BOUNCE           # Bouncy effect
```

## Tween

Animate widget properties:

```python
from castella.animation import Tween, AnimationScheduler, EasingFunction

tween = Tween(
    target=my_widget,
    property_name="x",      # "x", "y", "width", "height"
    from_value=0,
    to_value=200,
    duration_ms=500,
    easing=EasingFunction.EASE_OUT_CUBIC,
    on_complete=lambda: print("Done!"),
)
AnimationScheduler.get().add(tween)
```

## ValueTween

Generic value interpolation with callbacks:

```python
from castella.animation import ValueTween, AnimationScheduler

def on_update(value):
    my_state.set(value)

tween = ValueTween(
    from_value=0,
    to_value=100,
    duration_ms=500,
    on_update=on_update,
    on_complete=lambda: print("Animation complete!"),
)
AnimationScheduler.get().add(tween)
```

## AnimatedState

State wrapper that automatically animates between values:

```python
from castella import Component, Column, Text, Button
from castella.animation import AnimatedState

class Counter(Component):
    def __init__(self):
        super().__init__()
        # Value changes animate smoothly over 200ms
        self._value = AnimatedState(0, duration_ms=200)
        self._value.attach(self)

    def view(self):
        return Column(
            Text(f"Value: {self._value():.1f}"),
            Button("Add 10").on_click(lambda _: self._value.set(self._value() + 10)),
        )
```

### AnimatedState Control

```python
state = AnimatedState(0, duration_ms=300)

state.set(100)                    # Animate to value (default)
state.set(100, animate=True)      # Explicit animate
state.set_immediate(100)          # Set without animation
state.stop()                      # Stop at current value
state.finish()                    # Jump to target value
```

## Widget Animation Methods

Convenient animation methods on widgets:

### animate_to

Animate to target position/size:

```python
widget.animate_to(x=200, y=100, duration_ms=400)
widget.animate_to(width=300, height=200, easing=EasingFunction.BOUNCE)
```

### slide_in / slide_out

Slide animations from/to directions:

```python
# Slide in from direction
widget.slide_in("left", distance=100, duration_ms=300)
widget.slide_in("right", distance=100, duration_ms=300)
widget.slide_in("top", distance=100, duration_ms=300)
widget.slide_in("bottom", distance=100, duration_ms=300)

# Slide out to direction
widget.slide_out("left", distance=100, duration_ms=300)
widget.slide_out("right", distance=100, duration_ms=300)
```

## Animation Control

### Cancel Animation

```python
tween = Tween(...)
AnimationScheduler.get().add(tween)

# Later, cancel if needed
tween.cancel()
```

## Animation Patterns

### Fade In Effect

```python
from castella.animation import ValueTween, AnimationScheduler

def fade_in(widget, duration_ms=300):
    def update_opacity(value):
        widget.opacity = value

    AnimationScheduler.get().add(
        ValueTween(0, 1, duration_ms, on_update=update_opacity)
    )
```

### Staggered Animations

```python
import time
from castella.animation import Tween, AnimationScheduler

def stagger_slide_in(widgets, delay_ms=50):
    for i, widget in enumerate():
        widget.x = -100  # Start off-screen

        def delayed_animation(w=widget, d=i * delay_ms):
            time.sleep(d / 1000)
            AnimationScheduler.get().add(
                Tween(w, "x", -100, 0, 300, EasingFunction.EASE_OUT)
            )

        threading.Thread(target=delayed_animation).start()
```

### Progress Animation

```python
from castella.animation import ValueTween, AnimationScheduler

def animate_progress(state, target_value, duration_ms=500):
    current = state.value()

    AnimationScheduler.get().add(
        ValueTween(
            current, target_value, duration_ms,
            on_update=lambda v: state.set(v),
        )
    )
```
