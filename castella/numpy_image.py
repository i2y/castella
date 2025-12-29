import sys
from typing import cast

try:
    import numpy as np
except ImportError:
    import_success = False
else:
    import_success = True

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

if import_success and "pyodide" in sys.modules:

    class NumpyImage(Widget):  # type: ignore
        def __init__(self, array: np.ndarray | SimpleValue[np.ndarray]):
            if isinstance(array, SimpleValue):
                state = array
            else:
                state = State(array)

            super().__init__(
                state=state,
                size=Size(width=0, height=0),
                pos=Point(x=0, y=0),
                pos_policy=None,
                width_policy=SizePolicy.FIXED,
                height_policy=SizePolicy.FIXED,
            )

        def redraw(self, p: Painter, _: bool) -> None:
            state: SimpleValue[np.ndarray] = cast(SimpleValue[np.ndarray], self._state)
            array = state.value()
            img = p.get_numpy_image_async(array, self.callback)
            if img is None:
                return
            p.draw_image_object(img, 0, 0)

        def callback(self):
            self.dirty(True)
            if self.get_parent() is None:
                self.update()
            else:
                self.ask_parent_to_render(True)

        def width_policy(self, sp: SizePolicy):
            if sp is SizePolicy.CONTENT:
                raise RuntimeError("NumpyImage doesn't accept SizePolicy.CONTENT")
            return super().width_policy(sp)

        def height_policy(self, sp: SizePolicy):
            if sp is SizePolicy.CONTENT:
                raise RuntimeError("NumpyImage doesn't accept SizePolicy.CONTENT")
            return super().height_policy(sp)

elif import_success:

    class NumpyImage(Widget):
        def __init__(self, array: np.ndarray | SimpleValue[np.ndarray]):
            if isinstance(array, SimpleValue):
                state = array
            else:
                state = State(array)

            super().__init__(
                state=state,
                size=Size(width=0, height=0),
                pos=Point(x=0, y=0),
                pos_policy=None,
                width_policy=SizePolicy.CONTENT,
                height_policy=SizePolicy.CONTENT,
            )

        def redraw(self, p: Painter, _: bool) -> None:
            state: SimpleValue[np.ndarray] = cast(SimpleValue[np.ndarray], self._state)
            p.draw_np_array_as_an_image_rect(
                state.value(), Rect(origin=Point(x=0, y=0), size=self.get_size())
            )

        def measure(self, p: Painter) -> Size:
            state: SimpleValue[np.ndarray] = cast(SimpleValue[np.ndarray], self._state)
            return p.measure_np_array_as_an_image(state.value())
