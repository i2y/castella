"""JSONL stream parser for A2UI messages.

This module provides utilities for parsing JSONL (newline-delimited JSON)
streams of A2UI server messages, enabling progressive/streaming UI rendering.

Example:
    # Parse from file
    with open("ui.jsonl") as f:
        for message in parse_sync_stream(f):
            renderer.handle_message(message)

    # Parse from async stream
    async for message in parse_async_stream(response.aiter_lines()):
        renderer.handle_message(message)
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator, Iterator

from castella.a2ui.types import ServerMessage


class JSONLParser:
    """JSONL (newline-delimited JSON) parser.

    Handles partial chunks and buffers incomplete lines until a full
    JSON line is received.

    Example:
        parser = JSONLParser()

        # Feed chunks as they arrive
        for chunk in network_stream:
            for message in parser.feed(chunk):
                handle_message(message)
    """

    def __init__(self):
        self._buffer = ""

    def feed(self, chunk: str) -> Iterator[ServerMessage]:
        """Feed a chunk of data and yield complete messages.

        Args:
            chunk: A string chunk (may contain partial lines)

        Yields:
            Complete ServerMessage objects as they become available
        """
        self._buffer += chunk

        while "\n" in self._buffer:
            line, self._buffer = self._buffer.split("\n", 1)
            line = line.strip()

            if not line:
                continue

            try:
                data = json.loads(line)
                yield ServerMessage.model_validate(data)
            except json.JSONDecodeError:
                # Skip malformed JSON lines
                continue
            except Exception:
                # Skip messages that don't validate
                continue

    def flush(self) -> ServerMessage | None:
        """Flush any remaining buffered data.

        Returns:
            A ServerMessage if buffer contained a complete message, None otherwise
        """
        if not self._buffer.strip():
            return None

        try:
            data = json.loads(self._buffer.strip())
            self._buffer = ""
            return ServerMessage.model_validate(data)
        except (json.JSONDecodeError, Exception):
            self._buffer = ""
            return None


def parse_sync_stream(stream: Iterator[str]) -> Iterator[ServerMessage]:
    """Parse a synchronous stream of JSONL data.

    Args:
        stream: An iterator yielding strings (e.g., file lines or chunks)

    Yields:
        ServerMessage objects

    Example:
        with open("ui.jsonl") as f:
            for message in parse_sync_stream(f):
                renderer.handle_message(message)
    """
    parser = JSONLParser()

    for chunk in stream:
        yield from parser.feed(chunk)

    # Flush any remaining data
    final = parser.flush()
    if final:
        yield final


async def parse_async_stream(
    stream: AsyncIterator[str],
) -> AsyncIterator[ServerMessage]:
    """Parse an asynchronous stream of JSONL data.

    Args:
        stream: An async iterator yielding strings (e.g., SSE events)

    Yields:
        ServerMessage objects

    Example:
        async for message in parse_async_stream(response.aiter_lines()):
            await renderer.handle_message_async(message)
    """
    parser = JSONLParser()

    async for chunk in stream:
        for message in parser.feed(chunk):
            yield message

    # Flush any remaining data
    final = parser.flush()
    if final:
        yield final


def parse_jsonl_string(jsonl_content: str) -> Iterator[ServerMessage]:
    """Parse a complete JSONL string.

    Args:
        jsonl_content: A string containing multiple JSON lines

    Yields:
        ServerMessage objects

    Example:
        messages = list(parse_jsonl_string(file_content))
    """
    parser = JSONLParser()
    yield from parser.feed(jsonl_content)

    final = parser.flush()
    if final:
        yield final
