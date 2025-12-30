"""FileTree widget for displaying file system structure.

Provides a tree view of directories and files with automatic
icon assignment based on file type.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Self

from castella.tree import Tree, TreeNode, TreeState


# File type to icon mapping
FILE_ICONS: dict[str, str] = {
    # Folders
    "folder": "📁",
    "folder_open": "📂",
    # Programming languages
    ".py": "🐍",
    ".js": "📜",
    ".ts": "📘",
    ".jsx": "⚛️",
    ".tsx": "⚛️",
    ".html": "🌐",
    ".css": "🎨",
    ".scss": "🎨",
    ".sass": "🎨",
    ".json": "📋",
    ".xml": "📋",
    ".yaml": "📋",
    ".yml": "📋",
    ".toml": "📋",
    ".ini": "📋",
    ".cfg": "📋",
    ".conf": "📋",
    ".rs": "🦀",
    ".go": "🐹",
    ".java": "☕",
    ".kt": "🎯",
    ".swift": "🐦",
    ".c": "🔧",
    ".cpp": "🔧",
    ".h": "🔧",
    ".hpp": "🔧",
    ".rb": "💎",
    ".php": "🐘",
    ".sh": "🐚",
    ".bash": "🐚",
    ".zsh": "🐚",
    ".fish": "🐚",
    ".ps1": "🐚",
    ".sql": "🗃️",
    # Documents
    ".md": "📝",
    ".txt": "📄",
    ".pdf": "📕",
    ".doc": "📘",
    ".docx": "📘",
    ".xls": "📗",
    ".xlsx": "📗",
    ".ppt": "📙",
    ".pptx": "📙",
    ".csv": "📊",
    # Images
    ".png": "🖼️",
    ".jpg": "🖼️",
    ".jpeg": "🖼️",
    ".gif": "🖼️",
    ".svg": "🖼️",
    ".ico": "🖼️",
    ".webp": "🖼️",
    # Media
    ".mp3": "🎵",
    ".wav": "🎵",
    ".flac": "🎵",
    ".mp4": "🎬",
    ".avi": "🎬",
    ".mkv": "🎬",
    ".mov": "🎬",
    # Archives
    ".zip": "📦",
    ".tar": "📦",
    ".gz": "📦",
    ".rar": "📦",
    ".7z": "📦",
    # Config/special files
    ".env": "🔐",
    ".gitignore": "🙈",
    ".dockerignore": "🙈",
    ".lock": "🔒",
    # Default
    "default": "📄",
}

# Special filename mappings
SPECIAL_FILES: dict[str, str] = {
    "Dockerfile": "🐳",
    "docker-compose.yml": "🐳",
    "docker-compose.yaml": "🐳",
    "Makefile": "🔨",
    "Justfile": "🔨",
    "CMakeLists.txt": "🔨",
    "package.json": "📦",
    "pyproject.toml": "📦",
    "Cargo.toml": "📦",
    "go.mod": "📦",
    "requirements.txt": "📦",
    "README.md": "📖",
    "README": "📖",
    "LICENSE": "⚖️",
    "LICENSE.md": "⚖️",
    "LICENSE.txt": "⚖️",
    ".gitignore": "🙈",
    ".env": "🔐",
    ".env.local": "🔐",
    ".env.example": "🔐",
}


def get_file_icon(path: Path) -> str:
    """Get icon for a file based on its name or extension.

    Args:
        path: Path to the file

    Returns:
        Icon string (emoji)
    """
    name = path.name

    # Check special filenames first
    if name in SPECIAL_FILES:
        return SPECIAL_FILES[name]

    # Check by extension
    suffix = path.suffix.lower()
    if suffix in FILE_ICONS:
        return FILE_ICONS[suffix]

    return FILE_ICONS["default"]


class FileTreeState(TreeState):
    """State for FileTree widget.

    Extends TreeState with file system specific functionality.
    """

    def __init__(
        self,
        root_path: str | Path | None = None,
        show_hidden: bool = False,
        dirs_first: bool = True,
        multi_select: bool = False,
    ):
        """Initialize FileTreeState.

        Args:
            root_path: Root directory to display
            show_hidden: Whether to show hidden files (starting with .)
            dirs_first: Whether to sort directories before files
            multi_select: Whether to allow multiple selection
        """
        super().__init__(nodes=[], multi_select=multi_select)
        self._root_path: Path | None = None
        self._show_hidden = show_hidden
        self._dirs_first = dirs_first

        if root_path is not None:
            self.set_root(root_path)

    def set_root(self, path: str | Path) -> None:
        """Set the root directory.

        Args:
            path: Path to the root directory
        """
        self._root_path = Path(path).resolve()
        if not self._root_path.exists():
            raise FileNotFoundError(f"Path does not exist: {self._root_path}")
        if not self._root_path.is_dir():
            raise NotADirectoryError(f"Path is not a directory: {self._root_path}")

        nodes = self._build_tree(self._root_path)
        self.set_nodes(nodes)

    def _build_tree(self, directory: Path, depth: int = 0) -> list[TreeNode]:
        """Build tree nodes from directory.

        Args:
            directory: Directory to scan
            depth: Current depth (for limiting recursion)

        Returns:
            List of TreeNode instances
        """
        nodes: list[TreeNode] = []

        try:
            entries = list(directory.iterdir())
        except PermissionError:
            return nodes

        # Filter hidden files if needed
        if not self._show_hidden:
            entries = [e for e in entries if not e.name.startswith(".")]

        # Sort entries
        if self._dirs_first:
            entries.sort(key=lambda e: (not e.is_dir(), e.name.lower()))
        else:
            entries.sort(key=lambda e: e.name.lower())

        for entry in entries:
            node_id = str(entry)

            if entry.is_dir():
                # Recursively build children
                children = self._build_tree(entry, depth + 1)
                node = TreeNode(
                    id=node_id,
                    label=entry.name,
                    icon=FILE_ICONS["folder"],
                    children=children,
                    data={"path": entry, "is_dir": True},
                )
            else:
                icon = get_file_icon(entry)
                node = TreeNode(
                    id=node_id,
                    label=entry.name,
                    icon=icon,
                    children=[],
                    data={"path": entry, "is_dir": False},
                )

            nodes.append(node)

        return nodes

    def refresh(self) -> None:
        """Refresh the tree from the file system."""
        if self._root_path is not None:
            # Save current expansion state
            expanded = self._expanded_ids.copy()
            selected = self._selected_ids.copy()

            # Rebuild tree
            nodes = self._build_tree(self._root_path)
            self._nodes = nodes
            self._rebuild_node_map()

            # Restore valid states
            valid_ids = set(self._node_map.keys())
            self._expanded_ids = expanded & valid_ids
            self._selected_ids = selected & valid_ids

            self.notify()

    def get_root_path(self) -> Path | None:
        """Get the current root path.

        Returns:
            The root path or None if not set
        """
        return self._root_path

    def is_showing_hidden(self) -> bool:
        """Check if hidden files are shown.

        Returns:
            True if hidden files are shown
        """
        return self._show_hidden

    def set_show_hidden(self, show: bool) -> None:
        """Set whether to show hidden files.

        Args:
            show: True to show hidden files
        """
        if self._show_hidden != show:
            self._show_hidden = show
            self.refresh()


class FileTree(Tree):
    """FileTree widget for displaying file system structure.

    A specialized Tree widget for browsing directories and files.

    Example:
        # Create file tree for current directory
        state = FileTreeState(".", show_hidden=False)
        file_tree = FileTree(state).on_select(
            lambda node: print(f"Selected: {node.data['path']}")
        )

        # Refresh when files change
        state.refresh()
    """

    def __init__(
        self,
        state: FileTreeState | None = None,
        root_path: str | Path | None = None,
        show_hidden: bool = False,
        dirs_first: bool = True,
        indent_width: int = 20,
        row_height: int = 28,
    ):
        """Initialize FileTree widget.

        Args:
            state: FileTreeState (if not provided, creates one from root_path)
            root_path: Root directory to display (used if state not provided)
            show_hidden: Whether to show hidden files
            dirs_first: Whether to sort directories before files
            indent_width: Pixels to indent each level
            row_height: Height of each tree row in pixels
        """
        if state is None:
            state = FileTreeState(
                root_path=root_path,
                show_hidden=show_hidden,
                dirs_first=dirs_first,
            )

        self._file_tree_state = state
        super().__init__(state, indent_width=indent_width, row_height=row_height)

        # File-specific callbacks
        self._on_file_select: Callable[[Path], None] = lambda _: None
        self._on_dir_select: Callable[[Path], None] = lambda _: None

    def on_file_select(self, callback: Callable[[Path], None]) -> Self:
        """Set callback for file selection.

        Args:
            callback: Function called with file path when a file is selected

        Returns:
            Self for method chaining
        """
        self._on_file_select = callback

        # Wrap the original on_select to also call file-specific callback
        original_callback = self._on_select

        def wrapped_callback(node: TreeNode) -> None:
            original_callback(node)
            if node.data and not node.data.get("is_dir", False):
                self._on_file_select(node.data["path"])

        self._on_select = wrapped_callback
        return self

    def on_dir_select(self, callback: Callable[[Path], None]) -> Self:
        """Set callback for directory selection.

        Args:
            callback: Function called with directory path when a directory is selected

        Returns:
            Self for method chaining
        """
        self._on_dir_select = callback

        # Wrap the original on_select to also call dir-specific callback
        original_callback = self._on_select

        def wrapped_callback(node: TreeNode) -> None:
            original_callback(node)
            if node.data and node.data.get("is_dir", False):
                self._on_dir_select(node.data["path"])

        self._on_select = wrapped_callback
        return self

    def refresh(self) -> Self:
        """Refresh the tree from the file system.

        Returns:
            Self for method chaining
        """
        self._file_tree_state.refresh()
        return self

    def get_selected_paths(self) -> list[Path]:
        """Get list of selected file/directory paths.

        Returns:
            List of Path objects for selected items
        """
        selected = self.get_selected()
        return [node.data["path"] for node in selected if node.data]

    def get_state(self) -> FileTreeState:
        """Get the underlying FileTreeState.

        Returns:
            The FileTreeState instance
        """
        return self._file_tree_state
