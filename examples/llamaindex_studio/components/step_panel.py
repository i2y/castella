"""Step panel for LlamaIndex Workflow Studio.

Displays step details including signature, docstring, and source code.
"""

from __future__ import annotations

from castella import Component, Column, Row, Text, Spacer, Button, SizePolicy
from castella.markdown import Markdown

from ..models.steps import StepModel, InputMode, OutputMode
from ..models.execution import StepExecution


# UI Constants
HEADER_HEIGHT = 28
SECTION_HEADER_HEIGHT = 24


class StepPanel(Component):
    """Panel displaying details of a selected step.

    Shows:
    - Step name and label
    - Input event signature
    - Output event signature
    - Docstring (if present)
    - Source code (if available)
    """

    def __init__(
        self,
        step: StepModel | None = None,
        execution: StepExecution | None = None,
    ):
        """Initialize the step panel.

        Args:
            step: The step model to display.
            execution: Most recent execution of this step (optional).
        """
        super().__init__()

        self._step = step
        self._execution = execution

    def view(self):
        """Build the step panel UI."""
        if self._step is None:
            return Column(
                Spacer().fixed_height(8),
                Row(
                    Spacer().fixed_width(12),
                    Text("Select a step to view details").text_color("#6b7280"),
                    Spacer(),
                ),
                Spacer(),
            )

        step = self._step

        rows = [
            # Header with step name
            self._build_header(step),
            Spacer().fixed_height(8),

            # Input signature
            self._build_signature_section("Input", step.get_input_signature()),

            # Output signature
            self._build_signature_section("Output", step.get_output_signature()),

            Spacer().fixed_height(8),
        ]

        # Docstring
        if step.docstring:
            rows.append(self._build_docstring_section(step.docstring))
            rows.append(Spacer().fixed_height(8))

        # Execution info if available
        if self._execution:
            rows.append(self._build_execution_section(self._execution))
            rows.append(Spacer().fixed_height(8))

        # Source code
        if step.source_code:
            rows.append(self._build_source_section(step.source_code))

        return Column(*rows, scrollable=True)

    def _build_header(self, step: StepModel) -> Row:
        """Build the header with step name."""
        return Row(
            Spacer().fixed_width(8),
            Text(step.label).text_color("#3b82f6"),
            Spacer().fixed_width(8),
            Text(f"({step.id})").text_color("#6b7280"),
            Spacer(),
        ).fixed_height(HEADER_HEIGHT)

    def _build_signature_section(self, label: str, signature: str) -> Row:
        """Build a signature display row."""
        return Row(
            Spacer().fixed_width(12),
            Text(f"{label}:").fixed_width(60).text_color("#9ca3af"),
            Text(signature).text_color("#f59e0b"),
            Spacer(),
        ).fixed_height(SECTION_HEADER_HEIGHT)

    def _build_docstring_section(self, docstring: str) -> Column:
        """Build the docstring section."""
        return Column(
            Row(
                Spacer().fixed_width(8),
                Text("Description").text_color("#9ca3af"),
                Spacer(),
            ).fixed_height(SECTION_HEADER_HEIGHT),
            Row(
                Spacer().fixed_width(12),
                Text(docstring.strip()).text_color("#e5e7eb"),
                Spacer().fixed_width(8),
            ),
        )

    def _build_execution_section(self, execution: StepExecution) -> Column:
        """Build the execution info section."""
        duration = f"{execution.duration_ms:.2f}ms"

        return Column(
            Row(
                Spacer().fixed_width(8),
                Text("Last Execution").text_color("#9ca3af"),
                Spacer(),
            ).fixed_height(SECTION_HEADER_HEIGHT),
            Row(
                Spacer().fixed_width(12),
                Text(f"Duration: {duration}").text_color("#22c55e"),
                Spacer(),
            ).fixed_height(20),
            Row(
                Spacer().fixed_width(12),
                Text(f"Input: {execution.input_event_type}").text_color("#3b82f6"),
                Spacer(),
            ).fixed_height(20) if execution.input_event_type else Spacer().fixed_height(0),
            Row(
                Spacer().fixed_width(12),
                Text(f"Output: {execution.output_event_type or 'None'}").text_color("#22c55e"),
                Spacer(),
            ).fixed_height(20) if execution.output_event_type else Spacer().fixed_height(0),
        )

    def _build_source_section(self, source_code: str) -> Column:
        """Build the source code section."""
        # Wrap in markdown code block for syntax highlighting
        md_content = f"```python\n{source_code}\n```"

        return Column(
            Row(
                Spacer().fixed_width(8),
                Text("Source Code").text_color("#9ca3af"),
                Spacer(),
            ).fixed_height(SECTION_HEADER_HEIGHT),
            Row(
                Spacer().fixed_width(8),
                Markdown(md_content, base_font_size=11),
                Spacer().fixed_width(8),
            ),
        )


class StepListPanel(Component):
    """Panel showing list of all steps in the workflow.

    Shows step names with execution status indicators.
    """

    def __init__(
        self,
        steps: list[StepModel] | None = None,
        active_step_ids: set[str] | None = None,
        selected_step_id: str | None = None,
        on_step_select: callable | None = None,
    ):
        """Initialize the step list panel.

        Args:
            steps: List of step models.
            active_step_ids: Set of currently executing step IDs.
            selected_step_id: Currently selected step ID.
            on_step_select: Callback when a step is clicked.
        """
        super().__init__()

        self._steps = steps or []
        self._active_step_ids = active_step_ids or set()
        self._selected_step_id = selected_step_id
        self._on_step_select = on_step_select

    def view(self):
        """Build the step list panel UI."""
        rows = []

        # Header
        rows.append(
            Row(
                Spacer().fixed_width(8),
                Text("Steps").fixed_height(HEADER_HEIGHT),
                Spacer(),
            ).fixed_height(HEADER_HEIGHT)
        )

        # Step rows
        for step in self._steps:
            rows.append(self._build_step_row(step))

        return Column(*rows, scrollable=True)

    def _build_step_row(self, step: StepModel) -> Row:
        """Build a row for a step.

        Args:
            step: Step model.

        Returns:
            Row widget.
        """
        is_active = step.id in self._active_step_ids
        is_selected = step.id == self._selected_step_id

        # Status indicator
        if is_active:
            symbol = "⚡"
        else:
            symbol = "○"

        # Build button styled as text
        display_text = f"{symbol}  {step.label}"

        if self._on_step_select:
            btn = (
                Button(display_text)
                .on_click(lambda _, sid=step.id: self._on_step_select(sid))
                .fixed_height(SECTION_HEADER_HEIGHT)
                .width_policy(SizePolicy.EXPANDING)
            )
        else:
            btn = (
                Button(display_text)
                .fixed_height(SECTION_HEADER_HEIGHT)
                .width_policy(SizePolicy.EXPANDING)
            )

        return Row(
            Spacer().fixed_width(8),
            btn,
            Spacer().fixed_width(8),
        ).fixed_height(SECTION_HEADER_HEIGHT)
