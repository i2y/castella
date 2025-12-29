"""Font types as Pydantic models."""

from __future__ import annotations

import os
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class FontSizePolicy(str, Enum):
    """How font size should be determined."""

    FIXED = "fixed"
    EXPANDING = "expanding"


class FontWeight(str, Enum):
    """Font weight options."""

    NORMAL = "normal"
    BOLD = "bold"


class FontSlant(str, Enum):
    """Font slant options."""

    UPRIGHT = "upright"
    ITALIC = "italic"


# Default EM size, can be overridden by environment variable
if "CASTELLA_FONT_SIZE" in os.environ:
    EM: int = int(os.environ["CASTELLA_FONT_SIZE"])
else:
    EM: int = 12


class FontSize:
    """Predefined font sizes."""

    TWO_X_SMALL = 10
    X_SMALL = EM
    SMALL = 14
    MEDIUM = 16
    LARGE = 20
    X_LARGE = 24
    TWO_X_LARGE = 36
    THREE_X_LARGE = 48
    FOUR_X_LARGE = 72


class Font(BaseModel):
    """Font specification with validation."""

    model_config = ConfigDict(frozen=True)

    family: str = Field(default="", description="Font family, empty for system default")
    size: int = Field(default=FontSize.MEDIUM, ge=1, le=1000)
    size_policy: FontSizePolicy = Field(default=FontSizePolicy.EXPANDING)
    weight: FontWeight = Field(default=FontWeight.NORMAL)
    slant: FontSlant = Field(default=FontSlant.UPRIGHT)

    def with_size(self, size: int) -> Font:
        return self.model_copy(update={"size": size})

    def bold(self) -> Font:
        return self.model_copy(update={"weight": FontWeight.BOLD})

    def italic(self) -> Font:
        return self.model_copy(update={"slant": FontSlant.ITALIC})


class FontMetrics(BaseModel):
    """Font measurement data."""

    model_config = ConfigDict(frozen=True)

    cap_height: float = Field(ge=0.0)
    ascent: float = Field(default=0.0, ge=0.0)
    descent: float = Field(default=0.0, ge=0.0)
    line_height: float = Field(default=0.0, ge=0.0)
