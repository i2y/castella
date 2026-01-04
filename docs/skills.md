# Agent Skills

Castella includes [Agent Skills](https://agentskills.io/) to help AI coding agents effectively use the framework. These skills follow the [agentskills.io specification](https://agentskills.io/specification) and are located in the `skills/` directory.

## Available Skills

| Skill | Description |
|-------|-------------|
| `castella-core` | Core UI development - widgets, components, state, layouts, themes |
| `castella-a2ui` | A2UI JSON rendering - parse messages, data binding, progressive rendering |
| `castella-a2a` | A2A protocol - connect to agents, agent cards, streaming responses |
| `castella-mcp` | MCP integration - servers, resources, tools, semantic IDs |
| `castella-agent-ui` | Agent UI components - AgentChat, MultiAgentChat, AgentHub |

## Skill Structure

Each skill follows a consistent structure:

```
skills/
└── castella-core/
    ├── SKILL.md           # Main skill document
    ├── references/        # Detailed API documentation
    │   ├── widgets.md
    │   ├── theme.md
    │   └── ...
    └── scripts/           # Executable examples
        ├── counter.py
        └── ...
```

### SKILL.md

The main skill document contains:

- **YAML frontmatter** with `name` and `description`
- **Quick Start** - Minimal code to get started
- **Core Concepts** - Key patterns and APIs
- **Best Practices** - Recommended usage patterns
- **Reference links** - Pointers to detailed documentation

### references/

Detailed API documentation for specific topics. These are loaded on-demand when the AI agent needs deeper information.

### scripts/

Executable Python examples that demonstrate the skill's features. These can be run directly:

```bash
uv run python skills/castella-core/scripts/counter.py
```

## Skill Descriptions

### castella-core

Core UI development with Castella. Covers:

- App and Frame setup
- Widgets (Text, Button, Input, etc.)
- Layout containers (Column, Row, Box)
- Component pattern with State and ListState
- Size policies (FIXED, EXPANDING, CONTENT)
- Theme system and styling
- Event handling
- Animation

**When to use**: Creating Castella apps, building UIs, working with widgets, managing state, handling events.

### castella-a2ui

A2UI (Agent-to-User Interface) JSON rendering. Covers:

- A2UIRenderer for parsing A2UI JSON
- Value types (literal vs binding)
- Supported components (17 total)
- Data binding with JSON Pointers
- Actions and event handling
- updateDataModel for dynamic updates
- TemplateChildren for dynamic lists
- Progressive rendering (JSONL streaming)
- A2UIClient for connecting to agents

**When to use**: Rendering A2UI JSON, connecting to A2UI-enabled agents, handling A2UI actions.

### castella-a2a

A2A (Agent-to-Agent) protocol integration. Covers:

- A2AClient for connecting to agents
- Agent cards and skills
- Synchronous and asynchronous messaging
- Streaming responses
- Error handling
- AgentCardView widget

**When to use**: Connecting to A2A agents, displaying agent information, sending messages.

### castella-mcp

MCP (Model Context Protocol) integration. Covers:

- CastellaMCPServer setup
- Semantic IDs for widgets
- MCP Resources (ui://tree, ui://elements, etc.)
- MCP Tools (click, type_text, toggle, etc.)
- Transports (stdio, SSE)
- A2UI + MCP integration

**When to use**: Enabling AI agents to control Castella UIs, creating MCP servers.

### castella-agent-ui

High-level components for agent UIs. Covers:

- AgentChat for quick chat UIs
- Chat components (ChatContainer, ChatMessage, ChatInput, ChatView)
- Tool call visualization
- Agent card display
- MultiAgentChat for tabbed interfaces
- AgentHub for agent management
- Scroll position patterns

**When to use**: Building chat interfaces, displaying tool calls, managing multiple agents.

## Using Skills with AI Agents

AI coding agents (like Claude Code) can use these skills to:

1. **Learn Castella patterns** - Quick start guides show idiomatic usage
2. **Find API details** - References provide comprehensive documentation
3. **See working examples** - Scripts demonstrate real implementations
4. **Follow best practices** - Each skill includes recommended patterns

The skills use progressive disclosure:

- **Metadata** (~100 tokens) - Name and description for skill selection
- **Instructions** (<5000 tokens) - Main SKILL.md content
- **Resources** (on-demand) - References and scripts loaded as needed
