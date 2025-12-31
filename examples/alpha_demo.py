"""Alpha channel demo - demonstrates color transparency with buttons."""

from castella import App, Box, Button, Column, Row, Text
from castella.core import Component, SizePolicy, State
from castella.frame import Frame


class StylishAlphaDemo(Component):
    """Demonstrates alpha channel with layered buttons."""

    def __init__(self):
        super().__init__()
        self._alpha = State(128)
        self._alpha.attach(self)

    def view(self):
        alpha = self._alpha()
        alpha_hex = f"{alpha:02x}"

        return Column(
            # Title
            Text("Alpha Channel Demo", font_size=22),
            Text(f"Alpha: {alpha} (0x{alpha_hex.upper()}) = {alpha * 100 // 255}%"),
            # Controls
            Row(
                Button("-20").on_click(lambda _: self._adjust(-20)),
                Button("-5").on_click(lambda _: self._adjust(-5)),
                Button("+5").on_click(lambda _: self._adjust(5)),
                Button("+20").on_click(lambda _: self._adjust(20)),
            ).fixed_height(45),
            Row(
                Button("0%").on_click(lambda _: self._alpha.set(0)),
                Button("25%").on_click(lambda _: self._alpha.set(64)),
                Button("50%").on_click(lambda _: self._alpha.set(128)),
                Button("75%").on_click(lambda _: self._alpha.set(192)),
                Button("100%").on_click(lambda _: self._alpha.set(255)),
            ).fixed_height(45),
            # Demo 1: Overlay effect
            Text("Overlay (blue over red):"),
            Box(
                Button("RED BASE").bg_color("#ff0000").fixed_size(300, 100).z_index(1),
                Button(f"BLUE α={alpha}").bg_color(f"#0000ff{alpha_hex}").fixed_size(300, 100).z_index(2),
            ).fixed_height(110),
            # Demo 2: Three layers
            Text("Three layers (R→G→B):"),
            Box(
                Button("R").bg_color("#ff0000").fixed_size(180, 80).z_index(1),
                Button("G").bg_color(f"#00ff00{alpha_hex}").fixed_size(180, 80).z_index(2),
                Button("B").bg_color(f"#0000ff{alpha_hex}").fixed_size(180, 80).z_index(3),
            ).fixed_height(90),
            # Demo 3: Gradient effect
            Text("Alpha gradient (100% → 10%):"),
            Row(
                Button("100%").bg_color("#e94560ff"),
                Button("75%").bg_color("#e94560c0"),
                Button("50%").bg_color("#e9456080"),
                Button("25%").bg_color("#e9456040"),
                Button("10%").bg_color("#e945601a"),
            ).fixed_height(50),
            # Demo 4: Glass buttons
            Text("Glass effect buttons:"),
            Row(
                Button("Glass").bg_color("#ffffff20"),
                Button("Glass").bg_color("#ffffff30"),
                Button("Glass").bg_color("#ffffff40"),
                Button("Glass").bg_color("#ffffff50"),
            ).fixed_height(50),
        )

    def _adjust(self, delta: int):
        self._alpha.set(max(0, min(255, self._alpha() + delta)))


if __name__ == "__main__":
    app = App(Frame("Alpha Channel Demo", 700, 550), StylishAlphaDemo())
    app.run()
