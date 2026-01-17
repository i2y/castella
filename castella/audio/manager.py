"""Audio manager singleton for managing audio playback."""

from __future__ import annotations

import threading
import time
from typing import TYPE_CHECKING, Callable, Self

from .state import AudioState, PlaybackState

if TYPE_CHECKING:
    from .protocols import AudioBackend


class AudioManager:
    """Singleton audio manager for loading and controlling audio playback.

    Similar to AnimationScheduler, this class manages audio resources
    using a background thread for position updates.

    Usage:
        manager = AudioManager.get()
        handle, state = manager.load("music.mp3")
        state.attach(my_component)  # UI rebuilds when state changes
        manager.play(handle)

    The manager automatically selects an appropriate backend based on
    available dependencies (SDL_mixer for desktop, Web Audio for web, etc.).
    """

    _instance: Self | None = None
    _lock = threading.Lock()

    def __init__(self) -> None:
        """Initialize the audio manager. Use get() to obtain the singleton instance."""
        self._backend: AudioBackend | None = None
        self._states: dict[str, AudioState] = {}
        self._states_lock = threading.Lock()
        self._position_thread: threading.Thread | None = None
        self._running = False
        self._update_interval = 0.1  # 100ms position update interval

    @classmethod
    def get(cls) -> Self:
        """Get the singleton AudioManager instance."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
                    cls._instance._init_backend()
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        """Reset the singleton instance. Mainly for testing."""
        with cls._lock:
            if cls._instance is not None:
                cls._instance._shutdown()
                cls._instance = None

    def _init_backend(self) -> None:
        """Initialize the audio backend based on available dependencies."""
        from .backends import get_backend

        self._backend = get_backend()

    def _shutdown(self) -> None:
        """Shutdown the manager and release all resources."""
        self._stop_position_thread()

        # Unload all audio resources
        with self._states_lock:
            for handle in list(self._states.keys()):
                self._unload_internal(handle)

    def _start_position_thread(self) -> None:
        """Start the background thread for position updates."""
        # If thread is running, just return
        if self._running and self._position_thread is not None:
            if self._position_thread.is_alive():
                return

        # Make sure any old thread is fully stopped
        self._stop_position_thread()

        self._running = True
        self._position_thread = threading.Thread(
            target=self._position_update_loop, daemon=True
        )
        self._position_thread.start()

    def _stop_position_thread(self) -> None:
        """Stop the background position update thread."""
        self._running = False
        if self._position_thread is not None:
            # Wait for thread to finish (with timeout)
            self._position_thread.join(timeout=2.0)
            self._position_thread = None

    def _position_update_loop(self) -> None:
        """Background thread loop for updating playback positions."""
        while self._running:
            self._update_positions()
            time.sleep(self._update_interval)

    def _update_positions(self) -> None:
        """Update positions for all playing audio."""
        if self._backend is None:
            return

        # Check if music finished (handles deferred callback from SDL audio thread)
        # This must be done BEFORE checking position to avoid missing the finish event
        self._backend.check_music_finished()

        with self._states_lock:
            for handle, state in list(self._states.items()):
                if state.state == PlaybackState.PLAYING:
                    try:
                        position = self._backend.get_position(handle)
                        state._update_position_silent(position)

                        # Check if playback ended
                        # Only check after playback has progressed (avoid race at start)
                        # and when position is near the end of the track
                        if not self._backend.is_playing(handle):
                            duration = state.duration_ms
                            # Consider ended if: position > 500ms AND
                            # (position near end OR duration is very short)
                            near_end = (
                                duration > 0
                                and position > 500
                                and (position >= duration - 500 or duration < 1000)
                            )
                            if near_end:
                                if state.loop:
                                    self._backend.seek(handle, 0)
                                    self._backend.play(handle, loop=False)
                                else:
                                    state._set_state(PlaybackState.STOPPED)
                                    state._set_position(0)
                    except Exception:
                        # Handle may have been unloaded
                        pass

        # Batch notify outside the lock
        with self._states_lock:
            for state in self._states.values():
                if state.state == PlaybackState.PLAYING:
                    state._notify_position_update()

    def _ensure_position_thread_running(self) -> None:
        """Ensure position update thread is running if there are playing tracks."""
        with self._states_lock:
            has_playing = any(
                s.state == PlaybackState.PLAYING for s in self._states.values()
            )

        if has_playing and not self._running:
            self._start_position_thread()
        elif not has_playing and self._running:
            self._stop_position_thread()

    def load(self, source: str, volume: float = 1.0) -> tuple[str, AudioState]:
        """Load an audio file and return a handle and state.

        Args:
            source: Path to audio file (local path or URL)
            volume: Initial volume (0.0 to 1.0)

        Returns:
            Tuple of (handle, AudioState)

        Raises:
            AudioLoadError: If the file cannot be loaded
            RuntimeError: If no audio backend is available
        """
        if self._backend is None:
            raise RuntimeError("No audio backend available")

        handle = self._backend.load(source)
        duration = self._backend.get_duration(handle)

        state = AudioState(
            handle=handle,
            source=source,
            duration_ms=duration,
            volume=volume,
        )

        # Set up ended callback
        def on_ended():
            with self._states_lock:
                if handle in self._states:
                    s = self._states[handle]
                    if not s.loop:
                        s._set_state(PlaybackState.STOPPED)
                        s._set_position(0)

        self._backend.set_on_ended(handle, on_ended)
        self._backend.set_volume(handle, volume)

        with self._states_lock:
            self._states[handle] = state

        return handle, state

    def play(self, handle: str, loop: bool | None = None) -> None:
        """Start playback of an audio resource.

        Args:
            handle: Handle ID from load()
            loop: If True, loop playback. If None, use state's loop setting.
        """
        if self._backend is None:
            return

        with self._states_lock:
            if handle not in self._states:
                return
            state = self._states[handle]

        if loop is not None:
            state._set_loop(loop)

        self._backend.play(handle, loop=state.loop)
        state._set_state(PlaybackState.PLAYING)
        self._ensure_position_thread_running()

    def pause(self, handle: str) -> None:
        """Pause playback of an audio resource.

        Args:
            handle: Handle ID from load()
        """
        if self._backend is None:
            return

        with self._states_lock:
            if handle not in self._states:
                return
            state = self._states[handle]

        self._backend.pause(handle)
        state._set_state(PlaybackState.PAUSED)
        self._ensure_position_thread_running()

    def resume(self, handle: str) -> None:
        """Resume playback of a paused audio resource.

        Args:
            handle: Handle ID from load()
        """
        if self._backend is None:
            return

        with self._states_lock:
            if handle not in self._states:
                return
            state = self._states[handle]

        if state.state == PlaybackState.PAUSED:
            self._backend.resume(handle)
            state._set_state(PlaybackState.PLAYING)
            self._ensure_position_thread_running()

    def stop(self, handle: str) -> None:
        """Stop playback of an audio resource.

        Args:
            handle: Handle ID from load()
        """
        if self._backend is None:
            return

        with self._states_lock:
            if handle not in self._states:
                return
            state = self._states[handle]

        self._backend.stop(handle)
        state._set_state(PlaybackState.STOPPED)
        state._set_position(0)
        self._ensure_position_thread_running()

    def seek(self, handle: str, position_ms: int) -> None:
        """Seek to a position in the audio.

        Args:
            handle: Handle ID from load()
            position_ms: Position in milliseconds
        """
        if self._backend is None:
            return

        with self._states_lock:
            if handle not in self._states:
                return
            state = self._states[handle]

        # Clamp position to valid range
        position_ms = max(0, min(position_ms, state.duration_ms))
        self._backend.seek(handle, position_ms)
        state._set_position(position_ms)

    def set_volume(self, handle: str, volume: float) -> None:
        """Set playback volume.

        Args:
            handle: Handle ID from load()
            volume: Volume level (0.0 to 1.0)
        """
        if self._backend is None:
            return

        with self._states_lock:
            if handle not in self._states:
                return
            state = self._states[handle]

        volume = max(0.0, min(1.0, volume))
        self._backend.set_volume(handle, volume)
        state._set_volume(volume)

    def set_loop(self, handle: str, loop: bool) -> None:
        """Set loop setting.

        Can be changed during playback - the change takes effect
        at the next loop boundary.

        Args:
            handle: Handle ID from load()
            loop: Whether to loop playback
        """
        with self._states_lock:
            if handle not in self._states:
                return
            state = self._states[handle]

        # Update backend's loop setting (takes effect at next loop boundary)
        self._backend.set_loop(handle, loop)
        state._set_loop(loop)

    def toggle_play_pause(self, handle: str) -> None:
        """Toggle between play and pause states.

        Args:
            handle: Handle ID from load()
        """
        with self._states_lock:
            if handle not in self._states:
                return
            state = self._states[handle]

        if state.state == PlaybackState.PLAYING:
            self.pause(handle)
        elif state.state in (PlaybackState.PAUSED, PlaybackState.STOPPED):
            self.play(handle)

    def unload(self, handle: str) -> None:
        """Unload an audio resource and free its resources.

        Args:
            handle: Handle ID from load()
        """
        self._unload_internal(handle)
        self._ensure_position_thread_running()

    def _unload_internal(self, handle: str) -> None:
        """Internal unload without thread management."""
        if self._backend is None:
            return

        with self._states_lock:
            if handle not in self._states:
                return
            del self._states[handle]

        try:
            self._backend.unload(handle)
        except Exception:
            pass

    def get_state(self, handle: str) -> AudioState | None:
        """Get the AudioState for a handle.

        Args:
            handle: Handle ID from load()

        Returns:
            AudioState or None if not found
        """
        with self._states_lock:
            return self._states.get(handle)

    def set_on_ended(self, handle: str, callback: Callable[[], None] | None) -> None:
        """Set callback for when playback ends.

        Note: This callback is called in addition to internal state management.
        The callback is invoked from a background thread.

        Args:
            handle: Handle ID from load()
            callback: Function to call when playback ends, or None to clear
        """
        if self._backend is None:
            return

        with self._states_lock:
            if handle not in self._states:
                return
            state = self._states[handle]

        # Wrap callback to handle both internal state and user callback
        def on_ended():
            if not state.loop:
                state._set_state(PlaybackState.STOPPED)
                state._set_position(0)
            if callback is not None:
                callback()

        self._backend.set_on_ended(handle, on_ended)

    @property
    def backend(self) -> AudioBackend | None:
        """Get the current audio backend."""
        return self._backend

    @property
    def backend_name(self) -> str:
        """Get the name of the current audio backend."""
        if self._backend is None:
            return "none"
        return self._backend.__class__.__name__
