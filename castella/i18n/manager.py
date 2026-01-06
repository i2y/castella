"""Internationalization manager for locale switching.

Provides a singleton I18nManager that:
- Manages translation catalogs
- Switches locales at runtime
- Notifies widgets when locale changes
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Any, Protocol
from weakref import WeakSet

if TYPE_CHECKING:
    from .catalog import TranslationCatalog


class I18nObserver(Protocol):
    """Protocol for objects that observe locale changes."""

    def on_locale_changed(self, locale: str) -> None:
        """Called when the active locale changes."""
        ...


def _detect_system_locale() -> str:
    """Detect system locale preference.

    Priority:
    1. CASTELLA_LOCALE environment variable
    2. System locale (LC_ALL, LANG)
    3. Default to 'en'
    """
    env_value = os.getenv("CASTELLA_LOCALE")
    if env_value:
        return env_value

    # Try system locale
    import locale

    try:
        system_locale = locale.getlocale()[0]
        if system_locale:
            # Extract language code (e.g., 'ja_JP' -> 'ja')
            return system_locale.split("_")[0]
    except Exception:
        pass

    return "en"


class I18nManager:
    """Singleton manager for internationalization.

    Manages translation catalogs and notifies observers on locale changes.

    Usage:
        manager = I18nManager()
        manager.load_catalog("en", en_catalog)
        manager.load_catalog("ja", ja_catalog)

        # Switch locale
        manager.set_locale("ja")

        # Translate
        text = manager.t("common.save")
    """

    _instance: "I18nManager | None" = None

    def __new__(cls) -> "I18nManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init()
        return cls._instance

    def _init(self) -> None:
        """Initialize the manager (called once on first instantiation)."""
        self._current_locale: str = "en"
        self._fallback_locale: str = "en"
        self._catalogs: dict[str, TranslationCatalog] = {}
        self._listeners: WeakSet[I18nObserver] = WeakSet()
        self._auto_detect: bool = True

    @property
    def locale(self) -> str:
        """Get the current locale."""
        if self._auto_detect and not self._catalogs:
            return _detect_system_locale()
        return self._current_locale

    @property
    def fallback_locale(self) -> str:
        """Get the fallback locale."""
        return self._fallback_locale

    @property
    def available_locales(self) -> list[str]:
        """Get list of available locales."""
        return list(self._catalogs.keys())

    def set_locale(self, locale: str) -> None:
        """Set the current locale.

        Args:
            locale: Locale code (e.g., 'en', 'ja')
        """
        if locale != self._current_locale:
            self._current_locale = locale
            self._auto_detect = False
            self._notify_listeners()

    def set_fallback_locale(self, locale: str) -> None:
        """Set the fallback locale used when translations are missing.

        Args:
            locale: Locale code (e.g., 'en')
        """
        self._fallback_locale = locale

    def load_catalog(self, locale: str, catalog: "TranslationCatalog") -> None:
        """Load a translation catalog for a locale.

        Args:
            locale: Locale code
            catalog: TranslationCatalog instance
        """
        self._catalogs[locale] = catalog

    def get_catalog(self, locale: str | None = None) -> "TranslationCatalog | None":
        """Get the catalog for a locale.

        Args:
            locale: Locale code, or None for current locale
        """
        if locale is None:
            locale = self.locale
        return self._catalogs.get(locale)

    def t(self, key: str, **kwargs: Any) -> str:
        """Translate a key with optional interpolation.

        Args:
            key: Translation key (dot-notation, e.g., 'common.save')
            **kwargs: Values for string interpolation

        Returns:
            Translated string, or the key itself if not found
        """
        # Try current locale
        catalog = self.get_catalog()
        if catalog:
            value = catalog.get(key)
            if value is not None:
                return self._interpolate(value, kwargs)

        # Try fallback locale
        if self._current_locale != self._fallback_locale:
            fallback_catalog = self.get_catalog(self._fallback_locale)
            if fallback_catalog:
                value = fallback_catalog.get(key)
                if value is not None:
                    return self._interpolate(value, kwargs)

        # Return key as fallback
        return key

    def tn(self, key: str, count: int, **kwargs: Any) -> str:
        """Translate with pluralization.

        Args:
            key: Translation key
            count: Count for pluralization
            **kwargs: Additional values for interpolation

        Returns:
            Translated string with appropriate plural form
        """
        catalog = self.get_catalog()
        if catalog:
            value = catalog.get_plural(key, count)
            if value is not None:
                return self._interpolate(value, {"count": count, **kwargs})

        # Try fallback
        if self._current_locale != self._fallback_locale:
            fallback_catalog = self.get_catalog(self._fallback_locale)
            if fallback_catalog:
                value = fallback_catalog.get_plural(key, count)
                if value is not None:
                    return self._interpolate(value, {"count": count, **kwargs})

        return key

    def _interpolate(self, template: str, values: dict[str, Any]) -> str:
        """Interpolate values into a template string.

        Args:
            template: String with {name} placeholders
            values: Values to substitute

        Returns:
            Interpolated string
        """
        if not values:
            return template
        try:
            return template.format(**values)
        except KeyError:
            return template

    def add_listener(self, listener: I18nObserver) -> None:
        """Add a locale change listener.

        Listeners are held with weak references, so they will be
        automatically removed when garbage collected.
        """
        self._listeners.add(listener)

    def remove_listener(self, listener: I18nObserver) -> None:
        """Remove a locale change listener."""
        self._listeners.discard(listener)

    def _notify_listeners(self) -> None:
        """Notify all listeners of locale change."""
        locale = self.locale
        for listener in list(self._listeners):
            listener.on_locale_changed(locale)

    @classmethod
    def reset(cls) -> None:
        """Reset the singleton instance (mainly for testing)."""
        cls._instance = None
