from typing import Any, List, Optional, Sequence

from pydantic import BaseModel, ConfigDict, PrivateAttr

from castella.column import Column
from castella.core import (
    Observer,
    ScrollState,
    StatefulComponent,
    Widget,
    EM,
)
from castella.row import Row
from castella.text import SimpleText


class TableEvent(BaseModel):
    source: Any
    row: int
    column: int
    old_value: Any = None
    new_value: Any = None


class TableModel(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    column_names: List[str]
    data: List[List[Any]]

    _listeners: List[Observer] = PrivateAttr(default_factory=list)

    @staticmethod
    def from_pydantic_model(model: Sequence[BaseModel]) -> "TableModel":
        return modelToTableModel(model)

    def reflect_pydantic_model(self, model: Sequence[BaseModel]) -> None:
        self.column_names = get_labels(model)
        self.data = [list(p.model_dump().values()) for p in model]
        ev = TableEvent(source=self, row=-1, column=-1)
        self.notify(ev)

    def get_row_count(self) -> int:
        return len(self.data)

    def get_column_count(self) -> int:
        return len(self.column_names)

    def get_value_at(self, row: int, column: int) -> Any:
        return self.data[row][column]

    def get_column_name(self, column: int) -> str:
        return self.column_names[column]

    def set_value_at(self, value: Any, row: int, column: int) -> None:
        old_value = self.data[row][column]
        self.data[row][column] = value

        event = TableEvent(
            source=self,
            row=row,
            column=column,
            old_value=old_value,
            new_value=value,
        )
        self.notify(event)

    def add_row(self, row_data: List[Any]) -> None:
        self.data.append(row_data)
        new_row_index = len(self.data) - 1

        event = TableEvent(
            source=self,
            row=new_row_index,
            column=-1,
            old_value=None,
            new_value=row_data,
        )
        self.notify(event)

    def remove_row(self, row_index: int) -> Optional[List[Any]]:
        if 0 <= row_index < len(self.data):
            removed = self.data.pop(row_index)

            event = TableEvent(
                source=self,
                row=row_index,
                column=-1,
                old_value=removed,
                new_value=None,
            )
            self.notify(event)
            return removed
        return None

    def add_column(
        self, column_name: str, column_data: Optional[List[Any]] = None
    ) -> None:
        self.column_names.append(column_name)
        col_index = len(self.column_names) - 1

        if column_data is None:
            column_data = [None] * self.get_row_count()

        for row_idx, row_val in enumerate(self.data):
            row_val.append(column_data[row_idx] if row_idx < len(column_data) else None)

        event = TableEvent(
            source=self,
            row=-1,
            column=col_index,
            old_value=None,
            new_value=column_data,
        )
        self.notify(event)

    def remove_column(self, column_index: int) -> Optional[List[Any]]:
        if 0 <= column_index < len(self.column_names):
            removed_col_name = self.column_names.pop(column_index)
            removed_data = []
            for row_val in self.data:
                removed_data.append(row_val.pop(column_index))

            event = TableEvent(
                source=self,
                row=-1,
                column=column_index,
                old_value={"column_name": removed_col_name, "values": removed_data},
                new_value=None,
            )
            self.notify(event)
            return removed_data
        return None

    def attach(self, observer: Observer) -> None:
        self._listeners.append(observer)

    def detach(self, observer: Observer) -> None:
        self._listeners.remove(observer)

    def notify(self, event: Any = None) -> None:
        for listener in self._listeners:
            listener.on_notify(event)


def get_labels(model: Sequence[BaseModel]) -> list[str]:
    return [
        "<undefined>" if f.title is None else f.title
        for f in model[0].model_fields.values()
    ]


def modelToTableModel(model: Sequence[BaseModel]) -> TableModel:
    column_names = get_labels(model)
    data = [list(p.model_dump().values()) for p in model]
    return TableModel(column_names=column_names, data=data)


class DataTable(StatefulComponent):
    def __init__(self, model: TableModel):
        super().__init__(model)
        self._model = model
        # ScrollState to preserve scroll position across re-renders
        self._scroll_state = ScrollState()

    def view(self) -> Widget:
        header = (
            Row(
                *[
                    SimpleText(name, font_size=EM)
                    .flex(1)
                    .bg_color("#ffcccc")
                    .fg_color("#000000")
                    for name in self._model.column_names
                ]
            )
            .bg_color("#ffcccc")
            .fixed_height(EM)
        )

        rows = [
            Row(
                *[
                    SimpleText(
                        str(self._model.get_value_at(row, col)), font_size=EM
                    ).flex(1)
                    for col in range(self._model.get_column_count())
                ]
            ).fixed_height(EM)
            for row in range(self._model.get_row_count())
        ]

        return Column(
            header, Column(*rows, scrollable=True, scroll_state=self._scroll_state)
        )
