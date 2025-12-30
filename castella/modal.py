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
from castella.models import Point
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
        show_backdrop: bool = True,
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
            show_backdrop: Whether to show semi-transparent backdrop (default True)
        """
        self._content = content
        self._title = title
        self._modal_width = width
        self._modal_height = height
        self._close_on_backdrop_click = close_on_backdrop_click
        self._show_close_button = show_close_button
        self._show_backdrop = show_backdrop
        self._on_close_callback: Callable[[], None] = lambda: None
        self._on_open_callback: Callable[[], None] = lambda: None

        self._modal_state = state or ModalState(False)
        super().__init__(self._modal_state)
        # Modal must have high z-index to receive events before other content
        self.z_index(98)

    def view(self) -> Widget:
        """Build the modal UI."""
        if not self._modal_state.is_open():
            # Return invisible placeholder when closed
            return Spacer().fixed_size(0, 0)

        theme = ThemeManager().current

        # Build backdrop (semi-transparent overlay) if enabled
        backdrop = None
        if self._show_backdrop:
            backdrop = (
                _ClickableBackdrop(
                    self._on_backdrop_click if self._close_on_backdrop_click else None
                )
                .bg_color("rgba(0, 0, 0, 0.5)")
                .z_index(99)
            )
        elif self._close_on_backdrop_click:
            # Invisible click catcher (no background drawing)
            backdrop = _ClickableBackdrop(self._on_backdrop_click).z_index(99)

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

        if backdrop:
            return Box(backdrop, modal_dialog)
        else:
            return Box(modal_dialog)

    def redraw(self, p, completely: bool) -> None:
        """Draw the modal. Skip drawing when closed to avoid covering other content."""
        if not self._modal_state.is_open():
            # Don't draw anything when closed - the child is a 0x0 Spacer
            # and we don't want to draw the Layout background
            return
        super().redraw(p, completely)

    def dispatch(self, p):
        """Dispatch mouse events. When closed, don't capture events."""
        if not self._modal_state.is_open():
            # When closed, don't capture any events - let them pass through
            return None, None

        # If Modal not yet laid out, still block events (don't pass through)
        size = self.get_size()
        if size.width == 0 or size.height == 0:
            # Block event by returning self, but don't dispatch to children
            return self, Point(x=0, y=0)

        # Ensure child widget is created (normally done in redraw)
        # This is needed because dispatch may be called before redraw
        if self._child is None:
            self._child = self.view()
            self.add(self._child)
            # Only do manual layout if child was just created
            # (real layout hasn't happened yet via redraw)
            self._layout_for_dispatch()

        return super().dispatch(p)

    def _layout_for_dispatch(self) -> None:
        """Layout child widgets for event dispatch without a Painter.

        This is a simplified layout that works for Modal's specific structure.
        Recursively layouts widgets using EXPANDING/FIXED policies.
        """
        size = self.get_size()
        pos = self.get_pos()

        if self._child is None:
            return

        # Size and position the Box (Modal's direct child)
        self._child.resize(size.model_copy())
        self._child.move(pos)

        # Recursively layout all descendants
        self._layout_widget_tree(self._child, size, pos)

    def _layout_widget_tree(self, widget: Widget, parent_size, parent_pos) -> None:
        """Recursively layout a widget and its children for dispatch."""
        from castella.core import SizePolicy

        if not hasattr(widget, "_children"):
            return

        # Calculate positions for children
        # This is a simplified layout - works for Box, Column, Row
        current_y = parent_pos.y
        current_x = parent_pos.x

        for c in widget._children:
            # Set size based on policy
            if c.get_width_policy() is SizePolicy.EXPANDING:
                c.width(parent_size.width)
            elif c.get_width_policy() is SizePolicy.FIXED:
                pass  # Already set

            if c.get_height_policy() is SizePolicy.EXPANDING:
                c.height(parent_size.height)
            elif c.get_height_policy() is SizePolicy.FIXED:
                pass  # Already set

            child_width = c.get_width()
            child_height = c.get_height()

            # Position based on widget type
            widget_type = type(widget).__name__

            if widget_type == "Box":
                # Box centers fixed-size children
                if (
                    c.get_width_policy() is SizePolicy.FIXED
                    and child_width < parent_size.width
                ):
                    c.move_x(parent_pos.x + (parent_size.width - child_width) / 2)
                else:
                    c.move_x(parent_pos.x)

                if (
                    c.get_height_policy() is SizePolicy.FIXED
                    and child_height < parent_size.height
                ):
                    c.move_y(parent_pos.y + (parent_size.height - child_height) / 2)
                else:
                    c.move_y(parent_pos.y)

            elif widget_type == "Column":
                # Column stacks vertically
                c.move_x(parent_pos.x)
                c.move_y(current_y)
                current_y += child_height

            elif widget_type == "Row":
                # Row stacks horizontally
                c.move_x(current_x)
                c.move_y(parent_pos.y)
                current_x += child_width

            else:
                # Default: position at parent origin
                c.move_x(parent_pos.x)
                c.move_y(parent_pos.y)

            # Recursively layout this child's children
            from castella.models import Size

            child_size = Size(width=child_width, height=child_height)
            child_pos = c.get_pos()
            self._layout_widget_tree(c, child_size, child_pos)

    def contain(self, p) -> bool:
        """Check if point is within modal.

        When closed, always return False.
        When open, return True to capture all events (modal is a fullscreen overlay).
        """
        if not self._modal_state.is_open():
            return False
        # Modal is a fullscreen overlay, so it captures all events when open
        return True

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
