"""Runtime module for Edda Workflow Manager.

Provides a persistent event loop for all Edda operations.
This module is separate from main.py to avoid issues with __main__ imports.
"""

from __future__ import annotations

import asyncio
import threading


# Global event loop for Edda operations
_edda_loop: asyncio.AbstractEventLoop | None = None
_edda_thread: threading.Thread | None = None


def get_edda_loop() -> asyncio.AbstractEventLoop:
    """Get the persistent event loop for Edda operations."""
    global _edda_loop
    if _edda_loop is None:
        raise RuntimeError("Edda event loop not initialized. Call init_edda_loop() first.")
    return _edda_loop


def run_in_edda_loop(coro):
    """Run a coroutine in the Edda event loop and return the result."""
    loop = get_edda_loop()
    future = asyncio.run_coroutine_threadsafe(coro, loop)
    return future.result()


def _run_edda_loop(loop: asyncio.AbstractEventLoop):
    """Run the Edda event loop in a background thread."""
    asyncio.set_event_loop(loop)
    loop.run_forever()


def init_edda_loop() -> asyncio.AbstractEventLoop:
    """Initialize and start the persistent Edda event loop.

    Returns:
        The event loop instance.
    """
    global _edda_loop, _edda_thread

    if _edda_loop is not None:
        return _edda_loop

    _edda_loop = asyncio.new_event_loop()
    _edda_thread = threading.Thread(target=_run_edda_loop, args=(_edda_loop,), daemon=True)
    _edda_thread.start()

    return _edda_loop


def shutdown_edda_loop() -> None:
    """Stop the Edda event loop."""
    global _edda_loop, _edda_thread

    if _edda_loop is not None:
        _edda_loop.call_soon_threadsafe(_edda_loop.stop)
        _edda_loop = None
        _edda_thread = None
