"""Animation demo for Castella UI framework.

This demo showcases the animation system:
- ValueTween: Animate values over time with easing
- AnimatedState: State that automatically animates between values
- ProgressBar: Visual progress indicator with animation
"""

from castella import (
    App,
    AnimatedState,
    Button,
    Column,
    Component,
    ProgressBar,
    ProgressBarState,
    Row,
    SizePolicy,
    Spacer,
    State,
    Text,
)
from castella.animation import ValueTween, AnimationScheduler, EasingFunction
from castella.frame import Frame


class AnimationDemo(Component):
    """Demo component showcasing animation features."""

    def __init__(self):
        super().__init__()
        # ProgressBar state for ValueTween demo
        self._progress_state = ProgressBarState(0, min_val=0, max_val=100)
        self._progress_state.attach(self)

        # AnimatedState demo
        self._counter = AnimatedState(0, duration_ms=300)
        self._counter.attach(self)

        self._status = State("Click a button to start animation")
        self._status.attach(self)

    def view(self):
        return Column(
            Text("Castella Animation Demo")
            .text_color("#7aa2f7")
            .fixed_height(40),
            Spacer().fixed_height(10),

            # ValueTween section
            Text("ValueTween Demo").fixed_height(25),

            # Progress bar (animated)
            ProgressBar(self._progress_state)
            .track_color("#1a1b26")
            .fill_color("#9ece6a")
            .border_radius(4)
            .fixed_height(24),

            Text(f"{self._progress_state():.0f}%")
            .text_color("#9ece6a")
            .fixed_height(25),

            Row(
                Button("Linear").on_click(
                    lambda _: self._animate(EasingFunction.LINEAR)
                ),
                Spacer().fixed_width(5),
                Button("Ease Out").on_click(
                    lambda _: self._animate(EasingFunction.EASE_OUT_CUBIC)
                ),
                Spacer().fixed_width(5),
                Button("Bounce").on_click(
                    lambda _: self._animate(EasingFunction.BOUNCE)
                ),
            ).fixed_height(40),
            Spacer().fixed_height(20),

            # AnimatedState section
            Text("AnimatedState Demo").fixed_height(25),
            Text(f"Counter: {self._counter()}")
            .text_color("#bb9af7")
            .fixed_height(35),
            Row(
                Button("-10").on_click(self._decrement),
                Spacer().fixed_width(10),
                Text(f"{self._counter()}").fixed_width(80),
                Spacer().fixed_width(10),
                Button("+10").on_click(self._increment),
            ).fixed_height(40),

            # Status
            Spacer(),
            Text(self._status())
            .text_color("#565f89")
            .fixed_height(30),
        ).height_policy(SizePolicy.EXPANDING)

    def _animate(self, easing: EasingFunction):
        # Reset and animate
        self._progress_state.set(0)
        self._status.set(f"Animating with {easing.value}...")

        AnimationScheduler.get().add(
            ValueTween(
                from_value=0,
                to_value=100,
                duration_ms=1500,
                easing=easing,
                on_update=lambda v: self._progress_state.set(v),
                on_complete=lambda: self._status.set(
                    f"Animation complete ({easing.value})"
                ),
            )
        )

    def _increment(self, _):
        self._counter.set(self._counter() + 10)
        self._status.set("AnimatedState: +10")

    def _decrement(self, _):
        self._counter.set(self._counter() - 10)
        self._status.set("AnimatedState: -10")


def main():
    app = App(Frame("Animation Demo", 450, 400), AnimationDemo())
    app.run()


if __name__ == "__main__":
    main()
