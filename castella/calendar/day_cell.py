"""DayCell widget for calendar day display."""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING, Callable

from castella.core import (
    Circle,
    FillStyle,
    Font,
    MouseEvent,
    Painter,
    Point,
    Rect,
    Size,
    SizePolicy,
    StrokeStyle,
    Style,
    Widget,
)
from castella.theme import ThemeManager

if TYPE_CHECKING:
    pass


class DayCell(Widget):
    """A single day cell in the calendar grid.

    Displays a day number with appropriate styling based on state:
    - Normal: Regular day in current month
    - Muted: Day from previous/next month
    - Today: Current date with border highlight
    - Selected: Currently selected date with filled background
    - Disabled: Unselectable date (grayed out)
    - Hover: Mouse-over effect
    """

    def __init__(
        self,
        day: int,
        cell_date: date,
        is_current_month: bool = True,
        is_today: bool = False,
        is_selected: bool = False,
        is_disabled: bool = False,
        cell_size: int = 32,
        on_click: Callable[[date], None] | None = None,
    ):
        """Initialize DayCell.

        Args:
            day: Day number to display (1-31)
            cell_date: Full date object for this cell
            is_current_month: Whether day is in the displayed month
            is_today: Whether day is today
            is_selected: Whether day is currently selected
            is_disabled: Whether day is unselectable
            cell_size: Size of the cell in pixels
            on_click: Callback when cell is clicked
        """
        self._day = day
        self._cell_date = cell_date
        self._is_current_month = is_current_month
        self._is_today = is_today
        self._is_selected = is_selected
        self._is_disabled = is_disabled
        self._cell_size = cell_size
        self._on_click = on_click or (lambda _: None)
        self._hovered = False

        super().__init__(
            state=None,
            pos=Point(x=0, y=0),
            pos_policy=None,
            size=Size(width=cell_size, height=cell_size),
            width_policy=SizePolicy.FIXED,
            height_policy=SizePolicy.FIXED,
        )

    def _on_update_widget_styles(self) -> None:
        """Update styles from theme."""
        self._update_styles()

    def _update_styles(self) -> None:
        """Update internal styles based on current state."""
        theme = ThemeManager().current
        styles = theme.calendar

        # Determine which style to use based on state priority
        if self._is_disabled:
            self._style = styles["day_disabled"]
        elif self._is_selected:
            self._style = styles["day_selected"]
        elif self._hovered and not self._is_disabled:
            self._style = styles["day_hover"]
        elif self._is_today:
            self._style = styles["day_today"]
        elif not self._is_current_month:
            self._style = styles["day_muted"]
        else:
            self._style = styles["day_normal"]

    def redraw(self, p: Painter, completely: bool) -> None:
        """Draw the day cell."""
        size = self.get_size()
        if size.width == 0 or size.height == 0:
            return

        theme = ThemeManager().current
        styles = theme.calendar
        self._update_styles()

        # Clear background
        bg_style = Style(fill=FillStyle(color=styles["day_normal"].bg_color))
        p.style(bg_style)
        p.fill_rect(Rect(origin=Point(x=0, y=0), size=size))

        # Draw cell background/border based on state
        center_x = size.width / 2
        center_y = size.height / 2
        radius = min(size.width, size.height) / 2 - 2

        if self._is_selected:
            # Filled circle for selected
            style = Style(fill=FillStyle(color=self._style.bg_color))
            p.style(style)
            p.fill_circle(Circle(center=Point(x=center_x, y=center_y), radius=radius))
        elif self._is_today and not self._is_disabled:
            # Border circle for today
            style = Style(stroke=StrokeStyle(color=self._style.border_color, width=2))
            p.style(style)
            p.stroke_circle(Circle(center=Point(x=center_x, y=center_y), radius=radius))
        elif self._hovered and not self._is_disabled:
            # Hover background
            style = Style(fill=FillStyle(color=self._style.bg_color))
            p.style(style)
            p.fill_circle(Circle(center=Point(x=center_x, y=center_y), radius=radius))

        # Draw day text
        text = str(self._day)
        font = self._style.text_font
        text_style = Style(
            fill=FillStyle(color=self._style.text_color),
            font=Font(family=font.family, size=font.size),
        )
        p.style(text_style)

        # Center text in cell
        text_width = p.measure_text(text)
        font_metrics = p.get_font_metrics()
        text_x = (size.width - text_width) / 2
        text_y = (size.height + font_metrics.cap_height) / 2

        p.fill_text(text=text, pos=Point(x=text_x, y=text_y), max_width=size.width)

    def mouse_over(self) -> None:
        """Handle mouse entering the cell."""
        if not self._is_disabled:
            self._hovered = True
            self.update()

    def mouse_out(self) -> None:
        """Handle mouse leaving the cell."""
        self._hovered = False
        self.update()

    def mouse_up(self, ev: MouseEvent) -> None:
        """Handle click on the cell."""
        if not self._is_disabled:
            self._on_click(self._cell_date)

    @property
    def cell_date(self) -> date:
        """Get the date this cell represents."""
        return self._cell_date

    @property
    def is_selected(self) -> bool:
        """Check if this cell is selected."""
        return self._is_selected

    def set_selected(self, selected: bool) -> None:
        """Set selected state."""
        if self._is_selected != selected:
            self._is_selected = selected
            self.update()
