"""Application bootstrap for wrks."""


def main() -> None:
    """Main entry point for wrks."""
    from castella import App
    from castella.frame import Frame
    from castella.theme import ThemeManager, TOKYO_NIGHT_DARK_THEME, TOKYO_NIGHT_LIGHT_THEME

    from castella.wrks.config import get_config
    from castella.wrks.ui import MainWindow

    # Load configuration
    config = get_config()

    # Apply Tokyo Night theme
    manager = ThemeManager()
    manager.set_dark_theme(TOKYO_NIGHT_DARK_THEME)
    manager.set_light_theme(TOKYO_NIGHT_LIGHT_THEME)

    # Apply dark mode preference
    if config.dark_mode is not None:
        manager.prefer_dark(config.dark_mode)
    else:
        # Default to dark mode for Tokyo Night aesthetic
        manager.prefer_dark(True)

    # Create main window
    window = MainWindow()

    # Create and run app
    app = App(
        Frame(config.window_title, config.window_width, config.window_height),
        window,
    )
    app.run()


def cli() -> None:
    """CLI entry point with argument parsing."""
    import argparse

    parser = argparse.ArgumentParser(
        prog="wrks",
        description="Claude Code GUI Wrapper using Castella",
    )
    parser.add_argument(
        "--dark-mode",
        action="store_true",
        help="Force dark mode",
    )
    parser.add_argument(
        "--light-mode",
        action="store_true",
        help="Force light mode",
    )
    parser.add_argument(
        "--permission-mode",
        choices=["default", "acceptEdits", "bypassPermissions"],
        default="default",
        help="Tool permission mode (default: default)",
    )
    parser.add_argument(
        "--width",
        type=int,
        default=1200,
        help="Window width (default: 1200)",
    )
    parser.add_argument(
        "--height",
        type=int,
        default=800,
        help="Window height (default: 800)",
    )

    args = parser.parse_args()

    # Apply config from CLI args
    from castella.wrks.config import WrksConfig, set_config

    config = WrksConfig(
        permission_mode=args.permission_mode,
        dark_mode=True if args.dark_mode else (False if args.light_mode else None),
        window_width=args.width,
        window_height=args.height,
    )
    set_config(config)

    # Run the app
    main()


if __name__ == "__main__":
    cli()
