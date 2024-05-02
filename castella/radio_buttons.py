from collections.abc import Sequence
from typing import Self

from castella import (
    CheckBox,
    Column,
    Row,
    StatefulComponent,
    Text,
    TextAlign,
    ObservableBase,
)


class RadioButtonsState(ObservableBase):
    def __init__(self, labels: Sequence[str], selected_index: int = 0) -> None:
        super().__init__()
        self._labels = labels
        self._selected_index = selected_index

    def select(self, index: int) -> Self:
        self._selected_index = index
        self.notify()
        return self

    def labels(self) -> Sequence[str]:
        return self._labels

    def selected_index(self) -> int:
        return self._selected_index


class RadioButtons(StatefulComponent):
    def __init__(self, state: RadioButtonsState):
        super().__init__(state)
        self._state = state
        self._button_width = 40

    def view(self):
        check_boxes = []
        selected_index = self._state.selected_index()
        for i, label in enumerate(self._state.labels()):
            check_boxes.append(
                Row(
                    CheckBox(i == selected_index, is_circle=True)
                    .on_click(self._create_select_callback(i))
                    .fixed_width(self._button_width),
                    # .fixed_size(self._style.font.size, self._.font.size),
                    Text(label, align=TextAlign.LEFT).erase_border(),
                )
            )
        return Column(*check_boxes)

    def button_width(self, width: int) -> Self:
        self._button_width = width
        return self

    def _create_select_callback(self, index: int):
        return lambda _: self._state.select(index)
