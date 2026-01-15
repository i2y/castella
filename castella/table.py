"""Enhanced DataTable widget with sorting, filtering, and selection."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum, auto
from typing import Any, Callable, Self, Sequence, Union, get_args, get_origin

from pydantic import BaseModel, ConfigDict, PrivateAttr

from castella.core import (
    KeyAction,
    KeyCode,
    MouseEvent,
    Observer,
    Painter,
    Widget,
    WheelEvent,
)
from castella.models.events import CursorType
from castella.models.geometry import Point, Rect, Size
from castella.models.style import FillStyle, Font, SizePolicy, StrokeStyle, Style
from castella.state.observers import ObservableBase
from castella.theme import ThemeManager


# =============================================================================
# Enums
# =============================================================================


class SortDirection(Enum):
    """Sort direction for columns."""

    NONE = auto()
    ASC = auto()
    DESC = auto()


class SelectionMode(Enum):
    """Selection mode for rows."""

    NONE = auto()
    SINGLE = auto()
    MULTI = auto()


# =============================================================================
# Configuration Classes
# =============================================================================


@dataclass
class ColumnConfig:
    """Configuration for a single column.

    Attributes:
        name: Display name for the column header.
        width: Column width in pixels.
        min_width: Minimum width when resizing.
        sortable: Whether the column can be sorted.
        filterable: Whether the column can be filtered.
        editable: Whether cells in this column can be edited.
        visible: Whether the column is visible.
        renderer: Optional custom renderer function (value, row, col) -> str.
        tooltip: Optional tooltip text (from Pydantic Field.description).
        cell_bg_color: Optional callback (value, row, col) -> str for cell background.
        auto_contrast_text: Auto-adjust text color for contrast with cell_bg_color.
    """

    name: str
    width: float = 100.0
    min_width: float = 40.0
    sortable: bool = True
    filterable: bool = True
    editable: bool = False
    visible: bool = True
    renderer: Callable[[Any, int, int], str] | None = None
    tooltip: str | None = None
    cell_bg_color: Callable[[Any, int, int], str | None] | None = None
    auto_contrast_text: bool = True


def _infer_width_from_annotation(annotation: type | None) -> float:
    """Infer column width from Python type annotation.

    Uses Pydantic field annotations to determine appropriate column widths:
    - bool: 60px (narrow for checkboxes)
    - int: 80px (narrow for integers)
    - float: 100px (medium for floats)
    - str: 150px (wide for strings)
    - date/datetime: 120px (medium for dates)
    - other: 100px (default)
    """
    if annotation is None:
        return 100.0

    # Handle Optional, Union types - extract the first non-None type
    origin = get_origin(annotation)
    if origin is Union:
        args = get_args(annotation)
        for arg in args:
            if arg is not type(None):
                annotation = arg
                break

    # Type-based width inference
    if annotation is bool:
        return 60.0
    elif annotation is int:
        return 80.0
    elif annotation is float:
        return 100.0
    elif annotation is str:
        return 150.0
    elif annotation in (date, datetime):
        return 120.0
    else:
        return 100.0


# =============================================================================
# Heatmap Helper
# =============================================================================


@dataclass
class ValueRange:
    """Range for value normalization in heatmaps.

    Attributes:
        min_val: Minimum value.
        max_val: Maximum value.
    """

    min_val: float
    max_val: float

    @classmethod
    def from_values(cls, values: Sequence[float]) -> "ValueRange":
        """Create range from a sequence of values.

        Args:
            values: Sequence of numeric values.

        Returns:
            ValueRange with min/max computed from values.
        """
        if not values:
            return cls(0.0, 1.0)
        return cls(min(values), max(values))

    def normalize(self, value: float) -> float:
        """Normalize a value to 0.0-1.0 range.

        Args:
            value: Raw value to normalize.

        Returns:
            Normalized value between 0.0 and 1.0.
        """
        if self.max_val == self.min_val:
            return 0.5
        return (value - self.min_val) / (self.max_val - self.min_val)


class HeatmapConfig:
    """Configuration for heatmap cell coloring in DataTable.

    Provides easy integration of colormap-based cell backgrounds
    for numeric columns in a DataTable.

    Example:
        >>> from castella import DataTable, DataTableState, ColumnConfig, HeatmapConfig
        >>> from castella.chart import ColormapType
        >>>
        >>> state = DataTableState(
        ...     columns=[
        ...         ColumnConfig(name="City"),
        ...         ColumnConfig(name="Q1"),
        ...         ColumnConfig(name="Q2"),
        ...     ],
        ...     rows=[["NYC", 85, 72], ["LA", 78, 65]],
        ... )
        >>>
        >>> # Apply heatmap to numeric columns
        >>> heatmap = HeatmapConfig(colormap=ColormapType.VIRIDIS)
        >>> state.columns[1].cell_bg_color = heatmap.create_color_fn(col_idx=1, state=state)
        >>> state.columns[2].cell_bg_color = heatmap.create_color_fn(col_idx=2, state=state)
    """

    def __init__(
        self,
        colormap: Any = None,
        value_range: ValueRange | None = None,
        reverse: bool = False,
    ):
        """Initialize heatmap configuration.

        Args:
            colormap: Colormap to use (ColormapType, string, or Colormap instance).
                     Defaults to "viridis".
            value_range: Fixed value range for normalization.
                        If None, auto-detects from data.
            reverse: Whether to reverse the colormap.
        """
        from castella.chart.colormap import get_colormap, ColormapType

        if colormap is None:
            colormap = ColormapType.VIRIDIS

        if isinstance(colormap, (str, ColormapType)):
            self._colormap = get_colormap(colormap)
        else:
            self._colormap = colormap

        if reverse:
            self._colormap = self._colormap.reversed()

        self._value_range = value_range
        self._cached_ranges: dict[int, ValueRange] = {}

    def create_color_fn(
        self,
        col_idx: int,
        state: "DataTableState",
    ) -> Callable[[Any, int, int], str | None]:
        """Create a cell_bg_color callback for a column.

        Args:
            col_idx: Column index in the DataTable.
            state: DataTableState to extract values from.

        Returns:
            Callback function suitable for ColumnConfig.cell_bg_color.
        """
        # Pre-compute value range for this column
        if self._value_range:
            value_range = self._value_range
        else:
            values = []
            for row in state.rows:
                if col_idx < len(row):
                    val = row[col_idx]
                    if isinstance(val, (int, float)):
                        values.append(val)
            value_range = ValueRange.from_values(values)

        self._cached_ranges[col_idx] = value_range

        def color_fn(value: Any, row: int, col: int) -> str | None:
            if not isinstance(value, (int, float)):
                return None
            t = value_range.normalize(value)
            return self._colormap(t)

        return color_fn

    def get_color(self, value: float, col_idx: int | None = None) -> str:
        """Get color for a value.

        Args:
            value: Numeric value.
            col_idx: Optional column index for cached range lookup.

        Returns:
            Hex color string.
        """
        if self._value_range:
            t = self._value_range.normalize(value)
        elif col_idx is not None and col_idx in self._cached_ranges:
            t = self._cached_ranges[col_idx].normalize(value)
        else:
            t = 0.5  # Default to middle if no range available
        return self._colormap(t)


# =============================================================================
# Events
# =============================================================================


@dataclass
class CellClickEvent:
    """Event for cell click."""

    row: int  # Data row index
    column: int
    view_row: int  # View row index (after sort/filter)
    value: Any


@dataclass
class SortEvent:
    """Event for sort changes."""

    column: int
    direction: SortDirection


@dataclass
class SelectionChangeEvent:
    """Event for selection changes."""

    selected_rows: set[int]


@dataclass
class FilterChangeEvent:
    """Event for filter changes."""

    global_filter: str
    column_filters: dict[int, str]


# =============================================================================
# State Classes
# =============================================================================


class DataTableState(ObservableBase):
    """Observable state for DataTable.

    Manages:
    - Data (columns and rows)
    - Sort state
    - Filter state
    - Selection state
    - Scroll position
    - View indices (filtered/sorted mapping)
    """

    def __init__(
        self,
        columns: list[ColumnConfig],
        rows: list[list[Any]],
        selection_mode: SelectionMode = SelectionMode.SINGLE,
    ):
        super().__init__()
        self._columns = columns
        self._rows = rows
        self._selection_mode = selection_mode

        # Sort state
        self._sort_column: int | None = None
        self._sort_direction: SortDirection = SortDirection.NONE

        # Filter state
        self._global_filter: str = ""
        self._column_filters: dict[int, str] = {}

        # Selection state
        self._selected_rows: set[int] = set()
        self._focused_row: int = 0

        # Scroll state
        self._scroll_x: int = 0
        self._scroll_y: int = 0

        # View indices (maps view row -> data row)
        self._view_indices: list[int] = list(range(len(rows)))
        self._rebuild_view_indices()

    # -------------------------------------------------------------------------
    # Factory methods
    # -------------------------------------------------------------------------

    @staticmethod
    def from_pydantic(models: Sequence[BaseModel]) -> DataTableState:
        """Create state from Pydantic model instances.

        Leverages Pydantic metadata:
        - Field.title → column name
        - Field.description → column tooltip
        - Field.annotation → infer column width
        """
        if not models:
            return DataTableState(columns=[], rows=[])

        columns = []
        for name, field_info in models[0].model_fields.items():
            # Column name from title (fallback to field name)
            col_name = field_info.title if field_info.title else name

            # Tooltip from description
            tooltip = field_info.description

            # Width from annotation type
            width = _infer_width_from_annotation(field_info.annotation)

            columns.append(
                ColumnConfig(
                    name=col_name,
                    width=width,
                    sortable=True,
                    tooltip=tooltip,
                )
            )

        # Extract rows
        rows = [list(m.model_dump().values()) for m in models]

        return DataTableState(columns=columns, rows=rows)

    # -------------------------------------------------------------------------
    # Properties
    # -------------------------------------------------------------------------

    @property
    def columns(self) -> list[ColumnConfig]:
        return self._columns

    @property
    def rows(self) -> list[list[Any]]:
        return self._rows

    @property
    def row_count(self) -> int:
        return len(self._rows)

    @property
    def view_row_count(self) -> int:
        return len(self._view_indices)

    @property
    def column_count(self) -> int:
        return len(self._columns)

    @property
    def sort_column(self) -> int | None:
        return self._sort_column

    @property
    def sort_direction(self) -> SortDirection:
        return self._sort_direction

    @property
    def selected_rows(self) -> set[int]:
        return self._selected_rows.copy()

    @property
    def focused_row(self) -> int:
        return self._focused_row

    @property
    def selection_mode(self) -> SelectionMode:
        return self._selection_mode

    # -------------------------------------------------------------------------
    # Data access
    # -------------------------------------------------------------------------

    def get_value(self, row: int, col: int) -> Any:
        """Get value at data indices."""
        return self._rows[row][col]

    def get_view_value(self, view_row: int, col: int) -> Any:
        """Get value at view indices (after sort/filter)."""
        data_row = self._view_indices[view_row]
        return self._rows[data_row][col]

    def get_data_row(self, view_row: int) -> int:
        """Convert view row index to data row index."""
        return self._view_indices[view_row]

    def get_view_row(self, data_row: int) -> int | None:
        """Convert data row index to view row index, or None if filtered out."""
        try:
            return self._view_indices.index(data_row)
        except ValueError:
            return None

    def get_row_data(self, row: int) -> list[Any]:
        """Get all values for a data row."""
        return self._rows[row].copy()

    # -------------------------------------------------------------------------
    # Data mutation
    # -------------------------------------------------------------------------

    def set_value(self, row: int, col: int, value: Any) -> None:
        """Set value at data indices."""
        self._rows[row][col] = value
        self._rebuild_view_indices()
        self.notify()

    def add_row(self, row_data: list[Any]) -> None:
        """Add a new row."""
        self._rows.append(row_data)
        self._rebuild_view_indices()
        self.notify()

    def remove_row(self, row: int) -> None:
        """Remove a row by data index."""
        if 0 <= row < len(self._rows):
            self._rows.pop(row)
            self._selected_rows.discard(row)
            # Adjust selected rows indices
            self._selected_rows = {r - 1 if r > row else r for r in self._selected_rows}
            self._rebuild_view_indices()
            self.notify()

    def set_rows(self, rows: list[list[Any]]) -> None:
        """Replace all rows."""
        self._rows = rows
        self._selected_rows.clear()
        self._rebuild_view_indices()
        self.notify()

    # -------------------------------------------------------------------------
    # Sorting
    # -------------------------------------------------------------------------

    def set_sort(self, column: int | None, direction: SortDirection) -> None:
        """Set sort state."""
        self._sort_column = column
        self._sort_direction = direction
        self._rebuild_view_indices()
        self.notify()

    def toggle_sort(self, column: int) -> SortDirection:
        """Toggle sort on a column. Returns the new direction."""
        if not self._columns[column].sortable:
            return SortDirection.NONE

        if self._sort_column == column:
            # Cycle: NONE -> ASC -> DESC -> NONE
            if self._sort_direction == SortDirection.NONE:
                new_dir = SortDirection.ASC
            elif self._sort_direction == SortDirection.ASC:
                new_dir = SortDirection.DESC
            else:
                new_dir = SortDirection.NONE
                column = None  # type: ignore
        else:
            new_dir = SortDirection.ASC

        self.set_sort(column, new_dir)
        return new_dir

    # -------------------------------------------------------------------------
    # Filtering
    # -------------------------------------------------------------------------

    def set_filter(self, text: str) -> None:
        """Set global filter."""
        self._global_filter = text.lower()
        self._rebuild_view_indices()
        self.notify()

    def set_column_filter(self, column: int, text: str) -> None:
        """Set filter for a specific column."""
        if text:
            self._column_filters[column] = text.lower()
        else:
            self._column_filters.pop(column, None)
        self._rebuild_view_indices()
        self.notify()

    def clear_filters(self) -> None:
        """Clear all filters."""
        self._global_filter = ""
        self._column_filters.clear()
        self._rebuild_view_indices()
        self.notify()

    # -------------------------------------------------------------------------
    # Selection
    # -------------------------------------------------------------------------

    def select_row(self, row: int) -> None:
        """Select a single row (clears previous selection in SINGLE mode)."""
        if self._selection_mode == SelectionMode.NONE:
            return

        if self._selection_mode == SelectionMode.SINGLE:
            self._selected_rows = {row}
        else:
            self._selected_rows = {row}

        self._focused_row = row
        self.notify()

    def toggle_row(self, row: int) -> None:
        """Toggle selection on a row (for MULTI mode with Ctrl)."""
        if self._selection_mode != SelectionMode.MULTI:
            self.select_row(row)
            return

        if row in self._selected_rows:
            self._selected_rows.discard(row)
        else:
            self._selected_rows.add(row)

        self._focused_row = row
        self.notify()

    def select_range(self, from_row: int, to_row: int) -> None:
        """Select a range of rows (for MULTI mode with Shift)."""
        if self._selection_mode != SelectionMode.MULTI:
            self.select_row(to_row)
            return

        start, end = min(from_row, to_row), max(from_row, to_row)
        self._selected_rows = set(range(start, end + 1))
        self._focused_row = to_row
        self.notify()

    def clear_selection(self) -> None:
        """Clear all selection."""
        self._selected_rows.clear()
        self.notify()

    def is_row_selected(self, row: int) -> bool:
        """Check if a row is selected."""
        return row in self._selected_rows

    def set_focused_row(self, row: int) -> None:
        """Set focused row without changing selection."""
        self._focused_row = max(0, min(row, self.view_row_count - 1))
        self.notify()

    # -------------------------------------------------------------------------
    # Scroll
    # -------------------------------------------------------------------------

    @property
    def scroll_x(self) -> int:
        return self._scroll_x

    @scroll_x.setter
    def scroll_x(self, value: int) -> None:
        self._scroll_x = max(0, value)

    @property
    def scroll_y(self) -> int:
        return self._scroll_y

    @scroll_y.setter
    def scroll_y(self, value: int) -> None:
        self._scroll_y = max(0, value)

    # -------------------------------------------------------------------------
    # Internal
    # -------------------------------------------------------------------------

    def _rebuild_view_indices(self) -> None:
        """Rebuild view indices based on current filter and sort state."""
        # Start with all rows
        indices = list(range(len(self._rows)))

        # Apply global filter
        if self._global_filter:
            indices = [
                i
                for i in indices
                if any(self._global_filter in str(v).lower() for v in self._rows[i])
            ]

        # Apply column filters
        for col, filter_text in self._column_filters.items():
            indices = [
                i for i in indices if filter_text in str(self._rows[i][col]).lower()
            ]

        # Apply sort
        if self._sort_column is not None and self._sort_direction != SortDirection.NONE:
            col = self._sort_column
            reverse = self._sort_direction == SortDirection.DESC
            indices = sorted(
                indices,
                key=lambda i: self._sort_key(self._rows[i][col]),
                reverse=reverse,
            )

        self._view_indices = indices

    def _sort_key(self, value: Any) -> Any:
        """Generate sort key for a value."""
        if value is None:
            return (1, "")  # Nulls last
        if isinstance(value, (int, float)):
            return (0, value)
        return (0, str(value).lower())


# =============================================================================
# Legacy TableModel compatibility
# =============================================================================


class TableEvent(BaseModel):
    """Legacy event class for backward compatibility."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    source: Any
    row: int
    column: int
    old_value: Any = None
    new_value: Any = None


class TableModel(BaseModel):
    """Legacy TableModel for backward compatibility.

    Prefer using DataTableState directly for new code.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    column_names: list[str]
    data: list[list[Any]]

    _listeners: list[Observer] = PrivateAttr(default_factory=list)

    @staticmethod
    def from_pydantic_model(model: Sequence[BaseModel]) -> TableModel:
        """Create TableModel from Pydantic models."""
        if not model:
            return TableModel(column_names=[], data=[])

        column_names = [
            f.title if f.title else name for name, f in model[0].model_fields.items()
        ]
        data = [list(m.model_dump().values()) for m in model]
        return TableModel(column_names=column_names, data=data)

    def to_state(self) -> DataTableState:
        """Convert to DataTableState."""
        columns = [ColumnConfig(name=name) for name in self.column_names]
        return DataTableState(columns=columns, rows=self.data)

    def get_row_count(self) -> int:
        return len(self.data)

    def get_column_count(self) -> int:
        return len(self.column_names)

    def get_value_at(self, row: int, column: int) -> Any:
        return self.data[row][column]

    def attach(self, observer: Observer) -> None:
        self._listeners.append(observer)

    def detach(self, observer: Observer) -> None:
        self._listeners.remove(observer)

    def notify(self, event: Any = None) -> None:
        for listener in self._listeners:
            listener.on_notify(event)


# =============================================================================
# DataTable Widget
# =============================================================================

# Callback types
CellClickCallback = Callable[[CellClickEvent], None]
SortCallback = Callable[[SortEvent], None]
SelectionCallback = Callable[[SelectionChangeEvent], None]
FilterCallback = Callable[[FilterChangeEvent], None]

# Constants
HEADER_HEIGHT = 32.0
ROW_HEIGHT = 28.0
SCROLLBAR_SIZE = 10
RESIZE_ZONE = 5  # Pixels for column resize drag zone


class DataTable(Widget):
    """High-performance data table with sorting, filtering, and selection.

    Uses custom paint rendering for efficient handling of large datasets
    with virtual scrolling.
    """

    def __init__(
        self,
        state: DataTableState | TableModel,
        row_height: float = ROW_HEIGHT,
        header_height: float = HEADER_HEIGHT,
        show_grid_lines: bool = True,
        alternating_row_colors: bool = True,
        show_scrollbar: bool = True,
    ):
        # Convert legacy TableModel
        if isinstance(state, TableModel):
            state = state.to_state()

        super().__init__(
            state=state,
            size=Size(width=0, height=0),
            pos=Point(x=0, y=0),
            pos_policy=None,
            width_policy=SizePolicy.EXPANDING,
            height_policy=SizePolicy.EXPANDING,
        )

        self._row_height = row_height
        self._header_height = header_height
        self._show_grid_lines = show_grid_lines
        self._alternating_row_colors = alternating_row_colors
        self._show_scrollbar = show_scrollbar

        # Interaction state
        self._resizing_column: int | None = None
        self._resize_start_x: float = 0
        self._resize_start_width: float = 0
        self._hovered_row: int = -1
        self._hovered_col: int = -1
        self._scroll_dragging: bool = False
        self._scroll_drag_start_y: float = 0
        self._scroll_drag_start_offset: int = 0
        self._hovered_header_col: int = -1  # For header tooltip
        self._mouse_pos: Point | None = None

        # Callbacks
        self._on_cell_click: CellClickCallback | None = None
        self._on_cell_double_click: CellClickCallback | None = None
        self._on_sort: SortCallback | None = None
        self._on_selection_change: SelectionCallback | None = None
        self._on_filter_change: FilterCallback | None = None

        # Custom colors (None = use theme)
        self._header_bg_color: str | None = None
        self._header_text_color: str | None = None
        self._row_bg_color: str | None = None
        self._alt_row_bg_color: str | None = None
        self._grid_color: str | None = None
        self._selected_bg_color: str | None = None
        self._hover_bg_color: str | None = None

        # Theme
        self._theme = ThemeManager()

    # -------------------------------------------------------------------------
    # Fluent API
    # -------------------------------------------------------------------------

    def on_cell_click(self, callback: CellClickCallback) -> Self:
        """Register callback for cell click events."""
        self._on_cell_click = callback
        return self

    def on_cell_double_click(self, callback: CellClickCallback) -> Self:
        """Register callback for cell double-click events."""
        self._on_cell_double_click = callback
        return self

    def on_sort(self, callback: SortCallback) -> Self:
        """Register callback for sort changes."""
        self._on_sort = callback
        return self

    def on_selection_change(self, callback: SelectionCallback) -> Self:
        """Register callback for selection changes."""
        self._on_selection_change = callback
        return self

    def on_filter_change(self, callback: FilterCallback) -> Self:
        """Register callback for filter changes."""
        self._on_filter_change = callback
        return self

    def header_bg_color(self, color: str) -> Self:
        """Set header background color."""
        self._header_bg_color = color
        return self

    def header_text_color(self, color: str) -> Self:
        """Set header text color."""
        self._header_text_color = color
        return self

    def row_bg_color(self, color: str) -> Self:
        """Set row background color."""
        self._row_bg_color = color
        return self

    def alt_row_bg_color(self, color: str) -> Self:
        """Set alternating row background color."""
        self._alt_row_bg_color = color
        return self

    def grid_color(self, color: str) -> Self:
        """Set grid line color."""
        self._grid_color = color
        return self

    def selected_bg_color(self, color: str) -> Self:
        """Set selected row background color."""
        self._selected_bg_color = color
        return self

    def hover_bg_color(self, color: str) -> Self:
        """Set hover row background color."""
        self._hover_bg_color = color
        return self

    # -------------------------------------------------------------------------
    # State access
    # -------------------------------------------------------------------------

    def _get_state(self) -> DataTableState:
        from typing import cast

        return cast(DataTableState, self._state)

    # -------------------------------------------------------------------------
    # Geometry calculations
    # -------------------------------------------------------------------------

    def _get_content_width(self) -> float:
        """Get total content width (sum of all column widths)."""
        state = self._get_state()
        return sum(c.width for c in state.columns if c.visible)

    def _get_content_height(self) -> float:
        """Get total content height (header + all rows)."""
        state = self._get_state()
        return self._header_height + state.view_row_count * self._row_height

    def _get_viewport_width(self) -> float:
        """Get viewport width (minus scrollbar if needed)."""
        width = self.get_width()
        if self._needs_vertical_scrollbar():
            width -= SCROLLBAR_SIZE
        return max(0, width)

    def _get_viewport_height(self) -> float:
        """Get viewport height for data rows."""
        return max(0, self.get_height() - self._header_height)

    def _needs_vertical_scrollbar(self) -> bool:
        """Check if vertical scrollbar is needed."""
        if not self._show_scrollbar:
            return False
        state = self._get_state()
        content_height = state.view_row_count * self._row_height
        viewport_height = self.get_height() - self._header_height
        return content_height > viewport_height

    def _get_visible_row_range(self) -> tuple[int, int]:
        """Get range of visible rows [start, end)."""
        state = self._get_state()
        viewport_height = self._get_viewport_height()

        start = int(state.scroll_y / self._row_height)
        visible_count = int(viewport_height / self._row_height) + 2
        end = min(start + visible_count, state.view_row_count)

        return max(0, start), end

    def _get_column_x_positions(self) -> list[float]:
        """Get x positions for each column."""
        state = self._get_state()
        positions = []
        x = 0.0
        for col in state.columns:
            if col.visible:
                positions.append(x)
                x += col.width
            else:
                positions.append(-1)  # Hidden
        return positions

    def _get_column_at_x(self, x: float) -> int | None:
        """Get column index at x position."""
        state = self._get_state()
        scroll_x = state.scroll_x
        x_in_content = x + scroll_x

        acc = 0.0
        for i, col in enumerate(state.columns):
            if not col.visible:
                continue
            if acc <= x_in_content < acc + col.width:
                return i
            acc += col.width

        return None

    def _get_row_at_y(self, y: float) -> int | None:
        """Get view row index at y position (in data area)."""
        state = self._get_state()

        # Subtract header height
        y_in_data = y - self._header_height
        if y_in_data < 0:
            return None

        # Account for scroll
        y_in_content = y_in_data + state.scroll_y
        row = int(y_in_content / self._row_height)

        if 0 <= row < state.view_row_count:
            return row
        return None

    def _is_in_header(self, y: float) -> bool:
        """Check if y position is in header area."""
        return 0 <= y < self._header_height

    def _is_on_column_border(self, x: float) -> int | None:
        """Check if x position is on a column border. Returns column index or None."""
        state = self._get_state()
        scroll_x = state.scroll_x
        x_in_content = x + scroll_x

        acc = 0.0
        for i, col in enumerate(state.columns):
            if not col.visible:
                continue
            acc += col.width
            # Check if near border
            if abs(x_in_content - acc) <= RESIZE_ZONE:
                return i
            if x_in_content < acc:
                break

        return None

    def _is_in_scrollbar(self, pos: Point) -> bool:
        """Check if position is in scrollbar area."""
        if not self._needs_vertical_scrollbar():
            return False
        width = self.get_width()
        return pos.x >= width - SCROLLBAR_SIZE and pos.y >= self._header_height

    # -------------------------------------------------------------------------
    # Scrolling
    # -------------------------------------------------------------------------

    def _scroll(self, delta_y: int) -> None:
        """Apply scroll delta."""
        state = self._get_state()
        content_height = state.view_row_count * self._row_height
        viewport_height = self._get_viewport_height()
        max_scroll = max(0, content_height - viewport_height)

        new_scroll = state.scroll_y - delta_y
        state.scroll_y = max(0, min(int(new_scroll), int(max_scroll)))

        self.dirty(True)
        self.update()

    def _ensure_row_visible(self, view_row: int) -> None:
        """Scroll to make a row visible."""
        state = self._get_state()
        viewport_height = self._get_viewport_height()

        row_top = view_row * self._row_height
        row_bottom = row_top + self._row_height

        if row_top < state.scroll_y:
            # Row is above viewport
            state.scroll_y = int(row_top)
        elif row_bottom > state.scroll_y + viewport_height:
            # Row is below viewport
            state.scroll_y = int(row_bottom - viewport_height)

    # -------------------------------------------------------------------------
    # Mouse event handlers
    # -------------------------------------------------------------------------

    def mouse_down(self, ev: MouseEvent) -> None:
        """Handle mouse down."""
        state = self._get_state()
        pos = ev.pos

        # Check scrollbar
        if self._is_in_scrollbar(pos):
            self._scroll_dragging = True
            self._scroll_drag_start_y = pos.y
            self._scroll_drag_start_offset = state.scroll_y
            return

        # Check column resize
        if self._is_in_header(pos.y):
            resize_col = self._is_on_column_border(pos.x)
            if resize_col is not None:
                self._resizing_column = resize_col
                self._resize_start_x = pos.x
                self._resize_start_width = state.columns[resize_col].width
                return

    def mouse_up(self, ev: MouseEvent) -> None:
        """Handle mouse up."""
        state = self._get_state()
        pos = ev.pos

        # End scrollbar drag
        if self._scroll_dragging:
            self._scroll_dragging = False
            return

        # End column resize
        if self._resizing_column is not None:
            self._resizing_column = None
            return

        # Header click (sort)
        if self._is_in_header(pos.y):
            col = self._get_column_at_x(pos.x)
            if col is not None:
                new_dir = state.toggle_sort(col)
                if self._on_sort:
                    self._on_sort(SortEvent(column=col, direction=new_dir))
            return

        # Row click (selection)
        row = self._get_row_at_y(pos.y)
        col = self._get_column_at_x(pos.x)
        if row is not None:
            # Handle selection (modifier keys not supported yet)
            data_row = state.get_data_row(row)
            state.select_row(row)

            self._ensure_row_visible(row)

            # Fire selection callback
            if self._on_selection_change:
                self._on_selection_change(
                    SelectionChangeEvent(selected_rows=state.selected_rows)
                )

            # Fire cell click callback
            if self._on_cell_click and col is not None:
                self._on_cell_click(
                    CellClickEvent(
                        row=data_row,
                        column=col,
                        view_row=row,
                        value=state.get_view_value(row, col),
                    )
                )

        self.dirty(True)
        self.update()

    def mouse_drag(self, ev: MouseEvent) -> None:
        """Handle mouse drag."""
        state = self._get_state()
        pos = ev.pos

        # Scrollbar drag
        if self._scroll_dragging:
            viewport_height = self._get_viewport_height()
            content_height = state.view_row_count * self._row_height
            if content_height > viewport_height:
                delta_y = pos.y - self._scroll_drag_start_y
                scroll_ratio = delta_y / viewport_height
                new_scroll = self._scroll_drag_start_offset + int(
                    scroll_ratio * content_height
                )
                state.scroll_y = max(
                    0, min(new_scroll, int(content_height - viewport_height))
                )
                self.dirty(True)
                self.update()
            return

        # Column resize
        if self._resizing_column is not None:
            col = self._resizing_column
            delta = pos.x - self._resize_start_x
            new_width = max(
                state.columns[col].min_width, self._resize_start_width + delta
            )
            state.columns[col].width = new_width
            self.dirty(True)
            self.update()

    def cursor_pos(self, ev: MouseEvent) -> None:
        """Handle cursor position (hover)."""
        pos = ev.pos
        self._mouse_pos = pos

        # Update cursor shape for column resize
        from castella.core import App

        app = App._instance
        if self._is_in_header(pos.y) and self._is_on_column_border(pos.x) is not None:
            if app and app._frame:
                app._frame.set_cursor(CursorType.RESIZE_H)
        else:
            if app and app._frame:
                app._frame.set_cursor(CursorType.ARROW)

        new_row = self._get_row_at_y(pos.y) if not self._is_in_header(pos.y) else -1
        new_col = self._get_column_at_x(pos.x) or -1

        # Track header hover for tooltip
        new_header_col = -1
        if self._is_in_header(pos.y):
            new_header_col = self._get_column_at_x(pos.x) or -1

        needs_update = False
        if new_row != self._hovered_row or new_col != self._hovered_col:
            self._hovered_row = new_row if new_row is not None else -1
            self._hovered_col = new_col
            needs_update = True

        if new_header_col != self._hovered_header_col:
            self._hovered_header_col = new_header_col
            needs_update = True

        if needs_update:
            self.dirty(True)
            self.update()

    def mouse_out(self) -> None:
        """Handle mouse leaving the widget."""
        # Reset cursor to default when leaving the widget
        from castella.core import App

        app = App._instance
        if app and app._frame:
            app._frame.set_cursor(CursorType.ARROW)

        needs_update = False
        if self._hovered_row != -1 or self._hovered_col != -1:
            self._hovered_row = -1
            self._hovered_col = -1
            needs_update = True
        if self._hovered_header_col != -1:
            self._hovered_header_col = -1
            needs_update = True
        self._mouse_pos = None
        if needs_update:
            self.dirty(True)
            self.update()

    def mouse_wheel(self, ev: WheelEvent) -> None:
        """Handle mouse wheel."""
        self._scroll(int(ev.y_offset))

    def dispatch_to_scrollable(
        self, p: Point, is_direction_x: bool
    ) -> tuple["Widget | None", "Point | None"]:
        """Return self if this widget can handle scroll events at point p."""
        # Handle vertical scrolling when point is within widget
        if not is_direction_x and self.contain(p):
            return self, p
        return None, None

    # -------------------------------------------------------------------------
    # Keyboard event handlers
    # -------------------------------------------------------------------------

    def input_key(self, ev) -> None:
        """Handle keyboard input."""
        if ev.action == KeyAction.RELEASE:
            return

        state = self._get_state()

        if ev.key == KeyCode.UP:
            new_row = max(0, state.focused_row - 1)
            if ev.is_shift and state.selection_mode == SelectionMode.MULTI:
                state.select_range(state.focused_row, new_row)
            else:
                state.select_row(new_row)
            self._ensure_row_visible(new_row)

        elif ev.key == KeyCode.DOWN:
            new_row = min(state.view_row_count - 1, state.focused_row + 1)
            if ev.is_shift and state.selection_mode == SelectionMode.MULTI:
                state.select_range(state.focused_row, new_row)
            else:
                state.select_row(new_row)
            self._ensure_row_visible(new_row)

        elif ev.key == KeyCode.HOME:
            state.select_row(0)
            self._ensure_row_visible(0)

        elif ev.key == KeyCode.END:
            last_row = state.view_row_count - 1
            state.select_row(last_row)
            self._ensure_row_visible(last_row)

        elif ev.key == KeyCode.PAGE_UP:
            visible_rows = int(self._get_viewport_height() / self._row_height)
            new_row = max(0, state.focused_row - visible_rows)
            state.select_row(new_row)
            self._ensure_row_visible(new_row)

        elif ev.key == KeyCode.PAGE_DOWN:
            visible_rows = int(self._get_viewport_height() / self._row_height)
            new_row = min(state.view_row_count - 1, state.focused_row + visible_rows)
            state.select_row(new_row)
            self._ensure_row_visible(new_row)

        elif ev.key == KeyCode.SPACE:
            state.toggle_row(state.focused_row)

        if self._on_selection_change:
            self._on_selection_change(
                SelectionChangeEvent(selected_rows=state.selected_rows)
            )

        self.dirty(True)
        self.update()

    # -------------------------------------------------------------------------
    # Rendering
    # -------------------------------------------------------------------------

    def redraw(self, p: Painter, completely: bool) -> None:
        """Render the table."""
        size = self.get_size()
        if size.width <= 0 or size.height <= 0:
            return

        state = self._get_state()
        theme = self._theme.current

        # Draw background
        bg_color = theme.colors.bg_primary
        p.style(Style(fill=FillStyle(color=bg_color)))
        p.fill_rect(Rect(origin=Point(x=0, y=0), size=size))

        # Draw rows first (clipped to data area)
        self._render_rows(p, state, theme)

        # Draw header after rows so it appears on top when scrolling
        self._render_header(p, state, theme)

        # Draw scrollbar
        if self._needs_vertical_scrollbar():
            self._render_scrollbar(p, state, theme)

        # Draw header tooltip (must be last to appear on top)
        self._render_header_tooltip(p, state, theme)

    def _render_header(self, p: Painter, state: DataTableState, theme) -> None:
        """Render the header row."""
        # Use full width for header (scrollbar is only in data area, not header)
        width = self.get_width()

        # Header background (custom or theme)
        header_bg = self._header_bg_color or theme.colors.bg_secondary
        p.style(Style(fill=FillStyle(color=header_bg)))
        p.fill_rect(
            Rect(
                origin=Point(x=0, y=0),
                size=Size(width=width, height=self._header_height),
            )
        )

        # Header text and sort indicators (custom or theme)
        text_color = self._header_text_color or theme.colors.text_primary
        font_size = 14
        p.style(Style(fill=FillStyle(color=text_color), font=Font(size=font_size)))

        x = -state.scroll_x
        for i, col in enumerate(state.columns):
            if not col.visible:
                continue

            # Clip to column
            if x + col.width > 0 and x < width:
                # Column text
                text = col.name
                text_x = x + 8
                text_y = (self._header_height + font_size) / 2

                p.fill_text(text, Point(x=text_x, y=text_y), None)

                # Sort indicator
                if state.sort_column == i:
                    indicator = (
                        " ▲" if state.sort_direction == SortDirection.ASC else " ▼"
                    )
                    text_width = p.measure_text(text)
                    p.fill_text(indicator, Point(x=text_x + text_width, y=text_y), None)

            x += col.width

        # Header border
        if self._show_grid_lines:
            border_color = self._grid_color or theme.colors.border_primary
            p.style(Style(stroke=StrokeStyle(color=border_color, width=1)))
            p.stroke_rect(
                Rect(
                    origin=Point(x=0, y=0),
                    size=Size(width=width, height=self._header_height),
                )
            )

    def _render_rows(self, p: Painter, state: DataTableState, theme) -> None:
        """Render data rows with virtual scrolling."""
        width = self._get_viewport_width()
        viewport_height = self._get_viewport_height()
        start_row, end_row = self._get_visible_row_range()

        # Clip to data area
        p.save()
        # Add row_height margin to clip to handle boundary issues where last row
        # would otherwise be clipped even when scroll is at max
        clip_height = viewport_height + self._row_height
        clip_rect = Rect(
            origin=Point(x=0, y=self._header_height),
            size=Size(width=width, height=clip_height),
        )
        p.clip(clip_rect)

        font_size = 13
        text_color = theme.colors.text_primary

        # Use custom colors or fall back to theme
        row_bg = self._row_bg_color  # None means transparent
        alt_bg = self._alt_row_bg_color or (
            theme.colors.bg_tertiary
            if hasattr(theme.colors, "bg_tertiary")
            else theme.colors.bg_secondary
        )
        selected_bg = self._selected_bg_color or (
            theme.colors.text_info if hasattr(theme.colors, "text_info") else "#3b82f6"
        )
        hover_bg = self._hover_bg_color or theme.colors.bg_secondary

        for view_row in range(start_row, end_row):
            data_row = state.get_data_row(view_row)
            y = self._header_height + view_row * self._row_height - state.scroll_y

            # Skip if fully outside viewport
            if y + self._row_height < self._header_height or y > self.get_height():
                continue

            # Row background
            is_selected = state.is_row_selected(view_row)
            is_hovered = view_row == self._hovered_row

            if is_selected:
                bg = selected_bg
                fg = "#ffffff"
            elif is_hovered:
                bg = hover_bg
                fg = text_color
            elif self._alternating_row_colors and view_row % 2 == 1:
                bg = alt_bg
                fg = text_color
            else:
                bg = row_bg
                fg = text_color

            if bg:
                p.style(Style(fill=FillStyle(color=bg)))
                p.fill_rect(
                    Rect(
                        origin=Point(x=0, y=y),
                        size=Size(width=width, height=self._row_height),
                    )
                )

            # Cell text
            x = -state.scroll_x
            for col_idx, col in enumerate(state.columns):
                if not col.visible:
                    continue

                if x + col.width > 0 and x < width:
                    value = state.get_view_value(view_row, col_idx)

                    # Check for cell-level background color
                    cell_bg = None
                    cell_fg = fg
                    if col.cell_bg_color:
                        cell_bg = col.cell_bg_color(value, data_row, col_idx)
                        if cell_bg and col.auto_contrast_text:
                            from castella.utils.color import contrast_text_color

                            cell_fg = contrast_text_color(cell_bg)

                    # Draw cell background if specified
                    if cell_bg:
                        p.style(Style(fill=FillStyle(color=cell_bg)))
                        p.fill_rect(
                            Rect(
                                origin=Point(x=max(0, x), y=y),
                                size=Size(
                                    width=min(col.width, width - max(0, x)),
                                    height=self._row_height,
                                ),
                            )
                        )

                    # Use custom renderer if provided
                    if col.renderer:
                        text = col.renderer(value, data_row, col_idx)
                    else:
                        text = str(value) if value is not None else ""

                    # Truncate if too long
                    max_text_width = col.width - 16
                    p.style(
                        Style(fill=FillStyle(color=cell_fg), font=Font(size=font_size))
                    )
                    while p.measure_text(text) > max_text_width and len(text) > 1:
                        text = text[:-2] + "…"

                    text_x = x + 8
                    text_y = y + (self._row_height + font_size) / 2 - 2

                    p.fill_text(text, Point(x=text_x, y=text_y), None)

                x += col.width

            # Row border (horizontal line)
            if self._show_grid_lines:
                border_color = self._grid_color or theme.colors.border_primary
                p.style(Style(fill=FillStyle(color=border_color)))
                p.fill_rect(
                    Rect(
                        origin=Point(x=0, y=y + self._row_height - 0.5),
                        size=Size(width=width, height=1),
                    )
                )

        # Column grid lines (vertical lines)
        if self._show_grid_lines:
            border_color = self._grid_color or theme.colors.border_primary
            p.style(Style(fill=FillStyle(color=border_color)))
            x = -state.scroll_x
            for col in state.columns:
                if not col.visible:
                    continue
                x += col.width
                if 0 < x < width:
                    p.fill_rect(
                        Rect(
                            origin=Point(x=x - 0.5, y=self._header_height),
                            size=Size(width=1, height=viewport_height),
                        )
                    )

        p.restore()

    def _render_scrollbar(self, p: Painter, state: DataTableState, theme) -> None:
        """Render vertical scrollbar."""
        width = self.get_width()
        viewport_height = self._get_viewport_height()
        content_height = state.view_row_count * self._row_height

        if content_height <= 0:
            return

        # Scrollbar track
        track_color = theme.colors.bg_secondary
        p.style(Style(fill=FillStyle(color=track_color)))
        p.fill_rect(
            Rect(
                origin=Point(x=width - SCROLLBAR_SIZE, y=self._header_height),
                size=Size(width=SCROLLBAR_SIZE, height=viewport_height),
            )
        )

        # Scrollbar thumb
        thumb_height = max(20, (viewport_height / content_height) * viewport_height)
        thumb_y = (
            self._header_height + (state.scroll_y / content_height) * viewport_height
        )

        thumb_color = (
            theme.colors.text_secondary
            if hasattr(theme.colors, "text_secondary")
            else "#888888"
        )
        p.style(Style(fill=FillStyle(color=thumb_color), border_radius=4))
        p.fill_rect(
            Rect(
                origin=Point(x=width - SCROLLBAR_SIZE + 2, y=thumb_y),
                size=Size(width=SCROLLBAR_SIZE - 4, height=thumb_height),
            )
        )

    def _render_header_tooltip(self, p: Painter, state: DataTableState, theme) -> None:
        """Render tooltip for hovered header column."""
        if self._hovered_header_col < 0 or self._mouse_pos is None:
            return

        col_idx = self._hovered_header_col
        if col_idx >= len(state.columns):
            return

        col = state.columns[col_idx]
        if not col.tooltip:
            return

        # Build tooltip text
        text = col.tooltip

        # Measure text
        font_size = 12
        p.style(Style(font=Font(size=font_size)))
        text_width = p.measure_text(text)
        text_height = font_size + 2
        padding = 6

        # Calculate tooltip dimensions
        tooltip_width = text_width + padding * 2
        tooltip_height = text_height + padding * 2

        # Position below header, near mouse
        x = self._mouse_pos.x - tooltip_width / 2
        y = self._header_height + 4

        # Clamp to widget bounds
        size = self.get_size()
        x = max(4, min(x, size.width - tooltip_width - 4))

        # Draw tooltip background
        bg_rect = Rect(
            origin=Point(x=x, y=y),
            size=Size(width=tooltip_width, height=tooltip_height),
        )
        bg_color = (
            theme.colors.bg_tertiary
            if hasattr(theme.colors, "bg_tertiary")
            else "#333333"
        )
        border_color = (
            theme.colors.border_primary
            if hasattr(theme.colors, "border_primary")
            else "#555555"
        )
        p.style(
            Style(
                fill=FillStyle(color=bg_color),
                stroke=StrokeStyle(color=border_color),
                border_radius=4,
            )
        )
        p.fill_rect(bg_rect)
        p.stroke_rect(bg_rect)

        # Draw text
        text_color = (
            theme.colors.text_primary
            if hasattr(theme.colors, "text_primary")
            else "#ffffff"
        )
        p.style(Style(fill=FillStyle(color=text_color), font=Font(size=font_size)))
        p.fill_text(text, Point(x=x + padding, y=y + padding + text_height - 4), None)

    # -------------------------------------------------------------------------
    # Measurement
    # -------------------------------------------------------------------------

    def measure(self, p: Painter) -> Size:
        """Measure preferred size."""
        state = self._get_state()
        width = sum(c.width for c in state.columns if c.visible)
        height = self._header_height + min(10, state.view_row_count) * self._row_height
        return Size(width=width, height=height)
