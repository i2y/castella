# Audio Playback

Castella provides cross-platform audio playback support through the `AudioPlayer` widget and `AudioManager` API. This enables playing music, sound effects, and other audio content in your applications.

## Installation

Audio support requires the SDL_mixer backend, which is included with the SDL backends:

```bash
# Option 1: Audio-only (minimal)
uv add "castella[audio]"

# Option 2: Full SDL2 backend (includes audio)
uv add "castella[sdl]"

# Option 3: Full SDL3 backend (includes audio)
uv add "castella[sdl3]"
```

## Supported Formats

The SDL_mixer backend supports:

- **MP3** - MPEG Audio Layer 3
- **OGG** - Ogg Vorbis
- **WAV** - Waveform Audio
- **FLAC** - Free Lossless Audio Codec
- **MIDI** - Musical Instrument Digital Interface
- **MOD** - Module formats (MOD, XM, IT, S3M)

## AudioPlayer Widget

The `AudioPlayer` widget provides a complete audio player UI with built-in controls:

```python
from castella import App
from castella.audio import AudioPlayer
from castella.frame import Frame

# Create player with audio file
player = AudioPlayer("music.mp3")

# Optional: callback when playback ends
player.on_ended(lambda: print("Playback finished!"))

App(Frame("Audio Player", 500, 200), player).run()
```

### AudioPlayer Features

- **Play/Pause button** - Toggle playback
- **Stop button** - Stop and reset to beginning
- **Seek slider** - Scrub through the audio
- **Volume slider** - Adjust volume (0-100%)
- **Loop toggle** - Enable/disable loop playback
- **Time display** - Shows current position and duration

### AudioPlayer Options

```python
player = AudioPlayer(
    source="music.mp3",    # Audio file path (optional, can load later)
    show_volume=True,      # Show volume slider (default: True)
    show_loop=True,        # Show loop toggle (default: True)
    show_time=True,        # Show time display (default: True)
)
```

### Loading Audio Later

```python
player = AudioPlayer()  # Create without source
player.load("music.mp3")  # Load later
player.play()
```

### Using AudioPlayer in Components

When using `AudioPlayer` in a `Component`, use `freeze()` to preserve the player across view rebuilds:

```python
from castella import Component, Column, Text
from castella.audio import AudioPlayer
from castella.core import State


class MusicPlayerComponent(Component):
    def __init__(self, audio_file: str):
        super().__init__()
        self._status = State("Ready")
        self._status.attach(self)

        # Create and freeze the player
        self._player = AudioPlayer(audio_file)
        self._player.on_ended(self._on_ended)
        self._player.freeze()  # Prevents audio unload on view rebuild

    def _on_ended(self):
        self._status.set("Playback finished!")

    def view(self):
        return Column(
            Text(f"Status: {self._status()}"),
            self._player,
        )
```

## AudioManager API

For more control over audio playback, use the low-level `AudioManager` API:

```python
from castella.audio import AudioManager

# Get the singleton manager
manager = AudioManager.get()

# Load an audio file
handle, state = manager.load("music.mp3")

# Control playback
manager.play(handle)
manager.pause(handle)
manager.stop(handle)

# Adjust settings
manager.set_volume(handle, 0.5)  # 50% volume (0.0 to 1.0)
manager.seek(handle, 30000)      # Seek to 30 seconds (milliseconds)
manager.set_loop(handle, True)   # Enable loop

# Cleanup when done
manager.unload(handle)
```

### AudioManager Methods

| Method | Description |
|--------|-------------|
| `load(source)` | Load audio file, returns `(handle, AudioState)` |
| `play(handle, loop=False)` | Start playback |
| `pause(handle)` | Pause playback |
| `stop(handle)` | Stop and reset position |
| `seek(handle, position_ms)` | Seek to position in milliseconds |
| `set_volume(handle, volume)` | Set volume (0.0 to 1.0) |
| `set_loop(handle, loop)` | Enable/disable loop |
| `get_state(handle)` | Get `AudioState` for a handle |
| `unload(handle)` | Unload audio and free resources |
| `set_on_ended(handle, callback)` | Set callback for playback end |

### Reactive AudioState

`AudioState` is observable and can be attached to components for automatic UI updates:

```python
from castella.audio import AudioManager, PlaybackState
from castella import StatefulComponent, Column, Text, Button


class CustomPlayer(StatefulComponent):
    def __init__(self, audio_file: str):
        manager = AudioManager.get()
        self._handle, self._state = manager.load(audio_file)
        super().__init__(self._state)  # Trigger view() on state change

    def view(self):
        return Column(
            Text(f"State: {self._state.state.value}"),
            Text(f"Position: {self._state.format_progress()}"),
            Text(f"Volume: {int(self._state.volume * 100)}%"),
            Button("Play").on_click(lambda _: AudioManager.get().play(self._handle)),
            Button("Pause").on_click(lambda _: AudioManager.get().pause(self._handle)),
        )
```

### AudioState Properties

| Property | Type | Description |
|----------|------|-------------|
| `state` | `PlaybackState` | Current state (STOPPED, PLAYING, PAUSED, LOADING, ERROR) |
| `position_ms` | `int` | Current position in milliseconds |
| `duration_ms` | `int` | Total duration in milliseconds |
| `volume` | `float` | Volume level (0.0 to 1.0) |
| `loop` | `bool` | Loop setting |
| `progress` | `float` | Playback progress (0.0 to 1.0) |
| `error_message` | `str \| None` | Error message if state is ERROR |

### AudioState Methods

| Method | Description |
|--------|-------------|
| `is_playing()` | Check if currently playing |
| `is_paused()` | Check if paused |
| `is_stopped()` | Check if stopped |
| `format_time(ms)` | Format milliseconds as "M:SS" or "H:MM:SS" |
| `format_duration()` | Format total duration |
| `format_progress()` | Format as "position / duration" |

## PlaybackState Enum

```python
from castella.audio import PlaybackState

PlaybackState.STOPPED   # Audio is stopped
PlaybackState.PLAYING   # Audio is playing
PlaybackState.PAUSED    # Audio is paused
PlaybackState.LOADING   # Audio is loading
PlaybackState.ERROR     # An error occurred
```

## Playback End Callback

Get notified when playback ends:

```python
# With AudioPlayer
player = AudioPlayer("music.mp3")
player.on_ended(lambda: print("Done!"))

# With AudioManager
manager = AudioManager.get()
handle, state = manager.load("music.mp3")
manager.set_on_ended(handle, lambda: print("Done!"))
```

## Backend Information

Check which audio backend is being used:

```python
from castella.audio import AudioManager

manager = AudioManager.get()
print(f"Backend: {manager.backend_name}")  # e.g., "SDL_mixer"
```

## Terminal Mode (TUI)

In terminal mode, a silent "noop" backend is used. Audio methods work but produce no sound:

```bash
CASTELLA_FRAME=tui uv run python your_app.py
```

## Complete Example

See [examples/audio_player_demo.py](https://github.com/i2y/castella/blob/main/examples/audio_player_demo.py) for a complete example demonstrating both the `AudioPlayer` widget and low-level `AudioManager` API.

```bash
uv run python examples/audio_player_demo.py path/to/audio.mp3
```
