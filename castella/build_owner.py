"""BuildOwner - Batched component rebuild management.

This module implements the BuildOwner pattern,
which batches multiple state changes into a single rebuild pass.

Key features:
- Collects dirty components during a build scope
- Rebuilds components in depth order (parents before children)
- Prevents cascade rebuilds from multiple state changes
- Maintains backward compatibility with immediate updates
"""

from __future__ import annotations

import threading
from contextlib import contextmanager
from typing import TYPE_CHECKING, Callable, Generator, Self

if TYPE_CHECKING:
    from castella.core import Component


class BuildOwner:
    """Manages the build lifecycle of component trees.

    Collects dirty components and rebuilds them in depth order
    during a build scope. This prevents cascade rebuilds and
    enables batching of multiple state changes.

    Usage:
        # Automatic batching via frame integration
        owner = BuildOwner.get()
        with owner.build_scope():
            # State changes here are batched
            state1.set(value1)
            state2.set(value2)
        # Single rebuild happens here

        # Manual scheduling
        owner.schedule_build_for(component)
    """

    _instance: Self | None = None
    _lock = threading.Lock()

    def __init__(self) -> None:
        self._dirty_components: list[Component] = []
        self._in_build_scope: bool = False
        self._build_scheduled: bool = False
        self._components_lock = threading.Lock()

    @classmethod
    def get(cls) -> Self:
        """Get the singleton BuildOwner instance."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        """Reset the singleton instance (for testing)."""
        with cls._lock:
            cls._instance = None

    def is_in_build_scope(self) -> bool:
        """Check if currently inside a build scope."""
        return self._in_build_scope

    def schedule_build_for(self, component: "Component") -> None:
        """Schedule a component for rebuild.

        If inside a build scope, the component is added to the dirty list
        and will be rebuilt when the scope exits.

        If outside a build scope, the component is rebuilt immediately
        (backward compatibility mode).

        Args:
            component: The component that needs to be rebuilt.
        """
        with self._components_lock:
            # Avoid duplicates
            if component not in self._dirty_components:
                self._dirty_components.append(component)

        # If not in build scope, trigger immediate rebuild
        if not self._in_build_scope and not self._build_scheduled:
            self._flush_builds()

    @contextmanager
    def build_scope(self) -> Generator[None, None, None]:
        """Context manager for batched rebuilds.

        All components scheduled for rebuild during this scope
        will be rebuilt in depth order when the scope exits.

        Nested scopes are allowed - only the outermost scope
        triggers the actual rebuild.

        Yields:
            None
        """
        was_in_scope = self._in_build_scope
        self._in_build_scope = True
        try:
            yield
        finally:
            self._in_build_scope = was_in_scope
            # Only rebuild when exiting the outermost scope
            if not was_in_scope:
                self._flush_builds()

    def _flush_builds(self) -> None:
        """Process all pending component rebuilds in depth order."""
        self._build_scheduled = True
        try:
            while True:
                with self._components_lock:
                    if not self._dirty_components:
                        break
                    # Sort by depth (parents before children)
                    # This ensures parent rebuilds don't invalidate child work
                    sorted_components = sorted(
                        self._dirty_components,
                        key=lambda c: c.get_depth(),
                    )
                    self._dirty_components.clear()

                # Rebuild each component
                for component in sorted_components:
                    component._do_rebuild()
        finally:
            self._build_scheduled = False

    def clear(self) -> None:
        """Clear all pending rebuilds (for cleanup/testing)."""
        with self._components_lock:
            self._dirty_components.clear()


def batch_updates(callback: Callable[[], None]) -> None:
    """Execute callback with batched component updates.

    This is a convenience function for explicit batching:

        def update_multiple_states():
            state1.set(value1)
            state2.set(value2)
            state3.set(value3)

        batch_updates(update_multiple_states)
        # Single rebuild happens here

    Args:
        callback: Function containing state updates to batch.
    """
    owner = BuildOwner.get()
    with owner.build_scope():
        callback()
