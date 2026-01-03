"""Mock workflow model for testing the studio UI.

This creates a mock workflow model without requiring llama-index-workflows.
"""

from examples.llamaindex_studio.models.events import EventTypeModel, EventCategory
from examples.llamaindex_studio.models.steps import StepModel, InputMode, OutputMode
from examples.llamaindex_studio.models.workflow import WorkflowModel, EventEdge


def create_mock_workflow() -> WorkflowModel:
    """Create a mock workflow model for testing.

    Creates a simple workflow with the following structure:

    StartEvent -> process -> ProcessedEvent
                                |
                          validate -> StopEvent
    """
    model = WorkflowModel(name="MockWorkflow")

    # Event types
    model.event_types = {
        "StartEvent": EventTypeModel(
            name="StartEvent",
            module="llama_index.core.workflow",
            category=EventCategory.START,
            docstring="Workflow entry point",
        ),
        "ProcessedEvent": EventTypeModel(
            name="ProcessedEvent",
            module="mock_workflow",
            category=EventCategory.USER,
            fields={"data": "str", "processed": "bool"},
            docstring="Event emitted after processing",
        ),
        "ValidatedEvent": EventTypeModel(
            name="ValidatedEvent",
            module="mock_workflow",
            category=EventCategory.USER,
            fields={"valid": "bool"},
            docstring="Event after validation",
        ),
        "StopEvent": EventTypeModel(
            name="StopEvent",
            module="llama_index.core.workflow",
            category=EventCategory.STOP,
            docstring="Workflow exit point",
        ),
    }

    # Steps
    model.steps = [
        StepModel(
            id="process",
            label="Process",
            input_events=["StartEvent"],
            input_mode=InputMode.SINGLE,
            output_events=["ProcessedEvent"],
            output_mode=OutputMode.SINGLE,
            docstring="Process the incoming data.",
            source_code="""@step
async def process(self, ev: StartEvent) -> ProcessedEvent:
    \"\"\"Process the incoming data.\"\"\"
    data = ev.data
    result = await self.do_processing(data)
    return ProcessedEvent(data=result, processed=True)
""",
        ),
        StepModel(
            id="validate",
            label="Validate",
            input_events=["ProcessedEvent"],
            input_mode=InputMode.SINGLE,
            output_events=["StopEvent"],
            output_mode=OutputMode.SINGLE,
            docstring="Validate the processed data.",
            source_code="""@step
async def validate(self, ev: ProcessedEvent) -> StopEvent:
    \"\"\"Validate the processed data.\"\"\"
    is_valid = self.check_validity(ev.data)
    return StopEvent(result={"valid": is_valid})
""",
        ),
    ]

    # Edges
    model.edges = [
        EventEdge(
            id="edge_0",
            event_type="StartEvent",
            source_step_id=None,
            target_step_id="process",
        ),
        EventEdge(
            id="edge_1",
            event_type="ProcessedEvent",
            source_step_id="process",
            target_step_id="validate",
        ),
        EventEdge(
            id="edge_2",
            event_type="StopEvent",
            source_step_id="validate",
            target_step_id=None,
        ),
    ]

    model.start_event_type = "StartEvent"
    model.stop_event_type = "StopEvent"

    return model


def create_branching_mock_workflow() -> WorkflowModel:
    """Create a mock workflow with branching (union output).

    StartEvent -> analyze -> SuccessEvent | ErrorEvent
                                |            |
                            success      error -> StopEvent
                                |
                            StopEvent
    """
    model = WorkflowModel(name="BranchingMockWorkflow")

    # Event types
    model.event_types = {
        "StartEvent": EventTypeModel(
            name="StartEvent",
            module="llama_index.core.workflow",
            category=EventCategory.START,
        ),
        "SuccessEvent": EventTypeModel(
            name="SuccessEvent",
            module="mock_workflow",
            category=EventCategory.USER,
            fields={"result": "str"},
        ),
        "ErrorEvent": EventTypeModel(
            name="ErrorEvent",
            module="mock_workflow",
            category=EventCategory.USER,
            fields={"message": "str"},
        ),
        "StopEvent": EventTypeModel(
            name="StopEvent",
            module="llama_index.core.workflow",
            category=EventCategory.STOP,
        ),
    }

    # Steps
    model.steps = [
        StepModel(
            id="analyze",
            label="Analyze",
            input_events=["StartEvent"],
            input_mode=InputMode.SINGLE,
            output_events=["SuccessEvent", "ErrorEvent"],
            output_mode=OutputMode.UNION,  # Branching!
            docstring="Analyze and branch based on result.",
            source_code="""@step
async def analyze(self, ev: StartEvent) -> SuccessEvent | ErrorEvent:
    \"\"\"Analyze and branch based on result.\"\"\"
    result = await self.do_analysis(ev.data)
    if result.is_valid:
        return SuccessEvent(result=result.data)
    else:
        return ErrorEvent(message=result.error)
""",
        ),
        StepModel(
            id="success",
            label="Handle Success",
            input_events=["SuccessEvent"],
            input_mode=InputMode.SINGLE,
            output_events=["StopEvent"],
            output_mode=OutputMode.SINGLE,
            docstring="Handle successful analysis.",
            source_code="""@step
async def handle_success(self, ev: SuccessEvent) -> StopEvent:
    \"\"\"Handle successful analysis.\"\"\"
    return StopEvent(result={"status": "success", "data": ev.result})
""",
        ),
        StepModel(
            id="error",
            label="Handle Error",
            input_events=["ErrorEvent"],
            input_mode=InputMode.SINGLE,
            output_events=["StopEvent"],
            output_mode=OutputMode.SINGLE,
            docstring="Handle error case.",
            source_code="""@step
async def handle_error(self, ev: ErrorEvent) -> StopEvent:
    \"\"\"Handle error case.\"\"\"
    return StopEvent(result={"status": "error", "message": ev.message})
""",
        ),
    ]

    # Edges
    model.edges = [
        EventEdge(id="edge_0", event_type="StartEvent", source_step_id=None, target_step_id="analyze"),
        EventEdge(id="edge_1", event_type="SuccessEvent", source_step_id="analyze", target_step_id="success", is_part_of_union=True),
        EventEdge(id="edge_2", event_type="ErrorEvent", source_step_id="analyze", target_step_id="error", is_part_of_union=True),
        EventEdge(id="edge_3", event_type="StopEvent", source_step_id="success", target_step_id=None),
        EventEdge(id="edge_4", event_type="StopEvent", source_step_id="error", target_step_id=None),
    ]

    model.start_event_type = "StartEvent"
    model.stop_event_type = "StopEvent"

    return model


def create_collect_mock_workflow() -> WorkflowModel:
    """Create a mock workflow with collect pattern (AND).

    StartEvent -> fetch_a -> DataA ─┐
              └-> fetch_b -> DataB ─┴-> merge -> StopEvent
    """
    model = WorkflowModel(name="CollectMockWorkflow")

    # Event types
    model.event_types = {
        "StartEvent": EventTypeModel(
            name="StartEvent",
            module="llama_index.core.workflow",
            category=EventCategory.START,
        ),
        "DataAEvent": EventTypeModel(
            name="DataAEvent",
            module="mock_workflow",
            category=EventCategory.USER,
            fields={"data_a": "str"},
        ),
        "DataBEvent": EventTypeModel(
            name="DataBEvent",
            module="mock_workflow",
            category=EventCategory.USER,
            fields={"data_b": "str"},
        ),
        "StopEvent": EventTypeModel(
            name="StopEvent",
            module="llama_index.core.workflow",
            category=EventCategory.STOP,
        ),
    }

    # Steps
    model.steps = [
        StepModel(
            id="fetch_a",
            label="Fetch A",
            input_events=["StartEvent"],
            input_mode=InputMode.SINGLE,
            output_events=["DataAEvent"],
            output_mode=OutputMode.SINGLE,
            docstring="Fetch data source A.",
            source_code="""@step
async def fetch_a(self, ev: StartEvent) -> DataAEvent:
    \"\"\"Fetch data source A.\"\"\"
    data = await self.fetch_from_source_a()
    return DataAEvent(data_a=data)
""",
        ),
        StepModel(
            id="fetch_b",
            label="Fetch B",
            input_events=["StartEvent"],
            input_mode=InputMode.SINGLE,
            output_events=["DataBEvent"],
            output_mode=OutputMode.SINGLE,
            docstring="Fetch data source B.",
            source_code="""@step
async def fetch_b(self, ev: StartEvent) -> DataBEvent:
    \"\"\"Fetch data source B.\"\"\"
    data = await self.fetch_from_source_b()
    return DataBEvent(data_b=data)
""",
        ),
        StepModel(
            id="merge",
            label="Merge",
            input_events=["DataAEvent", "DataBEvent"],
            input_mode=InputMode.COLLECT,  # AND - waits for both!
            output_events=["StopEvent"],
            output_mode=OutputMode.SINGLE,
            docstring="Merge data from both sources.",
            source_code="""@step
async def merge(
    self, ev_a: DataAEvent, ev_b: DataBEvent
) -> StopEvent:
    \"\"\"Merge data from both sources.\"\"\"
    merged = self.combine_data(ev_a.data_a, ev_b.data_b)
    return StopEvent(result={"merged": merged})
""",
        ),
    ]

    # Edges
    model.edges = [
        EventEdge(id="edge_0", event_type="StartEvent", source_step_id=None, target_step_id="fetch_a"),
        EventEdge(id="edge_1", event_type="StartEvent", source_step_id=None, target_step_id="fetch_b"),
        EventEdge(id="edge_2", event_type="DataAEvent", source_step_id="fetch_a", target_step_id="merge", is_part_of_collect=True),
        EventEdge(id="edge_3", event_type="DataBEvent", source_step_id="fetch_b", target_step_id="merge", is_part_of_collect=True),
        EventEdge(id="edge_4", event_type="StopEvent", source_step_id="merge", target_step_id=None),
    ]

    model.start_event_type = "StartEvent"
    model.stop_event_type = "StopEvent"

    return model
