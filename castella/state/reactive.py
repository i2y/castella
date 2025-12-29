"""Reactive state primitives."""

from __future__ import annotations

from typing import Any, Callable, Generic, Self, TypeVar

from pydantic import BaseModel, ConfigDict, PrivateAttr

from castella.state.observers import ObservableBase, Observer, UpdateListener

T = TypeVar("T")


class ReactiveValue(ObservableBase, Generic[T]):
    """
    A reactive value container that notifies observers when changed.

    This is the core reactive primitive - a container for a value that
    notifies observers when changed. Supports arithmetic operators for
    convenient state updates.

    Example:
        count = ReactiveValue(0)
        count.on_update(lambda _: print("Count changed!"))
        count += 1  # Prints: Count changed!
    """

    def __init__(self, value: T, validator: Callable[[T], T] | None = None):
        super().__init__()
        self._value: T = value
        self._validator = validator

    def value(self) -> T:
        """Get the current value."""
        return self._value

    def __call__(self) -> T:
        """Shorthand for value()."""
        return self._value

    def set(self, value: T) -> None:
        """Set a new value, validating and notifying observers."""
        if self._validator is not None:
            value = self._validator(value)

        self._value = value
        self.notify()

    def __str__(self) -> str:
        return str(self._value)

    def __repr__(self) -> str:
        return f"ReactiveValue({self._value!r})"

    # Operator overloads for convenience
    def __iadd__(self, value: Any) -> Self:
        self._value += value  # type: ignore
        self.notify()
        return self

    def __add__(self, value: Any) -> T:
        return self._value + value  # type: ignore

    def __isub__(self, value: Any) -> Self:
        self._value -= value  # type: ignore
        self.notify()
        return self

    def __imul__(self, value: Any) -> Self:
        self._value *= value  # type: ignore
        self.notify()
        return self

    def __itruediv__(self, value: Any) -> Self:
        self._value /= value  # type: ignore
        self.notify()
        return self


class ReactiveModel(BaseModel):
    """
    Base class for Pydantic models with reactive field change notifications.

    This replaces the old Model class and properly integrates Pydantic v2
    features with the observer pattern.

    Example:
        class User(ReactiveModel):
            name: str = "Anonymous"
            age: int = 0

        user = User()
        user.on_field_change("name", lambda old, new: print(f"Name: {old} -> {new}"))
        user.name = "Alice"  # Prints: Name: Anonymous -> Alice
    """

    model_config = ConfigDict(
        validate_assignment=True,
        arbitrary_types_allowed=True,
    )

    _observers: list[Observer] = PrivateAttr(default_factory=list)
    _field_callbacks: dict[str, list[Callable[[Any, Any], None]]] = PrivateAttr(
        default_factory=dict
    )
    _prev_values: dict[str, Any] = PrivateAttr(default_factory=dict)

    def model_post_init(self, __context: Any) -> None:
        """Store initial values for change detection."""
        for field_name in self.model_fields:
            self._prev_values[field_name] = getattr(self, field_name)

    def __setattr__(self, name: str, value: Any) -> None:
        if name.startswith("_") or name not in self.model_fields:
            super().__setattr__(name, value)
            return

        old_value = self._prev_values.get(name)
        super().__setattr__(name, value)
        new_value = getattr(self, name)

        if old_value != new_value:
            self._prev_values[name] = new_value
            self._notify_field_change(name, old_value, new_value)
            self.notify()

    def _notify_field_change(self, field: str, old: Any, new: Any) -> None:
        """Notify field-specific callbacks."""
        callbacks = self._field_callbacks.get(field, [])
        for callback in callbacks:
            callback(old, new)

    def on_field_change(
        self,
        field: str,
        callback: Callable[[Any, Any], None],
    ) -> None:
        """Register a callback for when a specific field changes."""
        if field not in self.model_fields:
            raise ValueError(f"Unknown field: {field}")

        if field not in self._field_callbacks:
            self._field_callbacks[field] = []
        self._field_callbacks[field].append(callback)

    # Observable protocol implementation
    def attach(self, observer: Observer) -> None:
        """Attach an observer to this model."""
        self._observers.append(observer)
        observer.on_attach(self)

    def detach(self, observer: Observer) -> None:
        """Detach an observer from this model."""
        self._observers.remove(observer)
        observer.on_detach(self)

    def notify(self, event: Any = None) -> None:
        """Notify all observers of a change."""
        for observer in self._observers:
            observer.on_notify(event)

    def on_update(self, callback: Callable[[Any], None]) -> None:
        """Convenience method to attach a callback as an observer."""
        self.attach(UpdateListener(callback))
