"""Workflow definitions view for Edda Workflow Manager."""

from __future__ import annotations

from typing import TYPE_CHECKING, Callable

from castella import (
    Component,
    Column,
    Row,
    Box,
    Button,
    Text,
    Spacer,
    State,
    Kind,
    SizePolicy,
)
from castella.multiline_text import MultilineText
from castella.studio.components.content_viewer_modal import ContentViewerModal
from castella.graph.canvas import GraphCanvas
from castella.graph.transform import CanvasTransform

from edda_workflow_manager.models.instance import WorkflowDefinition
from edda_workflow_manager.data.graph_builder import WorkflowGraphBuilder

if TYPE_CHECKING:
    from edda_workflow_manager.data.service import EddaDataService


class DefinitionsView(Component):
    """View and manage workflow definitions.

    ```
    ┌────────────────────────────────────────────────────────────────┐
    │  Left: Definition List    │  Right: Detail                    │
    │  ┌─────────────────────┐  │  Name: order_saga                 │
    │  │ order_saga          │  │  Hash: abc123...                  │
    │  │ payment_workflow    │  │  Created: 2024-01-01              │
    │  │ notification_wf     │  │                                   │
    │  └─────────────────────┘  │  [View Source]                    │
    │                           │  [Start Execution]                │
    └───────────────────────────┴───────────────────────────────────┘
    ```
    """

    def __init__(
        self,
        definitions: list[WorkflowDefinition] | None = None,
        workflow_templates: dict[str, list[str]] | None = None,
        on_view_source: Callable[[str, str], None] | None = None,
        on_start_execution: Callable[[str], None] | None = None,
        on_refresh: Callable[[], None] | None = None,
        can_start_execution: bool = False,
    ):
        """Initialize definitions view.

        Args:
            definitions: List of workflow definitions.
            workflow_templates: Dict mapping workflow_name to activity list.
            on_view_source: Callback to view source code.
            on_start_execution: Callback to start execution.
            on_refresh: Callback for refresh.
            can_start_execution: Whether Start Execution button should be shown.
        """
        super().__init__()
        self._definitions = definitions or []
        self._workflow_templates = workflow_templates or {}
        self._on_view_source = on_view_source
        self._on_start_execution = on_start_execution
        self._on_refresh = on_refresh
        self._can_start_execution = can_start_execution

        # Selected definition
        self._selected_name: State[str | None] = State(None)
        self._selected_name.attach(self)

        # Content viewer modal
        self._content_modal = ContentViewerModal()
        self._content_modal.attach(self)

        # Graph builder and transform
        self._graph_builder = WorkflowGraphBuilder()
        self._canvas_transform = CanvasTransform()

    def view(self):
        """Build the definitions view."""
        main_content = Row(
            # Left: Definition list
            self._build_definition_list(),

            # Right: Detail panel
            self._build_detail_panel(),
        ).height_policy(SizePolicy.EXPANDING)

        # Add modal if open
        if self._content_modal.is_open:
            return Box(main_content, self._content_modal.build())

        return main_content

    def _build_definition_list(self) -> Column:
        """Build the definition list."""
        items = []

        # Header row
        header = (
            Row(
                Text("Definitions").text_color("#bb9af7").fixed_width(100),
                Spacer(),
                Button("Refresh")
                .fixed_height(28)
                .fixed_width(70)
                .on_click(
                    lambda _: self._on_refresh() if self._on_refresh else None
                ),
            )
            .fixed_height(40)
            .bg_color("#1e1f2b")
        )

        # Definition list items
        list_items = []
        if not self._definitions:
            list_items.append(
                Text("No definitions found")
                .fixed_height(32)
                .text_color("#6b7280")
            )
        else:
            # Group by workflow name (show only latest per name)
            seen_names: set[str] = set()
            for defn in self._definitions:
                if defn.workflow_name in seen_names:
                    continue
                seen_names.add(defn.workflow_name)

                is_selected = self._selected_name() == defn.workflow_name
                list_items.append(self._build_definition_item(defn, is_selected))

        definition_list = (
            Column(*list_items, scrollable=True)
            .height_policy(SizePolicy.EXPANDING)
        )

        return (
            Column(header, definition_list)
            .fixed_width(220)
            .height_policy(SizePolicy.EXPANDING)
            .bg_color("#1a1b26")
        )

    def _build_definition_item(
        self, definition: WorkflowDefinition, is_selected: bool
    ) -> Button:
        """Build a single definition item."""
        bg_color = "#2a2b3d" if is_selected else "#1e1f2b"

        label = f"📋 {definition.workflow_name}"
        return (
            Button(label)
            .fixed_height(32)
            .bg_color(bg_color)
            .text_color("#c0caf5")
            .on_click(
                lambda _, name=definition.workflow_name: self._selected_name.set(name)
            )
        )

    def _build_detail_panel(self) -> Column:
        """Build the detail panel."""
        selected = self._selected_name()

        if not selected:
            return (
                Column(
                    Spacer(),
                    Text("Select a workflow to view details")
                    .text_color("#6b7280"),
                    Spacer(),
                )
                .width_policy(SizePolicy.EXPANDING)
                .height_policy(SizePolicy.EXPANDING)
                .bg_color("#1e1f2b")
            )

        # Find the selected definition
        definition = None
        for d in self._definitions:
            if d.workflow_name == selected:
                definition = d
                break

        if not definition:
            return (
                Column(
                    Text("Definition not found").text_color("#f7768e"),
                )
                .width_policy(SizePolicy.EXPANDING)
                .height_policy(SizePolicy.EXPANDING)
                .bg_color("#1e1f2b")
            )

        return (
            Column(
                # Header
                Text(definition.workflow_name)
                .text_color("#bb9af7")
                .fixed_height(40),

                # Details
                Row(
                    Text(f"Hash: {definition.source_hash[:20]}...")
                    .text_color("#9ca3af"),
                    Spacer().fixed_width(24),
                    Text(
                        f"Created: {definition.created_at.strftime('%Y-%m-%d %H:%M')}"
                    )
                    .text_color("#9ca3af"),
                    Spacer(),
                ).fixed_height(28),

                # Actions
                self._build_action_buttons(definition),

                # Workflow graph
                Text("Workflow Structure:")
                .text_color("#bb9af7")
                .fixed_height(28),

                self._build_workflow_graph(definition),
            )
            .width_policy(SizePolicy.EXPANDING)
            .height_policy(SizePolicy.EXPANDING)
            .bg_color("#1e1f2b")
        )

    def _build_action_buttons(self, definition: WorkflowDefinition) -> Row:
        """Build action buttons row."""
        buttons = [
            Button("View Source")
            .kind(Kind.INFO)
            .fixed_height(36)
            .on_click(lambda _: self._view_source(definition)),
        ]

        # Only show Start Execution button if execution is available
        if self._can_start_execution:
            buttons.append(Spacer().fixed_width(16))
            buttons.append(
                Button("Start Execution")
                .kind(Kind.SUCCESS)
                .fixed_height(36)
                .on_click(
                    lambda _, name=definition.workflow_name: (
                        self._on_start_execution(name)
                        if self._on_start_execution
                        else None
                    )
                )
            )

        buttons.append(Spacer())

        return Row(*buttons).fixed_height(52)

    def _view_source(self, definition: WorkflowDefinition) -> None:
        """Open source code in modal."""
        if definition.source_code:
            self._content_modal.open_source(
                definition.workflow_name,
                definition.source_code,
            )
        elif self._on_view_source:
            self._on_view_source(
                definition.workflow_name,
                definition.source_hash,
            )

    def _build_workflow_graph(self, definition: WorkflowDefinition) -> Column:
        """Build workflow graph from historical execution template."""
        # Get template for this workflow
        template = self._workflow_templates.get(definition.workflow_name, [])

        if not template:
            return (
                Column(
                    Text("No execution history available")
                    .text_color("#6b7280"),
                    Text("(Run the workflow once to see its structure)")
                    .text_color("#4b5563"),
                )
                .width_policy(SizePolicy.EXPANDING)
                .height_policy(SizePolicy.EXPANDING)
                .bg_color("#1a1b26")
            )

        # Build graph from template
        graph = self._graph_builder.build_from_template(
            template_activities=template,
            workflow_name=definition.workflow_name,
        )

        canvas = GraphCanvas(graph, transform=self._canvas_transform)
        canvas.width_policy(SizePolicy.EXPANDING)
        canvas.height_policy(SizePolicy.EXPANDING)

        return canvas
