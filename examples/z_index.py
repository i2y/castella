"""Z-index example demonstrating widget stacking order.

This example shows how z_index() controls which widgets appear on top.
Higher z-index values appear on top of lower ones.
"""

from castella import (
    App,
    Box,
    Button,
    Column,
    Component,
    Row,
    Spacer,
    MultilineText,
    State,
    Text,
    Kind,
)
from castella.frame import Frame


class StackedDialogsDemo(Component):
    """Multiple stacked dialogs - click buttons to change stacking order."""

    def __init__(self):
        super().__init__()
        # Track the order: list of dialog numbers from back to front
        # e.g., [1, 2, 3] means Dialog 1 at back, Dialog 3 at front
        self._order = State([1, 2, 3])
        self.model(self._order)

    def _bring_to_front(self, dialog_num):
        """Bring specified dialog to front."""
        order = list(self._order())
        order.remove(dialog_num)
        order.append(dialog_num)
        self._order.set(order)

    def _send_to_back(self, dialog_num):
        """Send specified dialog to back."""
        order = list(self._order())
        order.remove(dialog_num)
        order.insert(0, dialog_num)
        self._order.set(order)

    def view(self):
        order = self._order()
        # z-index based on position in order (1-indexed)
        z1 = order.index(1) + 1
        z2 = order.index(2) + 1
        z3 = order.index(3) + 1

        # Dialog 1 - largest (blue)
        dialog1 = Column(
            Text(f"Dialog 1 (z-index: {z1})", font_size=14),
            MultilineText("Largest dialog\nBlue/INFO style", font_size=12, kind=Kind.INFO),
            Spacer(),
            Row(
                Button("Front").on_click(lambda _: self._bring_to_front(1)),
                Button("Back").on_click(lambda _: self._send_to_back(1)),
            ).fixed_height(35),
        ).fixed_size(320, 240).z_index(z1)

        # Dialog 2 - medium (green)
        dialog2 = Column(
            Text(f"Dialog 2 (z-index: {z2})", font_size=14),
            MultilineText("Medium dialog\nGreen/SUCCESS style", font_size=12, kind=Kind.SUCCESS),
            Spacer(),
            Row(
                Button("Front").on_click(lambda _: self._bring_to_front(2)),
                Button("Back").on_click(lambda _: self._send_to_back(2)),
            ).fixed_height(35),
        ).fixed_size(250, 190).z_index(z2)

        # Dialog 3 - smallest (red)
        dialog3 = Column(
            Text(f"Dialog 3 (z-index: {z3})", font_size=14),
            MultilineText("Smallest dialog\nRed/DANGER style", font_size=12, kind=Kind.DANGER),
            Spacer(),
            Row(
                Button("Front").on_click(lambda _: self._bring_to_front(3)),
                Button("Back").on_click(lambda _: self._send_to_back(3)),
            ).fixed_height(35),
        ).fixed_size(200, 150).z_index(z3)

        stacked = Box(dialog1, dialog2, dialog3)

        # Header showing current order
        front_dialog = order[-1]
        header = Column(
            Text("Stacked Dialogs Demo", font_size=18),
            Text(f"Order (back to front): {order} - Dialog {front_dialog} is on top"),
        ).fixed_height(50)

        return Column(header, stacked)


class ModalDemo(Component):
    """Demonstrates modal dialog using z-index."""

    def __init__(self):
        super().__init__()
        self._show_modal = State(False)
        self.model(self._show_modal)

    def view(self):
        main_content = Column(
            Text("Modal Dialog Demo", font_size=24),
            Spacer(),
            Row(
                Spacer(),
                Button("Open Modal").on_click(lambda _: self._show_modal.set(True)),
                Spacer(),
            ).fixed_height(50),
            Spacer(),
            Text("Click the button to open a modal dialog"),
            Text("The modal appears on top using z-index"),
        ).z_index(1)

        if self._show_modal():
            modal = Column(
                MultilineText(
                    "Modal Dialog\n\nThis dialog has z-index: 10\nIt appears on top of everything",
                    font_size=16,
                    kind=Kind.WARNING,
                ),
                Spacer(),
                Button("Close").on_click(lambda _: self._show_modal.set(False)),
            ).fixed_size(300, 200).z_index(10)

            return Box(main_content, modal)

        return main_content


# Run the Stacked Dialogs demo
# Change to ModalDemo() to see the modal example
App(
    Frame("Z-Index Demo", width=480, height=400),
    StackedDialogsDemo(),
).run()
