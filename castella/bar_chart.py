from collections.abc import Sequence
from typing import Self, cast

import matplotlib.pyplot as plt
import numpy as np

from castella.core import (
    Painter,
    Point,
    Size,
    SizePolicy,
    Rect,
    Widget,
    ObservableBase,
)


class BarChartState(ObservableBase):
    def __init__(self, label: Sequence[str], value: Sequence[float]) -> None:
        super().__init__()
        self._label = label
        self._value = value

    def get_label(self) -> Sequence[str]:
        return self._label

    def get_value(self) -> Sequence[float]:
        return self._value

    def set(self, label: Sequence[str], value: Sequence[float]) -> Self:
        self._label = label
        self._value = value
        self.notify()
        return self


class BarChart(Widget):
    def __init__(self, data: BarChartState):
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
        data: BarChartState = cast(BarChartState, self._state)

        fig = self._fig
        ax = self._ax
        ax.cla()
        fig.canvas.draw()
        ax.bar(
            range(len(data.get_label())),
            data.get_value(),
            tick_label=data.get_label(),
            align="center",
        )
        fig.canvas.draw()
        array = np.array(fig.canvas.renderer.buffer_rgba())
        self._np_array = array

    def on_notify(self, ev=None) -> None:
        self._update_image()
        super().on_notify(ev)

    def redraw(self, p: Painter, _: bool) -> None:
        p.draw_np_array_as_an_image_rect(
            self._np_array, Rect(origin=Point(x=0, y=0), size=self.get_size())
        )

    def measure(self, p: Painter) -> Size:
        return p.measure_np_array_as_an_image(self._np_array)
