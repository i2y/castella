"""Start execution modal widget for Edda Workflow Manager."""

from __future__ import annotations

import json
from typing import Callable

from castella import Column, Row, Spacer, Button, Text, Kind, SizePolicy
from castella.modal import Modal, ModalState
from castella.multiline_input import MultilineInput, MultilineInputState
from castella.multiline_text import MultilineText


class StartExecutionModal:
    """Modal dialog for starting a workflow execution.

    Usage:
        modal = StartExecutionModal(on_execute=..., on_close=...)
        modal.open("order_workflow", can_direct=True, can_cloudevent=False)

        # In view():
        if modal.is_open:
            return Box(main_content, modal.build())
    """

    def __init__(
        self,
        on_execute: Callable[[str, dict, bool], None] | None = None,
        on_close: Callable[[], None] | None = None,
    ):
        """Initialize start execution modal.

        Args:
            on_execute: Callback to execute workflow (workflow_name, params, use_direct).
            on_close: Callback to close modal.
        """
        self._modal_state = ModalState()
        self._on_execute = on_execute
        self._on_close = on_close

        # Current workflow info
        self._workflow_name: str = ""
        self._can_direct: bool = False
        self._can_cloudevent: bool = False
        self._use_direct: bool = False
        self._message: str | None = None

        # Parameter input state
        self._params_text = MultilineInputState("{}")

    @property
    def state(self) -> ModalState:
        """Get the modal state for attaching to component."""
        return self._modal_state

    @property
    def is_open(self) -> bool:
        """Check if the modal is open."""
        return self._modal_state.is_open()

    def attach(self, component) -> None:
        """Attach modal state to a component for reactivity."""
        self._modal_state.attach(component)

    def open(
        self,
        workflow_name: str,
        can_direct: bool = False,
        can_cloudevent: bool = False,
    ) -> None:
        """Open the modal for a workflow.

        Args:
            workflow_name: Name of the workflow to start.
            can_direct: Whether direct execution is available.
            can_cloudevent: Whether CloudEvent execution is available.
        """
        self._workflow_name = workflow_name
        self._can_direct = can_direct
        self._can_cloudevent = can_cloudevent
        self._use_direct = can_direct  # Default to direct if available
        self._message = None
        self._params_text = MultilineInputState("{}")
        self._modal_state.open()

    def close(self) -> None:
        """Close the modal."""
        self._modal_state.close()
        self._workflow_name = ""
        self._message = None
        if self._on_close:
            self._on_close()

    def set_message(self, message: str | None) -> None:
        """Set status message and trigger UI update."""
        self._message = message
        # Notify observers to trigger UI rebuild
        self._modal_state.notify()

    def build(self) -> Modal:
        """Build the modal widget."""
        content_items = [
            # Parameters label
            Text("Parameters (JSON):").text_color("#9ca3af").fixed_height(28),

            # Parameters input
            MultilineInput(self._params_text, font_size=12)
            .fixed_height(120)
            .bg_color("#1a1b26"),
        ]

        # Execution mode info
        if self._can_direct and self._can_cloudevent:
            content_items.append(
                Text("Mode: Direct execution (in-process)")
                .text_color("#9ece6a")
                .fixed_height(28)
            )
        elif self._can_direct:
            content_items.append(
                Text("Mode: Direct execution (in-process)")
                .text_color("#9ece6a")
                .fixed_height(28)
            )
        elif self._can_cloudevent:
            content_items.append(
                Text("Mode: CloudEvent (to Edda server)")
                .text_color("#7aa2f7")
                .fixed_height(28)
            )

        # Message if any
        if self._message:
            color = "#9ece6a" if self._message.startswith("✓") else "#f7768e"
            content_items.append(
                MultilineText(self._message, font_size=12, wrap=True)
                .text_color(color)
                .fixed_height(60)
                .bg_color("#1a1b26")
            )

        # Buttons
        content_items.append(Spacer().fixed_height(8))
        content_items.append(
            Row(
                Spacer(),
                Button("Cancel")
                .kind(Kind.NORMAL)
                .fixed_height(36)
                .on_click(lambda _: self.close()),
                Spacer().fixed_width(16),
                Button("Start")
                .kind(Kind.SUCCESS)
                .fixed_height(36)
                .on_click(lambda _: self._on_start()),
            ).fixed_height(48)
        )

        modal_content = Column(*content_items)

        # Adjust height based on whether message is shown
        height = 420 if self._message else 350

        return Modal(
            content=modal_content,
            state=self._modal_state,
            title=f"Start Workflow: {self._workflow_name}",
            width=500,
            height=height,
        ).on_close(self.close)

    def _on_start(self) -> None:
        """Handle start button click."""
        if not self._on_execute:
            return

        # Parse parameters
        try:
            params_text = self._params_text.value()
            params = json.loads(params_text) if params_text.strip() else {}
        except json.JSONDecodeError as e:
            self._message = f"✗ Invalid JSON: {e}"
            return

        self._on_execute(self._workflow_name, params, self._use_direct)
