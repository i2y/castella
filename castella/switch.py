from typing import Callable, Self, cast

from castella.core import (
    AppearanceState,
    Circle,
    InputKeyEvent,
    KeyAction,
    KeyCode,
    Kind,
    MouseEvent,
    Painter,
    Point,
    Rect,
    SimpleValue,
    Size,
    SizePolicy,
    State,
    StrokeStyle,
    Widget,
    get_theme,
)


class Switch(Widget):
    def __init__(self, selected: bool | SimpleValue[bool]):
        self._kind = Kind.NORMAL
        self._callback = lambda _: ...
        self._focused = False
        super().__init__(
            state=selected if isinstance(selected, SimpleValue) else State(selected),
            size=Size(width=0, height=0),
            pos=Point(x=0, y=0),
            pos_policy=None,
            width_policy=SizePolicy.EXPANDING,
            height_policy=SizePolicy.EXPANDING,
        )

    def mouse_up(self, ev: MouseEvent) -> None:
        state = cast(SimpleValue[bool], self._state)
        new_value = not state.value()
        state.set(new_value)
        self._callback(new_value)

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
            state = cast(SimpleValue[bool], self._state)
            new_value = not state.value()
            state.set(new_value)
            self._callback(new_value)

    def _on_update_widget_styles(self) -> None:
        self._bg_style, self._fg_style = self._get_painter_styles(
            self._kind, AppearanceState.NORMAL
        )
        self._selected_bg_style, _ = self._get_painter_styles(
            self._kind, AppearanceState.SELECTED
        )

    def redraw(self, p: Painter, _: bool) -> None:
        self._draw_background(p)
        self._draw_knob(p)

    def _draw_background(self, p: Painter) -> None:
        s = self.get_size()
        r = s.height / 2 - 0.5
        left_circle = Circle(center=Point(x=r, y=r), radius=r)
        center_rect = Rect(origin=Point(x=r, y=0), size=s - Size(width=r * 2, height=0))
        right_circle = Circle(center=Point(x=s.width - r, y=r), radius=r)

        state = cast(SimpleValue[bool], self._state)
        if state.value():
            bg_style = self._selected_bg_style
        else:
            bg_style = self._bg_style

        # Apply focus ring if focused
        if self._focused:
            focus_color = get_theme().colors.border_focus
            bg_style = bg_style.model_copy(
                update={"stroke": StrokeStyle(color=focus_color)}
            )

        p.style(bg_style)
        p.fill_circle(left_circle)
        p.fill_circle(right_circle)
        if self._focused:
            p.stroke_circle(left_circle)
            p.stroke_circle(right_circle)

        # Draw center rect with border_radius=0 to connect smoothly with circles
        p.style(bg_style.model_copy(update={"border_radius": 0}))
        p.fill_rect(center_rect)

    def _draw_knob(self, p: Painter) -> None:
        s = self.get_size()
        r = s.height / 2 - 0.5
        inner_r = s.height * 0.75 / 2 - 0.5
        w = s.width
        state = cast(SimpleValue[bool], self._state)
        p.style(self._fg_style)
        if state.value():
            knob = Circle(center=Point(x=w - r, y=r), radius=inner_r)
        else:
            knob = Circle(center=Point(x=r, y=r), radius=inner_r)
        p.fill_circle(knob)

    def width_policy(self, sp: SizePolicy) -> Self:
        if sp is SizePolicy.CONTENT:
            raise RuntimeError("The switch doesn't accept SizePolicy.CONTENT")
        return super().width_policy(sp)

    def height_policy(self, sp: SizePolicy) -> Self:
        if sp is SizePolicy.CONTENT:
            raise RuntimeError("The switch doesn't accept SizePolicy.CONTENT")
        return super().height_policy(sp)

    def on_change(self, callback: Callable[[bool], None]) -> Self:
        self._callback = callback
        return self
