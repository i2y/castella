"""Command watcher for external control of Castella apps.

This module provides a file-based command interface that allows external
processes (including AI agents) to control Castella applications without
setting up full MCP stdio communication.

Example usage:
    ```python
    from castella import App, Column, Button, Text
    from castella.frame import Frame
    from castella.mcp import CastellaMCPServer, CommandWatcher

    app = App(Frame("Demo", 600, 400), MyComponent())
    mcp = CastellaMCPServer(app)

    # Start watching a command file
    watcher = CommandWatcher(mcp)
    watcher.start()

    app.run()
    ```

Command file format (one command per line):
    click:<element_id>
    type:<element_id>:<text>
    append:<element_id>:<text>
    toggle:<element_id>
    focus:<element_id>
    scroll:<element_id>:<direction>:<amount>
    select:<element_id>:<value>
    wait:<seconds>
"""

from __future__ import annotations

import threading
import time
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable

from .tools import (
    click_element,
    type_text,
    toggle_element,
    focus_element,
    scroll_element,
    select_value,
)

if TYPE_CHECKING:
    from .server import CastellaMCPServer


class CommandWatcher:
    """Watches a command file and executes MCP operations.

    This provides a simple way for external processes to control a
    Castella application by writing commands to a text file.
    """

    def __init__(
        self,
        mcp_server: "CastellaMCPServer",
        command_file: str | Path = ".castella_commands",
        poll_interval: float = 0.2,
        on_command: Callable[[str, dict], None] | None = None,
        on_error: Callable[[str, Exception], None] | None = None,
    ) -> None:
        """Initialize the command watcher.

        Args:
            mcp_server: The CastellaMCPServer instance
            command_file: Path to the command file to watch
            poll_interval: How often to check for new commands (seconds)
            on_command: Optional callback called before each command executes
            on_error: Optional callback called when a command fails
        """
        self._mcp = mcp_server
        self._command_file = Path(command_file)
        self._poll_interval = poll_interval
        self._on_command = on_command
        self._on_error = on_error

        self._thread: threading.Thread | None = None
        self._running = False
        self._last_mtime: float = 0

        # Create empty command file if it doesn't exist
        self._command_file.touch(exist_ok=True)

    @property
    def command_file(self) -> Path:
        """Get the command file path."""
        return self._command_file

    def start(self) -> None:
        """Start watching the command file in a background thread."""
        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(
            target=self._watch_loop,
            daemon=True,
            name="castella-command-watcher",
        )
        self._thread.start()

    def stop(self) -> None:
        """Stop watching the command file."""
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=1.0)
            self._thread = None

    def is_running(self) -> bool:
        """Check if the watcher is running."""
        return self._running

    def execute_command(self, command: str) -> dict[str, Any]:
        """Execute a single command string.

        Args:
            command: Command string in format "action:arg1:arg2:..."

        Returns:
            Result dictionary with success status and message
        """
        command = command.strip()
        if not command or command.startswith("#"):
            return {"success": True, "message": "skipped"}

        parts = command.split(":", 2)
        action = parts[0].lower()

        registry = self._mcp.registry
        app = self._mcp._app

        try:
            if self._on_command:
                self._on_command(command, {"action": action, "parts": parts})

            if action == "click" and len(parts) >= 2:
                element_id = parts[1]
                result = click_element(element_id, registry, app)
                return result.model_dump()

            elif action == "type" and len(parts) >= 3:
                element_id = parts[1]
                text = parts[2]
                result = type_text(element_id, text, True, registry, app)
                return result.model_dump()

            elif action == "append" and len(parts) >= 3:
                element_id = parts[1]
                text = parts[2]
                result = type_text(element_id, text, False, registry, app)
                return result.model_dump()

            elif action == "toggle" and len(parts) >= 2:
                element_id = parts[1]
                result = toggle_element(element_id, registry, app)
                return result.model_dump()

            elif action == "focus" and len(parts) >= 2:
                element_id = parts[1]
                result = focus_element(element_id, registry, app)
                return result.model_dump()

            elif action == "scroll" and len(parts) >= 3:
                element_id = parts[1]
                direction = parts[2]
                amount = int(parts[3]) if len(parts) >= 4 else 100
                result = scroll_element(element_id, direction, amount, registry, app)
                return result.model_dump()

            elif action == "select" and len(parts) >= 3:
                element_id = parts[1]
                value = parts[2]
                result = select_value(element_id, value, registry, app)
                return result.model_dump()

            elif action == "wait":
                seconds = float(parts[1]) if len(parts) >= 2 else 1.0
                time.sleep(seconds)
                return {"success": True, "message": f"waited {seconds}s"}

            elif action == "refresh":
                self._mcp.refresh_registry()
                return {"success": True, "message": "registry refreshed"}

            else:
                return {"success": False, "message": f"unknown command: {action}"}

        except Exception as e:
            if self._on_error:
                self._on_error(command, e)
            return {"success": False, "message": str(e)}

    def execute_commands(self, commands: list[str], delay: float = 0.1) -> list[dict]:
        """Execute multiple commands with optional delay between them.

        Args:
            commands: List of command strings
            delay: Delay between commands in seconds

        Returns:
            List of result dictionaries
        """
        results = []
        for cmd in commands:
            result = self.execute_command(cmd)
            results.append(result)
            if delay > 0:
                time.sleep(delay)
        return results

    def _watch_loop(self) -> None:
        """Main loop that watches for command file changes."""
        # Initial registry build
        time.sleep(0.5)
        self._mcp.refresh_registry()

        while self._running:
            try:
                if self._command_file.exists():
                    mtime = self._command_file.stat().st_mtime
                    if mtime > self._last_mtime:
                        self._last_mtime = mtime
                        self._process_command_file()

            except Exception as e:
                if self._on_error:
                    self._on_error("watch_loop", e)

            time.sleep(self._poll_interval)

    def _process_command_file(self) -> None:
        """Read and execute commands from the file."""
        try:
            content = self._command_file.read_text()
            commands = [line for line in content.splitlines() if line.strip()]

            if commands:
                # Clear the file
                self._command_file.write_text("")

                # Execute commands
                for cmd in commands:
                    self.execute_command(cmd)
                    time.sleep(0.15)  # Small delay between commands

        except Exception as e:
            if self._on_error:
                self._on_error("process_file", e)


class CommandQueue:
    """In-memory command queue for programmatic control.

    This provides a thread-safe way to queue commands from any thread
    and have them executed on the main UI thread.

    Example:
        ```python
        queue = CommandQueue(mcp)
        queue.start()

        # From any thread:
        queue.click("my-button")
        queue.type_text("my-input", "Hello!")
        queue.toggle("my-checkbox")
        ```
    """

    def __init__(
        self,
        mcp_server: "CastellaMCPServer",
        on_result: Callable[[str, dict], None] | None = None,
    ) -> None:
        """Initialize the command queue.

        Args:
            mcp_server: The CastellaMCPServer instance
            on_result: Optional callback called with each command result
        """
        self._mcp = mcp_server
        self._on_result = on_result
        self._queue: list[tuple[str, dict]] = []
        self._lock = threading.Lock()
        self._thread: threading.Thread | None = None
        self._running = False

    def start(self) -> None:
        """Start processing the command queue."""
        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(
            target=self._process_loop,
            daemon=True,
            name="castella-command-queue",
        )
        self._thread.start()

    def stop(self) -> None:
        """Stop processing the command queue."""
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=1.0)
            self._thread = None

    def _enqueue(self, command: str, **kwargs: Any) -> None:
        """Add a command to the queue."""
        with self._lock:
            self._queue.append((command, kwargs))

    def click(self, element_id: str) -> None:
        """Queue a click command."""
        self._enqueue("click", element_id=element_id)

    def type_text(self, element_id: str, text: str, replace: bool = True) -> None:
        """Queue a type command."""
        self._enqueue("type" if replace else "append", element_id=element_id, text=text)

    def toggle(self, element_id: str) -> None:
        """Queue a toggle command."""
        self._enqueue("toggle", element_id=element_id)

    def focus(self, element_id: str) -> None:
        """Queue a focus command."""
        self._enqueue("focus", element_id=element_id)

    def scroll(self, element_id: str, direction: str, amount: int = 100) -> None:
        """Queue a scroll command."""
        self._enqueue(
            "scroll", element_id=element_id, direction=direction, amount=amount
        )

    def select(self, element_id: str, value: str) -> None:
        """Queue a select command."""
        self._enqueue("select", element_id=element_id, value=value)

    def _process_loop(self) -> None:
        """Process commands from the queue."""
        time.sleep(0.5)
        self._mcp.refresh_registry()

        registry = self._mcp.registry
        app = self._mcp._app

        while self._running:
            commands_to_process = []
            with self._lock:
                if self._queue:
                    commands_to_process = self._queue.copy()
                    self._queue.clear()

            for cmd, kwargs in commands_to_process:
                try:
                    result = None
                    if cmd == "click":
                        result = click_element(kwargs["element_id"], registry, app)
                    elif cmd == "type":
                        result = type_text(
                            kwargs["element_id"], kwargs["text"], True, registry, app
                        )
                    elif cmd == "append":
                        result = type_text(
                            kwargs["element_id"], kwargs["text"], False, registry, app
                        )
                    elif cmd == "toggle":
                        result = toggle_element(kwargs["element_id"], registry, app)
                    elif cmd == "focus":
                        result = focus_element(kwargs["element_id"], registry, app)
                    elif cmd == "scroll":
                        result = scroll_element(
                            kwargs["element_id"],
                            kwargs["direction"],
                            kwargs.get("amount", 100),
                            registry,
                            app,
                        )
                    elif cmd == "select":
                        result = select_value(
                            kwargs["element_id"], kwargs["value"], registry, app
                        )

                    if self._on_result and result:
                        self._on_result(cmd, result.model_dump())

                except Exception as e:
                    if self._on_result:
                        self._on_result(cmd, {"success": False, "message": str(e)})

                time.sleep(0.1)

            time.sleep(0.05)
