"""Animation scheduler for managing animation tick loop."""

from __future__ import annotations

import os
import threading
import time
from typing import TYPE_CHECKING, Self

if TYPE_CHECKING:
    from .animation import Animation


class AnimationScheduler:
    """Singleton animation scheduler running in a background thread.

    The scheduler maintains a list of active animations and updates them
    at regular intervals (target 60 FPS for desktop, 10 FPS for TUI).

    Usage:
        scheduler = AnimationScheduler.get()
        scheduler.add(my_animation)
    """

    _instance: Self | None = None
    _lock = threading.Lock()

    def __init__(self) -> None:
        """Initialize the scheduler. Use get() to obtain the singleton instance."""
        self._animations: list[Animation] = []
        self._animations_lock = threading.Lock()
        self._thread: threading.Thread | None = None
        self._running = False
        self._target_fps = self._get_target_fps()
        self._frame_duration = 1.0 / self._target_fps
        self._last_time: float = 0.0

    @classmethod
    def get(cls) -> Self:
        """Get the singleton AnimationScheduler instance."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        """Reset the singleton instance. Mainly for testing."""
        with cls._lock:
            if cls._instance is not None:
                cls._instance.stop()
                cls._instance = None

    def _get_target_fps(self) -> int:
        """Determine target FPS based on environment."""
        if os.environ.get("CASTELLA_IS_TERMINAL_MODE") == "true":
            return 10  # Lower FPS for terminal UI
        return 60  # Full FPS for desktop/web

    def add(self, animation: Animation) -> None:
        """Add an animation to be updated.

        Args:
            animation: Animation to add

        Note:
            This method is thread-safe and will auto-start the scheduler
            if not already running.
        """
        with self._animations_lock:
            if animation not in self._animations:
                self._animations.append(animation)
        self._ensure_running()

    def remove(self, animation: Animation) -> None:
        """Remove an animation from updates.

        Args:
            animation: Animation to remove
        """
        with self._animations_lock:
            if animation in self._animations:
                self._animations.remove(animation)

    def clear(self) -> None:
        """Remove all animations."""
        with self._animations_lock:
            for anim in self._animations:
                anim.cancel()
            self._animations.clear()

    def start(self) -> None:
        """Start the animation loop (idempotent)."""
        if self._running:
            return

        self._running = True
        self._last_time = time.perf_counter()
        self._thread = threading.Thread(target=self._tick_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop the animation loop."""
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=1.0)
            self._thread = None

    def is_running(self) -> bool:
        """Check if the scheduler is running."""
        return self._running

    def _ensure_running(self) -> None:
        """Ensure the scheduler is running. Called when animations are added."""
        if not self._running:
            self.start()

    def _tick_loop(self) -> None:
        """Background thread main loop."""
        while self._running:
            now = time.perf_counter()
            dt = now - self._last_time
            self._last_time = now

            self._update_animations(dt)

            # Sleep to maintain target FPS
            elapsed = time.perf_counter() - now
            sleep_time = max(0, self._frame_duration - elapsed)
            if sleep_time > 0:
                time.sleep(sleep_time)

    def _update_animations(self, dt: float) -> None:
        """Update all active animations."""
        with self._animations_lock:
            completed: list[Animation] = []

            for anim in self._animations:
                if anim.is_cancelled():
                    completed.append(anim)
                    continue

                try:
                    if anim.tick(dt):
                        completed.append(anim)
                        anim._complete()
                except Exception:
                    # Animation errored, remove it
                    completed.append(anim)

            for anim in completed:
                if anim in self._animations:
                    self._animations.remove(anim)

    @property
    def animation_count(self) -> int:
        """Get the number of active animations."""
        with self._animations_lock:
            return len(self._animations)
