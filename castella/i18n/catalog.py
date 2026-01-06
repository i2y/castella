"""Translation catalog for storing translations."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .plural import PluralCategory, get_plural_rules


@dataclass
class TranslationCatalog:
    """Translation catalog for a single locale.

    Stores translations as a nested dictionary and provides
    dot-notation key lookup.

    Example:
        catalog = TranslationCatalog(
            locale="en",
            translations={
                "common": {
                    "save": "Save",
                    "cancel": "Cancel",
                },
                "items": {
                    "one": "{count} item",
                    "other": "{count} items",
                }
            }
        )

        catalog.get("common.save")  # Returns "Save"
        catalog.get_plural("items", 1)  # Returns "{count} item"
        catalog.get_plural("items", 5)  # Returns "{count} items"
    """

    locale: str
    translations: dict[str, Any] = field(default_factory=dict)
    name: str = ""

    def __post_init__(self) -> None:
        if not self.name:
            self.name = self.locale

    def get(self, key: str, default: str | None = None) -> str | None:
        """Get a translation by dot-notation key.

        Args:
            key: Dot-separated key (e.g., 'common.save')
            default: Default value if key not found

        Returns:
            Translation string or default
        """
        parts = key.split(".")
        current: Any = self.translations

        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return default

        if isinstance(current, str):
            return current
        return default

    def get_plural(
        self, key: str, count: int, default: str | None = None
    ) -> str | None:
        """Get a pluralized translation.

        Looks up the translation at `key` which should be a dict with
        plural category keys (zero, one, two, few, many, other).

        Args:
            key: Base key for plural translations
            count: Number for plural selection
            default: Default value if not found

        Returns:
            Appropriate plural form or default
        """
        parts = key.split(".")
        current: Any = self.translations

        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return default

        if not isinstance(current, dict):
            # If it's a string, return it directly (no pluralization)
            if isinstance(current, str):
                return current
            return default

        # Get plural category for this locale and count
        rules = get_plural_rules(self.locale)
        category = rules.select(count)

        # Try exact category first
        if category.value in current:
            return str(current[category.value])

        # Fall back to 'other' category
        if PluralCategory.OTHER.value in current:
            return str(current[PluralCategory.OTHER.value])

        return default

    def has(self, key: str) -> bool:
        """Check if a translation exists for a key.

        Args:
            key: Dot-separated key

        Returns:
            True if the key exists
        """
        return self.get(key) is not None

    def merge(self, other: "TranslationCatalog") -> "TranslationCatalog":
        """Merge another catalog into this one.

        Creates a new catalog with translations from both.
        Other catalog's translations take precedence on conflicts.

        Args:
            other: Catalog to merge

        Returns:
            New merged catalog
        """

        def deep_merge(base: dict, override: dict) -> dict:
            result = base.copy()
            for key, value in override.items():
                if (
                    key in result
                    and isinstance(result[key], dict)
                    and isinstance(value, dict)
                ):
                    result[key] = deep_merge(result[key], value)
                else:
                    result[key] = value
            return result

        merged = deep_merge(self.translations, other.translations)
        return TranslationCatalog(
            locale=self.locale,
            translations=merged,
            name=self.name,
        )
