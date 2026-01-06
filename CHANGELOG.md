# Changelog

All notable changes to Castella will be documented in this file.

## [0.9.0] - 2025-01-07

### Added
- **I18n Module** - Internationalization support with runtime locale switching, YAML translation loading, and reactive LocaleString

## [0.8.0] - 2025-01-06

### Added
- **Interactive Legend** - Click legend items to toggle series/slice visibility

## [0.7.0] - 2025-01-05

### Added
- **HeatmapChart** - Native heatmap chart with colorbar, tooltips, axis labels, and cell value annotations
- **Heatmap Table** - DataTable cell background coloring via `ColumnConfig.cell_bg_color`
- **Colormap System** - Scientific colormaps (Viridis, Plasma, Inferno, Magma) for both chart and table
- **HeatmapConfig** - Helper class for easy heatmap table setup
- **Auto-contrast Text** - WCAG luminance-based automatic text color selection

## [0.6.0] - 2025-01-05

### Added
- **Mouse Drag Text Selection** - Input widget now supports text selection via mouse drag

## [0.5.0] - 2025-01-04

### Added
- **Graph Visualization System** - Reusable graph module with Sugiyama layout algorithm, interactive canvas with zoom/pan
- **Workflow Studio Samples** - Visual development environments for LangGraph, LlamaIndex Workflows, pydantic-graph, and Edda
- **MCP Support** - Model Context Protocol integration for AI-UI interaction
- **Animation System** - ValueTween, AnimatedState, ProgressBar, and easing functions
- **Agent Skills** - 5 built-in skills for AI coding agents (castella-core, castella-a2ui, castella-a2a, castella-mcp, castella-agent-ui)
- **A2UIClient** - Connect to A2A agents with A2UI extension
- **DataTable** - High-performance data table with sorting, filtering, selection, virtual scrolling, and Pydantic integration
- **Tree & FileTree** - Hierarchical data display with multi-select support
- **DateTimeInput** - Visual calendar picker with locale support (EN, JA)
- **MultilineText** - Text display with selection and copy support
- **Markdown** - Clickable links with hover underline, extended syntax support
- **IME Support** - Japanese/Chinese input on macOS GLFW backend

### Changed
- **A2UI 0.9 Compatibility** - Auto-normalization of A2UI 0.9 spec format
- **Theme System** - Built-in themes (Tokyo Night, Cupertino, Material Design 3)
- **Widget Lifecycle** - Added `on_mount()`, `on_unmount()`, `is_mounted()` hooks
- **Size Policies** - Added syntax sugar methods (`fixed_width()`, `fit_content()`, etc.)
- **Color System** - Alpha channel support and color utilities

### Fixed
- Slider rendering to prevent thumb afterimages
- Switch border_radius affecting center rect
- Modal event handling improvements
- Font fallback for special characters and emoji

## [0.2.3] - 2025-01-05
- Previous stable release
