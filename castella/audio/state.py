"""Audio state management with Observable pattern."""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

from castella.core import ObservableBase

if TYPE_CHECKING:
    pass


class PlaybackState(Enum):
    """Playback state enumeration."""

    STOPPED = "stopped"
    PLAYING = "playing"
    PAUSED = "paused"
    LOADING = "loading"
    ERROR = "error"


class AudioState(ObservableBase):
    """Observable state for audio playback.

    Tracks playback state, position, duration, volume, and loop settings.
    Attach to a Component to trigger UI rebuilds when state changes.

    Example:
        manager = AudioManager.get()
        handle, state = manager.load("music.mp3")
        state.attach(my_component)  # UI rebuilds when state changes
        manager.play(handle)

    Properties:
        state: Current playback state (PlaybackState enum)
        position_ms: Current playback position in milliseconds
        duration_ms: Total duration in milliseconds
        volume: Volume level (0.0 to 1.0)
        loop: Whether playback should loop
        progress: Playback progress (0.0 to 1.0)
        error_message: Error message if state is ERROR
    """

    def __init__(
        self,
        handle: str,
        source: str,
        duration_ms: int = 0,
        volume: float = 1.0,
        loop: bool = False,
    ):
        """Initialize AudioState.

        Args:
            handle: Handle ID for the audio resource
            source: Source path or URL
            duration_ms: Total duration in milliseconds
            volume: Initial volume (0.0 to 1.0)
            loop: Whether to loop playback
        """
        super().__init__()
        self._handle = handle
        self._source = source
        self._state = PlaybackState.STOPPED
        self._position_ms = 0
        self._duration_ms = duration_ms
        self._volume = max(0.0, min(1.0, volume))
        self._loop = loop
        self._error_message: str | None = None

    @property
    def handle(self) -> str:
        """Get the handle ID."""
        return self._handle

    @property
    def source(self) -> str:
        """Get the source path or URL."""
        return self._source

    @property
    def state(self) -> PlaybackState:
        """Get current playback state."""
        return self._state

    @property
    def position_ms(self) -> int:
        """Get current playback position in milliseconds."""
        return self._position_ms

    @property
    def duration_ms(self) -> int:
        """Get total duration in milliseconds."""
        return self._duration_ms

    @property
    def volume(self) -> float:
        """Get current volume (0.0 to 1.0)."""
        return self._volume

    @property
    def loop(self) -> bool:
        """Get loop setting."""
        return self._loop

    @property
    def progress(self) -> float:
        """Get playback progress (0.0 to 1.0)."""
        if self._duration_ms == 0:
            return 0.0
        return self._position_ms / self._duration_ms

    @property
    def error_message(self) -> str | None:
        """Get error message if state is ERROR."""
        return self._error_message

    def is_playing(self) -> bool:
        """Check if audio is currently playing."""
        return self._state == PlaybackState.PLAYING

    def is_paused(self) -> bool:
        """Check if audio is paused."""
        return self._state == PlaybackState.PAUSED

    def is_stopped(self) -> bool:
        """Check if audio is stopped."""
        return self._state == PlaybackState.STOPPED

    def is_loading(self) -> bool:
        """Check if audio is loading."""
        return self._state == PlaybackState.LOADING

    def has_error(self) -> bool:
        """Check if there was an error."""
        return self._state == PlaybackState.ERROR

    # Internal setters (called by AudioManager, notify observers)

    def _set_state(self, state: PlaybackState) -> None:
        """Set playback state (internal)."""
        if self._state != state:
            self._state = state
            if state != PlaybackState.ERROR:
                self._error_message = None
            self.notify()

    def _set_position(self, position_ms: int) -> None:
        """Set playback position (internal)."""
        if self._position_ms != position_ms:
            self._position_ms = position_ms
            self.notify()

    def _set_duration(self, duration_ms: int) -> None:
        """Set duration (internal)."""
        if self._duration_ms != duration_ms:
            self._duration_ms = duration_ms
            self.notify()

    def _set_volume(self, volume: float) -> None:
        """Set volume (internal)."""
        volume = max(0.0, min(1.0, volume))
        if self._volume != volume:
            self._volume = volume
            self.notify()

    def _set_loop(self, loop: bool) -> None:
        """Set loop setting (internal)."""
        if self._loop != loop:
            self._loop = loop
            self.notify()

    def _set_error(self, message: str) -> None:
        """Set error state (internal)."""
        self._state = PlaybackState.ERROR
        self._error_message = message
        self.notify()

    def _update_position_silent(self, position_ms: int) -> None:
        """Update position without notifying (for frequent updates)."""
        self._position_ms = position_ms

    def _notify_position_update(self) -> None:
        """Notify observers of position change (called periodically)."""
        self.notify()

    def format_time(self, ms: int | None = None) -> str:
        """Format milliseconds as M:SS or H:MM:SS.

        Args:
            ms: Milliseconds to format, or None to use current position

        Returns:
            Formatted time string
        """
        if ms is None:
            ms = self._position_ms

        total_seconds = ms // 1000
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60

        if hours > 0:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        return f"{minutes}:{seconds:02d}"

    def format_time_precise(self, ms: int | None = None) -> str:
        """Format milliseconds as M:SS.m (with deciseconds).

        Args:
            ms: Milliseconds to format, or None to use current position

        Returns:
            Formatted time string with decisecond precision
        """
        if ms is None:
            ms = self._position_ms

        total_seconds = ms // 1000
        deciseconds = (ms % 1000) // 100
        minutes = total_seconds // 60
        seconds = total_seconds % 60

        return f"{minutes}:{seconds:02d}.{deciseconds}"

    def format_duration(self) -> str:
        """Format duration as MM:SS or HH:MM:SS."""
        return self.format_time(self._duration_ms)

    def format_duration_precise(self) -> str:
        """Format duration as M:SS.m (with deciseconds)."""
        return self.format_time_precise(self._duration_ms)

    def format_progress_precise(self) -> str:
        """Format as 'position / duration' with decisecond precision."""
        return f"{self.format_time_precise()} / {self.format_duration_precise()}"

    def format_progress(self) -> str:
        """Format as 'position / duration' (e.g., '1:23 / 4:56')."""
        return f"{self.format_time()} / {self.format_duration()}"
