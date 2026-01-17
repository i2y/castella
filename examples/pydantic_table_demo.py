"""Pydantic Integration Demo for DataTable.

This example demonstrates how Castella's DataTable leverages Pydantic metadata:
- Field.title → Column header name
- Field.description → Column tooltip (hover header to see)
- Field.annotation → Automatic column width inference

Run with: uv run python examples/pydantic_table_demo.py
"""

from datetime import date

from pydantic import BaseModel, Field

from castella import App, Column, DataTable, DataTableState, Text
from castella.core import State, StatefulComponent, TextAlign
from castella.frame import Frame


class Employee(BaseModel):
    """Employee model demonstrating Pydantic metadata usage."""

    id: int = Field(..., title="ID", description="Unique identifier")
    name: str = Field(..., title="Name", description="Full name")
    age: int = Field(..., title="Age", ge=18, le=100, description="Age (18-100)")
    salary: float = Field(..., title="Salary", gt=0, description="Annual salary")
    active: bool = Field(..., title="Active", description="Is active")
    hire_date: date = Field(..., title="Hired", description="Hire date")


employees = [
    Employee(id=1, name="Alice Johnson", age=28, salary=75000.0, active=True, hire_date=date(2020, 3, 15)),
    Employee(id=2, name="Bob Smith", age=35, salary=85000.0, active=True, hire_date=date(2018, 7, 1)),
    Employee(id=3, name="Carol White", age=42, salary=95000.0, active=False, hire_date=date(2015, 1, 10)),
    Employee(id=4, name="David Lee", age=31, salary=72000.0, active=True, hire_date=date(2021, 9, 20)),
    Employee(id=5, name="Eva Chen", age=26, salary=68000.0, active=True, hire_date=date(2022, 4, 5)),
    Employee(id=6, name="Frank Brown", age=38, salary=92000.0, active=True, hire_date=date(2017, 11, 8)),
    Employee(id=7, name="Grace Kim", age=29, salary=71000.0, active=False, hire_date=date(2019, 6, 22)),
]


class PydanticDemo(StatefulComponent):
    def __init__(self):
        self._table_state = DataTableState.from_pydantic(employees)
        self._status = State("Hover header to see tooltip from Field.description")
        super().__init__(self._status)

    def view(self):
        return Column(
            # Header
            Text("Pydantic Integration Demo", font_size=16).fixed_height(35),
            Text("Column widths auto-inferred from type: int=80px, str=150px, float=100px, bool=60px, date=120px", font_size=11).fixed_height(20),

            # Table with custom styling for better visibility
            DataTable(self._table_state)
                .header_bg_color("#3d5a80")      # Blue header
                .header_text_color("#ffffff")    # White text
                .alt_row_bg_color("#293241")     # Darker alt rows
                .hover_bg_color("#415a77")       # Visible hover
                .selected_bg_color("#ee6c4d")    # Orange selection
                .grid_color("#4a5568")           # Visible grid
                .on_cell_click(lambda e: self._status.set(f"Clicked: {e.value}")),

            # Status bar
            Text(self._status(), font_size=11, align=TextAlign.LEFT).fixed_height(25),
        )


if __name__ == "__main__":
    App(
        Frame("Pydantic Table Demo", width=900, height=450),
        PydanticDemo(),
    ).run()
