"""Graph canvas for pydantic-graph Studio."""

from __future__ import annotations

from castella.graph import GraphModel, LayoutConfig
from castella.graph.theme import GraphTheme, DARK_THEME
from castella.graph.transform import CanvasTransform
from castella.studio.widgets.canvas import BaseStudioCanvas
from castella.studio.models.execution import BaseExecutionState


class PydanticGraphCanvas(BaseStudioCanvas):
    """Graph canvas for pydantic-graph visualization.

    Extends BaseStudioCanvas with pydantic-graph specific features.
    The base class already provides:
    - Active node highlighting (yellow for currently executing)
    - Executed edge highlighting (green for traversed edges)
    - Breakpoint indicators
    """

    def __init__(
        self,
        graph: GraphModel | None = None,
        execution_state: BaseExecutionState | None = None,
        layout_config: LayoutConfig | None = None,
        theme: GraphTheme | None = None,
        transform: CanvasTransform | None = None,
    ):
        """Initialize the pydantic-graph canvas.

        Args:
            graph: Graph model to display.
            execution_state: Current execution state for highlighting.
            layout_config: Layout configuration.
            theme: Visual theme (defaults to DARK_THEME).
            transform: Initial transform state for zoom/pan.
        """
        # Note: auto_layout=False because layout is already applied
        # in to_castella_graph_model() using SugiyamaLayout
        super().__init__(
            graph=graph,
            execution_state=execution_state,
            layout_config=layout_config or LayoutConfig(direction="LR"),
            theme=theme or DARK_THEME,
            auto_layout=False,
            transform=transform,
        )
        self._current_graph_id: int | None = None

    def update_graph(self, graph: GraphModel | None) -> None:
        """Update the displayed graph if it changed.

        Only calls set_graph if the graph actually changed,
        to preserve zoom/pan state on rebuilds.

        Args:
            graph: New graph to display.
        """
        new_id = id(graph) if graph else None
        if new_id != self._current_graph_id:
            self._current_graph_id = new_id
            self.set_graph(graph)
