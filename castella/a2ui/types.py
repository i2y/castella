"""A2UI type definitions using Pydantic v2.

This module defines the data models for the A2UI (Agent-to-User Interface) protocol,
which enables AI agents to generate rich, interactive UIs that render natively
across platforms.

Reference: https://a2ui.org/specification/v0.9-a2ui/
"""

from __future__ import annotations

from enum import Enum
from typing import Annotated, Any, Literal, Union

from pydantic import BaseModel, ConfigDict, Field


# =============================================================================
# Enums
# =============================================================================


class TextUsageHint(str, Enum):
    """Text styling hints for Text components."""

    H1 = "h1"
    H2 = "h2"
    H3 = "h3"
    H4 = "h4"
    H5 = "h5"
    BODY = "body"
    CAPTION = "caption"


class TextFieldUsageHint(str, Enum):
    """Input type hints for TextField components.

    Supports both A2UI 0.9 spec values and Castella-specific values:
    - A2UI 0.9 spec: shortText, longText, obscured, number
    - Castella: text, email, password, phone, url, multiline
    """

    # A2UI 0.9 spec values
    SHORT_TEXT = "shortText"
    LONG_TEXT = "longText"
    OBSCURED = "obscured"

    # Castella values (mapped from 0.9 spec via compat layer)
    TEXT = "text"
    EMAIL = "email"
    PASSWORD = "password"
    NUMBER = "number"
    PHONE = "phone"
    URL = "url"
    MULTILINE = "multiline"


class Distribution(str, Enum):
    """Flex distribution (justify-content equivalent)."""

    START = "start"
    END = "end"
    CENTER = "center"
    SPACE_BETWEEN = "spaceBetween"
    SPACE_AROUND = "spaceAround"
    SPACE_EVENLY = "spaceEvenly"


class Alignment(str, Enum):
    """Flex alignment (align-items equivalent)."""

    START = "start"
    END = "end"
    CENTER = "center"
    STRETCH = "stretch"


class DividerOrientation(str, Enum):
    """Divider orientation."""

    HORIZONTAL = "horizontal"
    VERTICAL = "vertical"


# =============================================================================
# Value Types (Literal or Data Binding)
# =============================================================================


class LiteralString(BaseModel):
    """A literal string value."""

    literal_string: str = Field(alias="literalString")


class LiteralNumber(BaseModel):
    """A literal number value."""

    literal_number: float = Field(alias="literalNumber")


class LiteralBoolean(BaseModel):
    """A literal boolean value."""

    literal_boolean: bool = Field(alias="literalBoolean")


class DataBinding(BaseModel):
    """A data binding reference using JSON Pointer (RFC 6901)."""

    path: str


# Type aliases for values that can be either literal or bound
StringValue = Union[LiteralString, DataBinding]
NumberValue = Union[LiteralNumber, DataBinding]
BooleanValue = Union[LiteralBoolean, DataBinding]
AnyValue = Union[LiteralString, LiteralNumber, LiteralBoolean, DataBinding]


# =============================================================================
# Action Types
# =============================================================================


class ActionContextItem(BaseModel):
    """A single context item for an action."""

    key: str
    value: AnyValue


class Action(BaseModel):
    """An action triggered by user interaction."""

    name: str
    context: list[ActionContextItem] = Field(default_factory=list)


# =============================================================================
# Children Types
# =============================================================================


class ExplicitChildren(BaseModel):
    """Explicit list of child component IDs."""

    explicit_list: list[str] = Field(alias="explicitList")


class TemplateChildren(BaseModel):
    """Template-based children with data binding."""

    path: str  # JSON Pointer to array data
    component_id: str = Field(alias="componentId")  # Template component ID


Children = Union[ExplicitChildren, TemplateChildren]


# =============================================================================
# Component Definitions
# =============================================================================


class BaseComponent(BaseModel):
    """Base class for all A2UI components."""

    id: str
    weight: float | None = None  # flex-grow equivalent

    model_config = ConfigDict(populate_by_name=True)


class TextComponent(BaseComponent):
    """Text display component."""

    component: Literal["Text"] = "Text"
    text: StringValue
    usage_hint: TextUsageHint | None = Field(default=None, alias="usageHint")


class ButtonComponent(BaseComponent):
    """Interactive button component."""

    component: Literal["Button"] = "Button"
    text: StringValue | None = None
    child: str | None = None  # Child component ID
    action: Action | None = None


class TextFieldComponent(BaseComponent):
    """Text input component."""

    component: Literal["TextField"] = "TextField"
    label: StringValue | None = None
    text: StringValue | None = None  # Current value (use DataBinding for two-way)
    usage_hint: TextFieldUsageHint | None = Field(default=None, alias="usageHint")
    validation_regexp: str | None = Field(default=None, alias="validationRegexp")


class CheckBoxComponent(BaseComponent):
    """Checkbox component."""

    component: Literal["CheckBox"] = "CheckBox"
    label: StringValue | None = None
    checked: BooleanValue | None = None


class SliderComponent(BaseComponent):
    """Slider input component."""

    component: Literal["Slider"] = "Slider"
    value: NumberValue | None = None
    min: float = 0
    max: float = 100


class ImageComponent(BaseComponent):
    """Image display component."""

    component: Literal["Image"] = "Image"
    src: StringValue
    alt: StringValue | None = None


class DividerComponent(BaseComponent):
    """Divider/separator component."""

    component: Literal["Divider"] = "Divider"
    orientation: DividerOrientation = DividerOrientation.HORIZONTAL


class RowComponent(BaseComponent):
    """Horizontal layout component."""

    component: Literal["Row"] = "Row"
    children: Children | None = None
    distribution: Distribution = Distribution.START
    alignment: Alignment = Alignment.CENTER


class ColumnComponent(BaseComponent):
    """Vertical layout component."""

    component: Literal["Column"] = "Column"
    children: Children | None = None
    distribution: Distribution = Distribution.START
    alignment: Alignment = Alignment.STRETCH


class CardComponent(BaseComponent):
    """Card container component."""

    component: Literal["Card"] = "Card"
    children: Children | None = None


class ListComponent(BaseComponent):
    """Dynamic list component with data binding."""

    component: Literal["List"] = "List"
    children: TemplateChildren


class DateTimeInputComponent(BaseComponent):
    """Date/time input component."""

    component: Literal["DateTimeInput"] = "DateTimeInput"
    label: StringValue | None = None
    value: StringValue | None = None  # ISO 8601 format
    enable_date: bool = Field(default=True, alias="enableDate")
    enable_time: bool = Field(default=False, alias="enableTime")


class ChoicePickerComponent(BaseComponent):
    """Choice picker (dropdown/radio) component."""

    component: Literal["ChoicePicker"] = "ChoicePicker"
    label: StringValue | None = None
    choices: list[StringValue] = Field(default_factory=list)
    selected: StringValue | None = None
    allow_multiple: bool = Field(default=False, alias="allowMultiple")


class TabItem(BaseModel):
    """A single tab item."""

    id: str
    label: StringValue
    content_id: str = Field(alias="contentId")  # Content component ID


class TabsComponent(BaseComponent):
    """Tab navigation component."""

    component: Literal["Tabs"] = "Tabs"
    tab_items: list[TabItem] = Field(alias="tabItems")
    selected_tab: StringValue | None = Field(default=None, alias="selectedTab")


class ModalComponent(BaseComponent):
    """Modal dialog component."""

    component: Literal["Modal"] = "Modal"
    title: StringValue | None = None
    children: Children | None = None
    open: BooleanValue | None = None


class IconComponent(BaseComponent):
    """Icon display component (Material Icons)."""

    component: Literal["Icon"] = "Icon"
    name: StringValue  # Material icon name
    size: float | None = None
    color: str | None = None


# Custom component for Castella-specific features
class MarkdownComponent(BaseComponent):
    """Markdown display component (Castella extension)."""

    component: Literal["Markdown"] = "Markdown"
    content: StringValue
    base_font_size: int = Field(default=14, alias="baseFontSize")


# Union of all component types with discriminator for efficient parsing
Component = Annotated[
    Union[
        TextComponent,
        ButtonComponent,
        TextFieldComponent,
        CheckBoxComponent,
        SliderComponent,
        ImageComponent,
        DividerComponent,
        RowComponent,
        ColumnComponent,
        CardComponent,
        ListComponent,
        DateTimeInputComponent,
        ChoicePickerComponent,
        TabsComponent,
        ModalComponent,
        IconComponent,
        MarkdownComponent,
    ],
    Field(discriminator="component"),
]


# =============================================================================
# Message Types (Server → Client)
# =============================================================================


class CreateSurface(BaseModel):
    """Create a new UI surface."""

    surface_id: str = Field(alias="surfaceId")
    components: list[Component]
    root_id: str | None = Field(default=None, alias="rootId")


class UpdateComponents(BaseModel):
    """Update existing components."""

    surface_id: str = Field(alias="surfaceId")
    components: list[Component]


class UpdateDataModel(BaseModel):
    """Update data model values."""

    surface_id: str = Field(alias="surfaceId")
    data: dict[str, Any]  # JSON Pointer path -> value


class DeleteSurface(BaseModel):
    """Delete a UI surface."""

    surface_id: str = Field(alias="surfaceId")


class BeginRendering(BaseModel):
    """Signal the start of progressive rendering.

    Used in streaming scenarios to indicate that rendering is about to begin.
    The root component ID specifies which component will be the root of the surface.
    """

    surface_id: str = Field(alias="surfaceId")
    root: str  # Root component ID


class ServerMessage(BaseModel):
    """A message from server to client.

    Supports the following message types:
    - createSurface: Create a new UI surface with components
    - updateComponents: Update existing components (for progressive rendering)
    - updateDataModel: Update data model values
    - deleteSurface: Delete a UI surface
    - beginRendering: Signal the start of progressive rendering
    """

    create_surface: CreateSurface | None = Field(default=None, alias="createSurface")
    update_components: UpdateComponents | None = Field(
        default=None, alias="updateComponents"
    )
    update_data_model: UpdateDataModel | None = Field(
        default=None, alias="updateDataModel"
    )
    delete_surface: DeleteSurface | None = Field(default=None, alias="deleteSurface")
    begin_rendering: BeginRendering | None = Field(default=None, alias="beginRendering")


# =============================================================================
# Message Types (Client → Server)
# =============================================================================


class UserAction(BaseModel):
    """User action sent from client to server."""

    name: str
    surface_id: str = Field(alias="surfaceId")
    source_component_id: str = Field(alias="sourceComponentId")
    timestamp: str | None = None  # ISO 8601
    context: dict[str, Any] = Field(default_factory=dict)


class ClientMessage(BaseModel):
    """A message from client to server."""

    user_action: UserAction | None = Field(default=None, alias="userAction")


# =============================================================================
# Helper Functions
# =============================================================================


def literal(value: str | int | float | bool) -> AnyValue:
    """Create a literal value from a Python value."""
    if isinstance(value, str):
        return LiteralString(literalString=value)
    elif isinstance(value, bool):
        return LiteralBoolean(literalBoolean=value)
    elif isinstance(value, (int, float)):
        return LiteralNumber(literalNumber=float(value))
    else:
        raise TypeError(f"Unsupported literal type: {type(value)}")


def binding(path: str) -> DataBinding:
    """Create a data binding reference."""
    return DataBinding(path=path)


def get_literal_value(value: AnyValue) -> str | float | bool | None:
    """Extract the literal value from an AnyValue, or None if it's a binding."""
    if isinstance(value, LiteralString):
        return value.literal_string
    elif isinstance(value, LiteralNumber):
        return value.literal_number
    elif isinstance(value, LiteralBoolean):
        return value.literal_boolean
    elif isinstance(value, DataBinding):
        return None
    return None


def is_binding(value: AnyValue) -> bool:
    """Check if a value is a data binding."""
    return isinstance(value, DataBinding)
