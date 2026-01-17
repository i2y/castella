"""AudioPlayer widget for audio playback with controls."""

from __future__ import annotations

from typing import Callable, Self

from castella import Button, Column, Row, Slider, SliderState, Spacer, Text
from castella.animation import Animation, AnimationScheduler
from castella.core import App, Component, SizePolicy, State, Widget
from castella.models.events import UpdateEvent

from ..manager import AudioManager
from ..state import AudioState, PlaybackState


class _PositionPoller(Animation):
    """Animation that polls audio position and triggers UI updates.

    This runs on the AnimationScheduler's thread and uses post_update()
    to safely trigger Component rebuilds on the main thread.

    Focuses on:
    - Updating position during playback
    - Detecting natural end of playback (not user-initiated stop/pause)
    """

    def __init__(
        self,
        component: "AudioPlayer",
        audio_state_getter: Callable[[], AudioState | None],
    ):
        super().__init__()
        self._component = component
        self._get_audio_state = audio_state_getter
        self._last_position_ms = -1
        self._elapsed = 0.0
        self._update_interval = 1.0  # 1 second between UI updates

    def tick(self, dt: float) -> bool:
        """Called by AnimationScheduler. Returns True when animation should stop."""
        if self._cancelled:
            return True

        audio_state = self._get_audio_state()
        if audio_state is None:
            return True  # Stop if no audio state

        current_state = audio_state.state

        # Stop if not playing (natural end or user stopped)
        if current_state != PlaybackState.PLAYING:
            # Trigger final rebuild to update button text
            self._trigger_rebuild()
            return True

        # Throttle position updates during playback
        self._elapsed += dt
        if self._elapsed >= self._update_interval:
            self._elapsed = 0.0
            current_position = audio_state.position_ms
            # Only update UI if position actually changed
            if current_position != self._last_position_ms:
                self._last_position_ms = current_position
                self._trigger_rebuild()

        return False  # Keep running

    def _trigger_rebuild(self) -> None:
        """Trigger a Component rebuild via post_update."""
        self._component._pending_rebuild = True
        app = App.get()
        if app is not None:
            app._frame.post_update(UpdateEvent(target=self._component, completely=True))


class AudioPlayer(Component):
    """Audio player widget with playback controls.

    Provides a complete audio player UI with:
    - Play/Pause button
    - Stop button
    - Seek slider
    - Volume slider
    - Time display (current / duration)
    - Loop toggle

    Example:
        # Simple usage
        player = AudioPlayer("music.mp3")

        # With callbacks
        player = AudioPlayer("music.mp3")
        player.on_ended(lambda: print("Finished!"))

        # Load later
        player = AudioPlayer()
        player.load("music.mp3")
    """

    def __init__(
        self,
        source: str | None = None,
        show_volume: bool = True,
        show_loop: bool = True,
        show_time: bool = True,
    ):
        """Initialize AudioPlayer.

        Args:
            source: Path to audio file (optional, can load later)
            show_volume: Show volume slider
            show_loop: Show loop toggle button
            show_time: Show time display
        """
        super().__init__()
        self._source = source
        self._show_volume = show_volume
        self._show_loop = show_loop
        self._show_time = show_time

        self._handle: str | None = None
        self._audio_state: AudioState | None = None
        self._on_ended_callback: Callable[[], None] | None = None

        # UI state
        self._seek_state = SliderState(value=0, min_val=0, max_val=100)
        self._volume_state = SliderState(
            value=10, min_val=0, max_val=100
        )  # Default 10%
        self._is_loop = State(False)

        # Attach _is_loop for loop button updates (Component rebuilds view)
        self._is_loop.attach(self)

        # Position polling animation (managed by AnimationScheduler)
        self._position_poller: _PositionPoller | None = None

        # Load if source provided
        if source:
            self._load_source(source)

    def _load_source(self, source: str) -> None:
        """Load an audio source."""
        manager = AudioManager.get()

        # Stop and cancel previous poller
        self._stop_position_poller()

        # Unload previous
        if self._handle is not None:
            manager.unload(self._handle)

        # Load new
        self._handle, self._audio_state = manager.load(source)
        self._source = source

        # Update seek slider max to duration
        duration = self._audio_state.duration_ms
        self._seek_state.set_range(0, max(duration, 1))

        # Apply initial volume (default 10%)
        manager.set_volume(self._handle, self._volume_state.value() / 100.0)

        # Set up ended callback
        if self._on_ended_callback is not None:
            manager.set_on_ended(self._handle, self._on_ended_callback)

    def load(self, source: str) -> Self:
        """Load an audio file.

        Args:
            source: Path to audio file

        Returns:
            Self for method chaining
        """
        self._load_source(source)
        return self

    def _start_position_poller(self) -> None:
        """Start the position polling animation."""
        # Cancel existing poller if any
        self._stop_position_poller()

        # Create and start new poller
        self._position_poller = _PositionPoller(
            component=self,
            audio_state_getter=lambda: self._audio_state,
        )
        AnimationScheduler.get().add(self._position_poller)

    def _stop_position_poller(self) -> None:
        """Stop the position polling animation."""
        if self._position_poller is not None:
            self._position_poller.cancel()
            AnimationScheduler.get().remove(self._position_poller)
            self._position_poller = None

    def play(self) -> None:
        """Start playback."""
        if self._handle is None:
            return
        AudioManager.get().play(self._handle, loop=self._is_loop())
        # Start position polling for UI updates
        self._start_position_poller()

    def pause(self) -> None:
        """Pause playback."""
        if self._handle is None:
            return
        AudioManager.get().pause(self._handle)
        self._stop_position_poller()
        self._trigger_rebuild()

    def stop(self) -> None:
        """Stop playback."""
        if self._handle is None:
            return
        AudioManager.get().stop(self._handle)
        self._seek_state._value = 0  # Don't trigger notify
        self._stop_position_poller()
        self._trigger_rebuild()

    def toggle_play_pause(self) -> None:
        """Toggle between play and pause."""
        if self._handle is None or self._audio_state is None:
            return
        manager = AudioManager.get()
        if self._audio_state.is_playing():
            manager.pause(self._handle)
            # Stop poller and trigger immediate rebuild
            self._stop_position_poller()
            self._trigger_rebuild()
        else:
            manager.play(self._handle, loop=self._is_loop())
            # Start position polling for UI updates (works for both stopped and paused states)
            self._start_position_poller()

    def _trigger_rebuild(self) -> None:
        """Trigger an immediate UI rebuild."""
        self._pending_rebuild = True
        app = App.get()
        if app is not None:
            app._frame.post_update(UpdateEvent(target=self, completely=True))

    def on_ended(self, callback: Callable[[], None]) -> Self:
        """Set callback for when playback ends.

        Args:
            callback: Function to call when playback ends

        Returns:
            Self for method chaining
        """
        self._on_ended_callback = callback
        if self._handle is not None:
            AudioManager.get().set_on_ended(self._handle, callback)
        return self

    def _get_time_display(self) -> str:
        """Get the time display text from audio state."""
        if self._audio_state is not None:
            return self._audio_state.format_progress()
        return "0:00 / 0:00"

    def _on_seek(self, value: float) -> None:
        """Handle seek slider change."""
        if self._handle is None:
            return
        AudioManager.get().seek(self._handle, int(value))

    def _on_volume_change(self, value: float) -> None:
        """Handle volume slider change."""
        if self._handle is None:
            return
        AudioManager.get().set_volume(self._handle, value / 100.0)

    def _on_loop_toggle(self, _) -> None:
        """Handle loop button click."""
        new_loop = not self._is_loop()
        self._is_loop.set(new_loop)
        if self._handle is not None:
            AudioManager.get().set_loop(self._handle, new_loop)

    def _get_play_button_text(self) -> str:
        """Get play/pause button text based on state."""
        if self._audio_state is None:
            return "Play"
        if self._audio_state.is_playing():
            return "Pause"
        return "Play"

    def view(self) -> Widget:
        """Build the player UI."""
        # Update seek slider position from audio state
        if self._audio_state is not None:
            position = self._audio_state.position_ms
            duration = self._audio_state.duration_ms
            # Snap to end if very close (within 500ms) to prevent incomplete fill
            if duration > 0 and position > 0 and (duration - position) < 500:
                position = duration
            self._seek_state._value = position

        # Play/Pause button
        play_text = self._get_play_button_text()

        play_btn = (
            Button(play_text)
            .on_click(lambda _: self.toggle_play_pause())
            .fixed_width(70)
            .fixed_height(32)
        )

        # Stop button
        stop_btn = (
            Button("Stop")
            .on_click(lambda _: self.stop())
            .fixed_width(50)
            .fixed_height(32)
        )

        # Controls row
        controls = [play_btn, stop_btn]

        # Loop button
        if self._show_loop:
            loop_text = "Loop: ON" if self._is_loop() else "Loop: OFF"
            loop_btn = (
                Button(loop_text)
                .on_click(self._on_loop_toggle)
                .fixed_width(80)
                .fixed_height(32)
            )
            controls.append(loop_btn)

        controls.append(Spacer())

        # Time display (rebuilt with current value on each view() call)
        if self._show_time:
            time_label = Text(self._get_time_display()).fixed_size(100, 32)
            controls.append(time_label)

        controls_row = (
            Row(*controls).width_policy(SizePolicy.EXPANDING).fixed_height(40)
        )

        # Seek slider
        seek_slider = (
            Slider(self._seek_state)
            .on_change(self._on_seek)
            .width_policy(SizePolicy.EXPANDING)
            .fixed_height(24)
        )

        # Build main layout
        rows: list[Widget] = [controls_row, seek_slider]

        # Volume slider
        if self._show_volume:
            volume_label = Text("Volume:").fixed_width(60).fixed_height(24)
            volume_slider = (
                Slider(self._volume_state)
                .on_change(self._on_volume_change)
                .width_policy(SizePolicy.EXPANDING)
                .fixed_height(24)
            )
            volume_row = (
                Row(volume_label, volume_slider)
                .width_policy(SizePolicy.EXPANDING)
                .fixed_height(30)
            )
            rows.append(volume_row)

        return (
            Column(*rows)
            .width_policy(SizePolicy.EXPANDING)
            .height_policy(SizePolicy.CONTENT)
        )

    def detach(self) -> None:
        """Cleanup when widget is removed."""
        super().detach()
        # Only unload audio if not frozen (freeze() is used to preserve audio across rebuilds)
        if self._enable_to_detach and self._handle is not None:
            self._stop_position_poller()
            AudioManager.get().unload(self._handle)
            self._handle = None
            self._audio_state = None
