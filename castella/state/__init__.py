"""Castella State - Reactive state management."""

from castella.state.collections import ReactiveList
from castella.state.observers import (
    Observable,
    ObservableBase,
    Observer,
    UpdateListener,
)
from castella.state.reactive import ReactiveModel, ReactiveValue

# Aliases for backward compatibility
State = ReactiveValue
ListState = ReactiveList

__all__ = [
    # Observers
    "Observer",
    "Observable",
    "ObservableBase",
    "UpdateListener",
    # Reactive
    "ReactiveValue",
    "ReactiveModel",
    "ReactiveList",
    # Aliases
    "State",
    "ListState",
]
