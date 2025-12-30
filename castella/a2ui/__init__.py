"""A2UI (Agent-to-User Interface) support for Castella.

This module provides support for the A2UI protocol, enabling AI agents to
generate rich, interactive UIs that render natively across all Castella
platforms (Desktop, Web, Terminal).

A2UI is a declarative UI protocol where agents output JSON descriptions
of UI components, and the client (Castella) renders them using native
widgets.

Example:
    from castella.a2ui import A2UIRenderer, literal

    # Create renderer
    renderer = A2UIRenderer()

    # Render A2UI JSON
    widget = renderer.render_json({
        "components": [
            {"id": "root", "component": "Column", "children": {"explicitList": ["title", "btn"]}},
            {"id": "title", "component": "Text", "text": {"literalString": "Hello A2UI!"}},
            {"id": "btn", "component": "Button", "text": {"literalString": "Click Me"}}
        ],
        "rootId": "root"
    })

    # Use in a Castella app
    run_app(widget)

Streaming Example:
    from castella.a2ui import A2UIRenderer

    renderer = A2UIRenderer()

    # From JSONL file
    with open("ui.jsonl") as f:
        surface = renderer.handle_stream(f)
        widget = surface.root_widget

    # From SSE endpoint (requires httpx)
    from castella.a2ui.transports import sse_stream
    surface = await renderer.handle_stream_async(await sse_stream(url))

Reference:
    - A2UI Specification: https://a2ui.org/specification/v0.9-a2ui/
    - A2UI GitHub: https://github.com/google/A2UI
"""

from castella.a2ui.catalog import (
    ComponentCatalog,
    get_default_catalog,
    reset_default_catalog,
)
from castella.a2ui.client import (
    A2UIClient,
    A2UIClientError,
    A2UIConnectionError,
    A2UIResponseError,
)
from castella.a2ui.compat import (
    normalize_component,
    normalize_message,
)
from castella.a2ui.renderer import A2UIComponent, A2UIRenderer, A2UISurface
from castella.a2ui.stream import (
    JSONLParser,
    parse_async_stream,
    parse_jsonl_string,
    parse_sync_stream,
)
from castella.a2ui.types import (
    # Enums
    Alignment,
    Distribution,
    DividerOrientation,
    TextFieldUsageHint,
    TextUsageHint,
    # Value types
    AnyValue,
    BooleanValue,
    DataBinding,
    LiteralBoolean,
    LiteralNumber,
    LiteralString,
    NumberValue,
    StringValue,
    # Action types
    Action,
    ActionContextItem,
    # Children types
    Children,
    ExplicitChildren,
    TemplateChildren,
    # Components
    BaseComponent,
    ButtonComponent,
    CardComponent,
    CheckBoxComponent,
    ChoicePickerComponent,
    ColumnComponent,
    Component,
    DateTimeInputComponent,
    DividerComponent,
    ImageComponent,
    ListComponent,
    MarkdownComponent,
    ModalComponent,
    RowComponent,
    SliderComponent,
    TabItem,
    TabsComponent,
    TextComponent,
    TextFieldComponent,
    # Messages
    BeginRendering,
    ClientMessage,
    CreateSurface,
    DeleteSurface,
    ServerMessage,
    UpdateComponents,
    UpdateDataModel,
    UserAction,
    # Helpers
    binding,
    get_literal_value,
    is_binding,
    literal,
)

__all__ = [
    # Client
    "A2UIClient",
    "A2UIClientError",
    "A2UIConnectionError",
    "A2UIResponseError",
    # Renderer
    "A2UIComponent",
    "A2UIRenderer",
    "A2UISurface",
    # Catalog
    "ComponentCatalog",
    "get_default_catalog",
    "reset_default_catalog",
    # Compatibility
    "normalize_component",
    "normalize_message",
    # Stream parsing
    "JSONLParser",
    "parse_async_stream",
    "parse_jsonl_string",
    "parse_sync_stream",
    # Enums
    "Alignment",
    "Distribution",
    "DividerOrientation",
    "TextFieldUsageHint",
    "TextUsageHint",
    # Value types
    "AnyValue",
    "BooleanValue",
    "DataBinding",
    "LiteralBoolean",
    "LiteralNumber",
    "LiteralString",
    "NumberValue",
    "StringValue",
    # Action types
    "Action",
    "ActionContextItem",
    # Children types
    "Children",
    "ExplicitChildren",
    "TemplateChildren",
    # Components
    "BaseComponent",
    "ButtonComponent",
    "CardComponent",
    "CheckBoxComponent",
    "ChoicePickerComponent",
    "ColumnComponent",
    "Component",
    "DateTimeInputComponent",
    "DividerComponent",
    "ImageComponent",
    "ListComponent",
    "MarkdownComponent",
    "ModalComponent",
    "RowComponent",
    "SliderComponent",
    "TabItem",
    "TabsComponent",
    "TextComponent",
    "TextFieldComponent",
    # Messages
    "BeginRendering",
    "ClientMessage",
    "CreateSurface",
    "DeleteSurface",
    "ServerMessage",
    "UpdateComponents",
    "UpdateDataModel",
    "UserAction",
    # Helpers
    "binding",
    "get_literal_value",
    "is_binding",
    "literal",
]
