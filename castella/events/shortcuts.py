"""Global keyboard shortcut management.

Provides a registry for keyboard shortcuts that can be triggered
regardless of which widget has focus.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import Callable

from castella.models.events import KeyCode, KeyAction, InputKeyEvent
from castella.events.keyboard import MOD_SHIFT, MOD_CTRL, MOD_ALT, MOD_SUPER


# Platform-aware modifier for standard shortcuts (Ctrl on Win/Linux, Cmd on macOS)
MOD_CTRL_OR_CMD = MOD_SUPER if sys.platform == "darwin" else MOD_CTRL


@dataclass(frozen=True)
class Shortcut:
    """A keyboard shortcut definition.

    Args:
        key: The primary key for the shortcut.
        modifiers: Bitmask of required modifiers (MOD_CTRL, MOD_SHIFT, etc.).

    Example:
        # Ctrl+S (or Cmd+S on macOS)
        save_shortcut = Shortcut(KeyCode.S, MOD_CTRL_OR_CMD)

        # Ctrl+Shift+Z
        redo_shortcut = Shortcut(KeyCode.Z, MOD_CTRL_OR_CMD | MOD_SHIFT)
    """

    key: KeyCode
    modifiers: int = 0

    def matches(self, ev: InputKeyEvent) -> bool:
        """Check if this shortcut matches a key event.

        Args:
            ev: The key event to check.

        Returns:
            True if the event matches this shortcut.
        """
        if ev.action != KeyAction.PRESS:
            return False
        if ev.key != self.key:
            return False
        # Check that required modifiers are present
        # (allow extra modifiers like CapsLock)
        return (
            ev.mods & (MOD_CTRL | MOD_SHIFT | MOD_ALT | MOD_SUPER)
        ) == self.modifiers


# Common shortcuts
SHORTCUT_COPY = Shortcut(KeyCode.C, MOD_CTRL_OR_CMD)
SHORTCUT_CUT = Shortcut(KeyCode.X, MOD_CTRL_OR_CMD)
SHORTCUT_PASTE = Shortcut(KeyCode.V, MOD_CTRL_OR_CMD)
SHORTCUT_SELECT_ALL = Shortcut(KeyCode.A, MOD_CTRL_OR_CMD)
SHORTCUT_UNDO = Shortcut(KeyCode.Z, MOD_CTRL_OR_CMD)
SHORTCUT_REDO = Shortcut(KeyCode.Z, MOD_CTRL_OR_CMD | MOD_SHIFT)
SHORTCUT_SAVE = Shortcut(KeyCode.S, MOD_CTRL_OR_CMD)
SHORTCUT_FIND = Shortcut(KeyCode.F, MOD_CTRL_OR_CMD)


class ShortcutHandler:
    """Global keyboard shortcut registry and handler.

    Manages a collection of keyboard shortcuts and their handlers.
    Shortcuts are checked in registration order, first match wins.

    Example:
        handler = ShortcutHandler()

        handler.register(SHORTCUT_SAVE, lambda: save_document())
        handler.register(SHORTCUT_COPY, lambda: copy_selection())

        # In key event processing:
        if handler.handle(key_event):
            return  # Shortcut was triggered
    """

    def __init__(self) -> None:
        self._shortcuts: dict[Shortcut, Callable[[], None]] = {}

    def register(self, shortcut: Shortcut, handler: Callable[[], None]) -> None:
        """Register a shortcut handler.

        Args:
            shortcut: The shortcut to register.
            handler: Callback to invoke when shortcut is triggered.
        """
        self._shortcuts[shortcut] = handler

    def unregister(self, shortcut: Shortcut) -> None:
        """Unregister a shortcut.

        Args:
            shortcut: The shortcut to remove.
        """
        self._shortcuts.pop(shortcut, None)

    def handle(self, ev: InputKeyEvent) -> bool:
        """Try to handle a key event as a shortcut.

        Args:
            ev: The key event to check.

        Returns:
            True if a shortcut was triggered, False otherwise.
        """
        for shortcut, handler in self._shortcuts.items():
            if shortcut.matches(ev):
                handler()
                return True
        return False

    def clear(self) -> None:
        """Remove all registered shortcuts."""
        self._shortcuts.clear()
