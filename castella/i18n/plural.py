"""Plural rules for internationalization.

Implements CLDR plural rules for different locales.
See: https://cldr.unicode.org/index/cldr-spec/plural-rules
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Callable


class PluralCategory(Enum):
    """CLDR plural categories."""

    ZERO = "zero"
    ONE = "one"
    TWO = "two"
    FEW = "few"
    MANY = "many"
    OTHER = "other"


@dataclass
class PluralRules:
    """Plural rules for a locale.

    Each locale has different rules for selecting plural forms.
    For example:
    - English: 1 = one, everything else = other
    - Japanese: always other (no grammatical plural)
    - Russian: complex rules for one, few, many, other

    Usage:
        rules = get_plural_rules("en")
        category = rules.select(1)  # PluralCategory.ONE
        category = rules.select(5)  # PluralCategory.OTHER
    """

    locale: str
    selector: Callable[[int], PluralCategory]

    def select(self, count: int) -> PluralCategory:
        """Select the plural category for a count.

        Args:
            count: The number to select for

        Returns:
            The appropriate PluralCategory
        """
        return self.selector(count)


def _en_plural(count: int) -> PluralCategory:
    """English plural rules: 1 = one, else = other."""
    if count == 1:
        return PluralCategory.ONE
    return PluralCategory.OTHER


def _ja_plural(count: int) -> PluralCategory:
    """Japanese plural rules: always other (no grammatical plural)."""
    return PluralCategory.OTHER


def _zh_plural(count: int) -> PluralCategory:
    """Chinese plural rules: always other (no grammatical plural)."""
    return PluralCategory.OTHER


def _fr_plural(count: int) -> PluralCategory:
    """French plural rules: 0-1 = one, else = other."""
    if count in (0, 1):
        return PluralCategory.ONE
    return PluralCategory.OTHER


def _de_plural(count: int) -> PluralCategory:
    """German plural rules: 1 = one, else = other."""
    if count == 1:
        return PluralCategory.ONE
    return PluralCategory.OTHER


def _ru_plural(count: int) -> PluralCategory:
    """Russian plural rules (simplified).

    - one: 1, 21, 31, 41... (but not 11)
    - few: 2-4, 22-24, 32-34... (but not 12-14)
    - many: 0, 5-20, 25-30, 35-40...
    """
    n = abs(count)
    mod10 = n % 10
    mod100 = n % 100

    if mod10 == 1 and mod100 != 11:
        return PluralCategory.ONE
    if 2 <= mod10 <= 4 and not (12 <= mod100 <= 14):
        return PluralCategory.FEW
    return PluralCategory.MANY


# Built-in plural rules
_PLURAL_RULES: dict[str, PluralRules] = {
    "en": PluralRules("en", _en_plural),
    "ja": PluralRules("ja", _ja_plural),
    "zh": PluralRules("zh", _zh_plural),
    "fr": PluralRules("fr", _fr_plural),
    "de": PluralRules("de", _de_plural),
    "ru": PluralRules("ru", _ru_plural),
}

# Default rules (English-like)
_DEFAULT_RULES = PluralRules("default", _en_plural)


def get_plural_rules(locale: str) -> PluralRules:
    """Get plural rules for a locale.

    Args:
        locale: Locale code (e.g., 'en', 'ja')

    Returns:
        PluralRules for the locale, or default rules if not found
    """
    # Try exact match
    if locale in _PLURAL_RULES:
        return _PLURAL_RULES[locale]

    # Try language code only (e.g., 'en_US' -> 'en')
    lang_code = locale.split("_")[0].split("-")[0]
    if lang_code in _PLURAL_RULES:
        return _PLURAL_RULES[lang_code]

    return _DEFAULT_RULES


def register_plural_rules(locale: str, rules: PluralRules) -> None:
    """Register custom plural rules for a locale.

    Args:
        locale: Locale code
        rules: PluralRules instance
    """
    _PLURAL_RULES[locale] = rules
