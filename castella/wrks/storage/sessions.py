"""Session JSONL parsing and metadata extraction."""

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass
class SessionMetadata:
    """Metadata extracted from a session JSONL file."""

    session_id: str  # UUID from filename
    file_path: Path  # Full path to the JSONL file
    summary: str  # First user message or "New session"
    model: Optional[str]  # Model used (if detected)
    created_at: datetime  # File creation time
    modified_at: datetime  # File modification time
    message_count: int  # Approximate number of messages

    @property
    def display_date(self) -> str:
        """Get a human-readable date string."""
        now = datetime.now()
        diff = now - self.modified_at

        if diff.days == 0:
            hours = diff.seconds // 3600
            if hours == 0:
                minutes = diff.seconds // 60
                if minutes == 0:
                    return "just now"
                return f"{minutes}m ago"
            return f"{hours}h ago"
        elif diff.days == 1:
            return "yesterday"
        elif diff.days < 7:
            return f"{diff.days}d ago"
        else:
            return self.modified_at.strftime("%Y-%m-%d")


def parse_session_file(path: Path) -> SessionMetadata:
    """Extract metadata from a session JSONL file.

    Args:
        path: Path to the JSONL file

    Returns:
        SessionMetadata with extracted information
    """
    session_id = path.stem  # Filename without extension is the session ID

    stat = path.stat()
    created_at = datetime.fromtimestamp(stat.st_ctime)
    modified_at = datetime.fromtimestamp(stat.st_mtime)

    summary = "New session"
    model: Optional[str] = None
    message_count = 0

    try:
        with open(path, "r", encoding="utf-8") as f:
            for i, line in enumerate(f):
                if i > 100:  # Limit how much we read
                    break

                line = line.strip()
                if not line:
                    continue

                try:
                    data = json.loads(line)
                    message_count += 1

                    # Extract model from assistant messages or result
                    if "model" in data and model is None:
                        model = data["model"]
                    # Model might be in message.model for assistant messages
                    if model is None:
                        msg = data.get("message", {})
                        if isinstance(msg, dict) and "model" in msg:
                            model = msg["model"]

                    # Check for summary record (Claude Code stores this at the start)
                    if data.get("type") == "summary" and "summary" in data:
                        summary = _truncate_summary(data["summary"])
                        continue

                    # Try to get summary from first user message (fallback)
                    if summary == "New session":
                        # Check for user message in Claude Code format
                        if data.get("type") == "user":
                            msg = data.get("message", {})
                            if isinstance(msg, dict):
                                content = msg.get("content", "")
                                if isinstance(content, str) and content:
                                    summary = _truncate_summary(content)
                        # Check for user message in various formats
                        elif data.get("type") == "human":
                            content = data.get("message", {})
                            if isinstance(content, dict):
                                text_content = content.get("content", "")
                                if isinstance(text_content, str) and text_content:
                                    summary = _truncate_summary(text_content)
                            elif isinstance(content, str):
                                summary = _truncate_summary(content)
                        elif data.get("role") == "user":
                            content = data.get("content", "")
                            if isinstance(content, str) and content:
                                summary = _truncate_summary(content)
                            elif isinstance(content, list):
                                # Content might be a list of content blocks
                                for block in content:
                                    if isinstance(block, dict) and block.get("type") == "text":
                                        summary = _truncate_summary(block.get("text", ""))
                                        break

                except json.JSONDecodeError:
                    continue

    except Exception:
        # If we can't read the file, return minimal metadata
        pass

    return SessionMetadata(
        session_id=session_id,
        file_path=path,
        summary=summary,
        model=model,
        created_at=created_at,
        modified_at=modified_at,
        message_count=message_count,
    )


def _truncate_summary(text: str, max_length: int = 80) -> str:
    """Truncate text to a reasonable summary length."""
    # Remove newlines and extra whitespace
    text = " ".join(text.split())

    if len(text) <= max_length:
        return text

    # Find a good break point
    truncated = text[:max_length]
    last_space = truncated.rfind(" ")
    if last_space > max_length // 2:
        truncated = truncated[:last_space]

    return truncated + "..."


def list_sessions(project_path: Path) -> list[SessionMetadata]:
    """List all sessions in a project directory.

    Args:
        project_path: Path to the project directory in ~/.claude/projects/

    Returns:
        List of SessionMetadata sorted by modification time (newest first)
    """
    sessions: list[SessionMetadata] = []

    if not project_path.exists():
        return sessions

    for session_file in project_path.glob("*.jsonl"):
        sessions.append(parse_session_file(session_file))

    # Sort by modification time (newest first)
    sessions.sort(key=lambda s: s.modified_at, reverse=True)

    return sessions
