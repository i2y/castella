"""Project discovery and management."""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

from castella.wrks.utils.path_encoder import decode_project_path


@dataclass
class Project:
    """Represents a Claude Code project."""

    encoded_name: str  # The directory name in ~/.claude/projects/
    path: Path  # Decoded actual path
    session_count: int  # Number of sessions
    last_modified: Optional[datetime]  # Most recent session modification
    is_favorite: bool = False  # User-marked favorite

    @property
    def display_name(self) -> str:
        """Get a display-friendly name from the path."""
        return self.path.name

    @property
    def display_path(self) -> str:
        """Get the full path as string for display."""
        return str(self.path)


class ProjectManager:
    """Manages project discovery from ~/.claude/projects/."""

    def __init__(self, base_path: Optional[Path] = None):
        """Initialize with optional custom base path.

        Args:
            base_path: Override for ~/.claude/projects/ (mainly for testing)
        """
        if base_path is None:
            self._base_path = Path.home() / ".claude" / "projects"
        else:
            self._base_path = base_path

    @property
    def base_path(self) -> Path:
        """Get the base path for projects."""
        return self._base_path

    def list_projects(self, favorites: Optional[set[str]] = None) -> list[Project]:
        """List all projects with their metadata.

        Args:
            favorites: Set of encoded project names that are favorites

        Returns:
            List of Project objects sorted by last modified (newest first)
        """
        if favorites is None:
            favorites = set()

        projects: list[Project] = []

        if not self._base_path.exists():
            return projects

        for project_dir in self._base_path.iterdir():
            if not project_dir.is_dir():
                continue

            encoded_name = project_dir.name
            decoded_path = decode_project_path(encoded_name)

            # Count sessions and find most recent
            session_files = list(project_dir.glob("*.jsonl"))
            session_count = len(session_files)

            last_modified: Optional[datetime] = None
            if session_files:
                most_recent = max(session_files, key=lambda f: f.stat().st_mtime)
                last_modified = datetime.fromtimestamp(most_recent.stat().st_mtime)

            projects.append(
                Project(
                    encoded_name=encoded_name,
                    path=decoded_path,
                    session_count=session_count,
                    last_modified=last_modified,
                    is_favorite=encoded_name in favorites,
                )
            )

        # Sort: favorites first, then by last_modified (newest first)
        projects.sort(
            key=lambda p: (
                not p.is_favorite,  # Favorites first (False < True)
                -(p.last_modified.timestamp() if p.last_modified else 0),
            )
        )

        return projects

    def get_project_path(self, encoded_name: str) -> Path:
        """Get the full path to a project directory."""
        return self._base_path / encoded_name

    def get_sessions_path(self, project: Project) -> Path:
        """Get the path to sessions for a project."""
        return self._base_path / project.encoded_name
