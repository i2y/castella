"""Application entry point for pycode.

This module initializes and runs the pycode application.
"""

from __future__ import annotations

from pathlib import Path


def main(cwd: str | None = None, mock: bool = False) -> None:
    """Run the pycode application.

    Args:
        cwd: Working directory (defaults to current directory)
        mock: Use mock agent instead of real LLM
    """
    from castella import App
    from castella.frame import Frame

    from castella.pycode.config import Config
    from castella.pycode.theme import apply_pycode_theme
    from castella.pycode.ui.main_view import MainView

    # Apply Lithium theme
    apply_pycode_theme(dark_mode=True)

    # Load configuration
    config = Config.from_env()

    # Override cwd if provided
    if cwd:
        config.cwd = Path(cwd).resolve()

    # Create agent
    if mock:
        from castella.pycode.agent.coding_agent import MockCodingAgent

        agent = MockCodingAgent()
    else:
        # Check for API key
        if not config.has_api_key():
            print(f"Error: No API key found for {config.model.provider.value}.")
            print()
            print("Please set the appropriate environment variable:")
            print("  - Anthropic: ANTHROPIC_API_KEY")
            print("  - OpenAI: OPENAI_API_KEY")
            print("  - Google: GEMINI_API_KEY or GOOGLE_API_KEY")
            print()
            print("Or use --mock to run with a mock agent for testing.")
            return

        from castella.pycode.agent.coding_agent import CodingAgent

        agent = CodingAgent(model=config.model.to_pydantic_ai_model())

    # Create main view
    view = MainView(config=config, agent=agent)

    # Create and run app
    app = App(
        Frame(
            "pycode",
            config.window_width,
            config.window_height,
        ),
        view,
    )
    app.run()


def cli() -> None:
    """CLI entry point with argument parsing."""
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        prog="pycode",
        description="Python AI Coding Assistant",
    )
    parser.add_argument(
        "--cwd",
        "-C",
        type=str,
        default=None,
        help="Working directory (defaults to current directory)",
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Use mock agent (no API key needed)",
    )
    parser.add_argument(
        "--model",
        "-m",
        type=str,
        default=None,
        help="Model to use (e.g., 'claude-sonnet-4', 'gpt-4o')",
    )
    parser.add_argument(
        "--version",
        "-v",
        action="store_true",
        help="Show version and exit",
    )

    args = parser.parse_args()

    if args.version:
        print("pycode 0.1.0")
        sys.exit(0)

    # Set model via environment if specified
    if args.model:
        import os

        os.environ["PYCODE_MODEL"] = args.model

    main(cwd=args.cwd, mock=args.mock)


if __name__ == "__main__":
    cli()
