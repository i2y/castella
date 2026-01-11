from typing import Any, Callable, Self, cast

from castella.core import (
    AppearanceState,
    Circle,
    Font,
    FontSizePolicy,
    InputKeyEvent,
    KeyAction,
    KeyCode,
    Kind,
    MouseEvent,
    Painter,
    Point,
    Rect,
    Size,
    SizePolicy,
    State,
    StrokeStyle,
    Style,
    Widget,
    determine_font,
    get_theme,
)


class CheckBox(Widget):
    def __init__(
        self,
        checked: bool | State[bool] = False,
        on_label: str = "",
        off_label: str = "",
        is_circle: bool = False,
    ):
        self._on_label = on_label
        self._off_label = off_label
        self._is_circle = is_circle
        self._on_click = lambda _: ...
        self._on_change: Callable[[bool], Any] = lambda _: ...
        self._kind = Kind.NORMAL
        self._appearance_state = AppearanceState.NORMAL
        self._focused = False
        super().__init__(
            state=checked if isinstance(checked, State) else State(checked),
            size=Size(width=0, height=0),
            pos=Point(x=0, y=0),
            pos_policy=None,
            width_policy=SizePolicy.EXPANDING,
            height_policy=SizePolicy.EXPANDING,
        )

    def _on_update_widget_styles(self) -> None:
        self._style, self._text_style = self._get_painter_styles(
            self._kind, self._appearance_state
        )
        self._checked_style, self._checked_text_style = self._get_painter_styles(
            self._kind, AppearanceState.SELECTED
        )

    def mouse_up(self, ev: MouseEvent) -> None:
        state: State[bool] = cast(State[bool], self._state)
        new_value = not state.value()
        state.set(new_value)
        self._on_click(ev)
        self._on_change(new_value)

    def on_click(self, callback: Callable[[MouseEvent], Any]) -> Self:
        self._on_click = callback
        return self

    def on_change(self, callback: Callable[[bool], Any]) -> Self:
        """Set callback for when checkbox state changes.

        Args:
            callback: Function called with the new checked state (True/False)

        Returns:
            Self for method chaining
        """
        self._on_change = callback
        return self

    def focused(self) -> None:
        """Called when this widget receives focus."""
        self._focused = True
        self.update()

    def unfocused(self) -> None:
        """Called when this widget loses focus."""
        self._focused = False
        self.update()

    def can_focus(self) -> bool:
        """Return True if this widget can receive focus."""
        return True

    def focus_order(self) -> int:
        """Return the tab order (lower = earlier in tab sequence)."""
        return self._tab_index

    def input_key(self, ev: InputKeyEvent) -> None:
        """Handle keyboard input when focused."""
        if ev.action == KeyAction.RELEASE:
            return
        # Toggle on Enter or Space
        if ev.key in (KeyCode.ENTER, KeyCode.SPACE):
            state: State[bool] = cast(State[bool], self._state)
            new_value = not state.value()
            state.set(new_value)
            self._on_change(new_value)

    def redraw(self, p: Painter, _: bool) -> None:
        state: State[bool] = cast(State[bool], self._state)

        # Determine style based on focus state
        if self._focused:
            focus_color = get_theme().colors.border_focus
            draw_style = Style(
                fill=self._style.fill,
                stroke=StrokeStyle(color=focus_color),
                border_radius=self._style.border_radius,
                shadow=self._style.shadow,
            )
        else:
            draw_style = self._style

        size = self.get_size()
        if self._is_circle:
            center = Point(x=size.width / 2, y=size.height / 2)
            circle = Circle(center=center, radius=size.width / 2)
            p.style(draw_style)
            p.fill_circle(circle)
            p.stroke_circle(circle)
            if state.value():
                inner_circle = Circle(
                    center=center,
                    radius=size.width * 0.6 / 2,
                )
                p.style(self._checked_style)
                p.fill_circle(inner_circle)
        else:
            rect = Rect(origin=Point(x=0, y=0), size=size)
            p.style(draw_style)
            p.fill_rect(rect)
            p.stroke_rect(rect)
            if state.value():
                inner_rect = Rect(
                    origin=Point(x=size.width * 0.2, y=size.height * 0.2),
                    size=Size(width=size.width * 0.6, height=size.height * 0.6),
                )
                p.style(self._checked_style)
                p.fill_rect(inner_rect)

        if state.value():
            label = self._on_label
            text_style = self._checked_text_style
        else:
            label = self._off_label
            text_style = self._text_style

        width = self.get_width()
        height = self.get_height()
        font_family, font_size = determine_font(
            width,
            height,
            text_style.model_copy(
                update={
                    "font": Font(
                        family=self._text_style.font.family,
                        size=self._text_style.font.size,
                        size_policy=FontSizePolicy.EXPANDING,
                    )
                }
            ),
            label,
        )
        p.style(
            text_style.model_copy(
                update={
                    "font": Font(
                        family=font_family,
                        size=font_size,
                        size_policy=FontSizePolicy.EXPANDING,
                    )
                }
            ),
        )

        pos = Point(
            x=width / 2 - p.measure_text(label) / 2,
            y=height / 2 + p.get_font_metrics().cap_height / 2,
        )

        p.fill_text(
            text=label,
            pos=pos,
            max_width=width - 2 * self._style.padding,
        )

    def width_policy(self, sp: SizePolicy) -> Self:
        if sp is SizePolicy.CONTENT:
            raise RuntimeError("CheckBox doesn't accept SizePolicy.CONTENT")
        return super().width_policy(sp)

    def height_policy(self, sp: SizePolicy) -> Self:
        if sp is SizePolicy.CONTENT:
            raise RuntimeError("CheckBox doesn't accept SizePolicy.CONTENT")
        return super().height_policy(sp)
