"""Key mapping abstractions for different platforms."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from castella.models.events import KeyAction, KeyCode


class KeyMapper(ABC):
    """Abstract base for platform-specific key mapping."""

    @abstractmethod
    def to_key_code(self, platform_key: Any) -> KeyCode:
        """Convert platform key code to KeyCode."""
        ...

    @abstractmethod
    def to_key_action(self, platform_action: Any) -> KeyAction:
        """Convert platform action to KeyAction."""
        ...


class GLFWKeyMapper(KeyMapper):
    """GLFW-specific key mapping."""

    def __init__(self):
        import glfw

        self._key_map: dict[int, KeyCode] = {
            glfw.KEY_BACKSPACE: KeyCode.BACKSPACE,
            glfw.KEY_LEFT: KeyCode.LEFT,
            glfw.KEY_RIGHT: KeyCode.RIGHT,
            glfw.KEY_UP: KeyCode.UP,
            glfw.KEY_DOWN: KeyCode.DOWN,
            glfw.KEY_PAGE_UP: KeyCode.PAGE_UP,
            glfw.KEY_PAGE_DOWN: KeyCode.PAGE_DOWN,
            glfw.KEY_DELETE: KeyCode.DELETE,
            glfw.KEY_ENTER: KeyCode.ENTER,
            glfw.KEY_TAB: KeyCode.TAB,
            glfw.KEY_ESCAPE: KeyCode.ESCAPE,
            glfw.KEY_HOME: KeyCode.HOME,
            glfw.KEY_END: KeyCode.END,
        }
        self._action_map: dict[int, KeyAction] = {
            glfw.PRESS: KeyAction.PRESS,
            glfw.RELEASE: KeyAction.RELEASE,
            glfw.REPEAT: KeyAction.REPEAT,
        }

    def to_key_code(self, platform_key: int) -> KeyCode:
        return self._key_map.get(platform_key, KeyCode.UNKNOWN)

    def to_key_action(self, platform_action: int) -> KeyAction:
        return self._action_map.get(platform_action, KeyAction.UNKNOWN)


class SDLKeyMapper(KeyMapper):
    """SDL2-specific key mapping."""

    def __init__(self):
        import sdl2 as sdl

        self._key_map: dict[int, KeyCode] = {
            sdl.SDLK_BACKSPACE: KeyCode.BACKSPACE,
            sdl.SDLK_LEFT: KeyCode.LEFT,
            sdl.SDLK_RIGHT: KeyCode.RIGHT,
            sdl.SDLK_UP: KeyCode.UP,
            sdl.SDLK_DOWN: KeyCode.DOWN,
            sdl.SDLK_PAGEUP: KeyCode.PAGE_UP,
            sdl.SDLK_PAGEDOWN: KeyCode.PAGE_DOWN,
            sdl.SDLK_DELETE: KeyCode.DELETE,
            sdl.SDLK_RETURN: KeyCode.ENTER,
            sdl.SDLK_TAB: KeyCode.TAB,
            sdl.SDLK_ESCAPE: KeyCode.ESCAPE,
            sdl.SDLK_HOME: KeyCode.HOME,
            sdl.SDLK_END: KeyCode.END,
        }

    def to_key_code(self, platform_key: int) -> KeyCode:
        return self._key_map.get(platform_key, KeyCode.UNKNOWN)

    def to_key_action(self, platform_action: int) -> KeyAction:
        # SDL only provides key down events for our use case
        return KeyAction.PRESS


class PromptToolkitKeyMapper(KeyMapper):
    """prompt_toolkit-specific key mapping."""

    def __init__(self):
        from prompt_toolkit.keys import Keys

        self._key_map = {
            Keys.ControlH: KeyCode.BACKSPACE,
            Keys.Left: KeyCode.LEFT,
            Keys.Right: KeyCode.RIGHT,
            Keys.Up: KeyCode.UP,
            Keys.Down: KeyCode.DOWN,
            Keys.PageUp: KeyCode.PAGE_UP,
            Keys.PageDown: KeyCode.PAGE_DOWN,
            Keys.Delete: KeyCode.DELETE,
            Keys.Enter: KeyCode.ENTER,
            Keys.Tab: KeyCode.TAB,
            Keys.Escape: KeyCode.ESCAPE,
            Keys.Home: KeyCode.HOME,
            Keys.End: KeyCode.END,
        }

    def to_key_code(self, platform_key: Any) -> KeyCode:
        return self._key_map.get(platform_key, KeyCode.UNKNOWN)

    def to_key_action(self, platform_action: Any) -> KeyAction:
        return KeyAction.PRESS


class WebKeyMapper(KeyMapper):
    """Browser JavaScript keyCode mapping."""

    _KEY_MAP: dict[int, KeyCode] = {
        8: KeyCode.BACKSPACE,
        37: KeyCode.LEFT,
        39: KeyCode.RIGHT,
        38: KeyCode.UP,
        40: KeyCode.DOWN,
        33: KeyCode.PAGE_UP,
        34: KeyCode.PAGE_DOWN,
        46: KeyCode.DELETE,
        13: KeyCode.ENTER,
        9: KeyCode.TAB,
        27: KeyCode.ESCAPE,
        36: KeyCode.HOME,
        35: KeyCode.END,
    }

    def to_key_code(self, platform_key: int) -> KeyCode:
        return self._KEY_MAP.get(platform_key, KeyCode.UNKNOWN)

    def to_key_action(self, platform_action: Any) -> KeyAction:
        return KeyAction.PRESS
