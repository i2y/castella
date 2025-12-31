"""Base animation protocol and classes."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    pass


class Animation(ABC):
    """Base class for all animations.

    Animations are updated by the AnimationScheduler at regular intervals.
    Each tick receives the delta time since the last update.
    """

    def __init__(
        self,
        on_complete: Callable[[], None] | None = None,
        on_update: Callable[[float], None] | None = None,
    ) -> None:
        """Initialize animation.

        Args:
            on_complete: Callback when animation completes
            on_update: Callback on each update with current value
        """
        self._on_complete = on_complete
        self._on_update = on_update
        self._cancelled = False

    @abstractmethod
    def tick(self, dt: float) -> bool:
        """Update animation state.

        Args:
            dt: Delta time in seconds since last tick

        Returns:
            True if animation is complete, False otherwise
        """
        ...

    def cancel(self) -> None:
        """Cancel this animation."""
        self._cancelled = True

    def is_cancelled(self) -> bool:
        """Check if animation has been cancelled."""
        return self._cancelled

    def _complete(self) -> None:
        """Called when animation completes. Triggers callback if set."""
        if self._on_complete is not None:
            self._on_complete()
