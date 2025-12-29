"""Modal dialog widget with backdrop overlay.

Provides a modal dialog that appears on top of other content with
a semi-transparent backdrop that can optionally close the modal when clicked.
"""

from __future__ import annotations

from typing import Callable, Self

from castella.box import Box
from castella.button import Button
from castella.column import Column
from castella.core import (
    Kind,
    ObservableBase,
    SizePolicy,
    StatefulComponent,
    Widget,
)
from castella.row import Row
from castella.spacer import Spacer
from castella.text import Text
from castella.theme import ThemeManager


class ModalState(ObservableBase):
    """Observable state for Modal widget.

    Controls whether the modal is open or closed.
    """

    def __init__(self, open: bool = False):
        """Initialize ModalState.

        Args:
            open: Whether the modal is initially open
        """
        super().__init__()
        self._open = open

    def is_open(self) -> bool:
        """Check if modal is open."""
        return self._open

    def open(self) -> None:
        """Open the modal."""
        if not self._open:
            self._open = True
            self.notify()

    def close(self) -> None:
        """Close the modal."""
        if self._open:
            self._open = False
            self.notify()

    def toggle(self) -> None:
        """Toggle modal open/closed state."""
        self._open = not self._open
        self.notify()

    def set(self, open: bool) -> None:
        """Set modal open state.

        Args:
            open: Whether the modal should be open
        """
        if self._open != open:
            self._open = open
            self.notify()


class Modal(StatefulComponent):
    """Modal dialog with backdrop overlay.

    The modal uses z-index layering to appear on top of other content:
    - Content at z-index 1 (default)
    - Backdrop at z-index 99
    - Modal dialog at z-index 100

    Example:
        modal_state = ModalState(open=False)

        # In your component's view():
        modal = Modal(
            content=Column(Text("Modal content"), Button("Close")),
            state=modal_state,
            title="My Modal",
        )

        # Open the modal
        Button("Open").on_click(lambda _: modal_state.open())
    """

    def __init__(
        self,
        content: Widget,
        state: ModalState | None = None,
        title: str | None = None,
        width: int = 400,
        height: int = 300,
        close_on_backdrop_click: bool = True,
        show_close_button: bool = True,
    ):
        """Initialize Modal.

        Args:
            content: The content to display in the modal
            state: Optional ModalState (creates new state if not provided)
            title: Optional title for the modal header
            width: Width of the modal dialog
            height: Height of the modal dialog
            close_on_backdrop_click: Whether clicking the backdrop closes the modal
            show_close_button: Whether to show a close button in the header
        """
        self._content = content
        self._title = title
        self._modal_width = width
        self._modal_height = height
        self._close_on_backdrop_click = close_on_backdrop_click
        self._show_close_button = show_close_button
        self._on_close_callback: Callable[[], None] = lambda: None
        self._on_open_callback: Callable[[], None] = lambda: None

        self._modal_state = state or ModalState(False)
        super().__init__(self._modal_state)

    def view(self) -> Widget:
        """Build the modal UI."""
        if not self._modal_state.is_open():
            # Return invisible placeholder when closed
            return Spacer().fixed_size(0, 0)

        theme = ThemeManager().current

        # Build backdrop (semi-transparent overlay)
        backdrop = (
            _ClickableBackdrop(
                self._on_backdrop_click if self._close_on_backdrop_click else None
            )
            .bg_color("rgba(0, 0, 0, 0.5)")
            .z_index(99)
        )

        # Build modal content
        modal_children = []

        # Title bar with optional close button
        if self._title or self._show_close_button:
            title_elements = []
            if self._title:
                title_elements.append(
                    Text(self._title)
                    .text_color(theme.colors.text_primary)
                    .erase_border()
                )
            title_elements.append(Spacer())
            if self._show_close_button:
                title_elements.append(
                    Button("×")
                    .on_click(lambda _: self._close())
                    .kind(Kind.DANGER)
                    .fixed_size(32, 32)
                )

            title_bar = Row(*title_elements).height(40).height_policy(SizePolicy.FIXED)
            modal_children.append(title_bar)

        # Add content
        modal_children.append(self._content)

        # Modal dialog
        modal_dialog = (
            Column(*modal_children)
            .bg_color(theme.colors.bg_primary)
            .fixed_size(self._modal_width, self._modal_height)
            .z_index(100)
        )

        return Box(backdrop, modal_dialog)

    def _on_backdrop_click(self, _) -> None:
        """Handle backdrop click."""
        self._close()

    def _close(self) -> None:
        """Close the modal and call callback."""
        self._modal_state.close()
        self._on_close_callback()

    def on_close(self, callback: Callable[[], None]) -> Self:
        """Set callback for when modal closes.

        Args:
            callback: Function called when modal closes

        Returns:
            Self for method chaining
        """
        self._on_close_callback = callback
        return self

    def on_open(self, callback: Callable[[], None]) -> Self:
        """Set callback for when modal opens.

        Args:
            callback: Function called when modal opens

        Returns:
            Self for method chaining
        """
        self._on_open_callback = callback
        return self

    def modal_size(self, width: int, height: int) -> Self:
        """Set modal dialog size.

        Args:
            width: Width in pixels
            height: Height in pixels

        Returns:
            Self for method chaining
        """
        self._modal_width = width
        self._modal_height = height
        return self

    def title(self, title: str) -> Self:
        """Set modal title.

        Args:
            title: Title text

        Returns:
            Self for method chaining
        """
        self._title = title
        return self


class _ClickableBackdrop(Spacer):
    """Internal backdrop widget that handles click events."""

    def __init__(self, on_click: Callable | None = None):
        super().__init__()
        self._on_click_handler = on_click

    def mouse_up(self, ev) -> None:
        """Handle mouse up (click)."""
        if self._on_click_handler:
            self._on_click_handler(ev)
