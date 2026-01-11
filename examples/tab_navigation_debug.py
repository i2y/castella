"""Tab Navigation Debug Demo"""

from castella import App, Box, Button, Column, Input, Row, Spacer, Text
from castella.frame import Frame
from castella.multiline_input import MultilineInput, MultilineInputState


def main():
    message_state = MultilineInputState("")

    widget = Column(
        Text("Tab Navigation Debug").fixed_height(30),
        Spacer().fixed_height(10),
        Row(
            Text("Name:").fixed_width(80).fixed_height(30),
            Input("").tab_index(1).fixed_height(30),
        ).fixed_height(30),
        Spacer().fixed_height(10),
        Row(
            Text("Email:").fixed_width(80).fixed_height(30),
            Input("").tab_index(2).fixed_height(30),
        ).fixed_height(30),
        Spacer().fixed_height(10),
        Row(
            Text("Message:").fixed_width(80).fixed_height(100),
            MultilineInput(message_state, font_size=14, wrap=True)
            .tab_index(3)
            .fixed_height(100),
        ).fixed_height(100),
        Spacer().fixed_height(20),
        Row(
            Button("Submit").tab_index(4).fixed_width(100),
            Spacer().fixed_width(10),
            Button("Clear").tab_index(5).fixed_width(100),
        ).fixed_height(35),
    ).fixed_size(400, 350)

    root = Box(widget)
    frame = Frame("Tab Navigation Debug", 450, 400)
    app = App(frame, root)

    # Patch input_key to add debug logging
    original_input_key = app.input_key

    def debug_input_key(ev):
        from castella.models.events import KeyCode

        if ev.key == KeyCode.TAB:
            focus_mgr = app._event_manager.focus
            print(f"TAB pressed. Current focus: {focus_mgr.focus}")
            print(f"  Focusables: {[f.__class__.__name__ for f in focus_mgr._focusables]}")
        result = original_input_key(ev)
        if ev.key == KeyCode.TAB:
            focus_mgr = app._event_manager.focus
            print(f"  After TAB: focus = {focus_mgr.focus}")
            if focus_mgr.focus:
                print(f"    Class: {focus_mgr.focus.__class__.__name__}")
        return result

    app.input_key = debug_input_key

    app.run()


if __name__ == "__main__":
    main()
