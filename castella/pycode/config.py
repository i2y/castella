"""Configuration management for pycode.

Handles model selection, API keys, and other settings.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class ModelProvider(Enum):
    """Supported model providers."""

    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    GOOGLE = "google"
    OLLAMA = "ollama"


@dataclass
class ModelConfig:
    """Configuration for a specific model."""

    provider: ModelProvider
    model_id: str
    display_name: str

    def to_pydantic_ai_model(self) -> str:
        """Convert to pydantic-ai model string."""
        if self.provider == ModelProvider.ANTHROPIC:
            return f"anthropic:{self.model_id}"
        elif self.provider == ModelProvider.OPENAI:
            return f"openai:{self.model_id}"
        elif self.provider == ModelProvider.GOOGLE:
            return f"google-gla:{self.model_id}"
        elif self.provider == ModelProvider.OLLAMA:
            return f"ollama:{self.model_id}"
        return self.model_id


# Default available models
DEFAULT_MODELS: list[ModelConfig] = [
    ModelConfig(ModelProvider.ANTHROPIC, "claude-sonnet-4-20250514", "Claude Sonnet 4"),
    ModelConfig(ModelProvider.ANTHROPIC, "claude-3-5-haiku-latest", "Claude 3.5 Haiku"),
    ModelConfig(ModelProvider.OPENAI, "gpt-4o", "GPT-4o"),
    ModelConfig(ModelProvider.OPENAI, "gpt-4o-mini", "GPT-4o Mini"),
    ModelConfig(ModelProvider.GOOGLE, "gemini-2.0-flash", "Gemini 2.0 Flash"),
    ModelConfig(ModelProvider.OLLAMA, "llama3.2", "Llama 3.2 (Local)"),
]


@dataclass
class Config:
    """Application configuration."""

    # Model settings
    model: ModelConfig = field(
        default_factory=lambda: DEFAULT_MODELS[0]  # Claude Sonnet 4
    )

    # Available models
    available_models: list[ModelConfig] = field(
        default_factory=lambda: list(DEFAULT_MODELS)
    )

    # Working directory
    cwd: Path = field(default_factory=Path.cwd)

    # UI settings
    window_width: int = 1200
    window_height: int = 800
    font_size: int = 14

    # Feature flags
    auto_approve_reads: bool = True  # Auto-approve read operations
    auto_approve_writes: bool = False  # Require approval for writes
    auto_approve_bash: bool = False  # Require approval for bash commands

    @classmethod
    def from_env(cls) -> "Config":
        """Create config from environment variables."""
        config = cls()

        # Override model from environment
        model_env = os.environ.get("PYCODE_MODEL")
        if model_env:
            for model in config.available_models:
                if model.model_id == model_env or model.display_name == model_env:
                    config.model = model
                    break

        # Override cwd from environment
        cwd_env = os.environ.get("PYCODE_CWD")
        if cwd_env:
            config.cwd = Path(cwd_env)

        # Override font size
        font_size_env = os.environ.get("CASTELLA_FONT_SIZE")
        if font_size_env:
            try:
                config.font_size = int(font_size_env)
            except ValueError:
                pass

        return config

    def get_api_key(self) -> str | None:
        """Get the API key for the current model's provider."""
        if self.model.provider == ModelProvider.ANTHROPIC:
            return os.environ.get("ANTHROPIC_API_KEY")
        elif self.model.provider == ModelProvider.OPENAI:
            return os.environ.get("OPENAI_API_KEY")
        elif self.model.provider == ModelProvider.GOOGLE:
            return os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        elif self.model.provider == ModelProvider.OLLAMA:
            return None  # Ollama doesn't need an API key
        return None

    def has_api_key(self) -> bool:
        """Check if the required API key is available."""
        if self.model.provider == ModelProvider.OLLAMA:
            return True
        return self.get_api_key() is not None

    def set_model_by_name(self, name: str) -> bool:
        """Set model by display name or model ID.

        Returns True if model was found and set.
        """
        for model in self.available_models:
            if model.display_name == name or model.model_id == name:
                self.model = model
                return True
        return False
