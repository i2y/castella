"""Enhanced DataTable demo with sorting, filtering, selection, and column resize."""

from castella import (
    App,
    Button,
    Column,
    DataTable,
    DataTableState,
    ColumnConfig,
    Input,
    Row,
    SelectionMode,
    SortDirection,
    Text,
)
from castella.core import SizePolicy, State, StatefulComponent
from castella.frame import Frame


# Sample data
SAMPLE_DATA = [
    ["Alice", 30, "Japan", "Engineer"],
    ["Bob", 25, "USA", "Designer"],
    ["Charlie", 35, "UK", "Manager"],
    ["Diana", 28, "Germany", "Developer"],
    ["Eve", 32, "France", "Analyst"],
    ["Frank", 27, "Italy", "Consultant"],
    ["Grace", 29, "Spain", "Architect"],
    ["Henry", 31, "Canada", "Scientist"],
    ["Ivy", 26, "Australia", "Artist"],
    ["Jack", 33, "Japan", "Engineer"],
    ["Kate", 24, "USA", "Designer"],
    ["Leo", 36, "UK", "Director"],
    ["Mia", 22, "Germany", "Intern"],
    ["Nick", 38, "France", "VP"],
    ["Olivia", 34, "Italy", "Lead"],
    ["Paul", 29, "Spain", "Senior"],
    ["Quinn", 27, "Canada", "Junior"],
    ["Rose", 31, "Australia", "Principal"],
    ["Sam", 25, "Japan", "Associate"],
    ["Tina", 30, "USA", "Specialist"],
]


class TableDemo(StatefulComponent):
    """Demo component showcasing enhanced DataTable features."""

    def __init__(self):
        # Create table state with column configs
        self._table_state = DataTableState(
            columns=[
                ColumnConfig(name="Name", width=120, sortable=True),
                ColumnConfig(name="Age", width=80, sortable=True),
                ColumnConfig(name="Country", width=120, sortable=True),
                ColumnConfig(name="Role", width=150, sortable=True),
            ],
            rows=[row.copy() for row in SAMPLE_DATA],
            selection_mode=SelectionMode.MULTI,
        )
        # Don't attach _table_state - DataTable manages its own state observation

        # Filter state - don't attach, Input manages its own state
        self._filter_text = State("")

        # Status state - only this triggers view rebuild
        self._status = State("Ready")
        super().__init__(self._status)

    def _on_filter_change(self, text: str) -> None:
        self._filter_text.set(text)
        self._table_state.set_filter(text)

    def _on_sort(self, event) -> None:
        dir_name = (
            "ASC"
            if event.direction == SortDirection.ASC
            else "DESC" if event.direction == SortDirection.DESC else "NONE"
        )
        col_name = self._table_state.columns[event.column].name
        self._status.set(f"Sorted by {col_name} ({dir_name})")

    def _on_selection_change(self, event) -> None:
        count = len(event.selected_rows)
        self._status.set(f"Selected {count} row(s)")

    def _on_cell_click(self, event) -> None:
        col_name = self._table_state.columns[event.column].name
        self._status.set(f"Clicked: {col_name} = {event.value}")

    def _clear_filter(self, _) -> None:
        self._filter_text.set("")
        self._table_state.clear_filters()
        self._status.set("Filter cleared")

    def _clear_selection(self, _) -> None:
        self._table_state.clear_selection()
        self._status.set("Selection cleared")

    def view(self):
        return Column(
            # Header
            Text("Enhanced DataTable Demo")
            .fixed_height(40),
            # Filter row
            Row(
                Text("Filter:").fixed_width(60),
                Input(self._filter_text())
                .on_change(self._on_filter_change)
                .flex(1),
                Button("Clear").on_click(self._clear_filter).width(80).width_policy(
                    SizePolicy.FIXED
                ),
                Button("Deselect").on_click(self._clear_selection).width(80).width_policy(
                    SizePolicy.FIXED
                ),
            )
            .fixed_height(40),
            # Table
            DataTable(self._table_state)
            .on_sort(self._on_sort)
            .on_selection_change(self._on_selection_change)
            .on_cell_click(self._on_cell_click),
            # Status bar
            Row(
                Text(f"Rows: {self._table_state.view_row_count}/{self._table_state.row_count}"),
                Text(self._status()).flex(1),
            )
            .fixed_height(30),
        )


def main():
    frame = Frame("Enhanced DataTable Demo", 800, 600)
    app = App(frame, TableDemo())
    app.run()


if __name__ == "__main__":
    main()
