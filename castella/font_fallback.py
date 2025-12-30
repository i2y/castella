"""Font fallback support for Skia rendering.

This module provides automatic font fallback for characters not supported
by the primary font, such as emoji (⭐, ❤️) and special symbols (●, ★).
"""

from functools import lru_cache

import skia


@lru_cache(maxsize=1)
def get_font_mgr() -> skia.FontMgr:
    """Get the system FontMgr singleton (cached)."""
    return skia.FontMgr()


def has_glyph(typeface: skia.Typeface, codepoint: int) -> bool:
    """Check if typeface has a glyph for the given Unicode codepoint."""
    if typeface is None:
        return False
    return typeface.unicharToGlyph(codepoint) != 0


def find_fallback_typeface(
    codepoint: int,
    font_style: skia.FontStyle,
) -> skia.Typeface | None:
    """Find a system font that can render the given character.

    Uses Skia's FontMgr.matchFamilyStyleCharacter() to find an appropriate
    fallback font from the system's installed fonts.

    Args:
        codepoint: Unicode codepoint to find a font for
        font_style: Desired font style (weight, width, slant)

    Returns:
        A Typeface that can render the character, or None if not found
    """
    fm = get_font_mgr()
    return fm.matchFamilyStyleCharacter(
        "",  # Empty string = search system default fonts
        font_style,
        ["ja", "en"],  # Language hints for CJK fallback
        codepoint,
    )


@lru_cache(maxsize=4096)
def _get_typeface_for_codepoint(
    codepoint: int,
    primary_typeface_family: str,
    font_style_tuple: tuple[int, int, int],
) -> str | None:
    """Get the typeface family name for a codepoint (cached).

    Returns the family name string instead of the Typeface object
    to make the result hashable for caching.

    Args:
        codepoint: Unicode codepoint
        primary_typeface_family: Primary font family name (can be empty)
        font_style_tuple: (weight, width, slant) tuple for FontStyle

    Returns:
        Font family name that can render the codepoint, or None to use primary
    """
    # Create FontStyle from tuple
    font_style = skia.FontStyle(
        font_style_tuple[0], font_style_tuple[1], font_style_tuple[2]
    )

    # Check if primary typeface exists and can render this character
    fm = get_font_mgr()
    primary_typeface = None
    if primary_typeface_family:
        primary_typeface = fm.matchFamilyStyle(primary_typeface_family, font_style)

    if primary_typeface is not None and has_glyph(primary_typeface, codepoint):
        return None  # Use primary font

    # Primary font doesn't have this glyph (or doesn't exist), find fallback
    fallback = find_fallback_typeface(codepoint, font_style)
    if fallback is not None:
        family_name = fallback.getFamilyName()
        return family_name

    return None  # No fallback found, use primary anyway


def segment_text_by_font(
    text: str,
    primary_typeface: skia.Typeface,
    font_style: skia.FontStyle,
) -> list[tuple[str, skia.Typeface]]:
    """Segment text into runs, each with a font that can render it.

    Groups consecutive characters that use the same font to minimize
    the number of draw calls.

    Args:
        text: Text to segment
        primary_typeface: Primary typeface to use when possible (can be None)
        font_style: Font style for fallback lookup

    Returns:
        List of (text_segment, typeface) tuples
    """
    if not text:
        return []

    primary_family = primary_typeface.getFamilyName() if primary_typeface else ""
    font_style_tuple = (
        font_style.weight(),
        font_style.width(),
        font_style.slant(),
    )

    fm = get_font_mgr()
    segments: list[tuple[str, skia.Typeface]] = []
    current_segment = ""
    current_typeface = primary_typeface
    current_family: str | None = None  # None means primary

    for char in text:
        codepoint = ord(char)

        # Get the family name for this codepoint (cached)
        family = _get_typeface_for_codepoint(
            codepoint, primary_family, font_style_tuple
        )

        if family != current_family:
            # Font changed, flush current segment
            if current_segment:
                segments.append((current_segment, current_typeface))

            # Start new segment
            current_segment = char
            current_family = family

            if family is None:
                current_typeface = primary_typeface
            else:
                # Get typeface for the family
                typeface = fm.matchFamilyStyle(family, font_style)
                current_typeface = typeface if typeface else primary_typeface
        else:
            # Same font, extend segment
            current_segment += char

    # Flush remaining segment
    if current_segment:
        segments.append((current_segment, current_typeface))

    return segments
