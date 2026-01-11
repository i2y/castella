"""LaTeX math rendering using matplotlib."""

import hashlib
import os
import tempfile
from typing import Optional

import numpy as np

try:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from PIL import Image

    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False


class MathRenderer:
    """Renders LaTeX math expressions to images using matplotlib."""

    def __init__(
        self,
        font_size: int = 14,
        dpi: int = 100,
        text_color: str = "#000000",
        bg_transparent: bool = True,
    ):
        self._font_size = font_size
        self._dpi = dpi
        self._text_color = text_color
        self._bg_transparent = bg_transparent
        self._cache: dict[str, np.ndarray] = {}
        self._file_cache: dict[str, str] = {}  # cache_key -> file_path
        self._temp_dir: Optional[str] = None

    def render(self, latex: str, inline: bool = False) -> np.ndarray:
        """Render LaTeX expression to RGBA numpy array.

        Args:
            latex: LaTeX math expression (without $ delimiters)
            inline: If True, render smaller for inline display

        Returns:
            RGBA numpy array of the rendered math
        """
        if not MATPLOTLIB_AVAILABLE:
            return self._placeholder(100, 30)

        cache_key = f"{latex}:{inline}:{self._font_size}:{self._text_color}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        fontsize = self._font_size if inline else int(self._font_size * 1.5)

        fig = plt.figure(figsize=(10, 0.5 if inline else 2), dpi=self._dpi)
        if self._bg_transparent:
            fig.patch.set_alpha(0)
        else:
            fig.patch.set_facecolor("white")

        try:
            fig.text(
                0.01,
                0.5,
                f"${latex}$",
                fontsize=fontsize,
                verticalalignment="center",
                color=self._text_color,
                transform=fig.transFigure,
            )

            fig.canvas.draw()

            array = np.array(fig.canvas.renderer.buffer_rgba())
            cropped = self._crop_to_content(array)
            cropped = np.ascontiguousarray(cropped)

            self._cache[cache_key] = cropped
            return cropped

        except Exception:
            return self._placeholder(200, 40)
        finally:
            plt.close(fig)

    def _crop_to_content(self, array: np.ndarray) -> np.ndarray:
        """Crop image to non-transparent content."""
        alpha = array[:, :, 3]
        rows = np.any(alpha > 10, axis=1)
        cols = np.any(alpha > 10, axis=0)

        if not np.any(rows) or not np.any(cols):
            return array

        rmin, rmax = np.where(rows)[0][[0, -1]]
        cmin, cmax = np.where(cols)[0][[0, -1]]

        padding = 4
        rmin = max(0, rmin - padding)
        rmax = min(array.shape[0] - 1, rmax + padding)
        cmin = max(0, cmin - padding)
        cmax = min(array.shape[1] - 1, cmax + padding)

        return array[rmin : rmax + 1, cmin : cmax + 1]

    def _placeholder(self, width: int, height: int) -> np.ndarray:
        """Create a placeholder image for errors."""
        array = np.zeros((height, width, 4), dtype=np.uint8)
        array[:, :, 0] = 128
        array[:, :, 3] = 128
        return array

    def clear_cache(self) -> None:
        """Clear the rendering cache."""
        self._cache.clear()
        self._file_cache.clear()

    def render_to_file(self, latex: str, inline: bool = False) -> tuple[str, int, int]:
        """Render LaTeX expression to a PNG file.

        Args:
            latex: LaTeX math expression (without $ delimiters)
            inline: If True, render smaller for inline display

        Returns:
            Tuple of (file_path, width, height)
        """
        if not MATPLOTLIB_AVAILABLE:
            # Return empty placeholder
            return "", 100, 30

        cache_key = f"{latex}:{inline}:{self._font_size}:{self._text_color}"

        # Check file cache first
        if cache_key in self._file_cache:
            path = self._file_cache[cache_key]
            if os.path.exists(path):
                # Get dimensions from cached array or re-read
                if cache_key in self._cache:
                    arr = self._cache[cache_key]
                    return path, arr.shape[1], arr.shape[0]
                else:
                    # Read image to get dimensions
                    img = Image.open(path)
                    return path, img.width, img.height

        # Render to numpy array first (uses existing cache)
        array = self.render(latex, inline)

        # Create temp directory if needed
        if self._temp_dir is None:
            self._temp_dir = tempfile.mkdtemp(prefix="castella_math_")

        # Generate unique filename based on content
        hash_str = hashlib.md5(cache_key.encode()).hexdigest()[:12]
        file_path = os.path.join(self._temp_dir, f"math_{hash_str}.png")

        # Save to PNG
        img = Image.fromarray(array, mode="RGBA")
        img.save(file_path, "PNG")

        # Cache the file path
        self._file_cache[cache_key] = file_path

        return file_path, array.shape[1], array.shape[0]
