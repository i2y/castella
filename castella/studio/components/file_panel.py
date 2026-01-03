"""Shared file panel component for workflow studios."""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from castella import Component, Column, Row, Text, Spacer
from castella.file_tree import FileTree, FileTreeState


# UI Constants
HEADER_HEIGHT = 32


class FilePanel(Component):
    """File browser panel for selecting workflow files.

    Wraps Castella's FileTree widget with filtering for Python files.
    """

    def __init__(
        self,
        root_path: str = ".",
        title: str = "Files",
        on_file_select: Callable[[str], None] | None = None,
    ):
        """Initialize the file panel.

        Args:
            root_path: Root directory to browse.
            title: Panel header title.
            on_file_select: Callback when a .py file is selected.
        """
        super().__init__()

        self._root_path = root_path
        self._title = title
        self._on_file_select = on_file_select

        # Create file tree state
        self._tree_state = FileTreeState(
            root_path=root_path,
            show_hidden=False,
            dirs_first=True,
        )

    def view(self):
        """Build the file panel UI."""
        return Column(
            # Header
            Text(self._title).fixed_height(HEADER_HEIGHT),
            # File tree with padding
            Column(
                Spacer().fixed_height(4),
                Row(
                    Spacer().fixed_width(4),
                    self._build_file_tree(),
                    Spacer().fixed_width(4),
                ),
            ),
        )

    def _build_file_tree(self):
        """Build the file tree widget."""
        tree = FileTree(self._tree_state)

        if self._on_file_select:
            tree = tree.on_file_select(self._handle_file_select)

        return tree

    def _handle_file_select(self, path: Path) -> None:
        """Handle file selection, filtering for Python files.

        Args:
            path: Selected file path.
        """
        if path.suffix == ".py" and self._on_file_select:
            self._on_file_select(str(path))

    def refresh(self) -> None:
        """Refresh the file tree from disk."""
        self._tree_state.refresh()

    def set_root_path(self, path: str) -> None:
        """Change the root directory.

        Args:
            path: New root directory path.
        """
        self._root_path = path
        self._tree_state = FileTreeState(
            root_path=path,
            show_hidden=False,
            dirs_first=True,
        )
