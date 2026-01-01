"""Event handling subsystem.

This package provides centralized event management with:
- FocusManager: Keyboard focus and Tab navigation
- PointerTracker: Mouse/touch state tracking
- GestureRecognizer: Tap, double-tap, long-press, drag detection
- KeyboardState: Key press tracking
- ShortcutHandler: Global keyboard shortcuts
- EventManager: Central coordinator for all subsystems

Example:
    from castella.events import EventManager, SHORTCUT_SAVE

    manager = EventManager()
    manager.shortcuts.register(SHORTCUT_SAVE, lambda: save_document())
    manager.on_tap(lambda ev: print(f"Tapped {ev.target}"))
"""

from castella.events.manager import EventManager
from castella.events.focus import FocusManager, Focusable, FocusScope
from castella.events.pointer import PointerTracker
from castella.events.gesture import GestureRecognizer, GestureEvent, DragEvent
from castella.events.keyboard import (
    KeyboardState,
    MOD_SHIFT,
    MOD_CTRL,
    MOD_ALT,
    MOD_SUPER,
)
from castella.events.shortcuts import (
    ShortcutHandler,
    Shortcut,
    MOD_CTRL_OR_CMD,
    SHORTCUT_COPY,
    SHORTCUT_CUT,
    SHORTCUT_PASTE,
    SHORTCUT_SELECT_ALL,
    SHORTCUT_UNDO,
    SHORTCUT_REDO,
    SHORTCUT_SAVE,
    SHORTCUT_FIND,
)

__all__ = [
    # Main coordinator
    "EventManager",
    # Focus
    "FocusManager",
    "Focusable",
    "FocusScope",
    # Pointer
    "PointerTracker",
    # Gesture
    "GestureRecognizer",
    "GestureEvent",
    "DragEvent",
    # Keyboard
    "KeyboardState",
    "MOD_SHIFT",
    "MOD_CTRL",
    "MOD_ALT",
    "MOD_SUPER",
    # Shortcuts
    "ShortcutHandler",
    "Shortcut",
    "MOD_CTRL_OR_CMD",
    "SHORTCUT_COPY",
    "SHORTCUT_CUT",
    "SHORTCUT_PASTE",
    "SHORTCUT_SELECT_ALL",
    "SHORTCUT_UNDO",
    "SHORTCUT_REDO",
    "SHORTCUT_SAVE",
    "SHORTCUT_FIND",
]
