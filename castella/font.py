from dataclasses import dataclass
from enum import Enum, auto
import os


class FontSizePolicy(Enum):
    FIXED = auto()
    EXPANDING = auto()


class FontWeight(Enum):
    NORMAL = auto()
    BOLD = auto()


class FontSlant(Enum):
    UPRIGHT = auto()
    ITALIC = auto()


# If the environment variable CASTELLA_FONT_SIZE is set, the font size is set to the value of the environment variable.
if "CASTELLA_FONT_SIZE" in os.environ:
    font_size = int(os.environ["CASTELLA_FONT_SIZE"])
    EM = font_size
else:
    EM = 12


class FontSize:
    TWO_X_SMALL = 10
    X_SMALL = EM
    SMALL = 14
    MEDIUM = 16
    LARGE = 20
    X_LARGE = 24
    TWO_X_LARGE = 36
    THREE_X_LARGE = 48
    FOUR_X_LARGE = 72


@dataclass(slots=True, frozen=True)
class Font:
    family: str = ""  # expects the system default font is used.
    size: int = FontSize.MEDIUM
    size_policy: FontSizePolicy = FontSizePolicy.EXPANDING
    weight: FontWeight = FontWeight.NORMAL
    slant: FontSlant = FontSlant.UPRIGHT


@dataclass(slots=True, frozen=True)
class FontMetrics:
    cap_height: float
