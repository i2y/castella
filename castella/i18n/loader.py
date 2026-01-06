"""Translation file loaders."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .catalog import TranslationCatalog


def load_yaml_catalog(path: Path | str) -> TranslationCatalog:
    """Load a translation catalog from a YAML file.

    The YAML file should have optional 'locale' and 'name' fields
    at the top level. All other fields are treated as translations.

    Example YAML:
        locale: en
        name: English
        common:
          save: "Save"
          cancel: "Cancel"

    Args:
        path: Path to the YAML file

    Returns:
        TranslationCatalog instance

    Raises:
        ImportError: If PyYAML is not installed
        FileNotFoundError: If file doesn't exist
    """
    try:
        import yaml
    except ImportError as e:
        raise ImportError(
            "PyYAML is required for loading YAML translation files. Install with: pip install pyyaml"
        ) from e

    path = Path(path)
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    # Extract metadata
    locale = data.pop("locale", path.stem)
    name = data.pop("name", locale)

    return TranslationCatalog(
        locale=locale,
        translations=data,
        name=name,
    )


def load_json_catalog(path: Path | str) -> TranslationCatalog:
    """Load a translation catalog from a JSON file.

    The JSON file should have optional 'locale' and 'name' fields
    at the top level. All other fields are treated as translations.

    Args:
        path: Path to the JSON file

    Returns:
        TranslationCatalog instance
    """
    path = Path(path)
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    # Extract metadata
    locale = data.pop("locale", path.stem)
    name = data.pop("name", locale)

    return TranslationCatalog(
        locale=locale,
        translations=data,
        name=name,
    )


def load_catalog(path: Path | str) -> TranslationCatalog:
    """Load a translation catalog from a file (auto-detect format).

    Supports YAML (.yaml, .yml) and JSON (.json) files.

    Args:
        path: Path to the translation file

    Returns:
        TranslationCatalog instance

    Raises:
        ValueError: If file extension is not supported
    """
    path = Path(path)
    suffix = path.suffix.lower()

    if suffix in (".yaml", ".yml"):
        return load_yaml_catalog(path)
    elif suffix == ".json":
        return load_json_catalog(path)
    else:
        raise ValueError(
            f"Unsupported file format: {suffix}. Use .yaml, .yml, or .json"
        )


def load_catalogs_from_directory(
    directory: Path | str,
    pattern: str = "*.yaml",
) -> dict[str, TranslationCatalog]:
    """Load all translation catalogs from a directory.

    Args:
        directory: Directory containing translation files
        pattern: Glob pattern for translation files (default: "*.yaml")

    Returns:
        Dictionary mapping locale codes to catalogs
    """
    directory = Path(directory)
    catalogs: dict[str, TranslationCatalog] = {}

    for file_path in directory.glob(pattern):
        catalog = load_catalog(file_path)
        catalogs[catalog.locale] = catalog

    return catalogs


def create_catalog_from_dict(
    locale: str, translations: dict[str, Any], name: str = ""
) -> TranslationCatalog:
    """Create a translation catalog from a dictionary.

    Convenience function for creating catalogs programmatically.

    Args:
        locale: Locale code
        translations: Dictionary of translations
        name: Display name for the locale

    Returns:
        TranslationCatalog instance
    """
    return TranslationCatalog(
        locale=locale,
        translations=translations,
        name=name or locale,
    )
