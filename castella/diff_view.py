"""Diff viewer widget for Castella.

This module provides a component for displaying unified diff output
with syntax highlighting, line numbers, and color-coded changes.

Example:
    from castella import App, Frame
    from castella.diff_view import DiffView

    diff_text = '''
    diff --git a/example.py b/example.py
    --- a/example.py
    +++ b/example.py
    @@ -1,3 +1,4 @@
     def hello():
    -    print("Hello")
    +    print("Hello, World!")
    +    return True
    '''

    App(Frame("Diff Viewer", 600, 400), DiffView(diff_text)).run()
"""

import re
from dataclasses import dataclass
from typing import Optional

from castella import Column, Row, SimpleText, Spacer, Widget
from castella.core import Component, SizePolicy
from castella.theme import ThemeManager


@dataclass
class DiffHunk:
    """A single hunk in a diff.

    Attributes:
        old_start: Starting line number in the old file
        old_count: Number of lines from the old file
        new_start: Starting line number in the new file
        new_count: Number of lines in the new file
        lines: List of (type, content) tuples where type is '+', '-', or ' '
    """

    old_start: int
    old_count: int
    new_start: int
    new_count: int
    lines: list[tuple[str, str]]  # (type: '+'/'-'/' ', content)


@dataclass
class FileDiff:
    """Parsed diff for a single file.

    Attributes:
        old_file: Path of the old file
        new_file: Path of the new file
        hunks: List of DiffHunk objects
    """

    old_file: str
    new_file: str
    hunks: list[DiffHunk]

    @property
    def added_lines(self) -> int:
        """Count of added lines."""
        return sum(1 for h in self.hunks for t, _ in h.lines if t == "+")

    @property
    def removed_lines(self) -> int:
        """Count of removed lines."""
        return sum(1 for h in self.hunks for t, _ in h.lines if t == "-")


def parse_diff(diff_text: str) -> list[FileDiff]:
    """Parse unified diff text into structured format.

    Args:
        diff_text: Raw unified diff text

    Returns:
        List of FileDiff objects, one per modified file
    """
    files: list[FileDiff] = []
    current_file: Optional[FileDiff] = None
    current_hunk: Optional[DiffHunk] = None

    lines = diff_text.split("\n")
    i = 0

    while i < len(lines):
        line = lines[i]

        # File header: diff --git a/... b/...
        if line.startswith("diff --git"):
            if current_file and current_file.hunks:
                files.append(current_file)
            # Extract file path
            match = re.search(r"diff --git a/(.*) b/(.*)", line)
            if match:
                current_file = FileDiff(
                    old_file=match.group(1),
                    new_file=match.group(2),
                    hunks=[],
                )
            else:
                current_file = FileDiff(old_file="", new_file="", hunks=[])
            current_hunk = None
            i += 1
            continue

        # Old file: --- a/...
        if line.startswith("--- "):
            if current_file:
                match = re.search(r"--- (?:a/)?(.*)", line)
                if match:
                    current_file.old_file = match.group(1)
            i += 1
            continue

        # New file: +++ b/...
        if line.startswith("+++ "):
            if current_file:
                match = re.search(r"\+\+\+ (?:b/)?(.*)", line)
                if match:
                    current_file.new_file = match.group(1)
            i += 1
            continue

        # Hunk header: @@ -old_start,old_count +new_start,new_count @@
        if line.startswith("@@"):
            match = re.search(r"@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@", line)
            if match and current_file:
                current_hunk = DiffHunk(
                    old_start=int(match.group(1)),
                    old_count=int(match.group(2) or 1),
                    new_start=int(match.group(3)),
                    new_count=int(match.group(4) or 1),
                    lines=[],
                )
                current_file.hunks.append(current_hunk)
            i += 1
            continue

        # Diff lines
        if current_hunk is not None:
            if line.startswith("+"):
                current_hunk.lines.append(("+", line[1:]))
            elif line.startswith("-"):
                current_hunk.lines.append(("-", line[1:]))
            elif line.startswith(" ") or line == "":
                current_hunk.lines.append(
                    (" ", line[1:] if line.startswith(" ") else "")
                )

        # Skip other lines (index, etc.)
        i += 1

    # Add last file
    if current_file and current_file.hunks:
        files.append(current_file)

    return files


class DiffView(Component):
    """Displays diff output with syntax highlighting.

    Shows unified diff format with:
    - Color-coded additions (green) and deletions (red)
    - Line numbers
    - File headers with change statistics
    - Truncation for large diffs

    Example:
        diff_text = '''
        diff --git a/file.py b/file.py
        --- a/file.py
        +++ b/file.py
        @@ -1,2 +1,3 @@
         unchanged
        -removed
        +added
        +new line
        '''
        view = DiffView(diff_text, max_lines=100)
    """

    def __init__(self, diff_text: str, max_lines: int = 200):
        """Initialize the diff view.

        Args:
            diff_text: Raw diff output text
            max_lines: Maximum number of lines to display (default: 200)
        """
        super().__init__()
        self._diff_text = diff_text
        self._max_lines = max_lines

    def view(self) -> Widget:
        """Build the diff view."""
        theme = ThemeManager().current

        # Parse the diff
        files = parse_diff(self._diff_text)

        if not files:
            # Fallback: show raw diff if parsing fails
            return self._build_raw_diff(theme)

        widgets: list[Widget] = []
        line_count = 0

        for file_diff in files:
            if line_count >= self._max_lines:
                break

            # File header
            file_name = file_diff.new_file or file_diff.old_file
            added = file_diff.added_lines
            removed = file_diff.removed_lines

            header_text = f"Update({file_name})"
            stats_text = f"Added {added} lines, removed {removed} lines"

            widgets.append(
                Column(
                    Row(
                        SimpleText("*", font_size=10)
                        .text_color(theme.colors.text_info)
                        .fixed_width(16)
                        .fixed_height(20)
                        .height_policy(SizePolicy.FIXED),
                        SimpleText(header_text, font_size=12)
                        .text_color(theme.colors.text_primary)
                        .fixed_height(20)
                        .height_policy(SizePolicy.FIXED),
                    )
                    .fixed_height(20)
                    .height_policy(SizePolicy.FIXED),
                    Row(
                        Spacer().fixed_width(16),
                        SimpleText(f"L {stats_text}", font_size=11)
                        .text_color(theme.colors.border_secondary)
                        .fixed_height(18)
                        .height_policy(SizePolicy.FIXED),
                    )
                    .fixed_height(18)
                    .height_policy(SizePolicy.FIXED),
                ).height_policy(SizePolicy.CONTENT)
            )
            line_count += 2

            # Hunks
            for hunk in file_diff.hunks:
                old_line = hunk.old_start
                new_line = hunk.new_start

                for line_type, content in hunk.lines:
                    if line_count >= self._max_lines:
                        break

                    # Determine line number and colors using theme
                    if line_type == "+":
                        line_num = str(new_line).rjust(4)
                        marker = "+"
                        text_color = theme.colors.text_success
                        bg_color = theme.colors.bg_success
                        new_line += 1
                    elif line_type == "-":
                        line_num = str(old_line).rjust(4)
                        marker = "-"
                        text_color = theme.colors.text_danger
                        bg_color = theme.colors.bg_danger
                        old_line += 1
                    else:
                        line_num = str(new_line).rjust(4)
                        marker = " "
                        text_color = theme.colors.text_primary
                        bg_color = None  # Transparent for context lines
                        old_line += 1
                        new_line += 1

                    # Combine marker and content into single line
                    line_text = f"{marker} {content}" if content else f"{marker} "

                    # Build text widget
                    text_widget = (
                        SimpleText(line_text, font_size=11)
                        .text_color(text_color)
                        .fixed_height(18)
                        .height_policy(SizePolicy.FIXED)
                        .fit_content_width()
                    )
                    if bg_color:
                        text_widget.bg_color(bg_color)

                    # Build spacer
                    spacer = Spacer()
                    if bg_color:
                        spacer.bg_color(bg_color)

                    widgets.append(
                        Row(
                            SimpleText(line_num, font_size=10)
                            .text_color(theme.colors.border_secondary)
                            .fixed_width(36)
                            .fixed_height(18)
                            .height_policy(SizePolicy.FIXED),
                            text_widget,
                            spacer,
                        )
                        .fixed_height(18)
                        .height_policy(SizePolicy.FIXED)
                    )
                    line_count += 1

        if line_count >= self._max_lines:
            widgets.append(
                SimpleText(f"... (truncated, {self._max_lines}+ lines)", font_size=10)
                .text_color(theme.colors.border_secondary)
                .fixed_height(18)
                .height_policy(SizePolicy.FIXED)
            )

        return Column(*widgets).height_policy(SizePolicy.CONTENT)

    def _build_raw_diff(self, theme) -> Widget:
        """Build a raw diff view when parsing fails."""
        lines = self._diff_text.split("\n")
        if len(lines) > self._max_lines:
            lines = lines[: self._max_lines]
            lines.append(
                f"... ({len(self._diff_text.split(chr(10))) - self._max_lines} more lines)"
            )

        line_widgets: list[Widget] = []

        for i, line in enumerate(lines):
            # Determine line color based on diff syntax
            if line.startswith("+++") or line.startswith("---"):
                text_color = theme.colors.text_info
                bg_color = theme.colors.bg_tertiary
            elif line.startswith("@@"):
                text_color = theme.colors.text_warning
                bg_color = theme.colors.bg_tertiary
            elif line.startswith("+"):
                text_color = theme.colors.text_success
                bg_color = theme.colors.bg_success
            elif line.startswith("-"):
                text_color = theme.colors.text_danger
                bg_color = theme.colors.bg_danger
            elif line.startswith("diff "):
                text_color = theme.colors.text_primary
                bg_color = None
            else:
                text_color = theme.colors.text_primary
                bg_color = None  # Transparent for context lines

            line_num = str(i + 1).rjust(4)

            # Build text widget
            text_widget = (
                SimpleText(line if line else " ", font_size=11)
                .text_color(text_color)
                .fixed_height(18)
                .height_policy(SizePolicy.FIXED)
                .fit_content_width()
            )
            if bg_color:
                text_widget.bg_color(bg_color)

            spacer = Spacer()
            if bg_color:
                spacer.bg_color(bg_color)

            line_widgets.append(
                Row(
                    SimpleText(line_num, font_size=10)
                    .text_color(theme.colors.border_secondary)
                    .fixed_width(36)
                    .fixed_height(18)
                    .height_policy(SizePolicy.FIXED),
                    text_widget,
                    spacer,
                )
                .fixed_height(18)
                .height_policy(SizePolicy.FIXED)
            )

        return Column(*line_widgets).height_policy(SizePolicy.CONTENT)


def is_diff_output(text: str) -> bool:
    """Check if text appears to be diff output.

    Args:
        text: Text to check

    Returns:
        True if text looks like unified diff output
    """
    lines = text.strip().split("\n")[:10]  # Check first 10 lines

    # Check for common diff indicators
    diff_indicators = 0
    for line in lines:
        if line.startswith("diff "):
            return True
        if line.startswith("--- ") or line.startswith("+++ "):
            diff_indicators += 1
        if line.startswith("@@") and "@@" in line[2:]:
            diff_indicators += 1

    return diff_indicators >= 2
