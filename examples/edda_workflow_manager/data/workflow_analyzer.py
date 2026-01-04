"""Workflow static analyzer for LlamaIndex Workflow.

Parses workflow source code to extract step definitions and event flow.
Supports both:
1. LlamaIndex Workflow classes with @step decorators
2. Edda @workflow functions that use DurableWorkflowRunner
"""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass, field
from typing import Any


@dataclass
class StepInfo:
    """Information about a workflow step."""

    name: str
    input_events: list[str] = field(default_factory=list)
    output_events: list[str] = field(default_factory=list)
    docstring: str | None = None
    lineno: int = 0


@dataclass
class WorkflowStructure:
    """Parsed workflow structure."""

    workflow_name: str
    steps: list[StepInfo] = field(default_factory=list)
    start_event: str = "StartEvent"
    stop_event: str = "StopEvent"

    def get_graph_edges(self) -> list[tuple[str, str]]:
        """Build edges from event flow.

        Returns:
            List of (source_step, target_step) tuples.
        """
        # Build map: event -> steps that produce it
        event_producers: dict[str, list[str]] = {}
        for step in self.steps:
            for event in step.output_events:
                if event not in event_producers:
                    event_producers[event] = []
                event_producers[event].append(step.name)

        # Build map: event -> steps that consume it
        event_consumers: dict[str, list[str]] = {}
        for step in self.steps:
            for event in step.input_events:
                if event not in event_consumers:
                    event_consumers[event] = []
                event_consumers[event].append(step.name)

        # Build edges: producer -> consumer for each event
        edges: list[tuple[str, str]] = []
        seen_edges: set[tuple[str, str]] = set()

        for event, producers in event_producers.items():
            consumers = event_consumers.get(event, [])
            for producer in producers:
                for consumer in consumers:
                    edge = (producer, consumer)
                    if edge not in seen_edges:
                        seen_edges.add(edge)
                        edges.append(edge)

        return edges


class WorkflowAnalyzer:
    """Analyzes LlamaIndex Workflow source code to extract structure.

    Handles two patterns:
    1. Direct LlamaIndex Workflow classes with @step methods
    2. Edda @workflow functions that use DurableWorkflowRunner
       (analyzes the underlying Workflow class in the same module)
    """

    def analyze(self, source_code: str, workflow_name: str = "") -> WorkflowStructure:
        """Analyze workflow source code.

        Args:
            source_code: Python source code of the workflow.
            workflow_name: Optional workflow name override.

        Returns:
            WorkflowStructure with steps and event flow.
        """
        structure = WorkflowStructure(workflow_name=workflow_name)

        try:
            tree = ast.parse(source_code)
        except SyntaxError:
            return structure

        # Find all Workflow classes (there may be multiple in the file)
        workflow_classes: list[ast.ClassDef] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # Check if it inherits from Workflow
                for base in node.bases:
                    base_name = self._get_name(base)
                    if base_name in ("Workflow", "DurableWorkflow"):
                        workflow_classes.append(node)
                        break

        # Analyze each workflow class
        for class_node in workflow_classes:
            self._analyze_class(class_node, structure)

        # If we found steps from a class, use the class name as workflow name
        if structure.steps and not workflow_name and workflow_classes:
            structure.workflow_name = workflow_classes[0].name

        return structure

    def _analyze_class(self, class_node: ast.ClassDef, structure: WorkflowStructure) -> None:
        """Analyze a workflow class for step methods."""
        for node in class_node.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                step_info = self._analyze_method(node)
                if step_info:
                    structure.steps.append(step_info)

    def _analyze_method(self, func_node: ast.FunctionDef | ast.AsyncFunctionDef) -> StepInfo | None:
        """Analyze a method for @step decorator and event types."""
        # Check for @step decorator
        is_step = False
        for decorator in func_node.decorator_list:
            decorator_name = self._get_name(decorator)
            if decorator_name == "step":
                is_step = True
                break

        if not is_step:
            return None

        step = StepInfo(
            name=func_node.name,
            lineno=func_node.lineno,
        )

        # Get docstring
        if (func_node.body
            and isinstance(func_node.body[0], ast.Expr)
            and isinstance(func_node.body[0].value, ast.Constant)
            and isinstance(func_node.body[0].value.value, str)):
            step.docstring = func_node.body[0].value.value

        # Analyze parameters for input event type
        for arg in func_node.args.args:
            if arg.arg == "self":
                continue
            if arg.annotation:
                event_type = self._get_event_type(arg.annotation)
                if event_type:
                    step.input_events.append(event_type)

        # Analyze return type for output event types
        if func_node.returns:
            output_types = self._get_output_event_types(func_node.returns)
            step.output_events.extend(output_types)

        return step

    def _get_event_type(self, annotation: ast.expr) -> str | None:
        """Extract event type name from annotation."""
        name = self._get_name(annotation)
        if name:
            # Skip Context and other non-event types
            if name in ("Context", "str", "int", "float", "bool", "dict", "list", "None"):
                return None
            return name
        return None

    def _get_output_event_types(self, returns: ast.expr) -> list[str]:
        """Extract output event types from return annotation.

        Handles:
        - Simple: SomeEvent
        - Union: SomeEvent | OtherEvent
        - Multiple: Union[SomeEvent, OtherEvent]
        """
        types: list[str] = []

        if isinstance(returns, ast.BinOp) and isinstance(returns.op, ast.BitOr):
            # Handle SomeEvent | OtherEvent
            types.extend(self._get_output_event_types(returns.left))
            types.extend(self._get_output_event_types(returns.right))
        elif isinstance(returns, ast.Subscript):
            # Handle Union[SomeEvent, OtherEvent] or list[SomeEvent]
            type_name = self._get_name(returns.value)
            if type_name == "Union":
                if isinstance(returns.slice, ast.Tuple):
                    for elt in returns.slice.elts:
                        event_type = self._get_event_type(elt)
                        if event_type:
                            types.append(event_type)
        else:
            event_type = self._get_event_type(returns)
            if event_type:
                types.append(event_type)

        return types

    def _get_name(self, node: ast.expr) -> str | None:
        """Get the name from an AST node."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return node.attr
        elif isinstance(node, ast.Call):
            return self._get_name(node.func)
        return None
