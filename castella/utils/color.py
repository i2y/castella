"""Color conversion utilities."""

from __future__ import annotations


def hex_to_rgb(color_code: str) -> tuple[int, int, int]:
    """Convert hex color code to RGB tuple.

    Args:
        color_code: Hex color string like "#FF00FF" or "FF00FF"

    Returns:
        Tuple of (r, g, b) values 0-255
    """
    code = color_code.lstrip("#")
    return (
        int(code[0:2], 16),
        int(code[2:4], 16),
        int(code[4:6], 16),
    )


def hex_to_rgba(color_code: str, alpha: float = 1.0) -> tuple[int, int, int, float]:
    """Convert hex color code to RGBA tuple.

    Args:
        color_code: Hex color string like "#FF00FF" or "#FF00FFAA"
        alpha: Alpha value 0.0-1.0 (used if not in color_code)

    Returns:
        Tuple of (r, g, b, a) where r,g,b are 0-255 and a is 0.0-1.0
    """
    code = color_code.lstrip("#")
    r = int(code[0:2], 16)
    g = int(code[2:4], 16)
    b = int(code[4:6], 16)

    # Check if alpha is included in the color code
    if len(code) == 8:
        alpha = int(code[6:8], 16) / 255.0

    return (r, g, b, alpha)


def rgb_to_hex(r: int, g: int, b: int) -> str:
    """Convert RGB tuple to hex color code.

    Args:
        r: Red value 0-255
        g: Green value 0-255
        b: Blue value 0-255

    Returns:
        Hex color string like "#FF00FF"
    """
    return f"#{r:02x}{g:02x}{b:02x}"


def rgba_to_hex(r: int, g: int, b: int, a: float) -> str:
    """Convert RGBA tuple to hex color code with alpha.

    Args:
        r: Red value 0-255
        g: Green value 0-255
        b: Blue value 0-255
        a: Alpha value 0.0-1.0

    Returns:
        Hex color string like "#FF00FFAA"
    """
    alpha_int = int(a * 255)
    return f"#{r:02x}{g:02x}{b:02x}{alpha_int:02x}"


class SkiaColorConverter:
    """Skia-specific color conversion."""

    @staticmethod
    def to_skia_color(color: str) -> int:
        """Convert hex color to Skia color integer."""
        import skia

        return skia.ColorSetRGB(*hex_to_rgb(color))


class CanvasKitColorConverter:
    """CanvasKit-specific color conversion."""

    @staticmethod
    def to_ck_color(color: str):
        """Convert hex color to CanvasKit color."""
        from js import window  # type: ignore

        return window.CK.Color(*hex_to_rgba(color))


class PTColorConverter:
    """prompt_toolkit style string conversion."""

    @staticmethod
    def to_bg_style(color: str) -> str:
        """Convert to prompt_toolkit background style."""
        return f"bg:{color}"

    @staticmethod
    def to_fg_style(color: str) -> str:
        """Convert to prompt_toolkit foreground style."""
        return f"fg:{color}"
