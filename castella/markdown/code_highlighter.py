"""Syntax highlighting for code blocks using Pygments."""

from io import BytesIO

import numpy as np
from pygments import highlight
from pygments.formatters import ImageFormatter
from pygments.lexers import get_lexer_by_name, guess_lexer, TextLexer

try:
    from PIL import Image
except ImportError:
    Image = None


class CodeHighlighter:
    """Renders code with syntax highlighting to numpy array."""

    def __init__(
        self,
        font_name: str = "Menlo",  # macOS default monospace font
        font_size: int = 12,
        style: str = "monokai",
        line_numbers: bool = True,
    ):
        self._font_name = font_name
        self._font_size = font_size
        self._style = style
        self._line_numbers = line_numbers
        self._cache: dict[str, np.ndarray] = {}

    def highlight(
        self,
        code: str,
        language: str = "",
        width: int | None = None,
    ) -> np.ndarray:
        """Render code with syntax highlighting to RGBA numpy array.

        Args:
            code: Source code to highlight
            language: Programming language (empty for auto-detect)
            width: Optional max width (not used currently)

        Returns:
            RGBA numpy array of the rendered code
        """
        cache_key = f"{code}:{language}:{self._style}:{self._font_size}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        lexer = self._get_lexer(language, code)

        formatter = ImageFormatter(
            font_name=self._font_name,
            font_size=self._font_size,
            style=self._style,
            line_numbers=self._line_numbers,
            line_number_bg="#1e1e1e" if "monokai" in self._style else "#f0f0f0",
            line_number_fg="#858585",
        )

        result = highlight(code, lexer, formatter)

        if Image is not None:
            img = Image.open(BytesIO(result))
            array = np.ascontiguousarray(np.array(img.convert("RGBA")))
        else:
            array = np.zeros((100, 400, 4), dtype=np.uint8)
            array[:, :, 3] = 255

        self._cache[cache_key] = array
        return array

    def _get_lexer(self, language: str, code: str):
        """Get appropriate lexer for the code."""
        if language:
            try:
                return get_lexer_by_name(language)
            except Exception:
                pass

        try:
            return guess_lexer(code)
        except Exception:
            return TextLexer()

    def clear_cache(self) -> None:
        """Clear the rendering cache."""
        self._cache.clear()
