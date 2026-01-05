"""Heatmap chart data model."""

from __future__ import annotations

from typing import Self, Sequence

from pydantic import Field, PrivateAttr

from castella.chart.models.chart_data import ChartDataBase


class HeatmapChartData(ChartDataBase):
    """Data model for heatmap charts.

    Stores a 2D matrix of values with row and column labels.
    Supports automatic or manual value range for color normalization.

    Attributes:
        values: 2D matrix of values (list of rows).
        row_labels: Labels for each row.
        column_labels: Labels for each column.
        value_format: Format string for value display (e.g., "{:.2f}").
        min_value: Minimum value for color scale (None = auto from data).
        max_value: Maximum value for color scale (None = auto from data).

    Example:
        >>> data = HeatmapChartData.from_2d_array(
        ...     values=[[1, 2, 3], [4, 5, 6], [7, 8, 9]],
        ...     row_labels=["A", "B", "C"],
        ...     column_labels=["X", "Y", "Z"],
        ...     title="Correlation Matrix",
        ... )
        >>> data.get_value(0, 1)
        2.0
        >>> data.normalize_value(5.0)
        0.5
    """

    values: list[list[float]] = Field(default_factory=list)
    row_labels: list[str] = Field(default_factory=list)
    column_labels: list[str] = Field(default_factory=list)
    value_format: str = "{:.2f}"
    min_value: float | None = None
    max_value: float | None = None

    # Cached computed values
    _computed_min: float = PrivateAttr(default=0.0)
    _computed_max: float = PrivateAttr(default=1.0)

    def model_post_init(self, __context) -> None:
        """Compute min/max after initialization."""
        self._recompute_range()

    def _recompute_range(self) -> None:
        """Recompute the value range from data."""
        if not self.values or not self.values[0]:
            self._computed_min = 0.0
            self._computed_max = 1.0
            return

        all_values = [v for row in self.values for v in row]
        self._computed_min = min(all_values) if all_values else 0.0
        self._computed_max = max(all_values) if all_values else 1.0

    @property
    def num_rows(self) -> int:
        """Number of rows in the matrix."""
        return len(self.values)

    @property
    def num_cols(self) -> int:
        """Number of columns in the matrix."""
        if not self.values:
            return 0
        return len(self.values[0])

    @property
    def effective_min(self) -> float:
        """Get the effective minimum value for color scaling.

        Returns manual min_value if set, otherwise auto-computed from data.
        """
        return self.min_value if self.min_value is not None else self._computed_min

    @property
    def effective_max(self) -> float:
        """Get the effective maximum value for color scaling.

        Returns manual max_value if set, otherwise auto-computed from data.
        """
        return self.max_value if self.max_value is not None else self._computed_max

    def get_value(self, row: int, col: int) -> float:
        """Get value at row, col position.

        Args:
            row: Row index (0-based).
            col: Column index (0-based).

        Returns:
            Value at the specified position, or 0.0 if out of bounds.
        """
        if 0 <= row < self.num_rows and 0 <= col < self.num_cols:
            return self.values[row][col]
        return 0.0

    def get_row_label(self, row: int) -> str:
        """Get label for a row.

        Args:
            row: Row index (0-based).

        Returns:
            Label for the row, or row index as string if no label defined.
        """
        if 0 <= row < len(self.row_labels):
            return self.row_labels[row]
        return str(row)

    def get_column_label(self, col: int) -> str:
        """Get label for a column.

        Args:
            col: Column index (0-based).

        Returns:
            Label for the column, or column index as string if no label defined.
        """
        if 0 <= col < len(self.column_labels):
            return self.column_labels[col]
        return str(col)

    def normalize_value(self, value: float) -> float:
        """Normalize a value to 0.0-1.0 range for colormap.

        Args:
            value: Raw data value.

        Returns:
            Normalized value between 0.0 and 1.0.
        """
        v_min = self.effective_min
        v_max = self.effective_max
        if v_max == v_min:
            return 0.5
        return (value - v_min) / (v_max - v_min)

    def set_values(self, values: list[list[float]]) -> Self:
        """Set the value matrix and notify observers.

        Args:
            values: New 2D value matrix.

        Returns:
            Self for chaining.
        """
        self.values = values
        self._recompute_range()
        self.notify()
        return self

    def set_cell(self, row: int, col: int, value: float) -> Self:
        """Set a single cell value and notify observers.

        Args:
            row: Row index.
            col: Column index.
            value: New value.

        Returns:
            Self for chaining.
        """
        if 0 <= row < self.num_rows and 0 <= col < self.num_cols:
            # Create new row list to maintain immutability pattern
            new_row = list(self.values[row])
            new_row[col] = value
            new_values = list(self.values)
            new_values[row] = new_row
            self.values = new_values
            self._recompute_range()
            self.notify()
        return self

    def set_row_labels(self, labels: list[str]) -> Self:
        """Set row labels and notify observers.

        Args:
            labels: New row labels.

        Returns:
            Self for chaining.
        """
        self.row_labels = labels
        self.notify()
        return self

    def set_column_labels(self, labels: list[str]) -> Self:
        """Set column labels and notify observers.

        Args:
            labels: New column labels.

        Returns:
            Self for chaining.
        """
        self.column_labels = labels
        self.notify()
        return self

    def set_range(
        self,
        min_value: float | None = None,
        max_value: float | None = None,
    ) -> Self:
        """Set the value range for color normalization.

        Args:
            min_value: Minimum value (None for auto).
            max_value: Maximum value (None for auto).

        Returns:
            Self for chaining.
        """
        self.min_value = min_value
        self.max_value = max_value
        self.notify()
        return self

    @classmethod
    def from_2d_array(
        cls,
        values: Sequence[Sequence[float]],
        row_labels: Sequence[str] | None = None,
        column_labels: Sequence[str] | None = None,
        title: str = "",
    ) -> HeatmapChartData:
        """Create heatmap data from a 2D array.

        Args:
            values: 2D array of values (list of rows).
            row_labels: Optional row labels. Defaults to row indices.
            column_labels: Optional column labels. Defaults to column indices.
            title: Chart title.

        Returns:
            New HeatmapChartData instance.

        Example:
            >>> data = HeatmapChartData.from_2d_array(
            ...     values=[[1, 2], [3, 4]],
            ...     row_labels=["A", "B"],
            ...     column_labels=["X", "Y"],
            ... )
        """
        num_rows = len(values)
        num_cols = len(values[0]) if values else 0

        return cls(
            title=title,
            values=[list(row) for row in values],
            row_labels=(
                list(row_labels) if row_labels else [str(i) for i in range(num_rows)]
            ),
            column_labels=(
                list(column_labels)
                if column_labels
                else [str(i) for i in range(num_cols)]
            ),
        )
