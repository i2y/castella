"""Demo for new widgets: Slider, Tabs, Modal, DateTimeInput."""

from castella import (
    App,
    Column,
    Row,
    Text,
    Button,
    Spacer,
    Slider,
    SliderState,
    Tabs,
    TabsState,
    TabItem,
    DateTimeInput,
    DateTimeInputState,
)
from castella.core import Component, State
from castella.frame import Frame
from castella.theme import ThemeManager


class NewWidgetsDemo(Component):
    """Demo showcasing Slider, Tabs, and DateTimeInput widgets."""

    def __init__(self):
        super().__init__()

        # Slider state
        self._slider_value = SliderState(50, 0, 100)
        self._slider_value.attach(self)

        # DateTimeInput state
        self._datetime_state = DateTimeInputState(
            value="2024-12-25T14:30:00",
            enable_date=True,
            enable_time=True,
        )
        self._datetime_state.attach(self)

        # Tab selection state
        self._tab_id = State("slider")
        self._tab_id.attach(self)

    def view(self):
        theme = ThemeManager().current

        # Build tab content
        slider_content = self._build_slider_demo(theme)
        datetime_content = self._build_datetime_demo(theme)

        # Create tabs
        tabs_state = TabsState([
            TabItem(id="slider", label="Slider", content=slider_content),
            TabItem(id="datetime", label="DateTime", content=datetime_content),
        ], self._tab_id())

        tabs = Tabs(tabs_state).on_change(lambda id: self._tab_id.set(id))

        return Column(
            Text("New Widgets Demo")
            .text_color(theme.colors.text_primary)
            .fixed_height(40),
            tabs,
        ).bg_color(theme.colors.bg_primary)

    def _build_slider_demo(self, theme):
        """Build slider demo content."""
        value = self._slider_value.value()

        return Column(
            Text("Slider Widget")
            .text_color(theme.colors.text_primary)
            .fixed_height(30),
            Text(f"Value: {value:.1f}")
            .text_color(theme.colors.text_info)
            .fixed_height(24),
            Slider(self._slider_value)
            .fixed_height(40),
            Spacer(),
            Row(
                Button("Set 0").on_click(lambda _: self._slider_value.set(0)),
                Button("Set 50").on_click(lambda _: self._slider_value.set(50)),
                Button("Set 100").on_click(lambda _: self._slider_value.set(100)),
            ).fixed_height(50),
        ).bg_color(theme.colors.bg_secondary)

    def _build_datetime_demo(self, theme):
        """Build datetime input demo content."""
        iso_value = self._datetime_state.to_iso() or "Not set"
        display_value = self._datetime_state.to_display_string() or "Not set"

        return Column(
            Text("DateTimeInput Widget")
            .text_color(theme.colors.text_primary)
            .fixed_height(30),
            Text(f"Display: {display_value}")
            .text_color(theme.colors.text_info)
            .fixed_height(24),
            Text(f"ISO: {iso_value}")
            .text_color(theme.colors.text_info)
            .fixed_height(24),
            DateTimeInput(state=self._datetime_state, label="Select Date & Time")
            .fixed_height(100),
            Spacer(),
            Button("Clear")
            .on_click(lambda _: self._datetime_state.set(None))
            .fixed_height(40),
        ).bg_color(theme.colors.bg_secondary)


if __name__ == "__main__":
    app = App(
        Frame("New Widgets Demo", 600, 500),
        NewWidgetsDemo(),
    )
    app.run()
