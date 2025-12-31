"""Demo for the enhanced DateTimeInput with calendar picker."""


from castella import (
    App,
    Column,
    DateTimeInput,
    DateTimeInputState,
    Spacer,
    Text,
)
from castella.frame import Frame
from castella.theme import ThemeManager


def main():
    """Run the calendar demo."""
    ThemeManager()
    theme = ThemeManager().current

    # Create state
    date_state = DateTimeInputState(
        value="2024-12-25",
        enable_date=True,
        enable_time=False,
    )

    ui = Column(
        Text("DateTimeInput Calendar Picker Demo")
        .text_color(theme.colors.text_info)
        .fixed_height(40),
        Text("Select a date:").text_color(theme.colors.text_primary)
        .fixed_height(24),
        DateTimeInput(state=date_state, label="Birthday")
        .on_change(lambda v: print(f"Date selected: {v}")),
        Spacer(),
    ).bg_color(theme.colors.bg_canvas)

    frame = Frame("Calendar Demo", 400, 500)
    app = App(frame, ui)
    app.run()


if __name__ == "__main__":
    main()
