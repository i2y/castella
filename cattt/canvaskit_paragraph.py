from js import Object, window
from pyodide import to_js

import core


class Paragraph:
    def __init__(self, p):
        self._ck_paragraph = p

    def layout(self, width: float) -> None:
        self._ck_paragraph.layout(width)

    def get_height(self) -> float:
        return self._ck_paragraph.getHeight()

    def get_max_width(self) -> float:
        return self._ck_paragraph.getMaxWidth()

    def to_ck_paragraph(self):
        return self._ck_paragraph


def to_ck_paragraph_style(style: core.ParagraphStyle):
    ps = {
        "textStyle": {
            "color": window.CK.WHITE, # TODO
            "fontFamilies" : style.text_style.fontFamilies,
            "fontSize": style.text_style.fontSize,
        },
        "textAlign": window.CK.TextAlign.Left, # TODO
        "disableHinting": True,
    }
    pso = to_js(ps, dict_converter=Object.fromEntries)
    return window.CK.ParagraphStyle.new(pso)


class ParagraphBuilder:
    def __init__(self, style: core.ParagraphStyle):
        self._builder = window.CK.ParagraphBuilder.Make(to_ck_paragraph_style(style), window.fontMgr)

    def add_text(self, text: str) -> None:
        self._builder.addText(text)

    def build(self) -> Paragraph:
        return Paragraph(self._builder.build())
