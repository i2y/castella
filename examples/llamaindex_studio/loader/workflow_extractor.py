"""Workflow extraction for LlamaIndex Workflow Studio.

Extracts workflow structure from LlamaIndex Workflow classes using
type hint introspection.
"""

from __future__ import annotations

import inspect
import textwrap
import types
from types import ModuleType
from typing import Any, Union, get_type_hints, get_args, get_origin


def _is_union_type(type_hint: Any) -> bool:
    """Check if a type hint is a Union type (typing.Union or types.UnionType).

    Python 3.10+ uses types.UnionType for `A | B` syntax.
    """
    origin = get_origin(type_hint)
    if origin is Union:
        return True
    # Python 3.10+ pipe syntax creates types.UnionType
    if isinstance(type_hint, types.UnionType):
        return True
    return False

from ..models.events import EventTypeModel, EventCategory
from ..models.steps import StepModel, InputMode, OutputMode
from ..models.workflow import WorkflowModel, EventEdge


class WorkflowExtractionError(Exception):
    """Raised when workflow extraction fails."""

    pass


def find_workflow_class(module: ModuleType) -> type | None:
    """Find a Workflow class in the module.

    Searches for classes that inherit from llama_index.core.workflow.Workflow.

    Args:
        module: The loaded Python module.

    Returns:
        The Workflow class, or None if not found.
    """
    try:
        from llama_index.core.workflow import Workflow
    except ImportError:
        raise WorkflowExtractionError(
            "llama-index-workflows is not installed. "
            "Install with: pip install llama-index-workflows"
        )

    # Search for Workflow subclasses
    for name in dir(module):
        obj = getattr(module, name)
        if (
            isinstance(obj, type)
            and issubclass(obj, Workflow)
            and obj is not Workflow
            and obj.__module__ == module.__name__
        ):
            return obj

    # Also check common naming patterns
    for attr_name in ["workflow", "MyWorkflow", "Workflow"]:
        if hasattr(module, attr_name):
            obj = getattr(module, attr_name)
            if isinstance(obj, type) and issubclass(obj, Workflow):
                return obj

    return None


def extract_workflow_model(workflow_class: type) -> WorkflowModel:
    """Extract a WorkflowModel from a LlamaIndex Workflow class.

    Args:
        workflow_class: The Workflow class to extract from.

    Returns:
        A WorkflowModel representing the workflow structure.

    Raises:
        WorkflowExtractionError: If extraction fails.
    """
    try:
        from llama_index.core.workflow import Workflow, Event, StartEvent, StopEvent
    except ImportError:
        raise WorkflowExtractionError(
            "llama-index-workflows is not installed."
        )

    if not issubclass(workflow_class, Workflow):
        raise WorkflowExtractionError(
            f"{workflow_class.__name__} is not a Workflow subclass"
        )

    model = WorkflowModel(name=workflow_class.__name__)

    # Extract steps and event types
    steps = _extract_steps(workflow_class)
    model.steps = steps

    # Collect all event types from steps
    event_types = _collect_event_types(steps, workflow_class)
    model.event_types = event_types

    # Determine start and stop event types
    model.start_event_type = _find_start_event_type(steps, event_types)
    model.stop_event_type = _find_stop_event_type(steps, event_types)

    # Build edges based on event flow
    model.edges = _build_edges(model)

    return model


def _extract_steps(workflow_class: type) -> list[StepModel]:
    """Extract step models from workflow class.

    Args:
        workflow_class: The Workflow class.

    Returns:
        List of StepModel instances.
    """
    steps = []

    for name, method in inspect.getmembers(workflow_class, predicate=inspect.isfunction):
        # Skip private methods
        if name.startswith("_"):
            continue

        # Check if it's decorated with @step
        # The @step decorator adds attributes to the function
        if not _is_step_method(method):
            continue

        # Parse type hints for input/output events
        try:
            hints = get_type_hints(method)
        except Exception:
            # Type hint resolution might fail for some complex types
            hints = {}

        input_events, input_mode = _parse_input_events(hints, method)
        output_events, output_mode = _parse_output_events(hints)

        step = StepModel(
            id=name,
            label=_format_step_label(name),
            input_events=input_events,
            input_mode=input_mode,
            output_events=output_events,
            output_mode=output_mode,
            docstring=method.__doc__,
            source_code=_get_source_code(method),
        )
        steps.append(step)

    return steps


def _is_step_method(method: Any) -> bool:
    """Check if a method is decorated with @step.

    The @step decorator from llama_index.core.workflow adds specific
    attributes to the method.
    """
    # Check for step decorator attributes
    if hasattr(method, "__step_config"):
        return True

    # Also check function annotations for Event types
    try:
        hints = get_type_hints(method)
        # A step typically has an 'ev' parameter that's an Event type
        for param_name, param_type in hints.items():
            if param_name in ("ev", "event") or param_name.startswith("ev"):
                if _is_event_type(param_type):
                    return True
    except Exception:
        pass

    return False


def _is_event_type(type_hint: Any) -> bool:
    """Check if a type hint is an Event type."""
    try:
        from llama_index.core.workflow import Event
    except ImportError:
        return False

    # Handle Union types (typing.Union and types.UnionType from Python 3.10+)
    if _is_union_type(type_hint):
        return any(_is_event_type(arg) for arg in get_args(type_hint))

    # Check if it's an Event subclass
    if isinstance(type_hint, type):
        return issubclass(type_hint, Event)

    return False


def _parse_input_events(hints: dict, method: Any) -> tuple[list[str], InputMode]:
    """Parse input event types from type hints.

    Handles three patterns:
    - SINGLE: ev: TypeA
    - UNION: ev: TypeA | TypeB
    - COLLECT: ev1: TypeA, ev2: TypeB
    """
    input_events = []
    input_mode = InputMode.SINGLE

    # Find event parameters
    ev_params = []
    for param_name, param_type in hints.items():
        if param_name in ("self", "ctx", "context", "return"):
            continue
        if _is_event_type(param_type):
            ev_params.append((param_name, param_type))

    if len(ev_params) > 1:
        # Collect pattern: multiple event parameters
        input_mode = InputMode.COLLECT
        for _, param_type in ev_params:
            events = _extract_event_names(param_type)
            input_events.extend(events)
    elif ev_params:
        _, param_type = ev_params[0]
        events = _extract_event_names(param_type)
        input_events = events

        if len(events) > 1:
            input_mode = InputMode.UNION

    return input_events, input_mode


def _parse_output_events(hints: dict) -> tuple[list[str], OutputMode]:
    """Parse output event types from return type hint."""
    output_events = []
    output_mode = OutputMode.SINGLE

    return_type = hints.get("return")
    if return_type is None:
        return output_events, output_mode

    events = _extract_event_names(return_type)
    output_events = events

    if len(events) > 1:
        output_mode = OutputMode.UNION

    return output_events, output_mode


def _extract_event_names(type_hint: Any) -> list[str]:
    """Extract event type names from a type hint."""
    names = []

    # Handle Union types (typing.Union and types.UnionType from Python 3.10+)
    if _is_union_type(type_hint):
        for arg in get_args(type_hint):
            if arg is type(None):
                continue
            names.extend(_extract_event_names(arg))
    elif isinstance(type_hint, type):
        names.append(type_hint.__name__)

    return names


def _collect_event_types(
    steps: list[StepModel], workflow_class: type
) -> dict[str, EventTypeModel]:
    """Collect all event types from steps."""
    try:
        from llama_index.core.workflow import Event, StartEvent, StopEvent
    except ImportError:
        return {}

    event_types = {}

    # Add StartEvent and StopEvent
    event_types["StartEvent"] = EventTypeModel(
        name="StartEvent",
        module="llama_index.core.workflow",
        category=EventCategory.START,
        docstring="Workflow entry event",
    )
    event_types["StopEvent"] = EventTypeModel(
        name="StopEvent",
        module="llama_index.core.workflow",
        category=EventCategory.STOP,
        docstring="Workflow exit event",
    )

    # Collect from steps
    for step in steps:
        for event_name in step.input_events + step.output_events:
            if event_name not in event_types:
                # Try to find the event class
                event_cls = _find_event_class(event_name, workflow_class)
                category = _determine_event_category(event_name, event_cls)

                event_types[event_name] = EventTypeModel(
                    name=event_name,
                    module=event_cls.__module__ if event_cls else "",
                    category=category,
                    fields=_extract_event_fields(event_cls) if event_cls else {},
                    docstring=event_cls.__doc__ if event_cls else None,
                )

    return event_types


def _find_event_class(name: str, workflow_class: type) -> type | None:
    """Find an event class by name."""
    try:
        from llama_index.core.workflow import StartEvent, StopEvent
    except ImportError:
        return None

    if name == "StartEvent":
        return StartEvent
    if name == "StopEvent":
        return StopEvent

    # Search in workflow's module
    module = inspect.getmodule(workflow_class)
    if module and hasattr(module, name):
        return getattr(module, name)

    return None


def _determine_event_category(name: str, event_cls: type | None) -> EventCategory:
    """Determine the event category."""
    try:
        from llama_index.core.workflow import StartEvent, StopEvent
    except ImportError:
        return EventCategory.USER

    if name == "StartEvent" or (event_cls and issubclass(event_cls, StartEvent)):
        return EventCategory.START
    if name == "StopEvent" or (event_cls and issubclass(event_cls, StopEvent)):
        return EventCategory.STOP

    return EventCategory.USER


def _extract_event_fields(event_cls: type) -> dict[str, str]:
    """Extract field definitions from an event class."""
    fields = {}
    try:
        hints = get_type_hints(event_cls)
        for name, type_hint in hints.items():
            if not name.startswith("_"):
                fields[name] = str(type_hint)
    except Exception:
        pass
    return fields


def _find_start_event_type(
    steps: list[StepModel], event_types: dict[str, EventTypeModel]
) -> str:
    """Find the StartEvent type name."""
    for step in steps:
        for event_name in step.input_events:
            if event_name in event_types:
                if event_types[event_name].category == EventCategory.START:
                    return event_name
    return "StartEvent"


def _find_stop_event_type(
    steps: list[StepModel], event_types: dict[str, EventTypeModel]
) -> str:
    """Find the StopEvent type name."""
    for step in steps:
        for event_name in step.output_events:
            if event_name in event_types:
                if event_types[event_name].category == EventCategory.STOP:
                    return event_name
    return "StopEvent"


def _build_edges(model: WorkflowModel) -> list[EventEdge]:
    """Build event flow edges by matching outputs to inputs."""
    edges = []
    edge_id = 0

    for step in model.steps:
        for event_type in step.output_events:
            # Find steps that consume this event type
            consumers = model.get_steps_consuming_event(event_type)

            if not consumers:
                # No consumer - might be StopEvent
                if event_type == model.stop_event_type:
                    edges.append(EventEdge(
                        id=f"edge_{edge_id}",
                        event_type=event_type,
                        source_step_id=step.id,
                        target_step_id=None,  # StopEvent has no target
                        is_part_of_union=step.output_mode == OutputMode.UNION,
                    ))
                    edge_id += 1
                continue

            for consumer in consumers:
                edges.append(EventEdge(
                    id=f"edge_{edge_id}",
                    event_type=event_type,
                    source_step_id=step.id,
                    target_step_id=consumer.id,
                    is_part_of_union=step.output_mode == OutputMode.UNION,
                    is_part_of_collect=consumer.input_mode == InputMode.COLLECT,
                ))
                edge_id += 1

    # Add edges from StartEvent to steps that consume it
    for step in model.steps:
        if model.start_event_type in step.input_events:
            edges.append(EventEdge(
                id=f"edge_{edge_id}",
                event_type=model.start_event_type,
                source_step_id=None,  # StartEvent has no source
                target_step_id=step.id,
            ))
            edge_id += 1

    return edges


def _format_step_label(name: str) -> str:
    """Format a step name for display."""
    # Convert snake_case to Title Case
    return name.replace("_", " ").title()


def _get_source_code(method: Any) -> str | None:
    """Get the source code of a method with normalized indentation."""
    try:
        source = inspect.getsource(method)
        # Remove common leading whitespace from all lines
        return textwrap.dedent(source)
    except (TypeError, OSError):
        return None
