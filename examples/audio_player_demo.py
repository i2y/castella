"""Audio player demo for Castella.

This demo shows how to use the AudioPlayer widget and AudioManager
for audio playback.

Requirements:
    uv sync --extra sdl --extra audio

Usage:
    uv run python examples/audio_player_demo.py [audio_file.mp3]

If no audio file is provided, the demo will show the player UI
but you'll need to use the file picker or modify the code to load a file.
"""

import sys
from pathlib import Path

from castella import App, Button, Column, Row, Spacer, Text
from castella.audio import AudioManager, AudioPlayer
from castella.core import Component, State
from castella.frame import Frame


class AudioPlayerDemo(Component):
    """Demo component showing AudioPlayer widget usage."""

    def __init__(self, audio_file: str | None = None):
        super().__init__()
        self._audio_file = audio_file
        self._status = State("Ready")
        self._status.attach(self)

        # Create player once and reuse (don't recreate in view())
        self._player: AudioPlayer | None = None
        if audio_file:
            self._player = AudioPlayer(audio_file)
            self._player.on_ended(self._on_ended)
            # Freeze to prevent detach() from unloading audio on view rebuild
            self._player.freeze()

    def _on_ended(self) -> None:
        """Called when playback ends."""
        self._status.set("Playback finished!")

    def view(self):
        # Status display
        status_row = Row(
            Text("Status:").fixed_width(60).fixed_height(24),
            Text(self._status()).fixed_height(24),
        ).fixed_height(30)

        # Use existing player or create empty one
        if self._player is not None:
            player = self._player
            file_label = Text(f"File: {self._audio_file}").fixed_height(24)
        else:
            player = AudioPlayer()
            file_label = Text("No audio file specified").fixed_height(24)

        # Backend info
        manager = AudioManager.get()
        backend_label = Text(f"Backend: {manager.backend_name}").fixed_height(24)

        # Instructions
        instructions = Text(
            "Controls: Play/Pause, Stop, Seek slider, Volume slider, Loop toggle"
        ).fixed_height(24)

        return Column(
            Text("Castella Audio Player Demo").fixed_height(32),
            Spacer().fixed_height(10),
            file_label,
            backend_label,
            Spacer().fixed_height(10),
            player,
            Spacer().fixed_height(10),
            status_row,
            instructions,
            Spacer(),
        )


class LowLevelAudioDemo(Component):
    """Demo showing low-level AudioManager API usage."""

    def __init__(self, audio_file: str | None = None):
        super().__init__()
        self._audio_file = audio_file
        self._handle: str | None = None
        self._status = State("Ready")
        self._position = State("0:00 / 0:00")
        self._status.attach(self)
        self._position.attach(self)

        if audio_file:
            self._load_audio(audio_file)

    def _load_audio(self, path: str) -> None:
        """Load audio file using low-level API."""
        manager = AudioManager.get()

        # Unload previous
        if self._handle:
            manager.unload(self._handle)

        # Load new
        self._handle, state = manager.load(path)

        # Attach state for position updates
        state.attach(self)
        self._status.set(f"Loaded: {path}")

    def _on_play(self, _) -> None:
        if self._handle:
            AudioManager.get().play(self._handle)
            self._status.set("Playing")

    def _on_pause(self, _) -> None:
        if self._handle:
            AudioManager.get().pause(self._handle)
            self._status.set("Paused")

    def _on_stop(self, _) -> None:
        if self._handle:
            AudioManager.get().stop(self._handle)
            self._status.set("Stopped")

    def on_notify(self, event=None) -> None:
        """Update position display when audio state changes."""
        if self._handle:
            state = AudioManager.get().get_state(self._handle)
            if state:
                self._position.set(state.format_progress())
        super().on_notify(event)

    def view(self):
        return Column(
            Text("Low-Level AudioManager API Demo").fixed_height(32),
            Spacer().fixed_height(10),
            Text(f"Status: {self._status()}").fixed_height(24),
            Text(f"Position: {self._position()}").fixed_height(24),
            Spacer().fixed_height(10),
            Row(
                Button("Play").on_click(self._on_play).fixed_width(60).fixed_height(32),
                Button("Pause")
                .on_click(self._on_pause)
                .fixed_width(60)
                .fixed_height(32),
                Button("Stop").on_click(self._on_stop).fixed_width(60).fixed_height(32),
                Spacer(),
            ).fixed_height(40),
            Spacer(),
        )


def main():
    # Get audio file from command line args
    audio_file = None
    if len(sys.argv) > 1:
        audio_file = sys.argv[1]
        if not Path(audio_file).exists():
            print(f"Warning: File not found: {audio_file}")
            audio_file = None

    # Create the app
    frame = Frame("Castella Audio Player Demo", 500, 300)
    app = App(frame, AudioPlayerDemo(audio_file))
    app.run()


if __name__ == "__main__":
    main()
