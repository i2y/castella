"""Content viewer modal for studio applications.

Provides a reusable modal for displaying full content like
docstrings, source code, or other text content.
"""

from __future__ import annotations

from castella import Column, Row, Spacer
from castella.modal import Modal, ModalState
from castella.multiline_text import MultilineText


class ContentViewerModal:
    """Content viewer modal for displaying text/code content.

    Supports two modes:
    - Text mode: Wrapped text display (for docstrings, documentation)
    - Code mode: Non-wrapped text with horizontal scrolling (for source code)

    Usage:
        modal = ContentViewerModal()
        modal.open("Title", "Content here", mode="code")

        # In view():
        if modal.is_open:
            return Box(main_content, modal.build())
    """

    def __init__(
        self,
        default_text_width: int = 600,
        default_text_height: int = 400,
        default_code_width: int = 800,
        default_code_height: int = 600,
    ):
        """Initialize the content viewer modal.

        Args:
            default_text_width: Default modal width for text mode.
            default_text_height: Default modal height for text mode.
            default_code_width: Default modal width for code mode.
            default_code_height: Default modal height for code mode.
        """
        self._modal_state = ModalState()
        self._title: str = ""
        self._content: str = ""
        self._mode: str = "text"  # "text" or "code"

        self._text_width = default_text_width
        self._text_height = default_text_height
        self._code_width = default_code_width
        self._code_height = default_code_height

        self._on_close_callback = None

    @property
    def state(self) -> ModalState:
        """Get the modal state for attaching to component."""
        return self._modal_state

    @property
    def is_open(self) -> bool:
        """Check if the modal is open."""
        return self._modal_state.is_open()

    @property
    def mode(self) -> str:
        """Get the current display mode."""
        return self._mode

    def attach(self, component) -> None:
        """Attach modal state to a component for reactivity.

        Args:
            component: Component to attach to.
        """
        self._modal_state.attach(component)

    def open(self, title: str, content: str, mode: str = "text") -> None:
        """Open the modal with content.

        Args:
            title: Modal title.
            content: Content to display.
            mode: Display mode - "text" for wrapped text, "code" for source code.
        """
        self._title = title
        self._content = content
        self._mode = mode
        self._modal_state.open()

    def open_docstring(self, label: str, content: str) -> None:
        """Open modal for viewing a docstring.

        Args:
            label: Item label (used in title).
            content: Docstring content.
        """
        self.open(f"{label} - Description", content, mode="text")

    def open_source(self, label: str, content: str) -> None:
        """Open modal for viewing source code.

        Args:
            label: Item label (used in title).
            content: Source code content.
        """
        self.open(f"{label} - Source Code", content, mode="code")

    def close(self) -> None:
        """Close the modal."""
        self._modal_state.close()
        self._title = ""
        self._content = ""
        self._mode = "text"
        if self._on_close_callback:
            self._on_close_callback()

    def on_close(self, callback) -> "ContentViewerModal":
        """Set close callback.

        Args:
            callback: Function to call when modal is closed.

        Returns:
            Self for chaining.
        """
        self._on_close_callback = callback
        return self

    def build(self) -> Modal:
        """Build the modal widget.

        Returns:
            Modal widget configured for current content.
        """
        if self._mode == "code":
            return self._build_code_modal()
        else:
            return self._build_text_modal()

    def _build_text_modal(self) -> Modal:
        """Build modal for text (docstring) display."""
        content = self._content
        lines = content.split("\n")
        line_count = len(lines)
        # Calculate content height (16px per line + padding)
        content_height = max(60, line_count * 16 + 24)

        modal_content = Column(
            Spacer().fixed_height(8),
            Row(
                Spacer().fixed_width(8),
                MultilineText(
                    content,
                    font_size=13,
                    wrap=True,
                )
                .text_color("#e5e7eb")
                .fixed_height(content_height),
                Spacer().fixed_width(8),
            ).fixed_height(content_height),
            Spacer().fixed_height(8),
            scrollable=True,
        )

        return Modal(
            content=modal_content,
            state=self._modal_state,
            title=self._title,
            width=self._text_width,
            height=self._text_height,
        ).on_close(self.close)

    def _build_code_modal(self) -> Modal:
        """Build modal for source code display."""
        content = self._content
        lines = content.split("\n")
        line_count = len(lines)
        # Calculate content height (14px per line + padding)
        content_height = max(100, line_count * 14 + 24)
        # Add padding for scrollbar (approx 20px)
        padded_content_height = content_height + 20
        # Calculate content width based on longest line (approx 7px per char at font_size=12)
        max_line_len = max(len(line) for line in lines) if lines else 0
        content_width = max(300, max_line_len * 7 + 16)

        modal_content = Column(
            Spacer().fixed_height(8),
            Row(
                Spacer().fixed_width(8),
                Column(
                    Row(
                        MultilineText(
                            content,
                            font_size=12,
                            wrap=False,
                        )
                        .text_color("#a5d6ff")
                        .bg_color("#161b22")
                        .fixed_size(content_width, padded_content_height),
                        scrollable=True,
                    ).fixed_height(padded_content_height),
                    scrollable=True,
                ),
                Spacer().fixed_width(8),
            ),
            Spacer().fixed_height(8),
        )

        return Modal(
            content=modal_content,
            state=self._modal_state,
            title=self._title,
            width=self._code_width,
            height=self._code_height,
        ).on_close(self.close)
