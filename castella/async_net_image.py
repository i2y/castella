from typing import Self, cast

from castella.core import Painter, Point, SimpleValue, Size, SizePolicy, State, Widget


class AsyncNetImage(Widget):
    def __init__(self, url: str | SimpleValue[str]):
        if isinstance(url, SimpleValue):
            state = url
        else:
            state = State(url)

        super().__init__(
            state=state,
            size=Size(width=0, height=0),
            pos=Point(x=0, y=0),
            pos_policy=None,
            width_policy=SizePolicy.FIXED,
            height_policy=SizePolicy.FIXED,
        )

    def redraw(self, p: Painter, _: bool) -> None:
        state: SimpleValue[str] = cast(SimpleValue[str], self._state)
        url = state.value()
        img = p.get_net_image_async(url, url, self.callback)
        if img is None:
            return
        p.draw_image_object(img, 0, 0)

    def callback(self) -> None:
        if self.get_parent() is None:
            self.update()
        else:
            self.ask_parent_to_render(True)

    def width_policy(self, sp: SizePolicy) -> Self:
        if sp is SizePolicy.CONTENT:
            raise RuntimeError("AsyncNetImage doesn't accept SizePolicy.CONTENT")
        return super().width_policy(sp)

    def height_policy(self, sp: SizePolicy) -> Self:
        if sp is SizePolicy.CONTENT:
            raise RuntimeError("AsyncNetImage doesn't accept SizePolicy.CONTENT")
        return super().height_policy(sp)
