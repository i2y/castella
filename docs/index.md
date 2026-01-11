Castella is a pure Python cross-platform UI framework made for us Pythonista.

## Why
Dart has Flutter and Kotlin has Compose Multiplatform as cross-platform declarative UI frameworks. These frameworks describe the core parts of the framework in that language itself. They also make programmers to be able to define UI declaratively in that language, not XML, HTML, or something like their own languages. Probably, those would be very us programmer friendly and enhance our productivity. Unfortunately, at this moment (May 2022), at least as far as I know, there doesn't seem to be such a framework in Python. Castella is an attempt to see if such a thing can be made for us Pythonista in Python.

## Goals
The primary final goal of Castella is to provide features for Python programmers easy to create a UI application for several OS platforms and web browsers in a single most same code as possible as. The second goal is to provide a UI framework that Python programmers can easily understand, modify, and extend as needed.

## Features
- The core part as a UI framework of Castella is written in only Python. It's not a wrapper for existing something written in other programing languages. "pure Python cross-platform UI framework" specifies things like the above.
- Castella allows pythonista to define UI declaratively in Python.
- Castella provides hot-reloading or hot-restarting on development.
- Comprehensive theme system with design tokens (colors, typography, spacing).
- Built-in themes: Tokyo Night (default), Cupertino, Material Design 3, and classic Castella themes.
- Dark/light mode with automatic system detection and runtime switching.
- Rich markdown rendering with syntax highlighting and LaTeX math support.
- Native interactive charts (Bar, Line, Pie, Scatter, Area, Stacked Bar, Gauge) with tooltips, hover, and click events.
- **Animation system** - Smooth property animations with [ValueTween, AnimatedState](animation.md), and easing functions.
- Castella utilizes GPU via dependent libraries.
- Z-index support enables layered UIs with modals, popups, and overlays.
- **A2A Protocol support** - Connect to AI agents via Google's Agent-to-Agent protocol with `A2AClient`.
- **A2UI Protocol support** - Render agent-generated UIs with 17 standard components, tested with Google's sample agents.
- **MCP (Model Context Protocol) support** - AI agents can introspect and control UIs programmatically via [MCP](mcp.md).
- **AgentChat** - Build chat interfaces with AI agents in just 3 lines of code.

## Dependencies
- For desktop platforms, Castella is standing on existing excellent python bindings for window management library (GLFW or SDL2) and 2D graphics library (Skia).
- For web browsers, Castella is standing on awesome Pyodide/PyScript and CanvasKit (Wasm version of Skia).
- For terminals, Castella is standing on prompt_toolkit.

## Supported Platforms
Castella supports the following platforms:

- Windows 10/11
- Mac OS X
- Linux
- **iOS** (Simulator and Device) - via [castella-skia](castella-skia.md) Metal backend
- Web browsers
- Terminals