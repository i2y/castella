import re
from typing import Generator, cast

from castella.core import (
    AppearanceState,
    FontSizePolicy,
    Kind,
    Painter,
    Point,
    Rect,
    SimpleValue,
    Size,
    SizePolicy,
    State,
    Widget,
    replace_font_size,
)


class MultilineText(Widget):
    def __init__(
        self,
        text: str | SimpleValue[str],
        font_size: int,
        padding: int = 8,
        line_spacing: int = 4,
        kind: Kind = Kind.NORMAL,
        wrap: bool = False,  # only works if the size policy of width is not SizePolicy.CONTENT
    ):
        if isinstance(text, SimpleValue):
            state = text
        else:
            state = State(text)

        self._kind = kind
        self._font_size = font_size
        self._padding = padding
        self._border_width = 1  # currently this is fixed value, probably this will become variable later.
        self._line_spacing = line_spacing
        self._wrap = wrap

        super().__init__(
            state=state,
            size=Size(0, 0),
            pos=Point(0, 0),
            pos_policy=None,
            width_policy=SizePolicy.EXPANDING,
            height_policy=SizePolicy.CONTENT,
        )

    def _on_update_widget_styles(self) -> None:
        self._rect_style, self._text_style = self._get_painter_styles(
            self._kind, AppearanceState.NORMAL
        )
        self._text_style = replace_font_size(
            self._text_style, self._font_size, FontSizePolicy.FIXED
        )

    def redraw(self, p: Painter, _: bool) -> None:
        padding = self._padding
        line_spacing = self._line_spacing

        p.style(self._rect_style)
        rect = Rect(origin=Point(0, 0), size=self.get_size())
        p.fill_rect(rect)
        p.stroke_rect(rect)

        p.style(self._text_style)
        h = self._text_style.font.size
        y = h + padding
        for line in self._get_lines(p):
            p.fill_text(line, Point(padding + 0.1, y), None)
            y += h + line_spacing

    def _get_lines(self, p: Painter) -> Generator[str, None, None]:
        state: SimpleValue[str] = cast(SimpleValue[str], self._state)
        text = state.value()

        if self._size.width == 0:
            yield from []

        if self._wrap and self._width_policy is not SizePolicy.CONTENT:
            # for now, support only languages like English.
            # later a little, I will add other languages support.
            line_width = self._size.width - (self._padding + self._border_width) * 2
            for line in text.splitlines():
                retval_words = []
                words_width = 0
                for word in re.split(r"(?<=\s)", line):
                    word_width = p.measure_text(word)
                    words_width += word_width
                    if words_width > line_width:
                        yield "".join(retval_words)
                        retval_words = [word]
                        words_width = word_width
                    else:
                        retval_words.append(word)
                yield "".join(retval_words)
        else:
            yield from text.splitlines()

    def measure(self, p: Painter) -> Size:
        padding = self._padding
        border_width = self._border_width
        line_spacing = self._line_spacing

        w, h = 0, 0
        p.save()
        p.style(self._text_style)
        lines = list(self._get_lines(p))
        w = max(p.measure_text(line) for line in lines) + (padding + border_width) * 2
        h = (
            self._text_style.font.size * len(lines)
            + line_spacing * (len(lines) - 1)
            + padding * 2
            + border_width * 2
        )
        p.restore()
        return Size(w, h)
