"""Observer pattern protocols and base classes."""

from __future__ import annotations

from abc import ABC
from typing import TYPE_CHECKING, Any, Callable, Protocol, runtime_checkable

if TYPE_CHECKING:
    pass


@runtime_checkable
class Observer(Protocol):
    """Protocol for observers in the reactive system."""

    def on_attach(self, observable: Observable) -> None:
        """Called when attached to an observable."""
        ...

    def on_detach(self, observable: Observable) -> None:
        """Called when detached from an observable."""
        ...

    def on_notify(self, event: Any = None) -> None:
        """Called when the observable changes."""
        ...


@runtime_checkable
class Observable(Protocol):
    """Protocol for observable objects."""

    def attach(self, observer: Observer) -> None:
        """Attach an observer."""
        ...

    def detach(self, observer: Observer) -> None:
        """Detach an observer."""
        ...

    def notify(self, event: Any = None) -> None:
        """Notify all observers of a change."""
        ...


class UpdateListener:
    """Simple listener that calls a callback on notification."""

    __slots__ = ("_observable", "_callback")

    def __init__(self, callback: Callable[[Any], None]):
        self._observable: Observable | None = None
        self._callback = callback

    def on_attach(self, o: Observable) -> None:
        self._observable = o

    def on_detach(self, o: Observable) -> None:
        self._observable = None

    def on_notify(self, event: Any = None) -> None:
        self._callback(event)


class ObservableBase(ABC):
    """Base class for observable objects with observer management."""

    def __init__(self) -> None:
        self._observers: list[Observer] = []

    def attach(self, observer: Observer) -> None:
        """Attach an observer to this observable."""
        self._observers.append(observer)
        observer.on_attach(self)

    def detach(self, observer: Observer) -> None:
        """Detach an observer from this observable."""
        self._observers.remove(observer)
        observer.on_detach(self)

    def notify(self, event: Any = None) -> None:
        """Notify all attached observers of a change."""
        for o in self._observers:
            o.on_notify(event)

    def on_update(self, callback: Callable[[Any], None]) -> None:
        """Convenience method to attach a callback as an observer."""
        self.attach(UpdateListener(callback))
