from collections.abc import Sequence
from typing import Self, cast

import matplotlib.pyplot as plt
import numpy as np

from castella.core import (
    Painter,
    Point,
    Size,
    SizePolicy,
    Widget,
    ObservableBase,
)


class PieChartState(ObservableBase):
    def __init__(self, label: list[str], value: Sequence[float]) -> None:
        super().__init__()
        self._label = label
        self._value = value

    def get_label(self) -> list[str]:
        return self._label

    def get_value(self) -> Sequence[float]:
        return self._value

    def set(self, label: list[str], value: Sequence[float]) -> Self:
        self._label = label
        self._value = value
        self.notify()
        return self


class PieChart(Widget):
    def __init__(self, data: PieChartState):
        super().__init__(
            state=data,
            size=Size(0, 0),
            pos=Point(0, 0),
            pos_policy=None,
            width_policy=SizePolicy.CONTENT,
            height_policy=SizePolicy.CONTENT,
        )
        self._fig, self._ax = plt.subplots()
        self._update_image()

    def _update_image(self) -> None:
        data: PieChartState = cast(PieChartState, self._state)

        fig = self._fig
        ax = self._ax
        ax.cla()
        fig.canvas.draw()
        ax.pie(
            data.get_value(),
            labels=data.get_label(),
        )
        fig.canvas.draw()
        array = np.array(fig.canvas.renderer.buffer_rgba())
        self._np_array = array

    def on_notify(self) -> None:
        self._update_image()
        super().on_notify()

    def redraw(self, p: Painter, _: bool) -> None:
        p.draw_np_array_as_an_image(self._np_array, 0, 0)

    def measure(self, p: Painter) -> Size:
        return p.measure_np_array_as_an_image(self._np_array)
