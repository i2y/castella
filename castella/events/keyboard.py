"""Keyboard state tracking.

Tracks which keys are currently pressed and modifier state.
"""

from __future__ import annotations

from castella.models.events import KeyCode, KeyAction, InputKeyEvent


# Modifier key masks
MOD_SHIFT = 0x0001
MOD_CTRL = 0x0002
MOD_ALT = 0x0004
MOD_SUPER = 0x0008  # Cmd on macOS, Win on Windows


class KeyboardState:
    """Tracks keyboard key states and modifiers.

    Maintains a set of currently pressed keys and modifier state.
    Useful for detecting key combinations and modifier+key shortcuts.

    Example:
        keyboard = KeyboardState()
        keyboard.process_key_event(event)

        if keyboard.is_pressed(KeyCode.C) and keyboard.has_ctrl_or_cmd():
            # Ctrl+C or Cmd+C pressed
            handle_copy()
    """

    def __init__(self) -> None:
        self._pressed: set[KeyCode] = set()
        self._modifiers: int = 0

    def is_pressed(self, key: KeyCode) -> bool:
        """Check if a key is currently pressed."""
        return key in self._pressed

    @property
    def modifiers(self) -> int:
        """Get current modifier bitmask."""
        return self._modifiers

    def has_shift(self) -> bool:
        """Check if Shift is held."""
        return bool(self._modifiers & MOD_SHIFT)

    def has_ctrl(self) -> bool:
        """Check if Ctrl is held."""
        return bool(self._modifiers & MOD_CTRL)

    def has_alt(self) -> bool:
        """Check if Alt/Option is held."""
        return bool(self._modifiers & MOD_ALT)

    def has_super(self) -> bool:
        """Check if Super/Cmd/Win is held."""
        return bool(self._modifiers & MOD_SUPER)

    def has_ctrl_or_cmd(self) -> bool:
        """Check if Ctrl (Windows/Linux) or Cmd (macOS) is held.

        This is the standard modifier for shortcuts like Copy, Paste, etc.
        """
        import sys

        if sys.platform == "darwin":
            return self.has_super()
        return self.has_ctrl()

    def process_key_event(self, ev: InputKeyEvent) -> None:
        """Process a key event to update state.

        Args:
            ev: The key event to process.
        """
        # Update modifier state from event
        self._modifiers = ev.mods

        if ev.action == KeyAction.PRESS:
            self._pressed.add(ev.key)
        elif ev.action == KeyAction.RELEASE:
            self._pressed.discard(ev.key)
        # REPEAT doesn't change pressed state

    def reset(self) -> None:
        """Reset all key state (e.g., on window focus loss)."""
        self._pressed.clear()
        self._modifiers = 0

    def get_pressed_keys(self) -> frozenset[KeyCode]:
        """Get a snapshot of currently pressed keys."""
        return frozenset(self._pressed)
