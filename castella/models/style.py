"""Style types as Pydantic models."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from castella.models.font import EM, Font


class SizePolicy(str, Enum):
    """Widget size policy."""

    FIXED = "fixed"
    EXPANDING = "expanding"
    CONTENT = "content"


class PositionPolicy(str, Enum):
    """Widget position policy."""

    FIXED = "fixed"
    CENTER = "center"


class LineCap(str, Enum):
    """Line cap styles."""

    BUTT = "butt"
    ROUND = "round"
    SQUARE = "square"


class TextAlign(str, Enum):
    """Text alignment options."""

    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"


class Shadow(BaseModel):
    """Drop shadow style for widgets."""

    model_config = ConfigDict(frozen=True)

    color: str = Field(default="#00000040")  # Semi-transparent black
    offset_x: float = Field(default=0.0)
    offset_y: float = Field(default=2.0)
    blur_radius: float = Field(default=4.0)


class FillStyle(BaseModel):
    """Fill style for shapes."""

    model_config = ConfigDict(frozen=True)

    color: str = Field(default="#000000")


class StrokeStyle(BaseModel):
    """Stroke style for shape outlines."""

    model_config = ConfigDict(frozen=True)

    color: str = Field(default="#000000")


class LineStyle(BaseModel):
    """Line drawing style."""

    model_config = ConfigDict(frozen=True)

    width: float = Field(default=1.0, gt=0.0)
    cap: LineCap = Field(default=LineCap.BUTT)


class Style(BaseModel):
    """Composite style for rendering."""

    model_config = ConfigDict(frozen=True)

    fill: FillStyle = Field(default_factory=FillStyle)
    stroke: StrokeStyle = Field(default_factory=StrokeStyle)
    line: LineStyle = Field(default_factory=LineStyle)
    font: Font = Field(default_factory=Font)
    padding: int = Field(default=EM, ge=0)
    border_radius: float = Field(default=0.0, ge=0.0)
    shadow: Shadow | None = Field(default=None)

    def with_fill_color(self, color: str) -> Style:
        return self.model_copy(update={"fill": FillStyle(color=color)})

    def with_stroke_color(self, color: str) -> Style:
        return self.model_copy(update={"stroke": StrokeStyle(color=color)})

    def with_font(self, font: Font) -> Style:
        return self.model_copy(update={"font": font})


class TextStyle(BaseModel):
    """Text-specific styling."""

    model_config = ConfigDict(frozen=True)

    color: str = Field(default="#000000")
    font_families: list[str] = Field(default_factory=list)
    font_size: float = Field(default=16.0, gt=0.0)


class NewSizePolicy(BaseModel):
    """Combined width and height size policies."""

    model_config = ConfigDict(frozen=True)

    width: SizePolicy = Field(default=SizePolicy.FIXED)
    height: SizePolicy = Field(default=SizePolicy.FIXED)
