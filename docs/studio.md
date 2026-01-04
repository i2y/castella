# Workflow Studio Samples

Castella includes sample applications demonstrating visual development environments for popular AI workflow frameworks. These serve as references for building your own workflow visualization tools.

!!! note "Sample Applications"
    These are demonstration applications located in `examples/`. They showcase what's possible with Castella's graph visualization capabilities and can serve as a starting point for your own tools.

## Available Samples

| Sample | Framework | Description |
|--------|-----------|-------------|
| `langgraph_studio/` | LangGraph | Visual development environment for LangGraph |
| `llamaindex_studio/` | LlamaIndex Workflows | Workflow visualization and execution |
| `pydantic_graph_studio/` | pydantic-graph | Graph visualization and step-by-step execution |
| `edda_workflow_manager/` | Edda + LlamaIndex Workflows | Workflow management with execution history |

## LangGraph Studio

A visual development environment for [LangGraph](https://github.com/langchain-ai/langgraph).

**Features:**

- Graph structure visualization with automatic layout
- Step-by-step execution with state inspection
- File browser for loading graph definitions
- Zoom and pan controls

**Usage:**

```bash
# Run with file browser
uv run python -m examples.langgraph_studio.main

# Load a specific file on startup
uv run python -m examples.langgraph_studio.main path/to/graph.py

# Browse a specific directory
uv run python -m examples.langgraph_studio.main ./my_graphs/
```

## LlamaIndex Workflow Studio

A visual studio for [LlamaIndex Workflows](https://docs.llamaindex.ai/en/stable/module_guides/workflow/).

**Features:**

- Workflow structure visualization
- Breakpoint support
- Execution history tracking
- Step details modal

**Usage:**

```bash
# Run with sample workflows
uv run python examples/llamaindex_studio/main.py

# Load a specific workflow file
uv run python examples/llamaindex_studio/main.py path/to/workflow.py
```

## pydantic-graph Studio

A visual studio for [pydantic-graph](https://ai.pydantic.dev/pydantic-graph/).

**Features:**

- Graph structure visualization from Python files
- Step-by-step graph execution
- Breakpoints and state inspection
- Execution history view
- Mock graph for testing without dependencies

**Usage:**

```bash
# Run with mock graph (no pydantic-graph required)
uv run python -m examples.pydantic_graph_studio.main

# Load a specific Python file
uv run python -m examples.pydantic_graph_studio.main path/to/graph.py

# Browse a specific directory
uv run python -m examples.pydantic_graph_studio.main --path ./my_graphs/
```

## Edda Workflow Manager

A management GUI for [Edda](https://github.com/i2y/edda) with [LlamaIndex Workflows](https://docs.llamaindex.ai/en/stable/module_guides/workflow/) integration.

**Features:**

- Workflow visualization
- Execution history browsing
- Live execution monitoring
- Multiple execution modes (direct, CloudEvent)

**Usage:**

```bash
# Read-only mode (view execution history)
uv run python examples/edda_workflow_manager/main.py \
    --db sqlite+aiosqlite:///path/to/edda.db

# Direct execution mode (import and run workflows)
uv run python examples/edda_workflow_manager/main.py \
    --db sqlite+aiosqlite:///path/to/edda.db \
    --import-module my_app.workflows

# CloudEvent mode (send to external Edda server)
uv run python examples/edda_workflow_manager/main.py \
    --db sqlite+aiosqlite:///path/to/edda.db \
    --edda-url http://localhost:8001

# Both modes (user can choose)
uv run python examples/edda_workflow_manager/main.py \
    --db sqlite+aiosqlite:///path/to/edda.db \
    --import-module my_app.workflows \
    --edda-url http://localhost:8001
```

## Shared Infrastructure

These samples share common infrastructure from `castella/studio/`:

- **`BaseWorkflowExecutor`** - Abstract executor with threading support
- **`Toolbar`** - Run/pause/step/zoom controls
- **`StatusBar`** - Execution status display
- **`FilePanel`** - File browser panel
- **`ContentViewerModal`** - Docstring/source code viewer

You can use these components to build your own workflow visualization tools.

## Graph Visualization

The samples use Castella's graph visualization system (`castella/graph/`):

- **`GraphModel`** - Data model for nodes and edges
- **`GraphCanvas`** - Interactive canvas with zoom/pan
- **`SugiyamaLayout`** - Automatic layered graph layout
- **`GraphTheme`** - Visual styling (dark/light themes)
