from typing import Self

from castella.core import MouseEvent, Painter, Point, Size, SizePolicy, Widget


class Spacer(Widget):
    def __init__(self):
        super().__init__(
            state=None,
            size=Size(width=0, height=0),
            pos=Point(x=0, y=0),
            pos_policy=None,
            width_policy=SizePolicy.EXPANDING,
            height_policy=SizePolicy.EXPANDING,
        )

    def mouse_down(self, _: MouseEvent) -> None:
        pass

    def mouse_up(self, _: MouseEvent) -> None:
        pass

    def redraw(self, _: Painter, completely: bool) -> None:
        pass

    def width_policy(self, sp: SizePolicy) -> Self:
        if sp is SizePolicy.CONTENT:
            raise RuntimeError("Spacer doesn't accept SizePolicy.CONTENT")
        return super().width_policy(sp)

    def height_policy(self, sp: SizePolicy) -> Self:
        if sp is SizePolicy.CONTENT:
            raise RuntimeError("Spacer doesn't accept SizePolicy.CONTENT")
        return super().height_policy(sp)
