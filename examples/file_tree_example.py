"""FileTree widget example.

Demonstrates the FileTree widget with:
- File system browsing
- Automatic file type icons
- Hidden file toggle
- File/directory selection callbacks
"""

from pathlib import Path

from castella import (
    App,
    FileTree,
    FileTreeState,
    Column,
    Row,
    Button,
    Text,
)
from castella.frame import Frame


def main():
    # Use current directory as root
    root_path = Path.cwd()

    # Create file tree state
    state = FileTreeState(root_path, show_hidden=False, dirs_first=True)

    # Status display
    status_text = Text(f"Root: {root_path}", font_size=12)

    def on_file_select(path: Path):
        status_text._text = f"File: {path.name}"
        status_text.update()

    def on_dir_select(path: Path):
        status_text._text = f"Dir: {path.name}/"
        status_text.update()

    # Create file tree widget
    file_tree = (
        FileTree(state)
        .on_file_select(on_file_select)
        .on_dir_select(on_dir_select)
    )

    # Control buttons
    def expand_all(_):
        file_tree.expand_all()

    def collapse_all(_):
        file_tree.collapse_all()

    def toggle_hidden(_):
        current = state.is_showing_hidden()
        state.set_show_hidden(not current)
        mode = "Showing hidden" if not current else "Hiding hidden"
        status_text._text = mode
        status_text.update()

    def refresh(_):
        state.refresh()
        status_text._text = "Refreshed"
        status_text.update()

    controls = Row(
        Button("Expand All").on_click(expand_all),
        Button("Collapse All").on_click(collapse_all),
        Button("Toggle Hidden").on_click(toggle_hidden),
        Button("Refresh").on_click(refresh),
    ).fixed_height(40)

    # Main layout
    content = Column(
        Text("FileTree Demo", font_size=18)
        .fixed_height(30),
        controls,
        file_tree,
        status_text.fixed_height(30),
    )

    App(Frame("FileTree Demo", 500, 700), content).run()


if __name__ == "__main__":
    main()
