"""LangGraph-specific graph canvas with execution state highlighting.

Extends the shared BaseStudioCanvas with any LangGraph-specific
visualization needs.
"""

from __future__ import annotations

from castella.graph import GraphModel, LayoutConfig
from castella.graph.theme import GraphTheme, DARK_THEME

from castella.studio.widgets.canvas import BaseStudioCanvas

from ..models.execution import ExecutionState


class LangGraphCanvas(BaseStudioCanvas):
    """Graph canvas with LangGraph execution state visualization.

    Extends the shared BaseStudioCanvas. Currently no LangGraph-specific
    customizations needed beyond the base implementation.
    """

    def __init__(
        self,
        graph: GraphModel | None = None,
        execution_state: ExecutionState | None = None,
        layout_config: LayoutConfig | None = None,
        theme: GraphTheme | None = None,
    ):
        """Initialize the LangGraph canvas.

        Args:
            graph: Graph model to display.
            execution_state: Current execution state for highlighting.
            layout_config: Layout configuration.
            theme: Visual theme.
        """
        super().__init__(
            graph=graph,
            execution_state=execution_state,
            layout_config=layout_config or LayoutConfig(direction="LR"),
            theme=theme or DARK_THEME,
            auto_layout=False,
        )


# For backwards compatibility, also export as GraphCanvas
GraphCanvas = LangGraphCanvas
