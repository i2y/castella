"""Band scale for categorical data transformation."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class BandScale:
    """Maps categorical values to pixel bands (for bar charts).

    A band scale divides a pixel range into discrete bands,
    one for each category.

    Attributes:
        categories: List of category names.
        range_min: Minimum pixel value.
        range_max: Maximum pixel value.
        padding_inner: Padding between bands (0.0-1.0, as fraction of step).
        padding_outer: Padding at the outer edges (0.0-1.0, as fraction of step).
        align: Alignment of bands within their step (0.0 = left, 0.5 = center, 1.0 = right).
    """

    categories: list[str] = field(default_factory=list)
    range_min: float = 0.0
    range_max: float = 100.0
    padding_inner: float = 0.1
    padding_outer: float = 0.1
    align: float = 0.5

    @property
    def step(self) -> float:
        """Get the step size (distance between band starts)."""
        n = len(self.categories)
        if n == 0:
            return 0.0

        total_range = self.range_max - self.range_min
        return total_range / n

    @property
    def bandwidth(self) -> float:
        """Get the width of each band."""
        n = len(self.categories)
        if n == 0:
            return 0.0

        step = self.step
        # Bandwidth is step minus inner padding
        return step * (1.0 - self.padding_inner)

    def __call__(self, category: str) -> float:
        """Get the start x position for a category.

        Args:
            category: The category name.

        Returns:
            The pixel x position for the start of this category's band.
        """
        if category not in self.categories:
            return self.range_min

        idx = self.categories.index(category)
        step = self.step

        # Position is: range_min + outer_padding + idx * step + alignment offset
        outer_offset = step * self.padding_outer
        band_start = self.range_min + outer_offset + idx * step

        # Apply alignment within the step (considering inner padding)
        inner_padding = step * self.padding_inner
        align_offset = inner_padding * self.align

        return band_start + align_offset

    def center(self, category: str) -> float:
        """Get the center x position for a category.

        Args:
            category: The category name.

        Returns:
            The pixel x position for the center of this category's band.
        """
        return self(category) + self.bandwidth / 2

    def band_range(self, category: str) -> tuple[float, float]:
        """Get the pixel range for a category.

        Args:
            category: The category name.

        Returns:
            Tuple of (start, end) pixel positions.
        """
        start = self(category)
        return (start, start + self.bandwidth)

    def invert(self, pixel: float) -> str | None:
        """Find the category at a pixel position.

        Args:
            pixel: The pixel position.

        Returns:
            The category at this position, or None if outside all bands.
        """
        for category in self.categories:
            start, end = self.band_range(category)
            if start <= pixel <= end:
                return category
        return None

    def with_categories(self, categories: list[str]) -> BandScale:
        """Create a new scale with different categories.

        Args:
            categories: New list of categories.

        Returns:
            A new BandScale with the updated categories.
        """
        return BandScale(
            categories=categories,
            range_min=self.range_min,
            range_max=self.range_max,
            padding_inner=self.padding_inner,
            padding_outer=self.padding_outer,
            align=self.align,
        )

    def with_padding(
        self,
        inner: float | None = None,
        outer: float | None = None,
    ) -> BandScale:
        """Create a new scale with different padding.

        Args:
            inner: New inner padding (None to keep current).
            outer: New outer padding (None to keep current).

        Returns:
            A new BandScale with updated padding.
        """
        return BandScale(
            categories=self.categories,
            range_min=self.range_min,
            range_max=self.range_max,
            padding_inner=inner if inner is not None else self.padding_inner,
            padding_outer=outer if outer is not None else self.padding_outer,
            align=self.align,
        )
