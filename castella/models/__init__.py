"""Castella Models - Pydantic-based data models."""

from castella.models.events import (
    InputCharEvent,
    InputKeyEvent,
    KeyAction,
    KeyCode,
    MouseButton,
    MouseEvent,
    UpdateEvent,
    WheelEvent,
)
from castella.models.font import (
    EM,
    Font,
    FontMetrics,
    FontSize,
    FontSizePolicy,
    FontSlant,
    FontWeight,
)
from castella.models.geometry import Circle, Point, Rect, Size
from castella.models.style import (
    FillStyle,
    LineCap,
    LineStyle,
    NewSizePolicy,
    PositionPolicy,
    SizePolicy,
    StrokeStyle,
    Style,
    TextAlign,
    TextStyle,
)

__all__ = [
    # Geometry
    "Point",
    "Size",
    "Rect",
    "Circle",
    # Font
    "EM",
    "Font",
    "FontMetrics",
    "FontSize",
    "FontSizePolicy",
    "FontSlant",
    "FontWeight",
    # Style
    "FillStyle",
    "LineCap",
    "LineStyle",
    "NewSizePolicy",
    "PositionPolicy",
    "SizePolicy",
    "StrokeStyle",
    "Style",
    "TextAlign",
    "TextStyle",
    # Events
    "InputCharEvent",
    "InputKeyEvent",
    "KeyAction",
    "KeyCode",
    "MouseButton",
    "MouseEvent",
    "UpdateEvent",
    "WheelEvent",
]
