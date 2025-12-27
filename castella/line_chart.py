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


class LineChartState(ObservableBase):
    def __init__(self, value: Sequence[float]) -> None:
        super().__init__()
        self._value = value

    def get_value(self) -> Sequence[float]:
        return self._value

    def set(self, value: Sequence[float]) -> Self:
        self._value = value
        self.notify()
        return self


class LineChart(Widget):
    def __init__(self, data: LineChartState):
        super().__init__(
            state=data,
            size=Size(width=0, height=0),
            pos=Point(x=0, y=0),
            pos_policy=None,
            width_policy=SizePolicy.CONTENT,
            height_policy=SizePolicy.CONTENT,
        )
        self._fig, self._ax = plt.subplots()
        self._update_image()

    def _update_image(self) -> None:
        data: LineChartState = cast(LineChartState, self._state)

        fig = self._fig
        ax = self._ax
        ax.cla()
        fig.canvas.draw()
        fig, ax = plt.subplots()
        value = data.get_value()
        ax.plot(range(len(value)), value)
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
