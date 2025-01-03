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


class Image(Widget):
    def __init__(self, file_path: str | SimpleValue[str], use_cache: bool = True):
        if isinstance(file_path, SimpleValue):
            state = file_path
        else:
            state = State(file_path)

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
        p.draw_image(state.value(), Rect(Point(0, 0), self.get_size()), self._use_cache)

    def measure(self, p: Painter) -> Size:
        state: SimpleValue[str] = cast(SimpleValue[str], self._state)
        return p.measure_image(state.value())
