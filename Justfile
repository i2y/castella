# Castella - Development Commands
# Run `just` to see available commands

# Default recipe - show available commands
default:
    @just --list

# Install development dependencies
install:
    uv sync

# Install GLFW backend dependencies
install-glfw:
    uv sync --extra glfw

# Install SDL2 backend dependencies
install-sdl:
    uv sync --extra sdl

# Install Terminal UI backend dependencies
install-tui:
    uv sync --extra tui

# Format code with ruff
format:
    uv run ruff format castella

# Check code formatting
format-check:
    uv run ruff format --check castella

# Lint code with ruff
lint:
    uv run ruff check castella

# Run all checks (format-check + lint)
check: format-check lint

# Auto-fix issues (format + lint with auto-fix)
fix:
    uv run ruff check --fix castella
    uv run ruff format castella

# Build package
build:
    uv build

# Run an example (e.g., just run counter)
run EXAMPLE:
    uv run python examples/{{EXAMPLE}}.py

# Run an example with hot restart (e.g., just dev counter)
dev EXAMPLE:
    uv run python tools/hot_restarter.py examples/{{EXAMPLE}}.py

# Build documentation
docs:
    uv run mkdocs build

# Serve documentation locally (port 8000)
docs-serve:
    uv run mkdocs serve

# Clean build artifacts and caches
clean:
    rm -rf .ruff_cache
    rm -rf .mypy_cache
    rm -rf site
    rm -rf dist
    rm -rf build
    rm -rf *.egg-info
    find . -type d -name __pycache__ -exec rm -rf {} +
    find . -type f -name "*.pyc" -delete
