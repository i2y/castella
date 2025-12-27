from typing import cast

from castella.core import (
    Painter,
    Point,
    Rect,
    SimpleValue,
    Size,
    SizePolicy,
    State,
    Widget,
)


class NetImage(Widget):
    def __init__(self, url: str | SimpleValue[str], use_cache: bool = True):
        if isinstance(url, SimpleValue):
            state = url
        else:
            state = State(url)

        self._use_cache = use_cache

        super().__init__(
            state=state,
            size=Size(width=0, height=0),
            pos=Point(x=0, y=0),
            pos_policy=None,
            width_policy=SizePolicy.CONTENT,
            height_policy=SizePolicy.CONTENT,
        )

    def redraw(self, p: Painter, _: bool) -> None:
        state: SimpleValue[str] = cast(SimpleValue[str], self._state)
        p.draw_net_image(
            state.value(),
            Rect(origin=Point(x=0, y=0), size=self.get_size()),
            self._use_cache,
        )

    def measure(self, p: Painter) -> Size:
        state: SimpleValue[str] = cast(SimpleValue[str], self._state)
        return p.measure_net_image(state.value())
