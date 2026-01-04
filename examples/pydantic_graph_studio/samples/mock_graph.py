"""Mock graph for demonstration without pydantic-graph installed."""

from __future__ import annotations

from ..models.graph import EdgeInfo, GraphAPIType, NodeInfo, PydanticGraphModel


def create_mock_graph() -> PydanticGraphModel:
    """Create a mock graph for demonstration.

    This simulates a simple workflow with:
    - Start -> Process -> Validate -> (Success or Error) -> End

    Returns:
        PydanticGraphModel ready for visualization.
    """
    return PydanticGraphModel(
        name="Mock Workflow Graph",
        api_type=GraphAPIType.MOCK,
        nodes=[
            NodeInfo(
                id="__start__",
                label="Start",
                is_start=True,
            ),
            NodeInfo(
                id="InputNode",
                label="Input Node",
                node_class_name="InputNode",
                docstring="Entry node that receives input.",
                is_start=True,
                return_types=["ProcessNode"],
                fields={"text": "str"},
            ),
            NodeInfo(
                id="ProcessNode",
                label="Process Node",
                node_class_name="ProcessNode",
                docstring="Process the input data.",
                return_types=["ValidateNode"],
                fields={},
            ),
            NodeInfo(
                id="ValidateNode",
                label="Validate Node",
                node_class_name="ValidateNode",
                docstring="Validate the processed data.",
                return_types=["SuccessNode", "ErrorNode"],
                is_end=True,
                fields={},
            ),
            NodeInfo(
                id="SuccessNode",
                label="Success Node",
                node_class_name="SuccessNode",
                docstring="Handle successful validation.",
                is_end=True,
                fields={},
            ),
            NodeInfo(
                id="ErrorNode",
                label="Error Node",
                node_class_name="ErrorNode",
                docstring="Handle validation errors.",
                is_end=True,
                fields={},
            ),
            NodeInfo(
                id="__end__",
                label="End",
                is_end=True,
            ),
        ],
        edges=[
            EdgeInfo(id="e0", source_id="__start__", target_id="InputNode"),
            EdgeInfo(id="e1", source_id="InputNode", target_id="ProcessNode"),
            EdgeInfo(id="e2", source_id="ProcessNode", target_id="ValidateNode"),
            EdgeInfo(
                id="e3",
                source_id="ValidateNode",
                target_id="SuccessNode",
                label="valid",
                is_conditional=True,
            ),
            EdgeInfo(
                id="e4",
                source_id="ValidateNode",
                target_id="ErrorNode",
                label="invalid",
                is_conditional=True,
            ),
            EdgeInfo(id="e5", source_id="SuccessNode", target_id="__end__"),
            EdgeInfo(id="e6", source_id="ErrorNode", target_id="__end__"),
        ],
    )


def create_linear_mock_graph() -> PydanticGraphModel:
    """Create a simple linear mock graph.

    Returns:
        PydanticGraphModel with a simple linear flow.
    """
    return PydanticGraphModel(
        name="Linear Workflow",
        api_type=GraphAPIType.MOCK,
        nodes=[
            NodeInfo(id="__start__", label="Start", is_start=True),
            NodeInfo(
                id="Step1",
                label="Step 1",
                node_class_name="Step1Node",
                docstring="First step.",
                is_start=True,
                return_types=["Step2"],
            ),
            NodeInfo(
                id="Step2",
                label="Step 2",
                node_class_name="Step2Node",
                docstring="Second step.",
                return_types=["Step3"],
            ),
            NodeInfo(
                id="Step3",
                label="Step 3",
                node_class_name="Step3Node",
                docstring="Third step.",
                is_end=True,
            ),
            NodeInfo(id="__end__", label="End", is_end=True),
        ],
        edges=[
            EdgeInfo(id="e0", source_id="__start__", target_id="Step1"),
            EdgeInfo(id="e1", source_id="Step1", target_id="Step2"),
            EdgeInfo(id="e2", source_id="Step2", target_id="Step3"),
            EdgeInfo(id="e3", source_id="Step3", target_id="__end__"),
        ],
    )
