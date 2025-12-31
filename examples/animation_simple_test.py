"""Simple animation test - demonstrates ValueTween and AnimatedState."""

from castella import (
    App, Button, Column, Component, Row, Text, SizePolicy, Spacer,
    AnimatedState, ProgressBar, ProgressBarState,
)
from castella.animation import ValueTween, AnimationScheduler, EasingFunction
from castella.frame import Frame


class SimpleTest(Component):
    """Test animation with ProgressBar display."""

    def __init__(self):
        super().__init__()
        # ProgressBarState for ValueTween demo
        self._progress = ProgressBarState(0, min_val=0, max_val=100)
        self._progress.attach(self)

        # AnimatedState for auto-animation demo
        self._counter = AnimatedState(0, duration_ms=300)
        self._counter.attach(self)

    def view(self):
        return Column(
            Text("Animation Demo").fixed_height(30),
            Spacer().fixed_height(10),

            # ValueTween demo
            Text("ValueTween:").fixed_height(25),
            ProgressBar(self._progress)
            .track_color("#1a1b26")
            .fill_color("#9ece6a")
            .fixed_height(20)
            .fixed_width(250),
            Text(f"{self._progress():.0f}%").fixed_height(25),
            Button("Animate 0->100").on_click(self._animate_tween),
            Spacer().fixed_height(20),

            # AnimatedState demo
            Text("AnimatedState:").fixed_height(25),
            Text(f"Counter: {self._counter()}").fixed_height(30),
            Row(
                Button("-10").on_click(lambda _: self._counter.set(self._counter() - 10)),
                Spacer().fixed_width(10),
                Button("+10").on_click(lambda _: self._counter.set(self._counter() + 10)),
            ).fixed_height(40),
        ).height_policy(SizePolicy.EXPANDING)

    def _animate_tween(self, _):
        # Reset to 0 first
        self._progress.set(0)
        print("Starting ValueTween animation...")
        AnimationScheduler.get().add(
            ValueTween(
                from_value=0,
                to_value=100,
                duration_ms=1500,
                easing=EasingFunction.EASE_OUT_CUBIC,
                on_update=lambda v: self._progress.set(v),
                on_complete=lambda: print("Done!"),
            )
        )


def main():
    app = App(Frame("Animation Test", 400, 350), SimpleTest())
    app.run()


if __name__ == "__main__":
    main()
