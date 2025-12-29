"""Theme manager for dynamic theme switching.

Provides a singleton ThemeManager that:
- Manages dark and light themes
- Detects system dark mode preference
- Notifies widgets when theme changes
"""

from __future__ import annotations

import os
import sys
from typing import TYPE_CHECKING, Protocol
from weakref import WeakSet

if TYPE_CHECKING:
    from .core import Theme


class ThemeObserver(Protocol):
    """Protocol for objects that observe theme changes."""

    def on_theme_changed(self, theme: "Theme") -> None:
        """Called when the active theme changes."""
        ...


def _detect_system_dark_mode() -> bool:
    """Detect system dark mode preference.

    Priority:
    1. CASTELLA_DARK_MODE environment variable
    2. Browser preference (web)
    3. darkdetect library (desktop)
    """
    env_value = os.getenv("CASTELLA_DARK_MODE")
    if env_value == "true":
        return True
    if env_value == "false":
        return False

    if "pyodide" in sys.modules:
        import js  # type: ignore

        return js.window.matchMedia("(prefers-color-scheme: dark)").matches

    try:
        import darkdetect

        is_light = darkdetect.isLight()
        return not (is_light is not None and is_light)
    except ImportError:
        return True  # Default to dark mode


class ThemeManager:
    """Singleton manager for application themes.

    Manages dark/light theme variants and notifies observers on changes.

    Usage:
        manager = ThemeManager()
        manager.set_dark_theme(DARK_THEME)
        manager.set_light_theme(LIGHT_THEME)

        # Toggle theme
        manager.toggle_dark_mode()

        # Force dark mode
        manager.prefer_dark(True)
    """

    _instance: "ThemeManager | None" = None

    def __new__(cls) -> "ThemeManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init()
        return cls._instance

    def _init(self) -> None:
        """Initialize the manager (called once on first instantiation)."""
        self._dark_theme: Theme | None = None
        self._light_theme: Theme | None = None
        self._prefer_dark: bool | None = None  # None = auto-detect
        self._listeners: WeakSet[ThemeObserver] = WeakSet()
        self._initialized = False

    def _ensure_defaults(self) -> None:
        """Lazily initialize default themes."""
        if not self._initialized:
            from .presets import TOKYO_NIGHT_DARK_THEME, TOKYO_NIGHT_LIGHT_THEME

            if self._dark_theme is None:
                self._dark_theme = TOKYO_NIGHT_DARK_THEME
            if self._light_theme is None:
                self._light_theme = TOKYO_NIGHT_LIGHT_THEME
            self._initialized = True

    @property
    def current(self) -> "Theme":
        """Get the currently active theme."""
        self._ensure_defaults()
        is_dark = self._should_use_dark()
        if is_dark:
            assert self._dark_theme is not None
            return self._dark_theme
        assert self._light_theme is not None
        return self._light_theme

    @property
    def is_dark(self) -> bool:
        """Check if current theme is dark mode."""
        return self._should_use_dark()

    def _should_use_dark(self) -> bool:
        """Determine if dark mode should be used."""
        if self._prefer_dark is not None:
            return self._prefer_dark
        return _detect_system_dark_mode()

    def set_dark_theme(self, theme: "Theme") -> None:
        """Set the dark mode theme."""
        self._dark_theme = theme.model_copy(update={"is_dark": True})
        self._initialized = True
        if self._should_use_dark():
            self._notify_listeners()

    def set_light_theme(self, theme: "Theme") -> None:
        """Set the light mode theme."""
        self._light_theme = theme.model_copy(update={"is_dark": False})
        self._initialized = True
        if not self._should_use_dark():
            self._notify_listeners()

    def prefer_dark(self, prefer: bool | None = None) -> None:
        """Set dark mode preference.

        Args:
            prefer: True for dark, False for light, None for auto-detect
        """
        old_is_dark = self._should_use_dark()
        self._prefer_dark = prefer
        new_is_dark = self._should_use_dark()

        if old_is_dark != new_is_dark:
            self._notify_listeners()

    def toggle_dark_mode(self) -> None:
        """Toggle between dark and light mode."""
        current_is_dark = self._should_use_dark()
        self._prefer_dark = not current_is_dark
        self._notify_listeners()

    def add_listener(self, listener: ThemeObserver) -> None:
        """Add a theme change listener.

        Listeners are held with weak references, so they will be
        automatically removed when garbage collected.
        """
        self._listeners.add(listener)

    def remove_listener(self, listener: ThemeObserver) -> None:
        """Remove a theme change listener."""
        self._listeners.discard(listener)

    def _notify_listeners(self) -> None:
        """Notify all listeners of theme change."""
        theme = self.current
        for listener in list(self._listeners):
            listener.on_theme_changed(theme)

    @classmethod
    def reset(cls) -> None:
        """Reset the singleton instance (mainly for testing)."""
        cls._instance = None
