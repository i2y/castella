"""Path encoding/decoding utilities for Claude Code project paths."""

from pathlib import Path


def decode_project_path(encoded: str) -> Path:
    """Decode Claude Code project path format.

    Examples:
        -Users-i2y-castella -> /Users/i2y/castella
        -home-user-project -> /home/user/project
    """
    if not encoded:
        return Path(".")

    # Handle leading dash which represents root /
    if encoded.startswith("-"):
        decoded = encoded.replace("-", "/", 1)  # First dash becomes /
        decoded = decoded.replace("-", "/")  # Remaining dashes become /
    else:
        decoded = encoded.replace("-", "/")

    return Path(decoded)


def encode_project_path(path: Path) -> str:
    """Encode path to Claude Code project path format.

    Examples:
        /Users/i2y/castella -> -Users-i2y-castella
        /home/user/project -> -home-user-project
    """
    resolved = str(path.resolve())
    return resolved.replace("/", "-")
