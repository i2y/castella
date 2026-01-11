//! castella-skia-core - Core Skia rendering library for Castella UI framework.
//!
//! This crate provides GPU-accelerated 2D rendering for Castella across all platforms:
//! - Desktop (macOS, Linux, Windows) via OpenGL
//! - iOS via Metal
//! - Android via Vulkan (TODO)
//!
//! This is a pure Rust library without any FFI bindings. For language-specific
//! bindings, see the `bindings/` directory in the Castella repository.
//!
//! # Example (Rust)
//!
//! ```rust,ignore
//! use castella_skia_core::{Surface, SkiaPainter, Style};
//!
//! // Create a surface from OpenGL context (after context is made current)
//! let mut surface = Surface::from_gl_context(800, 600, 0, 0, 0)?;
//!
//! // Create a painter
//! let mut painter = SkiaPainter::new(&mut surface);
//!
//! // Set style and draw
//! let style = Style::new().with_fill_color("#ff0000");
//! painter.set_style(&style);
//! painter.fill_rect(10.0, 10.0, 100.0, 50.0);
//!
//! // Flush to screen
//! painter.flush();
//! surface.flush_and_submit();
//! ```

pub mod error;
pub mod font;
pub mod image;
pub mod painter;
pub mod surface;
pub mod types;

// Re-export main types at crate root for convenience
pub use error::{Error, Result};
pub use font::{
    create_font, create_typeface, debug_font_fallback, debug_segment_text,
    find_fallback_typeface, get_font_manager, get_metrics, has_glyph,
    segment_text_by_font, TextSegment,
};
pub use image::{clear_image_cache, load_image, load_image_from_bytes, measure_image};
pub use painter::SkiaPainter;
pub use surface::Surface;
pub use types::{parse_color, Circle, FontMetrics, Point, Rect, Shadow, Size, Style};

/// Version of the castella-skia-core library.
pub const VERSION: &str = env!("CARGO_PKG_VERSION");
