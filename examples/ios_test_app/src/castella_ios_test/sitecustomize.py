"""Site customization for iOS - patches locale before any app code runs."""

import locale

# Store original
_original_setlocale = locale.setlocale


def _patched_setlocale(category, locale_str=""):
    """Patched setlocale that handles iOS locale issues."""
    try:
        return _original_setlocale(category, locale_str)
    except locale.Error:
        try:
            return _original_setlocale(category, "C")
        except locale.Error:
            return _original_setlocale(category, None)


# Patch it
locale.setlocale = _patched_setlocale
