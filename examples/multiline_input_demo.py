"""Demo for MultilineInput widget."""

from castella import (
    App,
    Column,
    MultilineInput,
    MultilineInputState,
    SizePolicy,
    Text,
)
from castella.frame import Frame


def main():
    state = MultilineInputState("Type here...\nThis is a multi-line editor.\nUse arrow keys to navigate.")

    def on_change(text: str):
        line_count = text.count("\n") + 1
        print(f"Lines: {line_count}, Characters: {len(text)}")

    app = App(
        Frame("MultilineInput Demo", width=600, height=400),
        Column(
            Text("Multi-line Text Editor"),
            MultilineInput(state, font_size=14, padding=12)
            .width_policy(SizePolicy.EXPANDING)
            .height_policy(SizePolicy.EXPANDING)
            .on_change(on_change),
        ),
    )
    app.run()


if __name__ == "__main__":
    main()
