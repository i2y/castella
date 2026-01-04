"""Right panel component with tabs for pydantic-graph Studio."""

from __future__ import annotations

import json

from castella import Button, Column, Component, Kind, Row, SizePolicy, Spacer, State, Text
from castella.markdown import Markdown
from castella.multiline_text import MultilineText

from castella.studio.models.execution import compute_state_diff

from ..models.execution import GraphExecutionState, GraphStepResult
from ..models.graph import PydanticGraphModel


# UI Constants
TAB_BUTTON_WIDTH = 80
HEADER_HEIGHT = 32
SECTION_SPACING = 8
ROW_HEIGHT = 24


class RightPanel(Component):
    """Tabbed right panel for state, node details, and history.

    Tabs:
    - State: Current graph state as JSON
    - Node: Selected node details with source code
    - History: Execution step history
    """

    def __init__(
        self,
        execution: GraphExecutionState,
        graph_model: PydanticGraphModel | None = None,
        selected_node_id: str | None = None,
    ):
        """Initialize the right panel.

        Args:
            execution: Current execution state.
            graph_model: Graph model for node lookups.
            selected_node_id: ID of the selected node (for Node tab).
        """
        super().__init__()

        self._execution = execution
        self._graph_model = graph_model
        self._selected_node_id = selected_node_id

        # Tab state
        self._tab_id = State[str]("state")
        self._tab_id.attach(self)

        # Selected history step
        self._selected_step_idx = State[int | None](None)
        self._selected_step_idx.attach(self)

    def view(self):
        """Build the right panel UI."""
        tab_id = self._tab_id()

        return Column(
            # Tab bar
            self._build_tab_bar(),
            # Tab content
            self._build_tab_content(tab_id),
        )

    def _build_tab_bar(self):
        """Build the tab button bar."""
        tab_id = self._tab_id()

        return Row(
            Spacer().fixed_width(4),
            self._tab_button("state", "State", tab_id),
            Spacer().fixed_width(4),
            self._tab_button("node", "Node", tab_id),
            Spacer().fixed_width(4),
            self._tab_button("history", "History", tab_id),
            Spacer(),
        ).fixed_height(HEADER_HEIGHT)

    def _tab_button(self, id: str, label: str, current_tab: str):
        """Build a single tab button."""
        is_selected = current_tab == id
        kind = Kind.INFO if is_selected else Kind.NORMAL

        return (
            Button(label)
            .kind(kind)
            .fixed_width(TAB_BUTTON_WIDTH)
            .on_click(lambda _: self._tab_id.set(id))
        )

    def _build_tab_content(self, tab_id: str):
        """Build content for the selected tab."""
        if tab_id == "state":
            return self._build_state_tab()
        elif tab_id == "node":
            return self._build_node_tab()
        else:
            return self._build_history_tab()

    # ========== State Tab ==========

    def _build_state_tab(self):
        """Build the state tab content."""
        state = self._execution.current_graph_state
        node_id = self._execution.current_node_id

        # Header with current node
        header = self._section_header(
            f"Current State @ {node_id}" if node_id else "Current State"
        )

        # State content
        if not state:
            return Column(
                header,
                Spacer().fixed_height(SECTION_SPACING),
                self._text_row("No state data"),
            )

        try:
            state_str = json.dumps(state, indent=2, default=str)
        except Exception:
            state_str = str(state)

        # Use MultilineText for JSON display
        json_view = (
            MultilineText(state_str, font_size=12, wrap=False)
            .height_policy(SizePolicy.EXPANDING)
        )

        return Column(
            header,
            Spacer().fixed_height(SECTION_SPACING),
            Row(
                Spacer().fixed_width(SECTION_SPACING),
                json_view,
                Spacer().fixed_width(SECTION_SPACING),
            ),
        )

    # ========== Node Tab ==========

    def _build_node_tab(self):
        """Build the node details tab content."""
        # Use selected node or current executing node
        node_id = self._selected_node_id or self._execution.current_node_id

        if not node_id or not self._graph_model:
            return Column(
                self._section_header("Node Details"),
                Spacer().fixed_height(SECTION_SPACING),
                Row(
                    Spacer().fixed_width(SECTION_SPACING),
                    Text("Click a node to see details"),
                    Spacer(),
                ).fixed_height(ROW_HEIGHT),
            )

        node = self._graph_model.get_node(node_id)
        if not node:
            return Column(
                self._section_header("Node Details"),
                Spacer().fixed_height(SECTION_SPACING),
                Row(
                    Spacer().fixed_width(SECTION_SPACING),
                    Text(f"Node not found: {node_id}"),
                    Spacer(),
                ).fixed_height(ROW_HEIGHT),
            )

        # Check if has breakpoint
        has_breakpoint = node_id in self._execution.breakpoints

        # Get edges
        incoming = self._graph_model.get_edges_to(node_id)
        outgoing = self._graph_model.get_edges_from(node_id)

        # Build content
        content_widgets = [
            # Header
            self._section_header("Node Details"),
            Spacer().fixed_height(SECTION_SPACING),
            # Basic info
            self._info_row("ID:", node.id),
            self._info_row("Label:", node.label),
            self._info_row("Class:", node.node_class_name or "-"),
            self._info_row("Breakpoint:", "Yes" if has_breakpoint else "No"),
        ]

        # Dataclass fields
        if node.fields:
            content_widgets.append(Spacer().fixed_height(SECTION_SPACING))
            content_widgets.append(self._section_header("Fields"))
            for name, type_str in node.fields.items():
                content_widgets.append(self._info_row(f"  {name}:", type_str))

        # Return types
        if node.return_types:
            content_widgets.append(Spacer().fixed_height(SECTION_SPACING))
            content_widgets.append(self._section_header("Return Types"))
            for rt in node.return_types:
                content_widgets.append(self._text_row(f"  -> {rt}"))
            if node.is_end:
                content_widgets.append(self._text_row("  -> End[T]"))

        # Incoming edges
        content_widgets.append(Spacer().fixed_height(SECTION_SPACING))
        content_widgets.append(self._section_header(f"Incoming ({len(incoming)})"))
        for edge in incoming:
            label = f"  <- {edge.source_id}"
            if edge.label:
                label += f" [{edge.label}]"
            content_widgets.append(self._text_row(label))

        # Outgoing edges
        content_widgets.append(Spacer().fixed_height(SECTION_SPACING))
        content_widgets.append(self._section_header(f"Outgoing ({len(outgoing)})"))
        for edge in outgoing:
            label = f"  -> {edge.target_id}"
            if edge.label:
                label += f" [{edge.label}]"
            content_widgets.append(self._text_row(label))

        # Source code
        if node.source_code:
            content_widgets.append(Spacer().fixed_height(SECTION_SPACING))
            content_widgets.append(self._section_header("Source Code"))
            content_widgets.append(Spacer().fixed_height(4))
            # Use Markdown for syntax highlighting
            md_content = f"```python\n{node.source_code}\n```"
            content_widgets.append(
                Row(
                    Spacer().fixed_size(SECTION_SPACING, 1),
                    Markdown(md_content, base_font_size=11),
                    Spacer().fixed_size(SECTION_SPACING, 1),
                ).fit_content_height()
            )

        # Docstring
        if node.docstring:
            content_widgets.append(Spacer().fixed_height(SECTION_SPACING))
            content_widgets.append(self._section_header("Docstring"))
            content_widgets.append(Spacer().fixed_height(4))
            docstring_text = node.docstring[:200] + ("..." if len(node.docstring) > 200 else "")
            content_widgets.append(
                Row(
                    Spacer().fixed_size(SECTION_SPACING, ROW_HEIGHT),
                    Text(docstring_text),
                    Spacer().fixed_size(SECTION_SPACING, ROW_HEIGHT),
                ).fixed_height(ROW_HEIGHT)
            )

        return Column(*content_widgets, scrollable=True)

    def _section_header(self, title: str):
        """Build a section header row."""
        return Row(
            Spacer().fixed_width(SECTION_SPACING),
            Text(title),
            Spacer(),
        ).fixed_height(ROW_HEIGHT)

    def _info_row(self, label: str, value: str):
        """Build an info row with label and value."""
        return Row(
            Spacer().fixed_width(SECTION_SPACING),
            Text(label).fixed_width(90),
            Text(value),
            Spacer(),
        ).fixed_height(ROW_HEIGHT)

    def _text_row(self, text: str):
        """Build a simple text row."""
        return Row(
            Spacer().fixed_width(SECTION_SPACING),
            Text(text),
            Spacer(),
        ).fixed_height(20)

    # ========== History Tab ==========

    def _build_history_tab(self):
        """Build the execution history tab content."""
        history = self._execution.step_history
        selected_idx = self._selected_step_idx()

        header = self._section_header(f"Execution History ({len(history)} steps)")

        if not history:
            return Column(
                header,
                Spacer().fixed_height(SECTION_SPACING),
                Row(
                    Spacer().fixed_width(SECTION_SPACING),
                    Text("No execution history yet"),
                    Spacer(),
                ).fixed_height(ROW_HEIGHT),
            )

        # Build step list
        step_widgets = []
        for i, step in enumerate(history):
            is_selected = selected_idx == i
            step_widgets.append(self._build_step_row(i, step, is_selected))

        # Step list with limited height
        step_list = Column(*step_widgets, scrollable=True).fixed_height(
            min(len(history) * 28, 150)
        )

        # Detail view for selected step
        if selected_idx is not None and selected_idx < len(history):
            detail = self._build_step_detail(history[selected_idx])
        else:
            detail = Text("Select a step to see details").fixed_height(ROW_HEIGHT)

        return Column(
            header,
            step_list,
            Spacer().fixed_height(SECTION_SPACING),
            detail,
        )

    def _build_step_row(self, idx: int, step: GraphStepResult, is_selected: bool):
        """Build a single step row in history list."""
        kind = Kind.INFO if is_selected else Kind.NORMAL

        label = f"{idx + 1}. {step.node_id} ({step.duration_ms:.1f}ms)"
        if step.is_end:
            label += " [End]"

        return (
            Button(label)
            .kind(kind)
            .fixed_height(28)
            .on_click(lambda _, i=idx: self._selected_step_idx.set(i))
        )

    def _build_step_detail(self, step: GraphStepResult):
        """Build detail view for selected step."""
        widgets = [
            Spacer().fixed_height(SECTION_SPACING),
            self._section_header(f"Step: {step.node_id}"),
            self._info_row("Duration:", f"{step.duration_ms:.2f}ms"),
            self._info_row("Class:", step.node_class),
            self._info_row("Returned:", step.returned_type or "-"),
            self._info_row("Is End:", "Yes" if step.is_end else "No"),
        ]

        # Error display
        if step.error:
            widgets.append(self._info_row("Error:", step.error[:50]))

        # Node data (dataclass fields)
        if step.node_data:
            widgets.append(Spacer().fixed_height(SECTION_SPACING))
            widgets.append(self._section_header("Node Data"))
            try:
                data_str = json.dumps(step.node_data, indent=2, default=str)
            except Exception:
                data_str = str(step.node_data)[:200]
            data_view = MultilineText(data_str, font_size=11, wrap=False).fixed_height(60)
            widgets.append(
                Row(
                    Spacer().fixed_width(SECTION_SPACING),
                    data_view,
                    Spacer().fixed_width(SECTION_SPACING),
                ).fixed_height(60)
            )

        # State Before section
        widgets.append(Spacer().fixed_height(SECTION_SPACING))
        widgets.append(self._section_header("State Before"))
        try:
            before_str = json.dumps(step.state_before, indent=2, default=str)
        except Exception:
            before_str = str(step.state_before)[:200]
        before_view = MultilineText(before_str, font_size=11, wrap=False).fixed_height(80)
        widgets.append(
            Row(
                Spacer().fixed_width(SECTION_SPACING),
                before_view,
                Spacer().fixed_width(SECTION_SPACING),
            ).fixed_height(80)
        )

        # Changes section
        widgets.append(Spacer().fixed_height(SECTION_SPACING))
        widgets.append(self._section_header("Changes"))
        diff = compute_state_diff(step.state_before, step.state_after)
        output_lines = []
        if diff["added"]:
            for k, v in diff["added"].items():
                val_str = json.dumps(v, default=str)[:60]
                output_lines.append(f"+ {k}: {val_str}")
        if diff["modified"]:
            for k, v in diff["modified"].items():
                new_val = json.dumps(v["new"], default=str)[:40]
                output_lines.append(f"~ {k}: -> {new_val}")
        if diff["removed"]:
            for k in diff["removed"]:
                output_lines.append(f"- {k}")
        if not output_lines:
            output_lines.append("(no changes)")
        output_str = "\n".join(output_lines)
        output_view = MultilineText(output_str, font_size=11, wrap=False).fixed_height(60)
        widgets.append(
            Row(
                Spacer().fixed_width(SECTION_SPACING),
                output_view,
                Spacer().fixed_width(SECTION_SPACING),
            ).fixed_height(60)
        )

        return Column(*widgets, scrollable=True)
