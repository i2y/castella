"""Configuration management for wrks."""

import os
from dataclasses import dataclass
from typing import Literal, Optional


@dataclass
class WrksConfig:
    """Configuration for wrks application."""

    # Permission mode for tool execution
    # - "default": Ask for approval via callback
    # - "acceptEdits": Auto-accept file edits
    # - "bypassPermissions": Auto-accept all tools (dangerous)
    permission_mode: Literal["default", "acceptEdits", "bypassPermissions"] = "default"

    # UI settings
    dark_mode: Optional[bool] = None  # None = use system detection
    font_size: int = 14

    # Window settings
    window_width: int = 1200
    window_height: int = 800
    window_title: str = "wrks"

    @classmethod
    def from_env(cls) -> "WrksConfig":
        """Load configuration from environment variables.

        Environment variables:
            WRKS_PERMISSION_MODE: default | acceptEdits | bypassPermissions
            CASTELLA_DARK_MODE: true | false
            CASTELLA_FONT_SIZE: font size (int)
            WRKS_WINDOW_WIDTH: window width (int)
            WRKS_WINDOW_HEIGHT: window height (int)
        """
        config = cls()

        # Permission mode
        permission_mode = os.environ.get("WRKS_PERMISSION_MODE", "default").lower()
        if permission_mode in ("default", "acceptedits", "bypasspermissions"):
            # Normalize casing
            if permission_mode == "acceptedits":
                permission_mode = "acceptEdits"
            elif permission_mode == "bypasspermissions":
                permission_mode = "bypassPermissions"
            config.permission_mode = permission_mode  # type: ignore

        # Dark mode
        dark_mode = os.environ.get("CASTELLA_DARK_MODE", "").lower()
        if dark_mode == "true":
            config.dark_mode = True
        elif dark_mode == "false":
            config.dark_mode = False

        # Font size
        font_size = os.environ.get("CASTELLA_FONT_SIZE", "")
        if font_size.isdigit():
            config.font_size = int(font_size)

        # Window size
        width = os.environ.get("WRKS_WINDOW_WIDTH", "")
        if width.isdigit():
            config.window_width = int(width)

        height = os.environ.get("WRKS_WINDOW_HEIGHT", "")
        if height.isdigit():
            config.window_height = int(height)

        return config


# Global config instance
_config: Optional[WrksConfig] = None


def get_config() -> WrksConfig:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        _config = WrksConfig.from_env()
    return _config


def set_config(config: WrksConfig) -> None:
    """Set the global configuration instance."""
    global _config
    _config = config
