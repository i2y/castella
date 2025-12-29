"""Reactive collection types."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any, Callable, Generator, Generic, Self, TypeVar, overload

from castella.state.observers import Observer, UpdateListener

T = TypeVar("T")


class ReactiveList(list[T], Generic[T]):
    """
    A reactive list that notifies observers on mutations.

    Extends the built-in list with observer pattern support.
    Any mutation triggers notification to all attached observers.

    Example:
        items = ReactiveList([1, 2, 3])
        items.on_update(lambda _: print("List changed!"))
        items.append(4)  # Prints: List changed!
    """

    def __init__(self, items: Iterable[T] | None = None):
        if items is not None:
            super().__init__(items)
        else:
            super().__init__()
        self._observers: list[Observer] = []

    def __add__(self, rhs: Iterable[T]) -> ReactiveList[T]:
        return ReactiveList(super().__add__(list(rhs)))

    def __delattr__(self, name: str) -> None:
        super().__delattr__(name)
        self.notify()

    def __setattr__(self, name: str, value: Any) -> None:
        super().__setattr__(name, value)
        if name != "_observers":
            self.notify()

    def __iadd__(self, rhs: Iterable[T]) -> Self:
        super().__iadd__(rhs)
        self.notify()
        return self

    def __imul__(self, rhs: int) -> Self:
        super().__imul__(rhs)
        self.notify()
        return self

    def __mul__(self, rhs: int) -> ReactiveList[T]:
        return ReactiveList(super().__mul__(rhs))

    def __rmul__(self, lhs: int) -> ReactiveList[T]:
        return ReactiveList(super().__rmul__(lhs))

    def __reversed__(self) -> Self:
        super().__reversed__()
        self.notify()
        return self

    @overload
    def __setitem__(self, index: int, value: T) -> None: ...

    @overload
    def __setitem__(self, index: slice, value: Iterable[T]) -> None: ...

    def __setitem__(self, index: int | slice, value: T | Iterable[T]) -> None:
        super().__setitem__(index, value)  # type: ignore
        self.notify()

    def __delitem__(self, index: int | slice) -> None:
        super().__delitem__(index)
        self.notify()

    def __iter__(self) -> Generator[T, None, None]:
        for item in super().__iter__():
            yield item

    def __next__(self) -> T:
        return next(super().__iter__())

    def append(self, value: T) -> None:
        super().append(value)
        self.notify()

    def extend(self, it: Iterable[T]) -> None:
        super().extend(it)
        self.notify()

    def clear(self) -> None:
        super().clear()
        self.notify()

    def insert(self, index: int, value: T) -> None:
        super().insert(index, value)
        self.notify()

    def pop(self, index: int = -1) -> T:
        retval = super().pop(index)
        self.notify()
        return retval

    def remove(self, value: T) -> None:
        super().remove(value)
        self.notify()

    def sort(
        self, *, key: Callable[[T], Any] | None = None, reverse: bool = False
    ) -> None:
        super().sort(key=key, reverse=reverse)
        self.notify()

    def reverse(self) -> None:
        super().reverse()
        self.notify()

    # Value access (for compatibility with State interface)
    def value(self) -> list[T]:
        return list(self)

    def __call__(self) -> list[T]:
        return self.value()

    # Observable implementation
    def attach(self, observer: Observer) -> None:
        self._observers.append(observer)
        observer.on_attach(self)

    def detach(self, observer: Observer) -> None:
        self._observers.remove(observer)
        observer.on_detach(self)

    def notify(self, event: Any = None) -> None:
        if hasattr(self, "_observers"):
            for observer in self._observers:
                observer.on_notify(event)

    def on_update(self, callback: Callable[[Any], None]) -> None:
        self.attach(UpdateListener(callback))

    def __repr__(self) -> str:
        return f"ReactiveList({list(self)!r})"
