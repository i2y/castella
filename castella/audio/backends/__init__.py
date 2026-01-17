"""Audio backend auto-detection and selection."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from castella.audio.protocols import AudioBackend


def get_backend() -> "AudioBackend":
    """Get the appropriate audio backend for the current environment.

    Detection order:
    1. If CASTELLA_IS_TERMINAL_MODE is set, use NoopBackend
    2. Try SDL_mixer backend (desktop)
    3. Fall back to NoopBackend

    Returns:
        AudioBackend instance
    """
    # Check for terminal mode
    if os.environ.get("CASTELLA_IS_TERMINAL_MODE") == "true":
        from .noop import NoopBackend

        return NoopBackend()

    if os.environ.get("CASTELLA_FRAME") == "tui":
        from .noop import NoopBackend

        return NoopBackend()

    # Try SDL_mixer backend
    try:
        from .sdl_mixer import SDLMixerBackend

        return SDLMixerBackend()
    except ImportError:
        pass

    # Fall back to noop backend
    from .noop import NoopBackend

    return NoopBackend()


__all__ = ["get_backend"]
