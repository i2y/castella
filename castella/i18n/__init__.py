"""Internationalization support for Castella.

This module provides i18n functionality including:
- I18nManager: Singleton for managing translations and locale
- LocaleString: Reactive string that updates on locale change
- TranslationCatalog: Storage for translation dictionaries
- Loaders for YAML and JSON translation files

Basic Usage:
    from castella.i18n import I18nManager, t, LocaleString
    from castella.i18n import load_yaml_catalog

    # Load translations
    manager = I18nManager()
    manager.load_catalog("en", load_yaml_catalog("locales/en.yaml"))
    manager.load_catalog("ja", load_yaml_catalog("locales/ja.yaml"))

    # Set locale
    manager.set_locale("ja")

    # Static translation (doesn't update on locale change)
    label = t("common.save")

    # Reactive translation (updates automatically)
    from castella import Text
    Text(LocaleString("dashboard.title"))

    # With interpolation
    Text(LocaleString("greeting", name="World"))
"""

from typing import Any

from .catalog import TranslationCatalog
from .loader import (
    create_catalog_from_dict,
    load_catalog,
    load_catalogs_from_directory,
    load_json_catalog,
    load_yaml_catalog,
)
from .locale_string import LocalePluralString, LocaleString
from .manager import I18nManager, I18nObserver
from .plural import PluralCategory, PluralRules, get_plural_rules, register_plural_rules


def t(key: str, **kwargs: Any) -> str:
    """Translate a key using the current locale.

    Convenience function that uses the I18nManager singleton.

    Args:
        key: Translation key (dot-notation, e.g., 'common.save')
        **kwargs: Values for string interpolation

    Returns:
        Translated string, or the key itself if not found

    Example:
        t("common.save")  # Returns "Save" or localized equivalent
        t("greeting", name="World")  # Returns "Hello, World!"
    """
    return I18nManager().t(key, **kwargs)


def tn(key: str, count: int, **kwargs: Any) -> str:
    """Translate a key with pluralization.

    Convenience function for pluralized translations.

    Args:
        key: Translation key for plural forms
        count: Count for plural selection
        **kwargs: Additional interpolation values

    Returns:
        Translated string with appropriate plural form

    Example:
        tn("items", 1)  # Returns "1 item"
        tn("items", 5)  # Returns "5 items"
    """
    return I18nManager().tn(key, count, **kwargs)


__all__ = [
    # Manager
    "I18nManager",
    "I18nObserver",
    # Convenience functions
    "t",
    "tn",
    # Reactive strings
    "LocaleString",
    "LocalePluralString",
    # Catalog
    "TranslationCatalog",
    # Loaders
    "load_yaml_catalog",
    "load_json_catalog",
    "load_catalog",
    "load_catalogs_from_directory",
    "create_catalog_from_dict",
    # Plural rules
    "PluralCategory",
    "PluralRules",
    "get_plural_rules",
    "register_plural_rules",
]
