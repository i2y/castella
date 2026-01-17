"""Alpha channel demo - demonstrates color transparency."""

from castella import App, Box, Button, Column, Row, Text
from castella.core import SizePolicy, State, StatefulComponent
from castella.frame import Frame


class AlphaDemo(StatefulComponent):
    """Demonstrates alpha channel with buttons and layouts."""

    def __init__(self):
        self._alpha = State(128)
        super().__init__(self._alpha)

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
            # Demo 1: Text with transparent_bg inside colored Column
            Text("Text with transparent_bg inside colored layouts:"),
            Row(
                Column(Text("On Red", transparent_bg=True)).bg_color("#ff0000").width_policy(SizePolicy.EXPANDING),
                Column(Text("On Green", transparent_bg=True)).bg_color("#00ff00").width_policy(SizePolicy.EXPANDING),
                Column(Text("On Blue", transparent_bg=True)).bg_color("#0000ff").width_policy(SizePolicy.EXPANDING),
            ).fixed_height(50),
            # Demo 2: Overlay with Layout
            Text("Box with alpha background:"),
            Box(
                Button("Button inside").fixed_size(200, 50),
            ).bg_color(f"#e94560{alpha_hex}").fixed_height(70),
            # Demo 3: Button layers
            Text("Button overlay (blue over red):"),
            Box(
                Button("RED BASE").bg_color("#ff0000").fixed_size(250, 70).z_index(1),
                Button(f"BLUE α={alpha}").bg_color(f"#0000ff{alpha_hex}").fixed_size(250, 70).z_index(2),
            ).fixed_height(80),
            # Demo 4: Gradient effect
            Text("Alpha gradient:"),
            Row(
                Button("100%").bg_color("#9333eaff"),
                Button("75%").bg_color("#9333eac0"),
                Button("50%").bg_color("#9333ea80"),
                Button("25%").bg_color("#9333ea40"),
                Button("10%").bg_color("#9333ea1a"),
            ).fixed_height(45),
        )

    def _adjust(self, delta: int):
        self._alpha.set(max(0, min(255, self._alpha() + delta)))


if __name__ == "__main__":
    app = App(Frame("Alpha Channel Demo", 700, 550), AlphaDemo())
    app.run()
