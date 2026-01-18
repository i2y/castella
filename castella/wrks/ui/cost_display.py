"""Cost display widget for wrks."""

from castella import Row, Text, Widget
from castella.core import Component, State
from castella.theme import ThemeManager


class CostDisplay(Component):
    """Displays cumulative cost tracking."""

    def __init__(self, cost_state: State[float]):
        """Initialize the cost display."""
        super().__init__()
        self._cost = cost_state
        self._states_attached = False

    def _attach_states_if_needed(self) -> None:
        """Lazily attach states."""
        if not self._states_attached:
            self._cost.attach(self)
            self._states_attached = True

    def view(self) -> Widget:
        """Build the cost display view."""
        self._attach_states_if_needed()
        theme = ThemeManager().current
        cost = self._cost()

        if cost == 0:
            cost_text = "$0.00"
            color = theme.colors.border_primary
        elif cost < 0.01:
            cost_text = f"${cost:.4f}"
            color = theme.colors.border_secondary
        else:
            cost_text = f"${cost:.2f}"
            color = theme.colors.text_warning if cost > 1.0 else theme.colors.border_secondary

        return Row(
            Text("Cost: ", font_size=12).text_color(theme.colors.border_primary),
            Text(cost_text, font_size=12).text_color(color),
        )
