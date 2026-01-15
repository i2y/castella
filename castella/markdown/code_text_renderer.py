"""Text-based syntax highlighting for code blocks using Pygments."""

from dataclasses import dataclass

from pygments import lex
from pygments.lexers import get_lexer_by_name, guess_lexer, TextLexer
from pygments.styles import get_style_by_name


@dataclass
class CodeToken:
    """A single token in highlighted code."""

    text: str
    color: str
    bold: bool = False
    italic: bool = False


@dataclass
class CodeLine:
    """A line of highlighted code with tokens."""

    line_number: int
    tokens: list[CodeToken]


class CodeTextRenderer:
    """Renders code with syntax highlighting as styled text tokens.

    Unlike CodeHighlighter which renders to images, this class returns
    structured token data that can be rendered by the Painter API.
    """

    def __init__(
        self,
        style: str = "monokai",
    ):
        self._style_name = style
        self._style = get_style_by_name(style)
        self._cache: dict[str, list[CodeLine]] = {}

    @property
    def background_color(self) -> str:
        """Get the background color for code blocks."""
        bg = self._style.background_color
        return bg if bg else "#1e1e1e"

    @property
    def line_number_color(self) -> str:
        """Get the color for line numbers."""
        # Use a muted color for line numbers
        return "#858585"

    def highlight(
        self,
        code: str,
        language: str = "",
    ) -> list[CodeLine]:
        """Render code with syntax highlighting to styled tokens.

        Args:
            code: Source code to highlight
            language: Programming language (empty for auto-detect)

        Returns:
            List of CodeLine objects with tokens
        """
        cache_key = f"{code}:{language}:{self._style_name}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        lexer = self._get_lexer(language, code)
        tokens = list(lex(code, lexer))

        lines: list[CodeLine] = []
        current_line_tokens: list[CodeToken] = []
        line_number = 1

        for token_type, token_text in tokens:
            # Get style for this token type
            try:
                style = self._style.style_for_token(token_type)
                color = f"#{style['color']}" if style.get("color") else "#f8f8f2"
                bold = style.get("bold", False) or False
                italic = style.get("italic", False) or False
            except (KeyError, Exception):
                # Fallback for unknown token types
                color = "#f8f8f2"
                bold = False
                italic = False

            # Split by newlines
            parts = token_text.split("\n")
            for i, part in enumerate(parts):
                if part:  # Non-empty part
                    current_line_tokens.append(
                        CodeToken(text=part, color=color, bold=bold, italic=italic)
                    )

                # If not the last part, this means we hit a newline
                if i < len(parts) - 1:
                    lines.append(
                        CodeLine(line_number=line_number, tokens=current_line_tokens)
                    )
                    current_line_tokens = []
                    line_number += 1

        # Don't forget the last line if it has tokens
        if current_line_tokens:
            lines.append(CodeLine(line_number=line_number, tokens=current_line_tokens))
        elif lines and code.endswith("\n"):
            # If code ends with newline and we have lines, the last empty line was already handled
            pass
        elif not lines:
            # Empty code
            lines.append(CodeLine(line_number=1, tokens=[]))

        self._cache[cache_key] = lines
        return lines

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
