"""Entry point for running pycode as a module.

Usage:
    python -m castella.pycode
    python -m castella.pycode --cwd /path/to/project
    python -m castella.pycode --mock
"""

from castella.pycode.app import cli

if __name__ == "__main__":
    cli()
