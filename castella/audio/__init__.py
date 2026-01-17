"""Castella audio module for audio playback support.

This module provides audio playback capabilities for Castella applications.
It uses a backend abstraction to support different audio systems across platforms.

Basic usage:
    from castella.audio import AudioManager

    # Get the singleton manager
    manager = AudioManager.get()

    # Load an audio file
    handle, state = manager.load("music.mp3")

    # Optionally attach state to a component for UI updates
    state.attach(my_component)

    # Control playback
    manager.play(handle)
    manager.pause(handle)
    manager.set_volume(handle, 0.5)
    manager.seek(handle, 30000)  # 30 seconds
    manager.stop(handle)

    # Cleanup
    manager.unload(handle)

Widget usage:
    from castella.audio import AudioPlayer

    # Create a player widget with built-in controls
    player = AudioPlayer("music.mp3")
    player.on_ended(lambda: print("Playback finished"))

Supported backends:
    - SDL_mixer (desktop): MP3, OGG, WAV, FLAC, MIDI, MOD
    - Noop (TUI): Silent fallback for terminal mode

Environment variables:
    - CASTELLA_FRAME=tui: Force noop backend
    - CASTELLA_IS_TERMINAL_MODE=true: Force noop backend
"""

from .state import AudioState, PlaybackState
from .manager import AudioManager
from .protocols import AudioBackend, AudioLoadError, AudioPlaybackError

__all__ = [
    # Core classes
    "AudioManager",
    "AudioState",
    "PlaybackState",
    # Protocols and errors
    "AudioBackend",
    "AudioLoadError",
    "AudioPlaybackError",
]


# Lazy imports for widgets to avoid circular imports
def __getattr__(name: str):
    if name == "AudioPlayer":
        from .widgets import AudioPlayer

        return AudioPlayer
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
