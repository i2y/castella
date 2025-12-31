"""MCP tool handlers for Castella UI interaction."""

from __future__ import annotations

import threading
from concurrent.futures import Future
from typing import TYPE_CHECKING, Any

from castella.models.geometry import Point
from castella.models.events import MouseEvent, WheelEvent

from .types import ActionResult

if TYPE_CHECKING:
    from castella.core import App
    from .registry import SemanticWidgetRegistry
    from .introspection import WidgetIntrospector


class UIOperationExecutor:
    """Executes UI operations on the main thread.

    MCP tools run in a background thread, but UI operations must be
    performed on the main thread. This class queues operations and
    executes them safely.
    """

    def __init__(self, app: "App") -> None:
        self._app = app
        self._pending_operations: list[tuple[callable, Future]] = []
        self._lock = threading.Lock()

    def execute(self, operation: callable) -> Any:
        """Execute an operation on the main thread and return the result.

        This method blocks until the operation completes.
        """
        future: Future = Future()

        with self._lock:
            self._pending_operations.append((operation, future))

        # Signal the main thread to process pending operations
        self._signal_main_thread()

        # Wait for the result
        return future.result(timeout=5.0)

    def execute_async(self, operation: callable) -> None:
        """Execute an operation on the main thread without waiting."""
        with self._lock:
            self._pending_operations.append((operation, None))

        self._signal_main_thread()

    def process_pending(self) -> None:
        """Process all pending operations. Call from main thread."""
        with self._lock:
            operations = self._pending_operations.copy()
            self._pending_operations.clear()

        for operation, future in operations:
            try:
                result = operation()
                if future is not None:
                    future.set_result(result)
            except Exception as e:
                if future is not None:
                    future.set_exception(e)

    def _signal_main_thread(self) -> None:
        """Signal the main thread to process operations."""
        # Use the frame's update mechanism to wake up the main thread
        from castella.models.events import UpdateEvent

        # Create a dummy update event
        self._app._frame.post_update(UpdateEvent(target=self._app, completely=False))


def click_element(
    element_id: str,
    registry: "SemanticWidgetRegistry",
    app: "App",
) -> ActionResult:
    """Click/tap an element to trigger its action."""
    widget = registry.get_widget(element_id)
    if widget is None:
        return ActionResult(
            success=False,
            message=f"Element not found: {element_id}",
            element_id=element_id,
        )

    # Simulate mouse down/up at widget center
    center = Point(x=widget._size.width / 2, y=widget._size.height / 2)
    ev = MouseEvent(pos=center)

    try:
        widget.mouse_down(ev)
        widget.mouse_up(ev)
        widget.update()

        return ActionResult(
            success=True,
            message=f"Clicked {element_id}",
            element_id=element_id,
        )
    except Exception as e:
        return ActionResult(
            success=False,
            message=f"Click failed: {str(e)}",
            element_id=element_id,
        )


def type_text(
    element_id: str,
    text: str,
    replace: bool,
    registry: "SemanticWidgetRegistry",
    app: "App",
) -> ActionResult:
    """Type text into an input field."""
    widget = registry.get_widget(element_id)
    if widget is None:
        return ActionResult(
            success=False,
            message=f"Element not found: {element_id}",
            element_id=element_id,
        )

    widget_type = type(widget).__name__

    # Check if it's an input widget
    if widget_type not in ("Input", "MultilineInput"):
        return ActionResult(
            success=False,
            message=f"Element is not an input field: {widget_type}",
            element_id=element_id,
        )

    try:
        # Focus the widget
        if app._focused != widget:
            if app._focused is not None:
                app._focused.unfocused()
            app._focused = widget
            widget.focused()

        state = getattr(widget, "_state", None)
        if state is None:
            return ActionResult(
                success=False,
                message="Widget has no state",
                element_id=element_id,
            )

        if widget_type == "Input":
            if replace:
                # Clear existing text and set new
                state.set(text)
            else:
                # Append to existing
                current = getattr(state, "_text", "")
                state.set(current + text)

            # Trigger on_change callback to simulate user input
            # This updates A2UI data model so values persist across rebuilds
            callback = getattr(widget, "_callback", None)
            if callback is not None:
                callback(state._text)

        elif widget_type == "MultilineInput":
            if replace:
                state.set_text(text)
            else:
                current = state.get_text()
                state.set_text(current + text)

            # Trigger on_change callback
            callback = getattr(widget, "_on_change", None)
            if callback is not None:
                callback(state.get_text())

        widget.update()

        return ActionResult(
            success=True,
            message=f"Typed text into {element_id}",
            element_id=element_id,
            new_value=text if replace else None,
        )
    except Exception as e:
        return ActionResult(
            success=False,
            message=f"Type failed: {str(e)}",
            element_id=element_id,
        )


def focus_element(
    element_id: str,
    registry: "SemanticWidgetRegistry",
    app: "App",
) -> ActionResult:
    """Set focus to an element."""
    widget = registry.get_widget(element_id)
    if widget is None:
        return ActionResult(
            success=False,
            message=f"Element not found: {element_id}",
            element_id=element_id,
        )

    try:
        # Unfocus current
        if app._focused is not None and app._focused != widget:
            app._focused.unfocused()

        app._focused = widget
        widget.focused()
        widget.update()

        return ActionResult(
            success=True,
            message=f"Focused {element_id}",
            element_id=element_id,
        )
    except Exception as e:
        return ActionResult(
            success=False,
            message=f"Focus failed: {str(e)}",
            element_id=element_id,
        )


def scroll_element(
    element_id: str,
    direction: str,
    amount: int,
    registry: "SemanticWidgetRegistry",
    app: "App",
) -> ActionResult:
    """Scroll a scrollable container."""
    widget = registry.get_widget(element_id)
    if widget is None:
        return ActionResult(
            success=False,
            message=f"Element not found: {element_id}",
            element_id=element_id,
        )

    if not widget.is_scrollable():
        return ActionResult(
            success=False,
            message=f"Element is not scrollable: {element_id}",
            element_id=element_id,
        )

    try:
        # Calculate scroll delta based on direction
        dx, dy = 0.0, 0.0
        if direction == "up":
            dy = -amount
        elif direction == "down":
            dy = amount
        elif direction == "left":
            dx = -amount
        elif direction == "right":
            dx = amount
        else:
            return ActionResult(
                success=False,
                message=f"Invalid direction: {direction}. Use up/down/left/right.",
                element_id=element_id,
            )

        # Create wheel event
        center = Point(x=widget._size.width / 2, y=widget._size.height / 2)
        ev = WheelEvent(pos=center, dx=dx, dy=dy)
        widget.mouse_wheel(ev)
        widget.update()

        return ActionResult(
            success=True,
            message=f"Scrolled {direction} by {amount}",
            element_id=element_id,
        )
    except Exception as e:
        return ActionResult(
            success=False,
            message=f"Scroll failed: {str(e)}",
            element_id=element_id,
        )


def toggle_element(
    element_id: str,
    registry: "SemanticWidgetRegistry",
    app: "App",
) -> ActionResult:
    """Toggle a checkbox or switch."""
    widget = registry.get_widget(element_id)
    if widget is None:
        return ActionResult(
            success=False,
            message=f"Element not found: {element_id}",
            element_id=element_id,
        )

    widget_type = type(widget).__name__

    if widget_type not in ("CheckBox", "Switch"):
        return ActionResult(
            success=False,
            message=f"Element is not a checkbox or switch: {widget_type}",
            element_id=element_id,
        )

    try:
        state = getattr(widget, "_state", None)
        if state is None:
            return ActionResult(
                success=False,
                message="Widget has no state",
                element_id=element_id,
            )

        # Toggle the boolean state
        current = state()  # State[bool] is callable
        state.set(not current)

        # Trigger on_change callback to simulate user input
        callback = getattr(widget, "_on_change", None)
        if callback is not None:
            callback(not current)

        widget.update()

        return ActionResult(
            success=True,
            message=f"Toggled {element_id}",
            element_id=element_id,
            new_value=not current,
        )
    except Exception as e:
        return ActionResult(
            success=False,
            message=f"Toggle failed: {str(e)}",
            element_id=element_id,
        )


def select_value(
    element_id: str,
    value: str,
    registry: "SemanticWidgetRegistry",
    app: "App",
) -> ActionResult:
    """Select a value in a picker, dropdown, or radio buttons."""
    widget = registry.get_widget(element_id)
    if widget is None:
        return ActionResult(
            success=False,
            message=f"Element not found: {element_id}",
            element_id=element_id,
        )

    widget_type = type(widget).__name__

    try:
        if widget_type == "RadioButtons":
            state = getattr(widget, "_state", None)
            if state is not None:
                state.set(value)
                callback = getattr(widget, "_on_change", None)
                if callback is not None:
                    callback(value)

        elif widget_type == "Tabs":
            state = getattr(widget, "_state", None)
            if state is not None and hasattr(state, "select"):
                state.select(value)
                callback = getattr(widget, "_on_change", None)
                if callback is not None:
                    callback(value)

        else:
            return ActionResult(
                success=False,
                message=f"Element does not support selection: {widget_type}",
                element_id=element_id,
            )

        widget.update()

        return ActionResult(
            success=True,
            message=f"Selected '{value}' in {element_id}",
            element_id=element_id,
            new_value=value,
        )
    except Exception as e:
        return ActionResult(
            success=False,
            message=f"Select failed: {str(e)}",
            element_id=element_id,
        )


def list_actionable_elements(
    registry: "SemanticWidgetRegistry",
    introspector: "WidgetIntrospector",
    app: "App",
) -> list[dict[str, Any]]:
    """Get all elements that can be interacted with."""
    root = app._root_widget
    if root is None:
        return []

    # Rebuild registry
    registry.rebuild_from_tree(root)

    # Get interactive elements
    elements = introspector.get_interactive_elements(root, app)
    return [
        {
            "id": e.id,
            "type": e.type,
            "label": e.label,
            "interactive": e.interactive,
        }
        for e in elements
    ]


def send_a2ui_message(
    message: dict[str, Any],
    a2ui_renderer: Any,
    registry: "SemanticWidgetRegistry",
) -> ActionResult:
    """Send an A2UI message to render or update UI.

    Supports A2UI message types:
    - createSurface: Create a new A2UI surface
    - updateComponents: Update components in a surface
    - updateDataModel: Update data bindings
    - deleteSurface: Remove a surface
    """
    if a2ui_renderer is None:
        return ActionResult(
            success=False,
            message="A2UI renderer not configured",
        )

    try:
        surface = a2ui_renderer.handle_message(message)

        if surface is not None:
            # Register the new/updated surface widgets
            registry.register_a2ui_surface(surface)

            return ActionResult(
                success=True,
                message=f"A2UI message processed, surface: {surface.surface_id}",
                new_value=surface.surface_id,
            )

        return ActionResult(
            success=True,
            message="A2UI message processed",
        )
    except Exception as e:
        return ActionResult(
            success=False,
            message=f"A2UI message failed: {str(e)}",
        )


def register_tools(
    mcp: Any,
    app: "App",
    registry: "SemanticWidgetRegistry",
    introspector: "WidgetIntrospector",
    a2ui_renderer: Any = None,
) -> None:
    """Register all UI tools with the MCP server.

    Args:
        mcp: FastMCP server instance
        app: Castella App instance
        registry: SemanticWidgetRegistry instance
        introspector: WidgetIntrospector instance
        a2ui_renderer: Optional A2UIRenderer for bidirectional A2UI support
    """

    @mcp.tool()
    def click(element_id: str) -> dict[str, Any]:
        """Click/tap an element to trigger its action.

        Args:
            element_id: The semantic ID of the element to click

        Returns:
            Result with success status
        """
        result = click_element(element_id, registry, app)
        return result.model_dump()

    @mcp.tool()
    def type_text_tool(
        element_id: str,
        text: str,
        replace: bool = False,
    ) -> dict[str, Any]:
        """Type text into an input field.

        Args:
            element_id: The input element's semantic ID
            text: The text to type
            replace: If True, replace existing text; if False, append

        Returns:
            Result with success status
        """
        result = type_text(element_id, text, replace, registry, app)
        return result.model_dump()

    @mcp.tool()
    def focus(element_id: str) -> dict[str, Any]:
        """Set focus to an element.

        Args:
            element_id: The element's semantic ID

        Returns:
            Result with success status
        """
        result = focus_element(element_id, registry, app)
        return result.model_dump()

    @mcp.tool()
    def scroll(
        element_id: str,
        direction: str,
        amount: int = 100,
    ) -> dict[str, Any]:
        """Scroll a scrollable container.

        Args:
            element_id: The scrollable element's semantic ID
            direction: Direction to scroll (up/down/left/right)
            amount: Pixels to scroll (default 100)

        Returns:
            Result with success status
        """
        result = scroll_element(element_id, direction, amount, registry, app)
        return result.model_dump()

    @mcp.tool()
    def toggle(element_id: str) -> dict[str, Any]:
        """Toggle a checkbox or switch.

        Args:
            element_id: The checkbox/switch element's semantic ID

        Returns:
            Result with success status and new value
        """
        result = toggle_element(element_id, registry, app)
        return result.model_dump()

    @mcp.tool()
    def select(element_id: str, value: str) -> dict[str, Any]:
        """Select a value in a picker, dropdown, tabs, or radio buttons.

        Args:
            element_id: The picker element's semantic ID
            value: The value to select

        Returns:
            Result with success status
        """
        result = select_value(element_id, value, registry, app)
        return result.model_dump()

    @mcp.tool()
    def list_actionable() -> list[dict[str, Any]]:
        """Get all elements that can be interacted with.

        Returns a list of interactive elements with their IDs, types,
        and labels.
        """
        return list_actionable_elements(registry, introspector, app)

    # Only register A2UI tool if renderer is provided
    if a2ui_renderer is not None:

        @mcp.tool()
        def send_a2ui(message: dict[str, Any]) -> dict[str, Any]:
            """Send an A2UI message to render or update UI.

            Supports A2UI message types:
            - createSurface: Create a new A2UI surface
            - updateComponents: Update components in a surface
            - updateDataModel: Update data bindings
            - deleteSurface: Remove a surface

            Args:
                message: A2UI protocol message

            Returns:
                Result with success status
            """
            result = send_a2ui_message(message, a2ui_renderer, registry)
            return result.model_dump()
