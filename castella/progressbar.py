"""ProgressBar widget for displaying progress with animation support."""

from typing import Callable, Self, cast

from castella.core import (
    AppearanceState,
    FillStyle,
    Kind,
    ObservableBase,
    Painter,
    Point,
    Rect,
    Size,
    SizePolicy,
    Style,
    Widget,
    get_theme,
)


class ProgressBarState(ObservableBase):
    """Observable state for ProgressBar widget.

    Attributes:
        value: Current value (clamped between min and max)
        min_val: Minimum value
        max_val: Maximum value
    """

    def __init__(
        self,
        value: float = 0.0,
        min_val: float = 0.0,
        max_val: float = 100.0,
    ):
        super().__init__()
        self._min = min_val
        self._max = max_val
        self._value = self._clamp(value)

    def _clamp(self, value: float) -> float:
        """Clamp value to [min, max] range."""
        return max(self._min, min(self._max, value))

    def value(self) -> float:
        """Get current value."""
        return self._value

    def __call__(self) -> float:
        """Get current value (callable syntax)."""
        return self._value

    def set(self, value: float) -> None:
        """Set value (clamped to range)."""
        new_value = self._clamp(value)
        if new_value != self._value:
            self._value = new_value
            self.notify()

    def min_val(self) -> float:
        """Get minimum value."""
        return self._min

    def max_val(self) -> float:
        """Get maximum value."""
        return self._max

    def set_range(self, min_val: float, max_val: float) -> None:
        """Set min and max values."""
        self._min = min_val
        self._max = max_val
        self._value = self._clamp(self._value)
        self.notify()

    def ratio(self) -> float:
        """Get value as ratio (0.0 to 1.0)."""
        range_val = self._max - self._min
        if range_val == 0:
            return 0.0
        return (self._value - self._min) / range_val

    def set_from_ratio(self, ratio: float) -> None:
        """Set value from ratio (0.0 to 1.0)."""
        ratio = max(0.0, min(1.0, ratio))
        new_value = self._min + ratio * (self._max - self._min)
        self.set(new_value)


class ProgressBar(Widget):
    """ProgressBar widget for displaying progress.

    The progress bar consists of:
    - Track: Background bar showing the full range
    - Fill: Colored portion showing progress from min to current value

    Example:
        progress = ProgressBar(value=50, min_val=0, max_val=100)

    With state (for animation):
        state = ProgressBarState(value=0, min_val=0, max_val=100)
        progress = ProgressBar(state)
        state.set(75)  # Updates the bar
    """

    def __init__(
        self,
        value: float | ProgressBarState = 0.0,
        min_val: float = 0.0,
        max_val: float = 100.0,
        kind: Kind = Kind.NORMAL,
        show_text: bool = False,
    ):
        """Initialize ProgressBar.

        Args:
            value: Initial value or ProgressBarState
            min_val: Minimum value (ignored if value is ProgressBarState)
            max_val: Maximum value (ignored if value is ProgressBarState)
            kind: Visual style kind (default: NORMAL)
            show_text: Whether to show percentage text
        """
        self._kind = kind
        self._show_text = show_text
        self._track_color: str | None = None
        self._fill_color: str | None = None
        self._border_radius: float = 4.0
        self._on_change_callback: Callable[[float], None] | None = None

        if isinstance(value, ProgressBarState):
            state = value
        else:
            state = ProgressBarState(value, min_val, max_val)

        super().__init__(
            state=state,
            size=Size(width=0, height=20),
            pos=Point(x=0, y=0),
            pos_policy=None,
            width_policy=SizePolicy.EXPANDING,
            height_policy=SizePolicy.FIXED,
        )

    def _on_update_widget_styles(self) -> None:
        """Update styles based on theme."""
        # Track style (background bar) - always use NORMAL kind for slider-based styles
        self._track_style, _ = self._get_painter_styles(
            Kind.NORMAL, AppearanceState.NORMAL
        )
        # Fill style (filled portion)
        self._fill_style, _ = self._get_painter_styles(
            Kind.NORMAL, AppearanceState.SELECTED
        )

    def redraw(self, p: Painter, completely: bool) -> None:
        """Draw the progress bar."""
        state = cast(ProgressBarState, self._state)
        size = self.get_size()

        # Skip drawing if size is not yet set
        if size.width == 0 or size.height == 0:
            return

        # Clear background
        if completely or self.is_dirty():
            widget_style = get_theme().layout["normal"]
            clear_style = Style(
                fill=FillStyle(color=widget_style.bg_color),
            )
            p.style(clear_style)
            p.fill_rect(
                Rect(
                    origin=Point(x=0, y=0),
                    size=size + Size(width=1, height=1),
                )
            )

        # Draw track (background bar)
        track_color = self._track_color or self._track_style.fill.color
        track_style = Style(
            fill=FillStyle(color=track_color),
            border_radius=self._border_radius,
        )
        track_rect = Rect(
            origin=Point(x=0, y=0),
            size=Size(width=size.width, height=size.height),
        )
        p.style(track_style)
        p.fill_rect(track_rect)

        # Draw fill (progress)
        ratio = state.ratio()
        fill_width = size.width * ratio
        if fill_width > 0:
            fill_color = self._fill_color or self._fill_style.fill.color
            fill_style = Style(
                fill=FillStyle(color=fill_color),
                border_radius=self._border_radius,
            )
            fill_rect = Rect(
                origin=Point(x=0, y=0),
                size=Size(width=fill_width, height=size.height),
            )
            p.style(fill_style)
            p.fill_rect(fill_rect)

        # Optionally draw percentage text
        if self._show_text:
            percentage = int(ratio * 100)
            text = f"{percentage}%"
            # Draw text in center (simple implementation)
            text_style = get_theme().text["normal"]
            p.draw_text(
                text,
                Point(x=size.width / 2, y=size.height / 2),
                text_style.text_color,
                center=True,
            )

    def on_notify(self, event=None) -> None:
        """Handle state changes."""
        self.dirty(True)
        self.update()
        if self._on_change_callback:
            state = cast(ProgressBarState, self._state)
            self._on_change_callback(state.value())

    def on_change(self, callback: Callable[[float], None]) -> Self:
        """Set callback for value changes.

        Args:
            callback: Function called with new value when progress changes

        Returns:
            Self for method chaining
        """
        self._on_change_callback = callback
        return self

    def kind(self, kind: Kind) -> Self:
        """Set visual style kind.

        Args:
            kind: Visual style (NORMAL, INFO, SUCCESS, WARNING, DANGER)

        Returns:
            Self for method chaining
        """
        self._kind = kind
        self._on_update_widget_styles()
        return self

    def track_color(self, color: str) -> Self:
        """Set custom track (background) color.

        Args:
            color: Hex color string (e.g., "#1a1b26")

        Returns:
            Self for method chaining
        """
        self._track_color = color
        return self

    def fill_color(self, color: str) -> Self:
        """Set custom fill (progress) color.

        Args:
            color: Hex color string (e.g., "#9ece6a")

        Returns:
            Self for method chaining
        """
        self._fill_color = color
        return self

    def border_radius(self, radius: float) -> Self:
        """Set border radius for rounded corners.

        Args:
            radius: Border radius in pixels

        Returns:
            Self for method chaining
        """
        self._border_radius = radius
        return self

    def show_text(self, show: bool = True) -> Self:
        """Show or hide percentage text.

        Args:
            show: Whether to show percentage text

        Returns:
            Self for method chaining
        """
        self._show_text = show
        return self

    def width_policy(self, sp: SizePolicy) -> Self:
        """Set width sizing policy."""
        if sp is SizePolicy.CONTENT:
            raise RuntimeError(
                "ProgressBar doesn't accept SizePolicy.CONTENT for width"
            )
        return super().width_policy(sp)

    def height_policy(self, sp: SizePolicy) -> Self:
        """Set height sizing policy."""
        if sp is SizePolicy.CONTENT:
            raise RuntimeError(
                "ProgressBar doesn't accept SizePolicy.CONTENT for height"
            )
        return super().height_policy(sp)
