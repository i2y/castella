"""Animation configuration models for charts."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class EasingFunction(str, Enum):
    """Animation easing functions."""

    LINEAR = "linear"
    EASE_IN = "ease_in"
    EASE_OUT = "ease_out"
    EASE_IN_OUT = "ease_in_out"
    EASE_IN_CUBIC = "ease_in_cubic"
    EASE_OUT_CUBIC = "ease_out_cubic"
    EASE_IN_OUT_CUBIC = "ease_in_out_cubic"
    BOUNCE = "bounce"


class AnimationConfig(BaseModel):
    """Animation settings for charts.

    Attributes:
        enabled: Whether animations are enabled.
        duration_ms: Duration of animations in milliseconds.
        easing: Easing function to use.
        delay_ms: Delay before animation starts.
        stagger_ms: Delay between animating each series/point.
    """

    model_config = ConfigDict(frozen=True)

    enabled: bool = True
    duration_ms: int = Field(default=500, ge=0)
    easing: EasingFunction = EasingFunction.EASE_OUT_CUBIC
    delay_ms: int = Field(default=0, ge=0)
    stagger_ms: int = Field(default=50, ge=0)

    def disabled(self) -> AnimationConfig:
        """Create a copy with animations disabled."""
        return self.model_copy(update={"enabled": False})

    def with_duration(self, duration_ms: int) -> AnimationConfig:
        """Create a copy with a different duration."""
        return self.model_copy(update={"duration_ms": duration_ms})

    def with_easing(self, easing: EasingFunction) -> AnimationConfig:
        """Create a copy with a different easing function."""
        return self.model_copy(update={"easing": easing})
