"""Focus management and Tab navigation.

Provides focus tracking, Tab/Shift+Tab navigation, and focus scopes
for modal dialogs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from castella.models.events import KeyCode, KeyAction, InputKeyEvent

if TYPE_CHECKING:
    from castella.core import Widget


@runtime_checkable
class Focusable(Protocol):
    """Protocol for focusable widgets.

    Widgets that can receive keyboard focus should implement this protocol
    to participate in Tab navigation.

    Example:
        class MyInput(Widget, Focusable):
            def can_focus(self) -> bool:
                return self._enabled

            def focus_order(self) -> int:
                return self._tab_index

            def focused(self) -> None:
                self._show_cursor = True
                self.dirty(True)

            def unfocused(self) -> None:
                self._show_cursor = False
                self.dirty(True)
    """

    def can_focus(self) -> bool:
        """Return True if this widget can currently receive focus."""
        ...

    def focus_order(self) -> int:
        """Return the tab order (lower = earlier in tab sequence)."""
        ...

    def focused(self) -> None:
        """Called when this widget receives focus."""
        ...

    def unfocused(self) -> None:
        """Called when this widget loses focus."""
        ...


@dataclass
class FocusScope:
    """A focus scope for modal dialogs or focus trapping.

    When a scope is active, Tab navigation is limited to widgets
    within that scope. When the scope is popped, focus returns
    to the previously focused widget.

    Attributes:
        name: Identifier for the scope (for debugging).
        focusables: List of focusable widgets in this scope.
        previous_focus: Widget that had focus before this scope.
    """

    name: str
    focusables: list[Focusable] = field(default_factory=list)
    previous_focus: Widget | None = None


class FocusManager:
    """Manages keyboard focus and Tab navigation.

    Tracks the currently focused widget and provides Tab/Shift+Tab
    navigation through focusable widgets. Supports focus scopes
    for modal dialogs.

    Example:
        focus = FocusManager()

        # Set focus programmatically
        focus.set_focus(my_input)

        # Handle Tab key
        def on_key(ev):
            if ev.key == KeyCode.TAB:
                if ev.mods & MOD_SHIFT:
                    focus.focus_previous()
                else:
                    focus.focus_next()

        # Modal dialog
        scope = focus.push_scope("dialog")
        focus.collect_focusables(dialog_widget)
        focus.focus_first()
        # ... dialog interaction ...
        focus.pop_scope()  # Returns focus to previous widget
    """

    def __init__(self) -> None:
        self._focused: Widget | None = None
        self._focusables: list[Focusable] = []
        self._scopes: list[FocusScope] = []

    @property
    def focus(self) -> Widget | None:
        """Get the currently focused widget."""
        return self._focused

    def set_focus(self, target: Widget | None) -> bool:
        """Set focus to a widget.

        Args:
            target: Widget to focus, or None to clear focus.

        Returns:
            True if focus changed, False otherwise.
        """
        if target is self._focused:
            return False

        # Unfocus current
        if self._focused is not None:
            self._focused.unfocused()

        # Focus new target
        self._focused = target
        if target is not None:
            target.focused()

        return True

    def clear_focus(self) -> None:
        """Clear focus (no widget focused)."""
        self.set_focus(None)

    def focus_next(self) -> bool:
        """Move focus to the next focusable widget.

        Returns:
            True if focus moved, False if no focusable widgets.
        """
        if not self._focusables:
            return False

        # Find current index
        current_idx = -1
        if self._focused is not None:
            for i, f in enumerate(self._focusables):
                if f is self._focused:
                    current_idx = i
                    break

        # Find next focusable
        for i in range(1, len(self._focusables) + 1):
            idx = (current_idx + i) % len(self._focusables)
            candidate = self._focusables[idx]
            if candidate.can_focus():
                self.set_focus(candidate)  # type: ignore
                return True

        return False

    def focus_previous(self) -> bool:
        """Move focus to the previous focusable widget.

        Returns:
            True if focus moved, False if no focusable widgets.
        """
        if not self._focusables:
            return False

        # Find current index
        current_idx = len(self._focusables)
        if self._focused is not None:
            for i, f in enumerate(self._focusables):
                if f is self._focused:
                    current_idx = i
                    break

        # Find previous focusable
        for i in range(1, len(self._focusables) + 1):
            idx = (current_idx - i) % len(self._focusables)
            candidate = self._focusables[idx]
            if candidate.can_focus():
                self.set_focus(candidate)  # type: ignore
                return True

        return False

    def focus_first(self) -> bool:
        """Focus the first focusable widget.

        Returns:
            True if focus was set, False if no focusable widgets.
        """
        for f in self._focusables:
            if f.can_focus():
                self.set_focus(f)  # type: ignore
                return True
        return False

    def focus_last(self) -> bool:
        """Focus the last focusable widget.

        Returns:
            True if focus was set, False if no focusable widgets.
        """
        for f in reversed(self._focusables):
            if f.can_focus():
                self.set_focus(f)  # type: ignore
                return True
        return False

    def collect_focusables(self, root: Widget) -> None:
        """Collect all focusable widgets from a widget tree.

        Traverses the tree and collects widgets that implement
        the Focusable protocol, sorted by focus_order().

        Args:
            root: Root widget to traverse.
        """
        focusables: list[Focusable] = []
        self._collect_focusables_recursive(root, focusables)

        # Sort by focus order
        focusables.sort(key=lambda f: f.focus_order())

        # Store in current scope or global list
        if self._scopes:
            self._scopes[-1].focusables = focusables
        self._focusables = focusables

    def _collect_focusables_recursive(
        self, widget: Widget, result: list[Focusable]
    ) -> None:
        """Recursively collect focusable widgets."""
        if isinstance(widget, Focusable):
            result.append(widget)

        # Check for children (Layout subclasses)
        if hasattr(widget, "_children"):
            for child in widget._children:
                self._collect_focusables_recursive(child, result)

    def push_scope(self, name: str) -> FocusScope:
        """Push a new focus scope (e.g., for modal dialogs).

        The current focus is saved and will be restored when
        the scope is popped.

        Args:
            name: Identifier for the scope.

        Returns:
            The new FocusScope.
        """
        scope = FocusScope(name=name, previous_focus=self._focused)
        self._scopes.append(scope)
        self._focusables = []
        return scope

    def pop_scope(self) -> None:
        """Pop the current focus scope and restore previous focus."""
        if not self._scopes:
            return

        scope = self._scopes.pop()

        # Restore focusables from parent scope or clear
        if self._scopes:
            self._focusables = self._scopes[-1].focusables
        else:
            self._focusables = []

        # Restore previous focus
        if scope.previous_focus is not None:
            self.set_focus(scope.previous_focus)

    @property
    def current_scope(self) -> FocusScope | None:
        """Get the current focus scope, or None if at root."""
        return self._scopes[-1] if self._scopes else None

    def handle_key_event(self, ev: InputKeyEvent) -> bool:
        """Handle Tab key for navigation.

        Args:
            ev: The key event.

        Returns:
            True if the event was handled.
        """
        if ev.action != KeyAction.PRESS:
            return False

        if ev.key == KeyCode.TAB:
            # Check for Shift modifier
            from castella.events.keyboard import MOD_SHIFT

            if ev.mods & MOD_SHIFT:
                return self.focus_previous()
            else:
                return self.focus_next()

        return False
