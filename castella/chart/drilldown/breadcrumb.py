"""Breadcrumb navigation widget for drill-down charts."""

from __future__ import annotations

from typing import Callable

from castella.core import Component, Widget, SizePolicy
from castella.button import Button
from castella.row import Row
from castella.text import Text
from castella.spacer import Spacer

from .state import DrillDownState


class Breadcrumb(Component):
    """Breadcrumb navigation widget for drill-down charts.

    Displays the current path in the hierarchy and allows
    clicking on any level to navigate back.

    Example display:
        World > North America > USA
        ^^^^    ^^^^^^^^^^^^^^   ^^^
        (click) (click)          (current - not clickable)

    Attributes:
        state: The DrillDownState to observe and navigate.
        separator: Text between breadcrumb items (default: " > ").
        max_visible: Maximum visible items before collapsing.
    """

    def __init__(
        self,
        state: DrillDownState,
        separator: str = " > ",
        max_visible: int = 5,
    ):
        """Initialize the breadcrumb.

        Args:
            state: The drill-down state to observe.
            separator: Text between breadcrumb items.
            max_visible: Maximum visible items (older items collapsed).
        """
        super().__init__()
        self._drill_state = state
        self._separator = separator
        self._max_visible = max_visible
        state.attach(self)

    def view(self) -> Widget:
        """Build the breadcrumb widget."""
        breadcrumbs = self._drill_state.breadcrumbs

        if not breadcrumbs:
            return Spacer().height(30).height_policy(SizePolicy.FIXED)

        items: list[Widget] = []

        # Collapse if too many items
        if len(breadcrumbs) > self._max_visible:
            # Show: root > ... > last N items
            visible = [breadcrumbs[0]] + breadcrumbs[-(self._max_visible - 1) :]
            show_ellipsis = True
        else:
            visible = breadcrumbs
            show_ellipsis = False

        for i, (node_id, label) in enumerate(visible):
            is_last = i == len(visible) - 1
            is_first = i == 0

            # Add ellipsis after first item if collapsed
            if show_ellipsis and is_first:
                items.append(self._create_breadcrumb_button(node_id, label))
                items.append(self._create_separator_text())
                items.append(
                    Text("...", font_size=12).text_color("#666666").fixed_height(24)
                )
                items.append(self._create_separator_text())
                continue

            if is_last:
                # Current level - not clickable, different styling
                items.append(
                    Text(label, font_size=12).text_color("#ffffff").fixed_height(24)
                )
            else:
                # Clickable breadcrumb
                items.append(self._create_breadcrumb_button(node_id, label))
                items.append(self._create_separator_text())

        # Add spacer to push content left
        items.append(Spacer())

        return (
            Row(*items)
            .height(30)
            .height_policy(SizePolicy.FIXED)
            .width_policy(SizePolicy.EXPANDING)
        )

    def _create_separator_text(self) -> Widget:
        """Create separator text between breadcrumb items."""
        return (
            Text(self._separator, font_size=12).text_color("#888888").fixed_height(24)
        )

    def _create_breadcrumb_button(self, node_id: str, label: str) -> Widget:
        """Create a clickable breadcrumb button.

        Args:
            node_id: The node ID to navigate to.
            label: The display label.

        Returns:
            A Button widget.
        """
        return (
            Button(label, font_size=12)
            .on_click(self._create_nav_handler(node_id))
            .height(24)
            .height_policy(SizePolicy.FIXED)
            .width_policy(SizePolicy.CONTENT)
        )

    def _create_nav_handler(self, node_id: str) -> Callable:
        """Create a navigation handler for a breadcrumb click.

        Args:
            node_id: The node ID to navigate to.

        Returns:
            A click handler function.
        """

        def handler(_: object) -> None:
            self._drill_state.navigate_to(node_id)

        return handler
