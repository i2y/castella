"""Reactive locale string for dynamic translation updates."""

from __future__ import annotations

from typing import Any

from castella.state.observers import ObservableBase

from .manager import I18nManager, I18nObserver


class LocaleString(ObservableBase, I18nObserver):
    """Reactive string that updates when locale changes.

    LocaleString wraps a translation key and automatically notifies
    observers when the locale changes, causing widgets to re-render
    with the new translation.

    Usage with Text widget:
        # Automatically updates when locale changes
        Text(LocaleString("dashboard.title"))

        # With interpolation
        Text(LocaleString("greeting", name="World"))

    The widget will re-render when:
    - The locale changes via I18nManager.set_locale()
    - Any interpolation values change (if using dynamic values)
    """

    __slots__ = ("_key", "_kwargs", "_manager", "_cached_value")

    def __init__(self, key: str, **kwargs: Any) -> None:
        """Create a reactive locale string.

        Args:
            key: Translation key (dot-notation, e.g., 'common.save')
            **kwargs: Values for string interpolation
        """
        super().__init__()
        self._key = key
        self._kwargs = kwargs
        self._manager = I18nManager()
        self._cached_value: str | None = None
        self._manager.add_listener(self)

    @property
    def key(self) -> str:
        """Get the translation key."""
        return self._key

    def value(self) -> str:
        """Get the current translated string."""
        return self._manager.t(self._key, **self._kwargs)

    def __str__(self) -> str:
        """Return the translated string.

        This makes LocaleString compatible with Text widget
        which calls str() on its content.
        """
        return self.value()

    def __repr__(self) -> str:
        return f"LocaleString({self._key!r}, {self._kwargs!r})"

    def on_locale_changed(self, locale: str) -> None:
        """Called when locale changes - notify observers.

        This triggers widget re-renders for any widgets
        using this LocaleString.
        """
        new_value = self.value()
        if new_value != self._cached_value:
            self._cached_value = new_value
            self.notify()

    def with_values(self, **kwargs: Any) -> "LocaleString":
        """Create a new LocaleString with updated interpolation values.

        Args:
            **kwargs: New or updated interpolation values

        Returns:
            New LocaleString with merged kwargs
        """
        merged = {**self._kwargs, **kwargs}
        return LocaleString(self._key, **merged)


class LocalePluralString(ObservableBase, I18nObserver):
    """Reactive pluralized string that updates when locale changes.

    Similar to LocaleString but uses pluralization rules.

    Usage:
        # Shows "1 item" or "5 items" depending on count and locale
        Text(LocalePluralString("items", count=5))
    """

    __slots__ = ("_key", "_count", "_kwargs", "_manager", "_cached_value")

    def __init__(self, key: str, count: int, **kwargs: Any) -> None:
        """Create a reactive plural locale string.

        Args:
            key: Translation key for plural forms
            count: Count for pluralization
            **kwargs: Additional interpolation values
        """
        super().__init__()
        self._key = key
        self._count = count
        self._kwargs = kwargs
        self._manager = I18nManager()
        self._cached_value: str | None = None
        self._manager.add_listener(self)

    def value(self) -> str:
        """Get the current translated string with proper plural form."""
        return self._manager.tn(self._key, self._count, **self._kwargs)

    def __str__(self) -> str:
        return self.value()

    def __repr__(self) -> str:
        return (
            f"LocalePluralString({self._key!r}, count={self._count}, {self._kwargs!r})"
        )

    def on_locale_changed(self, locale: str) -> None:
        """Called when locale changes - notify observers."""
        new_value = self.value()
        if new_value != self._cached_value:
            self._cached_value = new_value
            self.notify()

    def set_count(self, count: int) -> None:
        """Update the count and notify observers if value changed.

        Args:
            count: New count value
        """
        if count != self._count:
            self._count = count
            new_value = self.value()
            if new_value != self._cached_value:
                self._cached_value = new_value
                self.notify()
