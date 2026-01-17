"""No-op audio backend for environments without audio support (TUI, etc.)."""

from __future__ import annotations

import uuid
from typing import Callable

from castella.audio.protocols import AudioBackend


class NoopBackend(AudioBackend):
    """No-op audio backend that does nothing.

    Used in environments where audio is not available, such as:
    - Terminal UI (TUI) mode
    - Headless environments
    - When no audio libraries are installed

    All methods are implemented as no-ops that don't raise errors,
    allowing applications to work without audio support.
    """

    def __init__(self) -> None:
        """Initialize the noop backend."""
        self._handles: set[str] = set()
        self._volumes: dict[str, float] = {}
        self._callbacks: dict[str, Callable[[], None] | None] = {}

    def load(self, source: str) -> str:
        """Load an audio file (no-op, returns a fake handle)."""
        handle = str(uuid.uuid4())
        self._handles.add(handle)
        self._volumes[handle] = 1.0
        self._callbacks[handle] = None
        return handle

    def play(self, handle: str, loop: bool = False) -> None:
        """Start playback (no-op)."""
        pass

    def pause(self, handle: str) -> None:
        """Pause playback (no-op)."""
        pass

    def resume(self, handle: str) -> None:
        """Resume playback (no-op)."""
        pass

    def stop(self, handle: str) -> None:
        """Stop playback (no-op)."""
        pass

    def seek(self, handle: str, position_ms: int) -> None:
        """Seek to a position (no-op)."""
        pass

    def set_volume(self, handle: str, volume: float) -> None:
        """Set volume (stored but not applied)."""
        if handle in self._handles:
            self._volumes[handle] = max(0.0, min(1.0, volume))

    def get_position(self, handle: str) -> int:
        """Get current position (always returns 0)."""
        return 0

    def get_duration(self, handle: str) -> int:
        """Get duration (always returns 0)."""
        return 0

    def is_playing(self, handle: str) -> bool:
        """Check if playing (always returns False)."""
        return False

    def unload(self, handle: str) -> None:
        """Unload an audio resource."""
        self._handles.discard(handle)
        self._volumes.pop(handle, None)
        self._callbacks.pop(handle, None)

    def set_on_ended(self, handle: str, callback: Callable[[], None] | None) -> None:
        """Set callback for when playback ends (stored but never called)."""
        if handle in self._handles:
            self._callbacks[handle] = callback

    def set_loop(self, handle: str, loop: bool) -> None:
        """Set loop setting (no-op)."""
        pass

    def check_music_finished(self) -> bool:
        """Check if music finished (always False for noop)."""
        return False
