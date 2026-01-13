"""Event types as Pydantic models."""

from __future__ import annotations

import platform
from enum import Enum, auto
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

from castella.models.geometry import Point

W = TypeVar("W")


class KeyCode(Enum):
    """Keyboard key codes."""

    BACKSPACE = auto()
    LEFT = auto()
    RIGHT = auto()
    UP = auto()
    DOWN = auto()
    PAGE_UP = auto()
    PAGE_DOWN = auto()
    DELETE = auto()
    ENTER = auto()
    TAB = auto()
    ESCAPE = auto()
    HOME = auto()
    END = auto()
    SPACE = auto()
    # Letter keys for shortcuts
    A = auto()
    C = auto()
    F = auto()
    S = auto()
    V = auto()
    X = auto()
    Z = auto()
    UNKNOWN = auto()


class KeyAction(Enum):
    """Keyboard action types."""

    PRESS = auto()
    REPEAT = auto()
    RELEASE = auto()
    UNKNOWN = auto()


class CursorType(Enum):
    """Mouse cursor types."""

    ARROW = auto()  # Default arrow cursor
    TEXT = auto()  # I-beam cursor for text input
    POINTER = auto()  # Hand cursor for clickable elements
    RESIZE_H = auto()  # Horizontal resize cursor (↔)
    RESIZE_V = auto()  # Vertical resize cursor (↕)
    CROSSHAIR = auto()  # Crosshair for selection
    WAIT = auto()  # Wait/loading cursor
    NOT_ALLOWED = auto()  # Forbidden/not-allowed cursor


class MouseButton(str, Enum):
    """Mouse button identifiers."""

    LEFT = "left"
    RIGHT = "right"
    MIDDLE = "middle"


class MouseEvent(BaseModel, Generic[W]):
    """Mouse event with position and optional target."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    pos: Point
    target: Any | None = Field(default=None)

    def translate(self, offset: Point) -> MouseEvent[W]:
        """Create new event with translated position."""
        return MouseEvent(
            pos=self.pos - offset,
            target=self.target,
        )

    def with_target(self, target: Any) -> MouseEvent[W]:
        """Create new event with different target."""
        return self.model_copy(update={"target": target})


class WheelEvent(BaseModel):
    """Mouse wheel event."""

    model_config = ConfigDict(frozen=True)

    pos: Point
    x_offset: float = Field(default=0.0)
    y_offset: float = Field(default=0.0)

    @property
    def is_horizontal(self) -> bool:
        return abs(self.x_offset) > abs(self.y_offset)


class InputCharEvent(BaseModel):
    """Character input event."""

    model_config = ConfigDict(frozen=True)

    char: str


class InputKeyEvent(BaseModel):
    """Keyboard key event."""

    model_config = ConfigDict(frozen=True)

    key: KeyCode
    scancode: int = Field(default=0)
    action: KeyAction
    mods: int = Field(default=0)

    @property
    def is_ctrl(self) -> bool:
        return bool(self.mods & 0x0002)

    @property
    def is_shift(self) -> bool:
        return bool(self.mods & 0x0001)

    @property
    def is_alt(self) -> bool:
        return bool(self.mods & 0x0004)

    @property
    def is_super(self) -> bool:
        """Check if Super/Cmd key is pressed (0x0008 for GLFW)."""
        return bool(self.mods & 0x0008)

    @property
    def is_cmd_or_ctrl(self) -> bool:
        """Platform-aware check: Cmd on macOS, Ctrl elsewhere."""
        if platform.system() == "Darwin":
            return self.is_super
        return self.is_ctrl

    @property
    def is_pressed(self) -> bool:
        return self.action in (KeyAction.PRESS, KeyAction.REPEAT)


class UpdateEvent(BaseModel):
    """Widget update event."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    target: Any
    completely: bool = Field(default=False)


class IMEPreeditEvent(BaseModel):
    """IME preedit (composition) event.

    Represents text being composed by an Input Method Editor (IME),
    such as when typing Japanese or Chinese characters.
    """

    model_config = ConfigDict(frozen=True)

    text: str  # The preedit text being composed
    cursor_pos: int = Field(default=0)  # Cursor position within preedit text
