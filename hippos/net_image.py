from typing import cast

from hippos.core import (
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
            size=Size(0, 0),
            pos=Point(0, 0),
            pos_policy=None,
            width_policy=SizePolicy.CONTENT,
            height_policy=SizePolicy.CONTENT,
        )

    def redraw(self, p: Painter, _: bool) -> None:
        state: SimpleValue[str] = cast(SimpleValue[str], self._state)
        p.draw_net_image(
            state.value(), Rect(Point(0, 0), self.get_size()), self._use_cache
        )

    def measure(self, p: Painter) -> Size:
        state: SimpleValue[str] = cast(SimpleValue[str], self._state)
        return p.measure_net_image(state.value())
