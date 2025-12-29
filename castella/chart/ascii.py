"""ASCII chart rendering for terminal environments."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from castella.core import (
    Painter,
    Point,
    Size,
    Rect,
    Style,
    FillStyle,
    Widget,
    SizePolicy,
)


# Unicode block characters for bar rendering (8 levels)
BLOCKS = " ▏▎▍▌▋▊▉█"


def _is_terminal_painter(p: Painter) -> bool:
    """Check if painter is a terminal painter without importing PTPainter."""
    return type(p).__name__ == "PTPainter"


@dataclass
class ASCIIBarData:
    """Data for ASCII bar chart."""

    labels: list[str]
    values: list[float]
    title: str = ""


class ASCIIBarChart(Widget):
    """ASCII bar chart for terminal rendering.

    Uses Unicode block characters for sub-character precision.

    Example:
        ```python
        data = ASCIIBarData(
            title="Sales",
            labels=["Q1", "Q2", "Q3", "Q4"],
            values=[100, 150, 120, 180],
        )
        chart = ASCIIBarChart(data, width=40)
        ```
    """

    def __init__(
        self,
        data: ASCIIBarData,
        width: int = 40,
        show_values: bool = True,
        bar_char: str = "█",
    ):
        """Initialize ASCII bar chart.

        Args:
            data: Chart data.
            width: Width in characters for the bar area.
            show_values: Whether to show values at end of bars.
            bar_char: Character to use for bars.
        """
        super().__init__(
            state=None,
            pos=Point(x=0, y=0),
            pos_policy=None,
            size=Size(width=0, height=0),
        )
        self._data = data
        self._chart_width = width
        self._show_values = show_values
        self._bar_char = bar_char
        self._width_policy = SizePolicy.EXPANDING
        self._height_policy = SizePolicy.CONTENT

    def content_width(self) -> float:
        # Label width + bar width + value width
        max_label = max((len(lbl) for lbl in self._data.labels), default=0)
        return (max_label + self._chart_width + 10) * 12  # Approximate

    def content_height(self) -> float:
        # One line per bar plus title
        lines = len(self._data.labels)
        if self._data.title:
            lines += 2
        return lines * 12  # Line height

    def redraw(self, p: Painter, completely: bool) -> None:
        if not _is_terminal_painter(p):
            # For non-terminal, just draw a placeholder
            self._draw_placeholder(p)
            return

        lines = self._render_lines()

        y = 0
        for line in lines:
            p.style(Style(fill=FillStyle(color="#ffffff")))
            p.fill_text(line, Point(x=0, y=y), None)
            y += 12  # Line height

    def _render_lines(self) -> list[str]:
        """Render the chart as lines of text."""
        lines = []

        if self._data.title:
            lines.append(self._data.title)
            lines.append("")

        if not self._data.values:
            lines.append("(no data)")
            return lines

        max_val = max(self._data.values)
        max_label_len = max((len(lbl) for lbl in self._data.labels), default=0)

        for label, value in zip(self._data.labels, self._data.values):
            # Calculate bar length
            if max_val > 0:
                ratio = value / max_val
                bar_len = int(ratio * self._chart_width)
                remainder = (ratio * self._chart_width) - bar_len
                partial_idx = int(remainder * 8)
            else:
                bar_len = 0
                partial_idx = 0

            # Build bar string
            bar = self._bar_char * bar_len
            if partial_idx > 0 and bar_len < self._chart_width:
                bar += BLOCKS[partial_idx]

            # Format line
            label_padded = label.ljust(max_label_len)
            if self._show_values:
                line = f"{label_padded} │{bar.ljust(self._chart_width)}│ {value:.1f}"
            else:
                line = f"{label_padded} │{bar.ljust(self._chart_width)}│"

            lines.append(line)

        return lines

    def _draw_placeholder(self, p: Painter) -> None:
        """Draw placeholder for non-terminal environments."""
        size = self.get_size()
        rect = Rect(origin=Point(x=0, y=0), size=size)
        p.style(Style(fill=FillStyle(color="#333333")))
        p.fill_rect(rect)
        p.style(Style(fill=FillStyle(color="#ffffff")))
        p.fill_text(
            f"[ASCII Bar Chart: {self._data.title}]",
            Point(x=10, y=20),
            None,
        )


@dataclass
class ASCIIPieData:
    """Data for ASCII pie chart."""

    labels: list[str]
    values: list[float]
    title: str = ""


class ASCIIPieChart(Widget):
    """ASCII pie chart for terminal rendering.

    Displays a simple text-based legend with percentages.

    Example:
        ```python
        data = ASCIIPieData(
            title="Market Share",
            labels=["A", "B", "C"],
            values=[50, 30, 20],
        )
        chart = ASCIIPieChart(data)
        ```
    """

    # Unicode pie symbols
    PIE_CHARS = ["●", "○", "◐", "◑", "◒", "◓", "◔", "◕"]

    def __init__(
        self,
        data: ASCIIPieData,
    ):
        """Initialize ASCII pie chart.

        Args:
            data: Chart data.
        """
        super().__init__(
            state=None,
            pos=Point(x=0, y=0),
            pos_policy=None,
            size=Size(width=0, height=0),
        )
        self._data = data
        self._width_policy = SizePolicy.EXPANDING
        self._height_policy = SizePolicy.CONTENT

    def content_width(self) -> float:
        max_label = max((len(lbl) for lbl in self._data.labels), default=0)
        return (max_label + 20) * 12

    def content_height(self) -> float:
        lines = len(self._data.labels)
        if self._data.title:
            lines += 2
        return lines * 12

    def redraw(self, p: Painter, completely: bool) -> None:
        if not _is_terminal_painter(p):
            self._draw_placeholder(p)
            return

        lines = self._render_lines()

        y = 0
        for line in lines:
            p.style(Style(fill=FillStyle(color="#ffffff")))
            p.fill_text(line, Point(x=0, y=y), None)
            y += 12

    def _render_lines(self) -> list[str]:
        """Render the chart as lines of text."""
        lines = []

        if self._data.title:
            lines.append(self._data.title)
            lines.append("")

        if not self._data.values:
            lines.append("(no data)")
            return lines

        total = sum(self._data.values)
        if total == 0:
            lines.append("(no data)")
            return lines

        max_label_len = max((len(lbl) for lbl in self._data.labels), default=0)

        for i, (label, value) in enumerate(zip(self._data.labels, self._data.values)):
            pct = (value / total) * 100
            marker = self.PIE_CHARS[i % len(self.PIE_CHARS)]
            bar_len = int(pct / 5)  # 20 chars = 100%
            bar = "█" * bar_len

            label_padded = label.ljust(max_label_len)
            line = f"{marker} {label_padded} {bar.ljust(20)} {pct:5.1f}%"
            lines.append(line)

        return lines

    def _draw_placeholder(self, p: Painter) -> None:
        """Draw placeholder for non-terminal environments."""
        size = self.get_size()
        rect = Rect(origin=Point(x=0, y=0), size=size)
        p.style(Style(fill=FillStyle(color="#333333")))
        p.fill_rect(rect)
        p.style(Style(fill=FillStyle(color="#ffffff")))
        p.fill_text(
            f"[ASCII Pie Chart: {self._data.title}]",
            Point(x=10, y=20),
            None,
        )


class ASCIILineChart(Widget):
    """ASCII line chart for terminal rendering.

    Uses braille characters for high-resolution display.

    Example:
        ```python
        data = [10, 25, 15, 30, 20, 35]
        chart = ASCIILineChart(data, width=60, height=10)
        ```
    """

    # Braille dots for plotting (2x4 grid per character)
    BRAILLE_BASE = 0x2800
    BRAILLE_DOTS = [
        0x01,
        0x02,
        0x04,
        0x40,  # Left column: top to bottom
        0x08,
        0x10,
        0x20,
        0x80,  # Right column: top to bottom
    ]

    def __init__(
        self,
        values: Sequence[float],
        width: int = 60,
        height: int = 10,
        title: str = "",
    ):
        """Initialize ASCII line chart.

        Args:
            values: Y values to plot.
            width: Width in characters.
            height: Height in characters.
            title: Chart title.
        """
        super().__init__(
            state=None,
            pos=Point(x=0, y=0),
            pos_policy=None,
            size=Size(width=0, height=0),
        )
        self._values = list(values)
        self._chart_width = width
        self._chart_height = height
        self._title = title
        self._width_policy = SizePolicy.EXPANDING
        self._height_policy = SizePolicy.CONTENT

    def content_width(self) -> float:
        return (self._chart_width + 10) * 12

    def content_height(self) -> float:
        lines = self._chart_height
        if self._title:
            lines += 2
        return lines * 12

    def redraw(self, p: Painter, completely: bool) -> None:
        if not _is_terminal_painter(p):
            self._draw_placeholder(p)
            return

        lines = self._render_lines()

        y = 0
        for line in lines:
            p.style(Style(fill=FillStyle(color="#ffffff")))
            p.fill_text(line, Point(x=0, y=y), None)
            y += 12

    def _render_lines(self) -> list[str]:
        """Render the chart as lines of text."""
        lines = []

        if self._title:
            lines.append(self._title)
            lines.append("")

        if not self._values:
            lines.append("(no data)")
            return lines

        min_val = min(self._values)
        max_val = max(self._values)
        val_range = max_val - min_val if max_val != min_val else 1

        # Create a 2D grid for the chart
        grid = [
            [" " for _ in range(self._chart_width)] for _ in range(self._chart_height)
        ]

        # Plot points
        for i, value in enumerate(self._values):
            x = int((i / max(len(self._values) - 1, 1)) * (self._chart_width - 1))
            y = int(((value - min_val) / val_range) * (self._chart_height - 1))
            y = self._chart_height - 1 - y  # Flip Y axis

            if 0 <= x < self._chart_width and 0 <= y < self._chart_height:
                grid[y][x] = "●"

        # Connect with lines (simple)
        for i in range(len(self._values) - 1):
            x1 = int((i / max(len(self._values) - 1, 1)) * (self._chart_width - 1))
            x2 = int(
                ((i + 1) / max(len(self._values) - 1, 1)) * (self._chart_width - 1)
            )
            y1 = int(
                ((self._values[i] - min_val) / val_range) * (self._chart_height - 1)
            )
            y2 = int(
                ((self._values[i + 1] - min_val) / val_range) * (self._chart_height - 1)
            )
            y1 = self._chart_height - 1 - y1
            y2 = self._chart_height - 1 - y2

            # Draw line between points
            steps = max(abs(x2 - x1), abs(y2 - y1), 1)
            for step in range(steps):
                t = step / steps
                x = int(x1 + t * (x2 - x1))
                y = int(y1 + t * (y2 - y1))
                if 0 <= x < self._chart_width and 0 <= y < self._chart_height:
                    if grid[y][x] == " ":
                        grid[y][x] = "·"

        # Build lines with axis
        for i, row in enumerate(grid):
            y_val = max_val - (i / (self._chart_height - 1)) * val_range
            line = f"{y_val:6.1f} │{''.join(row)}│"
            lines.append(line)

        # X axis
        lines.append(f"       └{'─' * self._chart_width}┘")

        return lines

    def _draw_placeholder(self, p: Painter) -> None:
        """Draw placeholder for non-terminal environments."""
        size = self.get_size()
        rect = Rect(origin=Point(x=0, y=0), size=size)
        p.style(Style(fill=FillStyle(color="#333333")))
        p.fill_rect(rect)
        p.style(Style(fill=FillStyle(color="#ffffff")))
        p.fill_text(
            f"[ASCII Line Chart: {self._title}]",
            Point(x=10, y=20),
            None,
        )


class ASCIIGaugeChart(Widget):
    """ASCII gauge chart for terminal rendering.

    Example:
        ```python
        chart = ASCIIGaugeChart(value=75, max_value=100, title="CPU")
        ```
    """

    def __init__(
        self,
        value: float,
        max_value: float = 100,
        min_value: float = 0,
        width: int = 30,
        title: str = "",
    ):
        """Initialize ASCII gauge chart.

        Args:
            value: Current value.
            max_value: Maximum value.
            min_value: Minimum value.
            width: Width in characters.
            title: Chart title.
        """
        super().__init__(
            state=None,
            pos=Point(x=0, y=0),
            pos_policy=None,
            size=Size(width=0, height=0),
        )
        self._value = value
        self._max_value = max_value
        self._min_value = min_value
        self._chart_width = width
        self._title = title
        self._width_policy = SizePolicy.EXPANDING
        self._height_policy = SizePolicy.CONTENT

    def content_width(self) -> float:
        return (self._chart_width + 20) * 12

    def content_height(self) -> float:
        return 3 * 12  # Title + gauge + value

    def redraw(self, p: Painter, completely: bool) -> None:
        if not _is_terminal_painter(p):
            self._draw_placeholder(p)
            return

        lines = self._render_lines()

        y = 0
        for line in lines:
            p.style(Style(fill=FillStyle(color="#ffffff")))
            p.fill_text(line, Point(x=0, y=y), None)
            y += 12

    def _render_lines(self) -> list[str]:
        """Render the gauge as lines of text."""
        lines = []

        if self._title:
            lines.append(self._title)

        val_range = self._max_value - self._min_value
        if val_range <= 0:
            pct = 0
        else:
            pct = (self._value - self._min_value) / val_range

        filled = int(pct * self._chart_width)
        remainder = (pct * self._chart_width) - filled
        partial_idx = int(remainder * 8)

        bar = "█" * filled
        if partial_idx > 0 and filled < self._chart_width:
            bar += BLOCKS[partial_idx]
        bar = bar.ljust(self._chart_width)

        # Gauge line
        lines.append(f"[{bar}] {self._value:.1f}/{self._max_value:.0f}")

        return lines

    def _draw_placeholder(self, p: Painter) -> None:
        """Draw placeholder for non-terminal environments."""
        size = self.get_size()
        rect = Rect(origin=Point(x=0, y=0), size=size)
        p.style(Style(fill=FillStyle(color="#333333")))
        p.fill_rect(rect)
        p.style(Style(fill=FillStyle(color="#ffffff")))
        p.fill_text(
            f"[ASCII Gauge: {self._title} = {self._value}]",
            Point(x=10, y=20),
            None,
        )
