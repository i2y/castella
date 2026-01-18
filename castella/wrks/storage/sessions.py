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


def simplify_context_in_message(content: str) -> str:
    """Simplify context file content in a user message.

    Converts full context content like:
        **Context files:**
        `file.py`:
        ```
        <full content>
        ```
        **User request:**
        actual message

    To a simplified form:
        [Context: `file.py`]

        actual message

    Args:
        content: The message content to simplify

    Returns:
        Simplified message content
    """
    import re

    # Check if the message starts with context files pattern
    if not content.startswith("**Context files:**"):
        return content

    # Find the "**User request:**" marker
    user_request_marker = "**User request:**"
    marker_pos = content.find(user_request_marker)

    if marker_pos == -1:
        return content

    # Extract the context section
    context_section = content[:marker_pos]

    # Extract file names from the context section
    # Pattern matches: `filename`:
    file_pattern = re.compile(r'`([^`]+)`:\s*\n```')
    file_names = file_pattern.findall(context_section)

    if not file_names:
        return content

    # Extract the actual user request (after the marker)
    user_request = content[marker_pos + len(user_request_marker):].strip()

    # Build simplified message
    file_list = ", ".join(f"`{name}`" for name in file_names)
    return f"[Context: {file_list}]\n\n{user_request}"


@dataclass
class ParsedMessage:
    """A parsed message from session history."""

    role: str  # "user" or "assistant"
    content: str
    timestamp: Optional[str] = None
    model_name: Optional[str] = None  # Model used (for assistant messages)


def load_session_messages(session_path: Path, limit: int = 100) -> list[ParsedMessage]:
    """Load message history from a session JSONL file.

    Args:
        session_path: Path to the session JSONL file
        limit: Maximum number of most recent messages to load

    Returns:
        List of ParsedMessage objects in chronological order (most recent N)
    """
    messages: list[ParsedMessage] = []

    if not session_path.exists():
        return messages

    try:
        with open(session_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                try:
                    data = json.loads(line)

                    # Skip non-message records
                    msg_type = data.get("type")
                    if msg_type not in ("user", "assistant"):
                        continue

                    msg = data.get("message", {})
                    if not isinstance(msg, dict):
                        continue

                    role = msg.get("role")
                    if role not in ("user", "assistant"):
                        continue

                    content = msg.get("content", "")
                    timestamp = data.get("timestamp")

                    # Extract model name for assistant messages
                    model_name: Optional[str] = None
                    if role == "assistant":
                        model_name = msg.get("model")

                    # Handle content as string or list of blocks
                    if isinstance(content, str) and content:
                        # Simplify context files in user messages
                        if role == "user":
                            content = simplify_context_in_message(content)
                        messages.append(ParsedMessage(
                            role=role,
                            content=content,
                            timestamp=timestamp,
                            model_name=model_name,
                        ))
                    elif isinstance(content, list):
                        # Extract text from content blocks
                        text_parts = []
                        tool_results = []
                        for block in content:
                            if isinstance(block, dict):
                                if block.get("type") == "text":
                                    text_parts.append(block.get("text", ""))
                                elif block.get("type") == "tool_use":
                                    tool_name = block.get("name", "unknown")
                                    text_parts.append(f"[Tool: {tool_name}]")
                                elif block.get("type") == "tool_result":
                                    # Collect tool results
                                    result_content = block.get("content", "")
                                    if isinstance(result_content, str) and result_content:
                                        tool_results.append(result_content)
                                    elif isinstance(result_content, list):
                                        for sub_block in result_content:
                                            if isinstance(sub_block, dict) and sub_block.get("type") == "text":
                                                tool_results.append(sub_block.get("text", ""))

                        # If this is a user message with only tool_results, append to previous assistant message
                        if role == "user" and tool_results and not text_parts:
                            if messages and messages[-1].role == "assistant":
                                # Append tool results to previous assistant message
                                result_text = "\n".join(tool_results)
                                if len(result_text) > 5000:
                                    result_text = result_text[:5000] + "\n... (truncated)"
                                # Use ```` (4 backticks) to avoid issues with nested code blocks
                                messages[-1] = ParsedMessage(
                                    role=messages[-1].role,
                                    content=messages[-1].content + f"\n\n**Result:**\n````\n{result_text}\n````",
                                    timestamp=messages[-1].timestamp,
                                    model_name=messages[-1].model_name,
                                )
                            # Skip creating a new "user" message for tool results
                            continue

                        if text_parts:
                            text_content = "\n".join(text_parts)
                            # Simplify context files in user messages
                            if role == "user":
                                text_content = simplify_context_in_message(text_content)
                            messages.append(ParsedMessage(
                                role=role,
                                content=text_content,
                                timestamp=timestamp,
                                model_name=model_name,
                            ))

                except json.JSONDecodeError:
                    continue

    except Exception:
        pass

    # Return only the most recent N messages
    if limit > 0 and len(messages) > limit:
        return messages[-limit:]
    return messages


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
