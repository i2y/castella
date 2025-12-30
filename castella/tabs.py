"""Tabs widget for tabbed navigation.

Provides a tabbed interface where each tab has a label and content.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Self

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


@dataclass
class TabItem:
    """A single tab with its label and content.

    Attributes:
        id: Unique identifier for this tab
        label: Display text for the tab button
        content: Widget to display when this tab is selected
    """

    id: str
    label: str
    content: Widget


class TabsState(ObservableBase):
    """Observable state for Tabs widget.

    Manages the list of tabs and the currently selected tab.
    """

    def __init__(
        self,
        tabs: list[TabItem] | None = None,
        selected_id: str | None = None,
    ):
        """Initialize TabsState.

        Args:
            tabs: List of TabItem instances
            selected_id: ID of initially selected tab (defaults to first tab)
        """
        super().__init__()
        self.__tabs = tabs or []  # Use __tabs for internal storage
        self._selected_id = selected_id

        # Default to first tab if not specified
        if self._selected_id is None and self.__tabs:
            self._selected_id = self.__tabs[0].id

    @property
    def _tabs(self) -> list[TabItem]:
        """Internal tab list property."""
        return self.__tabs

    @_tabs.setter
    def _tabs(self, value: list[TabItem]) -> None:
        """Set tab list with automatic cleanup of old content."""
        self._detach_old_content(self.__tabs)
        self.__tabs = value

    def _detach_old_content(self, old_tabs: list[TabItem]) -> None:
        """Detach content widgets from old tabs to prevent orphaned observers."""
        for tab in old_tabs:
            if tab.content is not None and hasattr(tab.content, "detach"):
                tab.content.detach()

    def tabs(self) -> list[TabItem]:
        """Get list of tabs."""
        return self.__tabs

    def selected_id(self) -> str | None:
        """Get ID of currently selected tab."""
        return self._selected_id

    def select(self, tab_id: str) -> None:
        """Select a tab by ID.

        Args:
            tab_id: ID of the tab to select
        """
        if any(t.id == tab_id for t in self.__tabs):
            if self._selected_id != tab_id:
                self._selected_id = tab_id
                self.notify()

    def get_selected_tab(self) -> TabItem | None:
        """Get the currently selected TabItem."""
        for tab in self.__tabs:
            if tab.id == self._selected_id:
                return tab
        return None

    def add_tab(self, tab: TabItem) -> None:
        """Add a new tab.

        Args:
            tab: The TabItem to add
        """
        self.__tabs.append(tab)
        if self._selected_id is None:
            self._selected_id = tab.id
        self.notify()

    def remove_tab(self, tab_id: str) -> None:
        """Remove a tab by ID.

        Args:
            tab_id: ID of the tab to remove
        """
        # Detach the removed tab's content
        for tab in self.__tabs:
            if tab.id == tab_id and tab.content is not None:
                if hasattr(tab.content, "detach"):
                    tab.content.detach()
                break
        self.__tabs = [t for t in self.__tabs if t.id != tab_id]
        # If removed tab was selected, select first available
        if self._selected_id == tab_id:
            self._selected_id = self.__tabs[0].id if self.__tabs else None
        self.notify()

    def set_tabs(self, tabs: list[TabItem]) -> None:
        """Replace all tabs.

        Args:
            tabs: New list of TabItem instances
        """
        # Detach old content widgets
        self._detach_old_content(self.__tabs)
        self.__tabs = tabs
        # Ensure selected_id is valid
        if self.__tabs:
            if not any(t.id == self._selected_id for t in self.__tabs):
                self._selected_id = self.__tabs[0].id
        else:
            self._selected_id = None
        self.notify()


class Tabs(StatefulComponent):
    """Tabbed container widget.

    Displays a row of tab buttons at the top and the selected tab's
    content below.

    Example:
        tabs = Tabs(TabsState([
            TabItem(id="home", label="Home", content=Text("Home page")),
            TabItem(id="settings", label="Settings", content=settings_panel),
        ]))

        # Or create tabs with fluent API
        tabs = (
            Tabs()
            .add_tab("home", "Home", home_content)
            .add_tab("settings", "Settings", settings_content)
        )
    """

    def __init__(
        self,
        state: TabsState | None = None,
        tab_height: int = 40,
    ):
        """Initialize Tabs.

        Args:
            state: Optional TabsState (creates empty state if not provided)
            tab_height: Height of the tab bar in pixels
        """
        self._tab_state = state or TabsState()
        super().__init__(self._tab_state)
        self._tab_height = tab_height
        self._callback: Callable[[str], None] = lambda _: None

    def view(self) -> Widget:
        """Build the tabs UI."""
        tabs = self._tab_state.tabs()
        selected_id = self._tab_state.selected_id()

        if not tabs:
            return Spacer()

        # Build tab buttons
        tab_buttons = []
        for tab in tabs:
            is_selected = tab.id == selected_id
            button = (
                Button(tab.label)
                .on_click(self._create_tab_click_handler(tab.id))
                .height(self._tab_height)
                .height_policy(SizePolicy.FIXED)
            )
            if is_selected:
                button = button.kind(Kind.INFO)
            tab_buttons.append(button)

        # Tab bar
        tab_bar = (
            Row(*tab_buttons).height(self._tab_height).height_policy(SizePolicy.FIXED)
        )

        # Selected content
        selected_tab = self._tab_state.get_selected_tab()
        content = selected_tab.content if selected_tab else Spacer()

        return Column(tab_bar, content)

    def _create_tab_click_handler(self, tab_id: str) -> Callable:
        """Create click handler for a tab button."""

        def handler(_) -> None:
            old_id = self._tab_state.selected_id()
            self._tab_state.select(tab_id)
            if old_id != tab_id:
                self._callback(tab_id)

        return handler

    def on_change(self, callback: Callable[[str], None]) -> Self:
        """Set callback for tab changes.

        Args:
            callback: Function called with new tab ID when tab changes

        Returns:
            Self for method chaining
        """
        self._callback = callback
        return self

    def tab_height(self, height: int) -> Self:
        """Set tab bar height.

        Args:
            height: Height in pixels

        Returns:
            Self for method chaining
        """
        self._tab_height = height
        return self

    def add_tab(self, id: str, label: str, content: Widget) -> Self:
        """Add a new tab.

        Args:
            id: Unique identifier for the tab
            label: Display text for the tab button
            content: Widget to show when this tab is selected

        Returns:
            Self for method chaining
        """
        self._tab_state.add_tab(TabItem(id=id, label=label, content=content))
        return self

    def select(self, tab_id: str) -> Self:
        """Select a tab programmatically.

        Args:
            tab_id: ID of the tab to select

        Returns:
            Self for method chaining
        """
        self._tab_state.select(tab_id)
        return self
