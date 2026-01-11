//! Python bindings for castella-skia-core.
//!
//! This module wraps the castella-skia-core Rust library for Python using PyO3.

use pyo3::prelude::*;
use pyo3::exceptions::PyRuntimeError;

use castella_skia_core as core;

// ============ Type Wrappers ============

/// A 2D point.
#[pyclass]
#[derive(Clone, Copy, Debug, Default)]
pub struct Point {
    #[pyo3(get, set)]
    pub x: f32,
    #[pyo3(get, set)]
    pub y: f32,
}

#[pymethods]
impl Point {
    #[new]
    #[pyo3(signature = (x=0.0, y=0.0))]
    pub fn new(x: f32, y: f32) -> Self {
        Self { x, y }
    }
}

impl From<Point> for core::Point {
    fn from(p: Point) -> Self {
        core::Point::new(p.x, p.y)
    }
}

impl From<core::Point> for Point {
    fn from(p: core::Point) -> Self {
        Point { x: p.x, y: p.y }
    }
}

/// A 2D size.
#[pyclass]
#[derive(Clone, Copy, Debug, Default)]
pub struct Size {
    #[pyo3(get, set)]
    pub width: f32,
    #[pyo3(get, set)]
    pub height: f32,
}

#[pymethods]
impl Size {
    #[new]
    #[pyo3(signature = (width=0.0, height=0.0))]
    pub fn new(width: f32, height: f32) -> Self {
        Self { width, height }
    }
}

/// A rectangle defined by origin point and size.
#[pyclass]
#[derive(Clone, Copy, Debug, Default)]
pub struct Rect {
    #[pyo3(get, set)]
    pub x: f32,
    #[pyo3(get, set)]
    pub y: f32,
    #[pyo3(get, set)]
    pub width: f32,
    #[pyo3(get, set)]
    pub height: f32,
}

#[pymethods]
impl Rect {
    #[new]
    #[pyo3(signature = (x=0.0, y=0.0, width=0.0, height=0.0))]
    pub fn new(x: f32, y: f32, width: f32, height: f32) -> Self {
        Self { x, y, width, height }
    }
}

/// A circle defined by center point and radius.
#[pyclass]
#[derive(Clone, Copy, Debug, Default)]
pub struct Circle {
    #[pyo3(get, set)]
    pub cx: f32,
    #[pyo3(get, set)]
    pub cy: f32,
    #[pyo3(get, set)]
    pub radius: f32,
}

#[pymethods]
impl Circle {
    #[new]
    #[pyo3(signature = (cx=0.0, cy=0.0, radius=0.0))]
    pub fn new(cx: f32, cy: f32, radius: f32) -> Self {
        Self { cx, cy, radius }
    }
}

/// Drop shadow configuration.
#[pyclass]
#[derive(Clone, Debug)]
pub struct Shadow {
    #[pyo3(get, set)]
    pub color: String,
    #[pyo3(get, set)]
    pub offset_x: f32,
    #[pyo3(get, set)]
    pub offset_y: f32,
    #[pyo3(get, set)]
    pub blur_radius: f32,
}

#[pymethods]
impl Shadow {
    #[new]
    #[pyo3(signature = (color="#00000080", offset_x=0.0, offset_y=2.0, blur_radius=4.0))]
    pub fn new(color: &str, offset_x: f32, offset_y: f32, blur_radius: f32) -> Self {
        Self {
            color: color.to_string(),
            offset_x,
            offset_y,
            blur_radius,
        }
    }
}

impl From<&Shadow> for core::Shadow {
    fn from(s: &Shadow) -> Self {
        core::Shadow::new(&s.color, s.offset_x, s.offset_y, s.blur_radius)
    }
}

impl From<&core::Shadow> for Shadow {
    fn from(s: &core::Shadow) -> Self {
        Shadow {
            color: s.color.clone(),
            offset_x: s.offset_x,
            offset_y: s.offset_y,
            blur_radius: s.blur_radius,
        }
    }
}

/// Font metrics returned from get_font_metrics().
#[pyclass]
#[derive(Clone, Debug, Default)]
pub struct FontMetrics {
    #[pyo3(get)]
    pub ascent: f32,
    #[pyo3(get)]
    pub descent: f32,
    #[pyo3(get)]
    pub leading: f32,
    #[pyo3(get)]
    pub height: f32,
}

#[pymethods]
impl FontMetrics {
    #[new]
    #[pyo3(signature = (ascent=0.0, descent=0.0, leading=0.0))]
    pub fn new(ascent: f32, descent: f32, leading: f32) -> Self {
        Self {
            ascent,
            descent,
            leading,
            height: ascent.abs() + descent.abs(),
        }
    }
}

impl From<core::FontMetrics> for FontMetrics {
    fn from(m: core::FontMetrics) -> Self {
        FontMetrics {
            ascent: m.ascent,
            descent: m.descent,
            leading: m.leading,
            height: m.height,
        }
    }
}

/// Drawing style configuration.
#[pyclass]
#[derive(Clone, Debug)]
pub struct Style {
    #[pyo3(get, set)]
    pub fill_color: Option<String>,
    #[pyo3(get, set)]
    pub stroke_color: Option<String>,
    #[pyo3(get, set)]
    pub stroke_width: f32,
    #[pyo3(get, set)]
    pub font_family: Option<String>,
    #[pyo3(get, set)]
    pub font_size: f32,
    #[pyo3(get, set)]
    pub border_radius: f32,
    #[pyo3(get, set)]
    pub shadow: Option<Shadow>,
}

impl Default for Style {
    fn default() -> Self {
        Self {
            fill_color: Some("#000000".to_string()),
            stroke_color: None,
            stroke_width: 1.0,
            font_family: None,
            font_size: 14.0,
            border_radius: 0.0,
            shadow: None,
        }
    }
}

#[pymethods]
impl Style {
    #[new]
    #[pyo3(signature = (
        fill_color=None,
        stroke_color=None,
        stroke_width=1.0,
        font_family=None,
        font_size=14.0,
        border_radius=0.0,
        shadow=None
    ))]
    pub fn new(
        fill_color: Option<String>,
        stroke_color: Option<String>,
        stroke_width: f32,
        font_family: Option<String>,
        font_size: f32,
        border_radius: f32,
        shadow: Option<Shadow>,
    ) -> Self {
        Self {
            fill_color,
            stroke_color,
            stroke_width,
            font_family,
            font_size,
            border_radius,
            shadow,
        }
    }
}

impl From<&Style> for core::Style {
    fn from(s: &Style) -> Self {
        core::Style {
            fill_color: s.fill_color.clone(),
            stroke_color: s.stroke_color.clone(),
            stroke_width: s.stroke_width,
            font_family: s.font_family.clone(),
            font_size: s.font_size,
            border_radius: s.border_radius,
            shadow: s.shadow.as_ref().map(|sh| sh.into()),
        }
    }
}

impl From<&core::Style> for Style {
    fn from(s: &core::Style) -> Self {
        Style {
            fill_color: s.fill_color.clone(),
            stroke_color: s.stroke_color.clone(),
            stroke_width: s.stroke_width,
            font_family: s.font_family.clone(),
            font_size: s.font_size,
            border_radius: s.border_radius,
            shadow: s.shadow.as_ref().map(|sh| sh.into()),
        }
    }
}

// ============ Surface Wrapper ============

/// A wrapper around skia_safe::Surface that can be created from different backends.
#[pyclass(unsendable)]
pub struct Surface {
    inner: core::Surface,
}

#[pymethods]
impl Surface {
    /// Create a raster (CPU) surface for testing.
    #[staticmethod]
    pub fn new_raster(width: i32, height: i32) -> PyResult<Self> {
        let inner = core::Surface::new_raster(width, height)
            .map_err(|e| PyRuntimeError::new_err(e.to_string()))?;
        Ok(Self { inner })
    }

    /// Get the width of the surface.
    #[getter]
    pub fn width(&self) -> i32 {
        self.inner.width()
    }

    /// Get the height of the surface.
    #[getter]
    pub fn height(&self) -> i32 {
        self.inner.height()
    }

    /// Flush and submit pending GPU operations.
    pub fn flush_and_submit(&mut self) {
        self.inner.flush_and_submit();
    }

    /// Save the surface to a PNG file.
    pub fn save_png(&mut self, path: &str) -> PyResult<()> {
        self.inner.save_png(path)
            .map_err(|e| PyRuntimeError::new_err(e.to_string()))
    }

    /// Get the surface pixel data as RGBA bytes.
    pub fn get_rgba_data(&mut self) -> PyResult<Vec<u8>> {
        self.inner.get_rgba_data()
            .map_err(|e| PyRuntimeError::new_err(e.to_string()))
    }

    /// Get the surface pixel data as PNG bytes.
    pub fn get_png_data(&mut self) -> PyResult<Vec<u8>> {
        self.inner.get_png_data()
            .map_err(|e| PyRuntimeError::new_err(e.to_string()))
    }

    /// Create a Surface from an OpenGL context.
    #[cfg(not(any(target_os = "ios", target_os = "android")))]
    #[staticmethod]
    #[pyo3(signature = (width, height, sample_count=0, stencil_bits=0, framebuffer_id=0))]
    pub fn from_gl_context(
        width: i32,
        height: i32,
        sample_count: usize,
        stencil_bits: usize,
        framebuffer_id: u32,
    ) -> PyResult<Self> {
        let inner = core::Surface::from_gl_context(width, height, sample_count, stencil_bits, framebuffer_id)
            .map_err(|e| PyRuntimeError::new_err(e.to_string()))?;
        Ok(Self { inner })
    }

    /// Resize the surface without recreating the DirectContext.
    #[cfg(not(any(target_os = "ios", target_os = "android")))]
    #[pyo3(signature = (width, height, sample_count=0, stencil_bits=0, framebuffer_id=0))]
    pub fn resize(
        &mut self,
        width: i32,
        height: i32,
        sample_count: usize,
        stencil_bits: usize,
        framebuffer_id: u32,
    ) -> PyResult<()> {
        self.inner.resize(width, height, sample_count, stencil_bits, framebuffer_id)
            .map_err(|e| PyRuntimeError::new_err(e.to_string()))
    }

    /// Create a Surface from Metal device and command queue pointers.
    #[cfg(target_os = "ios")]
    #[staticmethod]
    pub fn from_metal(
        device_ptr: usize,
        queue_ptr: usize,
        width: i32,
        height: i32,
    ) -> PyResult<Self> {
        let inner = core::Surface::from_metal(device_ptr, queue_ptr, width, height)
            .map_err(|e| PyRuntimeError::new_err(e.to_string()))?;
        Ok(Self { inner })
    }

    /// Resize the Metal surface without recreating the DirectContext.
    #[cfg(target_os = "ios")]
    #[pyo3(signature = (width, height))]
    pub fn resize_metal(
        &mut self,
        width: i32,
        height: i32,
    ) -> PyResult<()> {
        self.inner.resize_metal(width, height)
            .map_err(|e| PyRuntimeError::new_err(e.to_string()))
    }

    /// Create a Surface from a Vulkan surface.
    #[cfg(target_os = "android")]
    #[staticmethod]
    pub fn from_vulkan(surface_ptr: usize, width: i32, height: i32) -> PyResult<Self> {
        let inner = core::Surface::from_vulkan(surface_ptr, width, height)
            .map_err(|e| PyRuntimeError::new_err(e.to_string()))?;
        Ok(Self { inner })
    }
}

// ============ SkiaPainter Wrapper ============

/// State saved by save() and restored by restore().
#[derive(Clone)]
struct PainterState {
    style: Style,
}

/// SkiaPainter - implements BasePainter protocol.
#[pyclass(unsendable)]
pub struct SkiaPainter {
    surface: Py<Surface>,
    current_style: Style,
    current_font_size: f32,
    current_font_family: Option<String>,
    state_stack: Vec<PainterState>,
}

#[pymethods]
impl SkiaPainter {
    /// Create a new SkiaPainter from a Surface.
    #[new]
    pub fn new(surface: Py<Surface>) -> Self {
        Self {
            surface,
            current_style: Style::default(),
            current_font_size: 14.0,
            current_font_family: None,
            state_stack: Vec::new(),
        }
    }

    /// Clear the entire drawing surface with background color.
    pub fn clear_all(&mut self, py: Python<'_>) {
        let mut surface = self.surface.borrow_mut(py);
        let mut painter = core::SkiaPainter::new(&mut surface.inner);
        let core_style: core::Style = (&self.current_style).into();
        painter.set_style(&core_style);
        painter.clear_all();
    }

    /// Fill a rectangle with the current fill style.
    #[pyo3(signature = (x, y, width, height))]
    pub fn fill_rect(&mut self, py: Python<'_>, x: f32, y: f32, width: f32, height: f32) {
        let mut surface = self.surface.borrow_mut(py);
        let mut painter = core::SkiaPainter::new(&mut surface.inner);
        let core_style: core::Style = (&self.current_style).into();
        painter.set_style(&core_style);
        painter.fill_rect(x, y, width, height);
    }

    /// Stroke a rectangle outline with the current stroke style.
    #[pyo3(signature = (x, y, width, height))]
    pub fn stroke_rect(&mut self, py: Python<'_>, x: f32, y: f32, width: f32, height: f32) {
        let mut surface = self.surface.borrow_mut(py);
        let mut painter = core::SkiaPainter::new(&mut surface.inner);
        let core_style: core::Style = (&self.current_style).into();
        painter.set_style(&core_style);
        painter.stroke_rect(x, y, width, height);
    }

    /// Translate the canvas origin.
    pub fn translate(&mut self, py: Python<'_>, x: f32, y: f32) {
        let mut surface = self.surface.borrow_mut(py);
        let mut painter = core::SkiaPainter::new(&mut surface.inner);
        painter.translate(x, y);
    }

    /// Scale the canvas.
    pub fn scale(&mut self, py: Python<'_>, sx: f32, sy: f32) {
        let mut surface = self.surface.borrow_mut(py);
        let mut painter = core::SkiaPainter::new(&mut surface.inner);
        painter.scale(sx, sy);
    }

    /// Set the clipping region.
    #[pyo3(signature = (x, y, width, height))]
    pub fn clip(&mut self, py: Python<'_>, x: f32, y: f32, width: f32, height: f32) {
        let mut surface = self.surface.borrow_mut(py);
        let mut painter = core::SkiaPainter::new(&mut surface.inner);
        painter.clip(x, y, width, height);
    }

    /// Draw filled text at the given position.
    #[pyo3(signature = (text, x, y, max_width=None))]
    pub fn fill_text(&mut self, py: Python<'_>, text: &str, x: f32, y: f32, max_width: Option<f32>) {
        let mut surface = self.surface.borrow_mut(py);
        let mut painter = core::SkiaPainter::new(&mut surface.inner);
        let core_style: core::Style = (&self.current_style).into();
        painter.set_style(&core_style);
        painter.fill_text(text, x, y, max_width);
    }

    /// Draw stroked text at the given position.
    #[pyo3(signature = (text, x, y, max_width=None))]
    pub fn stroke_text(&mut self, py: Python<'_>, text: &str, x: f32, y: f32, max_width: Option<f32>) {
        let mut surface = self.surface.borrow_mut(py);
        let mut painter = core::SkiaPainter::new(&mut surface.inner);
        let core_style: core::Style = (&self.current_style).into();
        painter.set_style(&core_style);
        painter.stroke_text(text, x, y, max_width);
    }

    /// Measure the width of text with the current font.
    pub fn measure_text(&self, py: Python<'_>, text: &str) -> f32 {
        let mut surface = self.surface.borrow_mut(py);
        let mut painter = core::SkiaPainter::new(&mut surface.inner);
        let core_style: core::Style = (&self.current_style).into();
        painter.set_style(&core_style);
        painter.measure_text(text)
    }

    /// Get metrics for the current font.
    pub fn get_font_metrics(&self, py: Python<'_>) -> FontMetrics {
        let mut surface = self.surface.borrow_mut(py);
        let mut painter = core::SkiaPainter::new(&mut surface.inner);
        let core_style: core::Style = (&self.current_style).into();
        painter.set_style(&core_style);
        painter.get_font_metrics().into()
    }

    /// Save the current canvas state.
    pub fn save(&mut self, py: Python<'_>) {
        // Save style state in Python-side stack
        self.state_stack.push(PainterState {
            style: self.current_style.clone(),
        });

        // Save canvas state (transforms, clips)
        let mut surface = self.surface.borrow_mut(py);
        let canvas = surface.inner.canvas();
        canvas.save();
    }

    /// Restore the previously saved canvas state.
    pub fn restore(&mut self, py: Python<'_>) {
        // Restore style state from Python-side stack
        if let Some(state) = self.state_stack.pop() {
            self.current_style = state.style;
            self.current_font_size = self.current_style.font_size;
            self.current_font_family = self.current_style.font_family.clone();
        }

        // Restore canvas state (transforms, clips)
        let mut surface = self.surface.borrow_mut(py);
        let canvas = surface.inner.canvas();
        canvas.restore();
    }

    /// Set the current drawing style.
    pub fn style(&mut self, style: &Style) {
        self.current_style = style.clone();
        self.current_font_size = style.font_size;
        self.current_font_family = style.font_family.clone();
    }

    /// Flush pending drawing operations.
    pub fn flush(&mut self, py: Python<'_>) {
        let mut surface = self.surface.borrow_mut(py);
        let mut painter = core::SkiaPainter::new(&mut surface.inner);
        painter.flush();
    }

    /// Fill a circle with the current fill style.
    pub fn fill_circle(&mut self, py: Python<'_>, cx: f32, cy: f32, radius: f32) {
        let mut surface = self.surface.borrow_mut(py);
        let mut painter = core::SkiaPainter::new(&mut surface.inner);
        let core_style: core::Style = (&self.current_style).into();
        painter.set_style(&core_style);
        painter.fill_circle(cx, cy, radius);
    }

    /// Stroke a circle outline with the current stroke style.
    pub fn stroke_circle(&mut self, py: Python<'_>, cx: f32, cy: f32, radius: f32) {
        let mut surface = self.surface.borrow_mut(py);
        let mut painter = core::SkiaPainter::new(&mut surface.inner);
        let core_style: core::Style = (&self.current_style).into();
        painter.set_style(&core_style);
        painter.stroke_circle(cx, cy, radius);
    }

    /// Draw an image from a local file.
    #[pyo3(signature = (file_path, x, y, width, height, use_cache=true))]
    pub fn draw_image(
        &mut self,
        py: Python<'_>,
        file_path: &str,
        x: f32,
        y: f32,
        width: f32,
        height: f32,
        use_cache: bool,
    ) -> PyResult<()> {
        let mut surface = self.surface.borrow_mut(py);
        let mut painter = core::SkiaPainter::new(&mut surface.inner);
        painter.draw_image(file_path, x, y, width, height, use_cache)
            .map_err(|e| PyRuntimeError::new_err(e.to_string()))
    }

    /// Measure the size of an image from a local file.
    #[pyo3(signature = (file_path, use_cache=true))]
    pub fn measure_image(&self, py: Python<'_>, file_path: &str, use_cache: bool) -> PyResult<(i32, i32)> {
        let mut surface = self.surface.borrow_mut(py);
        let painter = core::SkiaPainter::new(&mut surface.inner);
        painter.measure_image(file_path, use_cache)
            .map_err(|e| PyRuntimeError::new_err(e.to_string()))
    }
}

// ============ Module Functions ============

/// Debug function to check font fallback for a character.
#[pyfunction]
fn debug_font_for_char(ch: char, primary_family: &str) -> (String, u32, bool, String) {
    let (c, codepoint, has_glyph, fallback) = core::debug_font_fallback(ch, primary_family);
    (c.to_string(), codepoint, has_glyph, fallback)
}

/// Debug function to segment text by font.
#[pyfunction]
fn debug_text_segments(text: &str, primary_family: &str) -> Vec<(String, String)> {
    core::debug_segment_text(text, primary_family)
}

/// Clear the image cache.
#[pyfunction]
fn clear_image_cache() {
    core::clear_image_cache();
}

// ============ Module Definition ============

/// castella-skia Python module.
#[pymodule]
fn castella_skia(m: &Bound<'_, PyModule>) -> PyResult<()> {
    // Types
    m.add_class::<Point>()?;
    m.add_class::<Size>()?;
    m.add_class::<Rect>()?;
    m.add_class::<Circle>()?;
    m.add_class::<Shadow>()?;
    m.add_class::<FontMetrics>()?;
    m.add_class::<Style>()?;

    // Core classes
    m.add_class::<Surface>()?;
    m.add_class::<SkiaPainter>()?;

    // Functions
    m.add_function(wrap_pyfunction!(clear_image_cache, m)?)?;
    m.add_function(wrap_pyfunction!(debug_font_for_char, m)?)?;
    m.add_function(wrap_pyfunction!(debug_text_segments, m)?)?;

    // Version info
    m.add("__version__", core::VERSION)?;

    Ok(())
}
