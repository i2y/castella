"""SDL_mixer audio backend using pysdl2."""

from __future__ import annotations

import ctypes
import threading
import uuid
from typing import Callable

from sdl2 import sdlmixer

from castella.audio.protocols import AudioBackend, AudioLoadError, AudioPlaybackError


class SDLMixerBackend(AudioBackend):
    """SDL_mixer-based audio backend for desktop platforms.

    Uses SDL2_mixer for audio playback, supporting MP3, OGG, WAV, and other formats.

    This backend uses:
    - Mix_LoadMUS() for streaming music files
    - Mix_LoadWAV() for sound effects (loaded entirely into memory)

    Music playback uses channel -1 (music channel), while sound effects
    use numbered channels. This backend focuses on music playback.
    """

    _initialized = False
    _init_lock = threading.Lock()

    def __init__(self) -> None:
        """Initialize SDL_mixer backend."""
        self._ensure_initialized()
        self._music_handles: dict[str, ctypes.c_void_p] = {}
        self._chunk_handles: dict[str, ctypes.c_void_p] = {}
        self._channels: dict[str, int] = {}  # handle -> channel for chunks
        self._volumes: dict[str, float] = {}
        self._callbacks: dict[str, Callable[[], None] | None] = {}
        self._loop_settings: dict[str, bool] = {}  # Track loop setting per handle
        self._current_music_handle: str | None = None
        self._music_position_ms: int = 0
        self._music_start_time: float = 0.0
        self._music_paused_position: int = 0
        self._lock = threading.Lock()

        # Flag set by SDL audio callback, processed by position thread
        # Using a simple flag avoids deadlock between audio thread and lock holders
        self._music_finished_flag: bool = False

        # Set up music finished callback
        # Note: SDL_mixer callback runs in the audio thread
        self._setup_music_finished_callback()

    @classmethod
    def _ensure_initialized(cls) -> None:
        """Ensure SDL_mixer is initialized."""
        with cls._init_lock:
            if cls._initialized:
                return

            # Initialize SDL_mixer with common audio settings
            # 44100 Hz, signed 16-bit, stereo, 2048 byte chunks
            result = sdlmixer.Mix_OpenAudio(44100, sdlmixer.MIX_DEFAULT_FORMAT, 2, 2048)
            if result < 0:
                raise AudioLoadError(
                    f"Failed to initialize SDL_mixer: {sdlmixer.Mix_GetError()}"
                )

            cls._initialized = True

    def _setup_music_finished_callback(self) -> None:
        """Set up the music finished callback."""
        # SDL_mixer's HookMusicFinished requires a C callback
        # We use ctypes to create one
        self._music_finished_callback = ctypes.CFUNCTYPE(None)(
            self._on_music_finished_internal
        )
        sdlmixer.Mix_HookMusicFinished(self._music_finished_callback)

    def _on_music_finished_internal(self) -> None:
        """Internal callback when music finishes.

        IMPORTANT: This is called from SDL's audio thread. We must NOT:
        - Acquire any locks (could deadlock with other threads calling SDL functions)
        - Call SDL functions (not safe from callback context)

        Instead, we just set a flag that will be checked by the position update thread.
        """
        self._music_finished_flag = True

    def _handle_music_finished(self) -> None:
        """Handle music finished event - called from position update thread.

        This is safe to call SDL functions and acquire locks because we're
        not in the SDL audio callback context.
        """
        with self._lock:
            if self._current_music_handle is None:
                return

            handle = self._current_music_handle

            # Check if loop is enabled - if so, restart playback
            if self._loop_settings.get(handle, False):
                music = self._music_handles.get(handle)
                if music is not None:
                    # Restart playback (always play once, check loop again when done)
                    sdlmixer.Mix_PlayMusic(music, 0)
                    self._music_position_ms = 0
                    import time

                    self._music_start_time = time.time()
                    return  # Don't call the ended callback for loops

            # Not looping or loop disabled - call the ended callback
            callback = self._callbacks.get(handle)
            if callback is not None:
                # Run callback in a separate thread to avoid blocking
                threading.Thread(target=callback, daemon=True).start()

    def check_music_finished(self) -> bool:
        """Check if music finished and handle it if so.

        Returns True if music finished and was handled.
        Should be called periodically from position update thread.
        """
        if self._music_finished_flag:
            self._music_finished_flag = False
            self._handle_music_finished()
            return True
        return False

    def load(self, source: str) -> str:
        """Load an audio file and return a handle ID."""
        handle = str(uuid.uuid4())

        # Determine if this is music or a sound effect based on file extension
        # Most audio files should be loaded as music for position tracking
        source_lower = source.lower()
        is_music = source_lower.endswith(
            (
                ".mp3",
                ".ogg",
                ".flac",
                ".wav",
                ".mid",
                ".midi",
                ".mod",
                ".s3m",
                ".it",
                ".xm",
            )
        )

        if is_music:
            music = sdlmixer.Mix_LoadMUS(source.encode("utf-8"))
            if not music:
                raise AudioLoadError(
                    f"Failed to load music '{source}': {sdlmixer.Mix_GetError()}"
                )
            with self._lock:
                self._music_handles[handle] = music
        else:
            chunk = sdlmixer.Mix_LoadWAV(source.encode("utf-8"))
            if not chunk:
                raise AudioLoadError(
                    f"Failed to load audio '{source}': {sdlmixer.Mix_GetError()}"
                )
            with self._lock:
                self._chunk_handles[handle] = chunk

        with self._lock:
            self._volumes[handle] = 1.0
            self._callbacks[handle] = None
            self._loop_settings[handle] = False

        return handle

    def play(self, handle: str, loop: bool = False) -> None:
        """Start playback of an audio resource."""
        with self._lock:
            # Store loop setting - can be changed during playback
            self._loop_settings[handle] = loop

            if handle in self._music_handles:
                music = self._music_handles[handle]
                # Always play once (loops=0), looping is handled in callback
                result = sdlmixer.Mix_PlayMusic(music, 0)
                if result < 0:
                    raise AudioPlaybackError(
                        f"Failed to play music: {sdlmixer.Mix_GetError()}"
                    )
                self._current_music_handle = handle
                self._music_position_ms = 0
                import time

                self._music_start_time = time.time()
                # Apply volume
                volume = self._volumes.get(handle, 1.0)
                sdlmixer.Mix_VolumeMusic(int(volume * sdlmixer.MIX_MAX_VOLUME))

            elif handle in self._chunk_handles:
                chunk = self._chunk_handles[handle]
                # Always play once (loops=0), looping is handled in callback
                channel = sdlmixer.Mix_PlayChannel(-1, chunk, 0)
                if channel < 0:
                    raise AudioPlaybackError(
                        f"Failed to play audio: {sdlmixer.Mix_GetError()}"
                    )
                self._channels[handle] = channel
                # Apply volume
                volume = self._volumes.get(handle, 1.0)
                sdlmixer.Mix_Volume(channel, int(volume * sdlmixer.MIX_MAX_VOLUME))

    def pause(self, handle: str) -> None:
        """Pause playback of an audio resource."""
        with self._lock:
            if handle in self._music_handles:
                if self._current_music_handle == handle:
                    sdlmixer.Mix_PauseMusic()
                    import time

                    elapsed = time.time() - self._music_start_time
                    self._music_paused_position = self._music_position_ms + int(
                        elapsed * 1000
                    )
            elif handle in self._channels:
                channel = self._channels[handle]
                sdlmixer.Mix_Pause(channel)

    def resume(self, handle: str) -> None:
        """Resume playback of a paused audio resource."""
        with self._lock:
            if handle in self._music_handles:
                if self._current_music_handle == handle:
                    sdlmixer.Mix_ResumeMusic()
                    import time

                    self._music_start_time = time.time()
                    self._music_position_ms = self._music_paused_position
            elif handle in self._channels:
                channel = self._channels[handle]
                sdlmixer.Mix_Resume(channel)

    def stop(self, handle: str) -> None:
        """Stop playback of an audio resource."""
        with self._lock:
            if handle in self._music_handles:
                if self._current_music_handle == handle:
                    sdlmixer.Mix_HaltMusic()
                    self._current_music_handle = None
                    self._music_position_ms = 0
            elif handle in self._channels:
                channel = self._channels[handle]
                sdlmixer.Mix_HaltChannel(channel)
                del self._channels[handle]

    def seek(self, handle: str, position_ms: int) -> None:
        """Seek to a position in the audio."""
        with self._lock:
            if handle in self._music_handles:
                if self._current_music_handle == handle:
                    # SDL_mixer supports seeking in seconds for music
                    position_sec = position_ms / 1000.0
                    sdlmixer.Mix_SetMusicPosition(position_sec)
                    self._music_position_ms = position_ms
                    import time

                    self._music_start_time = time.time()
            # Note: SDL_mixer doesn't support seeking for chunks

    def set_volume(self, handle: str, volume: float) -> None:
        """Set playback volume."""
        volume = max(0.0, min(1.0, volume))
        with self._lock:
            self._volumes[handle] = volume
            sdl_volume = int(volume * sdlmixer.MIX_MAX_VOLUME)

            if handle in self._music_handles:
                if self._current_music_handle == handle:
                    sdlmixer.Mix_VolumeMusic(sdl_volume)
            elif handle in self._channels:
                channel = self._channels[handle]
                sdlmixer.Mix_Volume(channel, sdl_volume)

    def get_position(self, handle: str) -> int:
        """Get current playback position in milliseconds."""
        with self._lock:
            if handle in self._music_handles:
                if self._current_music_handle == handle:
                    if sdlmixer.Mix_PausedMusic():
                        return self._music_paused_position
                    import time

                    elapsed = time.time() - self._music_start_time
                    return self._music_position_ms + int(elapsed * 1000)
                return 0
            # SDL_mixer doesn't provide position for chunks
            return 0

    def get_duration(self, handle: str) -> int:
        """Get total duration of the audio in milliseconds."""
        with self._lock:
            if handle in self._music_handles:
                music = self._music_handles[handle]
                # Mix_MusicDuration returns seconds (SDL2_mixer 2.6.0+)
                try:
                    duration_sec = sdlmixer.Mix_MusicDuration(music)
                    if duration_sec > 0:
                        return int(duration_sec * 1000)
                except AttributeError:
                    # Mix_MusicDuration not available in older versions
                    pass
                # Fallback: return 0 (unknown duration)
                return 0
            elif handle in self._chunk_handles:
                # For chunks, we can calculate from the struct
                # but this is complex; return 0 for now
                return 0
            return 0

    def is_playing(self, handle: str) -> bool:
        """Check if audio is currently playing."""
        with self._lock:
            if handle in self._music_handles:
                if self._current_music_handle == handle:
                    return (
                        sdlmixer.Mix_PlayingMusic() == 1
                        and sdlmixer.Mix_PausedMusic() == 0
                    )
                return False
            elif handle in self._channels:
                channel = self._channels[handle]
                return (
                    sdlmixer.Mix_Playing(channel) == 1
                    and sdlmixer.Mix_Paused(channel) == 0
                )
            return False

    def unload(self, handle: str) -> None:
        """Unload an audio resource and free its resources."""
        with self._lock:
            if handle in self._music_handles:
                if self._current_music_handle == handle:
                    sdlmixer.Mix_HaltMusic()
                    self._current_music_handle = None
                music = self._music_handles.pop(handle)
                sdlmixer.Mix_FreeMusic(music)
            elif handle in self._chunk_handles:
                if handle in self._channels:
                    channel = self._channels.pop(handle)
                    sdlmixer.Mix_HaltChannel(channel)
                chunk = self._chunk_handles.pop(handle)
                sdlmixer.Mix_FreeChunk(chunk)

            self._volumes.pop(handle, None)
            self._callbacks.pop(handle, None)
            self._loop_settings.pop(handle, None)

    def set_on_ended(self, handle: str, callback: Callable[[], None] | None) -> None:
        """Set callback for when playback ends."""
        with self._lock:
            self._callbacks[handle] = callback

    def set_loop(self, handle: str, loop: bool) -> None:
        """Set loop setting for an audio resource."""
        with self._lock:
            self._loop_settings[handle] = loop

    def __del__(self) -> None:
        """Cleanup on deletion."""
        # Note: We don't call Mix_CloseAudio here because it's a singleton
        # and other parts of the app might still need it
        with self._lock:
            for handle in list(self._music_handles.keys()):
                try:
                    self.unload(handle)
                except Exception:
                    pass
            for handle in list(self._chunk_handles.keys()):
                try:
                    self.unload(handle)
                except Exception:
                    pass
