"""Audio backend protocol definitions."""

from __future__ import annotations

from typing import Callable, Protocol, runtime_checkable


@runtime_checkable
class AudioBackend(Protocol):
    """Protocol for audio backend implementations.

    All audio backends must implement this protocol to be used with AudioManager.

    Methods handle audio resources identified by string handles (returned by load()).
    """

    def load(self, source: str) -> str:
        """Load an audio file and return a handle ID.

        Args:
            source: Path to audio file (local path or URL)

        Returns:
            Handle ID for the loaded audio resource

        Raises:
            AudioLoadError: If the file cannot be loaded
        """
        ...

    def play(self, handle: str, loop: bool = False) -> None:
        """Start playback of an audio resource.

        Args:
            handle: Handle ID from load()
            loop: If True, loop playback indefinitely
        """
        ...

    def pause(self, handle: str) -> None:
        """Pause playback of an audio resource.

        Args:
            handle: Handle ID from load()
        """
        ...

    def resume(self, handle: str) -> None:
        """Resume playback of a paused audio resource.

        Args:
            handle: Handle ID from load()
        """
        ...

    def stop(self, handle: str) -> None:
        """Stop playback of an audio resource.

        Args:
            handle: Handle ID from load()
        """
        ...

    def seek(self, handle: str, position_ms: int) -> None:
        """Seek to a position in the audio.

        Args:
            handle: Handle ID from load()
            position_ms: Position in milliseconds
        """
        ...

    def set_volume(self, handle: str, volume: float) -> None:
        """Set playback volume.

        Args:
            handle: Handle ID from load()
            volume: Volume level (0.0 to 1.0)
        """
        ...

    def get_position(self, handle: str) -> int:
        """Get current playback position.

        Args:
            handle: Handle ID from load()

        Returns:
            Position in milliseconds
        """
        ...

    def get_duration(self, handle: str) -> int:
        """Get total duration of the audio.

        Args:
            handle: Handle ID from load()

        Returns:
            Duration in milliseconds
        """
        ...

    def is_playing(self, handle: str) -> bool:
        """Check if audio is currently playing.

        Args:
            handle: Handle ID from load()

        Returns:
            True if playing, False otherwise
        """
        ...

    def unload(self, handle: str) -> None:
        """Unload an audio resource and free its resources.

        Args:
            handle: Handle ID from load()
        """
        ...

    def set_on_ended(self, handle: str, callback: Callable[[], None] | None) -> None:
        """Set callback for when playback ends.

        Args:
            handle: Handle ID from load()
            callback: Function to call when playback ends, or None to clear
        """
        ...

    def set_loop(self, handle: str, loop: bool) -> None:
        """Set loop setting for an audio resource.

        Can be changed during playback - the change takes effect
        at the next loop boundary.

        Args:
            handle: Handle ID from load()
            loop: Whether to loop playback
        """
        ...

    def check_music_finished(self) -> bool:
        """Check if music finished and handle it if so.

        This is used by backends that need to defer callback handling
        to avoid deadlocks (e.g., SDL_mixer).

        Returns:
            True if music finished and was handled, False otherwise
        """
        ...


class AudioLoadError(Exception):
    """Raised when an audio file cannot be loaded."""

    pass


class AudioPlaybackError(Exception):
    """Raised when a playback operation fails."""

    pass
