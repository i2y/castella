"""Linear scale for numeric data transformation."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence


@dataclass
class LinearScale:
    """Maps numeric data values to pixel coordinates.

    A linear scale creates a linear mapping from a data domain (min, max)
    to a pixel range (min, max).

    Attributes:
        domain_min: Minimum value in data domain.
        domain_max: Maximum value in data domain.
        range_min: Minimum value in pixel range.
        range_max: Maximum value in pixel range.
    """

    domain_min: float
    domain_max: float
    range_min: float
    range_max: float

    def __call__(self, value: float) -> float:
        """Map a domain value to a range (pixel) value.

        Args:
            value: A value in the data domain.

        Returns:
            The corresponding value in the pixel range.
        """
        domain_span = self.domain_max - self.domain_min
        if domain_span == 0:
            return self.range_min

        normalized = (value - self.domain_min) / domain_span
        return self.range_min + normalized * (self.range_max - self.range_min)

    def invert(self, pixel: float) -> float:
        """Map a pixel value back to a domain value.

        Args:
            pixel: A value in the pixel range.

        Returns:
            The corresponding value in the data domain.
        """
        range_span = self.range_max - self.range_min
        if range_span == 0:
            return self.domain_min

        normalized = (pixel - self.range_min) / range_span
        return self.domain_min + normalized * (self.domain_max - self.domain_min)

    def ticks(self, count: int = 5) -> list[float]:
        """Generate nice tick values for this scale.

        Args:
            count: Approximate number of ticks to generate.

        Returns:
            List of tick values.
        """
        if count < 2:
            count = 2

        domain_span = self.domain_max - self.domain_min
        if domain_span == 0:
            return [self.domain_min]

        # Calculate nice step size
        step = domain_span / (count - 1)
        magnitude = 10 ** math.floor(math.log10(step))
        normalized_step = step / magnitude

        if normalized_step <= 1:
            nice_step = 1
        elif normalized_step <= 2:
            nice_step = 2
        elif normalized_step <= 5:
            nice_step = 5
        else:
            nice_step = 10

        step = nice_step * magnitude

        # Generate ticks
        start = math.ceil(self.domain_min / step) * step
        ticks: list[float] = []
        current = start
        while (
            current <= self.domain_max + step * 0.001
        ):  # Small epsilon for float comparison
            ticks.append(round(current, 10))  # Round to avoid float precision issues
            current += step

        return ticks

    @classmethod
    def from_data(
        cls,
        data: Sequence[float],
        range_min: float,
        range_max: float,
        nice: bool = True,
        include_zero: bool = False,
    ) -> LinearScale:
        """Create a scale from data values.

        Args:
            data: Sequence of data values.
            range_min: Minimum pixel value.
            range_max: Maximum pixel value.
            nice: Whether to round bounds to nice numbers.
            include_zero: Whether to include zero in the domain.

        Returns:
            A new LinearScale instance.
        """
        if not data:
            return cls(0.0, 1.0, range_min, range_max)

        d_min = min(data)
        d_max = max(data)

        if include_zero:
            if d_min > 0:
                d_min = 0
            if d_max < 0:
                d_max = 0

        if nice:
            d_min, d_max = cls._nice_bounds(d_min, d_max)

        return cls(d_min, d_max, range_min, range_max)

    @staticmethod
    def _nice_bounds(d_min: float, d_max: float) -> tuple[float, float]:
        """Round bounds to nice numbers.

        Args:
            d_min: Minimum value.
            d_max: Maximum value.

        Returns:
            Tuple of (nice_min, nice_max).
        """
        range_val = d_max - d_min
        if range_val == 0:
            if d_min == 0:
                return -1.0, 1.0
            # Extend by 10% on each side
            margin = abs(d_min) * 0.1
            return d_min - margin, d_max + margin

        exponent = math.floor(math.log10(range_val))
        fraction = range_val / (10**exponent)

        if fraction <= 1:
            nice_fraction = 1
        elif fraction <= 2:
            nice_fraction = 2
        elif fraction <= 5:
            nice_fraction = 5
        else:
            nice_fraction = 10

        nice_range = nice_fraction * (10**exponent)
        nice_min = math.floor(d_min / nice_range) * nice_range
        nice_max = math.ceil(d_max / nice_range) * nice_range

        return nice_min, nice_max

    def with_padding(self, padding_ratio: float = 0.1) -> LinearScale:
        """Create a new scale with padding added to the domain.

        Args:
            padding_ratio: Ratio of domain span to add as padding (default 10%).

        Returns:
            A new LinearScale with expanded domain.
        """
        span = self.domain_max - self.domain_min
        padding = span * padding_ratio
        return LinearScale(
            domain_min=self.domain_min - padding,
            domain_max=self.domain_max + padding,
            range_min=self.range_min,
            range_max=self.range_max,
        )
