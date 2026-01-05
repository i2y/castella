"""Colormap implementations for value-to-color mapping.

Provides scientific colormaps (Viridis, Plasma, Inferno, Magma) for
heatmaps and other data visualizations. All colormaps are perceptually
uniform and colorblind-friendly.

Example:
    >>> from castella.chart.colormap import viridis, get_colormap, ColormapType
    >>> cmap = viridis()
    >>> cmap(0.5)  # Get color at midpoint
    '#21918c'
    >>> cmap = get_colormap(ColormapType.PLASMA)
    >>> cmap.get_colors(5)  # Get 5 evenly spaced colors
    ['#0d0887', '#7e03a8', '#cc4778', '#f89540', '#f0f921']
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Sequence

from castella.utils.color import rgb_to_hex


class ColormapType(Enum):
    """Available colormap types."""

    VIRIDIS = "viridis"
    PLASMA = "plasma"
    INFERNO = "inferno"
    MAGMA = "magma"


@dataclass(slots=True)
class ColorStop:
    """A color stop in a gradient colormap.

    Attributes:
        position: Position in the gradient (0.0 to 1.0).
        r: Red component (0-255).
        g: Green component (0-255).
        b: Blue component (0-255).
    """

    position: float
    r: int
    g: int
    b: int


class Colormap(ABC):
    """Abstract base class for colormaps."""

    @abstractmethod
    def __call__(self, value: float) -> str:
        """Map a normalized value to a hex color.

        Args:
            value: Normalized value between 0.0 and 1.0.

        Returns:
            Hex color string (e.g., "#ff00ff").
        """
        ...

    @abstractmethod
    def get_colors(self, n: int) -> list[str]:
        """Get n evenly spaced colors from the colormap.

        Args:
            n: Number of colors to return.

        Returns:
            List of hex color strings.
        """
        ...

    def reversed(self) -> Colormap:
        """Return a reversed version of this colormap."""
        return ReversedColormap(self)


class GradientColormap(Colormap):
    """A colormap defined by gradient color stops.

    Linearly interpolates between color stops to produce smooth
    color gradients.

    Example:
        >>> stops = [
        ...     ColorStop(0.0, 0, 0, 0),
        ...     ColorStop(1.0, 255, 255, 255),
        ... ]
        >>> cmap = GradientColormap(stops)
        >>> cmap(0.5)
        '#7f7f7f'
    """

    def __init__(self, stops: Sequence[ColorStop]):
        """Initialize with color stops.

        Args:
            stops: Sequence of ColorStop, will be sorted by position.
        """
        self._stops = sorted(stops, key=lambda s: s.position)

    def __call__(self, value: float) -> str:
        """Map normalized value to color via linear interpolation."""
        # Clamp value to [0, 1]
        value = max(0.0, min(1.0, value))

        # Find bounding stops
        lower = self._stops[0]
        upper = self._stops[-1]

        for i, stop in enumerate(self._stops):
            if stop.position >= value:
                upper = stop
                if i > 0:
                    lower = self._stops[i - 1]
                break
            lower = stop

        # Interpolate between stops
        if upper.position == lower.position:
            t = 0.0
        else:
            t = (value - lower.position) / (upper.position - lower.position)

        r = int(lower.r + t * (upper.r - lower.r))
        g = int(lower.g + t * (upper.g - lower.g))
        b = int(lower.b + t * (upper.b - lower.b))

        return rgb_to_hex(r, g, b)

    def get_colors(self, n: int) -> list[str]:
        """Get n evenly spaced colors."""
        if n <= 0:
            return []
        if n == 1:
            return [self(0.5)]
        return [self(i / (n - 1)) for i in range(n)]


class ReversedColormap(Colormap):
    """A reversed version of another colormap."""

    def __init__(self, base: Colormap):
        """Initialize with base colormap to reverse.

        Args:
            base: The colormap to reverse.
        """
        self._base = base

    def __call__(self, value: float) -> str:
        """Map value using reversed colormap."""
        return self._base(1.0 - value)

    def get_colors(self, n: int) -> list[str]:
        """Get n evenly spaced colors (reversed order)."""
        return list(reversed(self._base.get_colors(n)))


# =============================================================================
# Pre-defined Colormaps
# Color stops sampled from matplotlib's scientific colormaps
# =============================================================================


def viridis() -> Colormap:
    """Viridis colormap - perceptually uniform, colorblind-friendly.

    A blue-green-yellow colormap that is:
    - Perceptually uniform (equal steps in data = equal perceptual changes)
    - Readable when printed in black and white
    - Accessible to viewers with common color vision deficiencies

    Returns:
        Colormap instance.
    """
    stops = [
        ColorStop(0.0, 68, 1, 84),
        ColorStop(0.125, 72, 40, 120),
        ColorStop(0.25, 62, 74, 137),
        ColorStop(0.375, 49, 104, 142),
        ColorStop(0.5, 38, 130, 142),
        ColorStop(0.625, 31, 158, 137),
        ColorStop(0.75, 53, 183, 121),
        ColorStop(0.875, 109, 205, 89),
        ColorStop(1.0, 253, 231, 37),
    ]
    return GradientColormap(stops)


def plasma() -> Colormap:
    """Plasma colormap - perceptually uniform, vibrant purple-orange-yellow.

    A vibrant colormap ranging from dark purple through pink and orange
    to bright yellow. Excellent for scientific visualization.

    Returns:
        Colormap instance.
    """
    stops = [
        ColorStop(0.0, 13, 8, 135),
        ColorStop(0.125, 75, 3, 161),
        ColorStop(0.25, 125, 3, 168),
        ColorStop(0.375, 168, 34, 150),
        ColorStop(0.5, 203, 70, 121),
        ColorStop(0.625, 229, 107, 93),
        ColorStop(0.75, 248, 148, 65),
        ColorStop(0.875, 253, 195, 40),
        ColorStop(1.0, 240, 249, 33),
    ]
    return GradientColormap(stops)


def inferno() -> Colormap:
    """Inferno colormap - perceptually uniform, high contrast black-red-yellow.

    A dramatic colormap from black through red and orange to bright yellow.
    Provides excellent contrast for data visualization.

    Returns:
        Colormap instance.
    """
    stops = [
        ColorStop(0.0, 0, 0, 4),
        ColorStop(0.125, 40, 11, 84),
        ColorStop(0.25, 89, 15, 109),
        ColorStop(0.375, 137, 34, 106),
        ColorStop(0.5, 181, 54, 81),
        ColorStop(0.625, 219, 92, 49),
        ColorStop(0.75, 246, 139, 30),
        ColorStop(0.875, 252, 196, 59),
        ColorStop(1.0, 252, 255, 164),
    ]
    return GradientColormap(stops)


def magma() -> Colormap:
    """Magma colormap - perceptually uniform, warm black-purple-pink-white.

    A warm colormap from black through purple and pink to near-white.
    Similar to inferno but with warmer tones.

    Returns:
        Colormap instance.
    """
    stops = [
        ColorStop(0.0, 0, 0, 4),
        ColorStop(0.125, 28, 16, 68),
        ColorStop(0.25, 79, 18, 123),
        ColorStop(0.375, 129, 37, 129),
        ColorStop(0.5, 181, 54, 122),
        ColorStop(0.625, 229, 80, 100),
        ColorStop(0.75, 251, 135, 97),
        ColorStop(0.875, 254, 194, 135),
        ColorStop(1.0, 252, 253, 191),
    ]
    return GradientColormap(stops)


# =============================================================================
# Colormap Registry
# =============================================================================

_COLORMAP_REGISTRY: dict[str, type[Colormap] | callable] = {
    "viridis": viridis,
    "plasma": plasma,
    "inferno": inferno,
    "magma": magma,
}


def get_colormap(name: ColormapType | str) -> Colormap:
    """Get a colormap by name.

    Args:
        name: Colormap name (string or ColormapType enum).

    Returns:
        The requested Colormap instance.

    Raises:
        ValueError: If colormap name is unknown.

    Example:
        >>> cmap = get_colormap("viridis")
        >>> cmap = get_colormap(ColormapType.PLASMA)
    """
    if isinstance(name, ColormapType):
        name = name.value

    if name not in _COLORMAP_REGISTRY:
        available = ", ".join(_COLORMAP_REGISTRY.keys())
        raise ValueError(f"Unknown colormap: {name}. Available: {available}")

    return _COLORMAP_REGISTRY[name]()


def register_colormap(name: str, colormap_factory: callable) -> None:
    """Register a custom colormap.

    Args:
        name: Name for the colormap.
        colormap_factory: Callable that returns a Colormap instance.

    Example:
        >>> def my_colormap():
        ...     return GradientColormap([...])
        >>> register_colormap("my_colormap", my_colormap)
    """
    _COLORMAP_REGISTRY[name] = colormap_factory
