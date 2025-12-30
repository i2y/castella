from enum import Enum
from typing import Self, cast

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


class ImageFit(Enum):
    """How the image should be fitted within its bounds.

    FILL: Stretch image to fill bounds (may distort aspect ratio)
    CONTAIN: Scale image to fit within bounds, maintaining aspect ratio (may have letterboxing)
    COVER: Scale image to cover bounds, maintaining aspect ratio (may crop)
    """

    FILL = "fill"
    CONTAIN = "contain"
    COVER = "cover"


class NetImage(Widget):
    def __init__(
        self,
        url: str | SimpleValue[str],
        use_cache: bool = True,
        fit: ImageFit = ImageFit.FILL,
    ):
        if isinstance(url, SimpleValue):
            state = url
        else:
            state = State(url)

        self._use_cache = use_cache
        self._fit = fit

        super().__init__(
            state=state,
            size=Size(width=0, height=0),
            pos=Point(x=0, y=0),
            pos_policy=None,
            width_policy=SizePolicy.CONTENT,
            height_policy=SizePolicy.CONTENT,
        )

    def fit(self, fit_mode: ImageFit) -> Self:
        """Set the image fit mode."""
        self._fit = fit_mode
        return self

    def redraw(self, p: Painter, _: bool) -> None:
        state: SimpleValue[str] = cast(SimpleValue[str], self._state)
        url = state.value()
        widget_size = self.get_size()

        if self._fit == ImageFit.FILL:
            # Original behavior - stretch to fill
            p.draw_net_image(
                url,
                Rect(origin=Point(x=0, y=0), size=widget_size),
                self._use_cache,
            )
        else:
            # Need to calculate destination rect based on image aspect ratio
            image_size = p.measure_net_image(url, self._use_cache)

            if image_size.width == 0 or image_size.height == 0:
                return

            image_aspect = image_size.width / image_size.height
            widget_aspect = (
                widget_size.width / widget_size.height if widget_size.height > 0 else 1
            )

            if self._fit == ImageFit.CONTAIN:
                # Scale to fit within bounds (letterbox)
                if image_aspect > widget_aspect:
                    # Image is wider - fit to width
                    new_width = widget_size.width
                    new_height = widget_size.width / image_aspect
                else:
                    # Image is taller - fit to height
                    new_height = widget_size.height
                    new_width = widget_size.height * image_aspect
            else:  # COVER
                # Scale to cover bounds (may crop)
                if image_aspect > widget_aspect:
                    # Image is wider - fit to height
                    new_height = widget_size.height
                    new_width = widget_size.height * image_aspect
                else:
                    # Image is taller - fit to width
                    new_width = widget_size.width
                    new_height = widget_size.width / image_aspect

            # Center the image
            x = (widget_size.width - new_width) / 2
            y = (widget_size.height - new_height) / 2

            p.draw_net_image(
                url,
                Rect(
                    origin=Point(x=x, y=y),
                    size=Size(width=new_width, height=new_height),
                ),
                self._use_cache,
            )

    def measure(self, p: Painter) -> Size:
        state: SimpleValue[str] = cast(SimpleValue[str], self._state)
        return p.measure_net_image(state.value())
