"""Safe dynamic Python module loading for workflow studios."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType


class ModuleLoadError(Exception):
    """Raised when module loading fails."""

    pass


def load_module(
    file_path: str | Path,
    prefix: str = "castella_studio",
) -> ModuleType:
    """Safely load a Python module from a file path.

    This function dynamically loads a Python file as a module,
    adding its parent directory to sys.path temporarily to resolve
    relative imports.

    Args:
        file_path: Path to the Python file to load.
        prefix: Prefix for the generated module name.

    Returns:
        The loaded module.

    Raises:
        ModuleLoadError: If the file doesn't exist, isn't a Python file,
            or loading fails for any reason.
    """
    path = Path(file_path).resolve()

    if not path.exists():
        raise ModuleLoadError(f"File not found: {path}")

    if path.suffix != ".py":
        raise ModuleLoadError(f"Not a Python file: {path}")

    # Generate unique module name to avoid collisions
    module_name = f"{prefix}_{path.stem}_{id(path)}"

    try:
        spec = importlib.util.spec_from_file_location(module_name, path)
        if spec is None or spec.loader is None:
            raise ModuleLoadError(f"Cannot create module spec for: {path}")

        module = importlib.util.module_from_spec(spec)

        # Add parent directory to path temporarily for imports
        parent_dir = str(path.parent)
        original_path = sys.path.copy()

        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)

        try:
            # Register module before execution (for circular imports)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
        finally:
            sys.path = original_path

        return module

    except ModuleLoadError:
        raise
    except Exception as e:
        raise ModuleLoadError(f"Failed to load module: {e}") from e


def unload_module(module: ModuleType) -> None:
    """Unload a previously loaded module.

    Args:
        module: The module to unload.
    """
    module_name = module.__name__
    if module_name in sys.modules:
        del sys.modules[module_name]


def get_module_path(module: ModuleType) -> Path | None:
    """Get the file path of a loaded module.

    Args:
        module: The module to get the path for.

    Returns:
        The file path, or None if not available.
    """
    if hasattr(module, "__file__") and module.__file__:
        return Path(module.__file__)
    return None
