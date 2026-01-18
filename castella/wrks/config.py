"""Configuration management for wrks."""

import os
from dataclasses import dataclass
from typing import Literal, Optional

# Load .env file if python-dotenv is available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


@dataclass
class WrksConfig:
    """Configuration for wrks application."""

    # Permission mode for tool execution
    # - "default": Ask for approval via callback
    # - "acceptEdits": Auto-accept file edits
    # - "bypassPermissions": Auto-accept all tools (dangerous)
    permission_mode: Literal["default", "acceptEdits", "bypassPermissions"] = "default"

    # Model settings
    # - "haiku": Claude Haiku 4.5 (fast, cheap - $1/$5 per MTok)
    # - "sonnet": Claude Sonnet 4.5 (balanced - $3/$15 per MTok)
    # - "opus": Claude Opus 4.5 (most capable - $5/$25 per MTok)
    # Default: opus (production), can override with WRKS_MODEL=haiku for dev
    model: Literal["haiku", "sonnet", "opus"] = "opus"

    # Extended thinking mode (only works with Opus)
    # When enabled, Claude will show its thinking process
    extended_thinking: bool = True

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
            WRKS_MODEL: haiku | sonnet | opus (default: haiku)
            WRKS_EXTENDED_THINKING: true | false (default: false, Opus only)
            WRKS_PERMISSION_MODE: default | acceptEdits | bypassPermissions
            CASTELLA_DARK_MODE: true | false
            CASTELLA_FONT_SIZE: font size (int)
            WRKS_WINDOW_WIDTH: window width (int)
            WRKS_WINDOW_HEIGHT: window height (int)
        """
        config = cls()

        # Model
        model = os.environ.get("WRKS_MODEL", "haiku").lower()
        if model in ("haiku", "sonnet", "opus"):
            config.model = model  # type: ignore

        # Extended thinking
        extended_thinking = os.environ.get("WRKS_EXTENDED_THINKING", "").lower()
        if extended_thinking in ("true", "1", "yes"):
            config.extended_thinking = True
        elif extended_thinking in ("false", "0", "no"):
            config.extended_thinking = False

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
