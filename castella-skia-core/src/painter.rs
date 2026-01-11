//! SkiaPainter implementation - the core painting API.
//!
//! This implements the BasePainter protocol from castella.protocols.painter.

use skia_safe::{
    Canvas, ClipOp, Color, Font, FontMgr, Paint, PaintStyle, RRect, Rect,
    textlayout::{FontCollection, ParagraphBuilder, ParagraphStyle, TextStyle},
};
use std::cell::RefCell;

use crate::error::Result;
use crate::font::{create_font, get_metrics};
use crate::image::{load_image, measure_image};
use crate::surface::Surface;
use crate::types::{parse_color, FontMetrics, Style};

// Thread-local FontCollection cache (FontCollection is not Send/Sync)
thread_local! {
    static FONT_COLLECTION: RefCell<Option<FontCollection>> = const { RefCell::new(None) };
}

fn get_font_collection() -> FontCollection {
    FONT_COLLECTION.with(|cell| {
        let mut cache = cell.borrow_mut();
        if cache.is_none() {
            let mut fc = FontCollection::new();
            fc.set_default_font_manager(FontMgr::default(), None);
            *cache = Some(fc);
        }
        cache.as_ref().unwrap().clone()
    })
}

/// State saved by save() and restored by restore().
#[derive(Clone)]
struct PainterState {
    style: Style,
    font: Font,
}

/// SkiaPainter - implements BasePainter protocol.
///
/// Provides GPU-accelerated 2D drawing using Skia.
/// Note: SkiaPainter is not Send-safe because it holds a reference to Surface.
pub struct SkiaPainter<'a> {
    surface: &'a mut Surface,
    current_style: Style,
    current_font: Font,
    state_stack: Vec<PainterState>,
}

impl<'a> SkiaPainter<'a> {
    /// Create a new SkiaPainter from a Surface.
    pub fn new(surface: &'a mut Surface) -> Self {
        Self {
            surface,
            current_style: Style::default(),
            current_font: create_font(None, 14.0),
            state_stack: Vec::new(),
        }
    }

    // ========== BasePainter Required Methods ==========

    /// Clear the entire drawing surface with background color.
    pub fn clear_all(&mut self) {
        let color = self.current_style.fill_color
            .as_ref()
            .map(|c| parse_color(c))
            .unwrap_or(Color::WHITE);

        self.with_canvas(|canvas| {
            canvas.clear(color);
        });
    }

    /// Fill a rectangle with the current fill style.
    pub fn fill_rect(&mut self, x: f32, y: f32, width: f32, height: f32) {
        let radius = self.current_style.border_radius;

        // Draw shadow first (behind the shape)
        // Clone shadow to avoid borrow checker issues
        if let Some(shadow) = self.current_style.shadow.clone() {
            self.draw_shadow(x, y, width, height, &shadow, radius);
        }

        let rect = Rect::from_xywh(x, y, width, height);
        let paint = self.make_fill_paint();

        self.with_canvas(|canvas| {
            if radius > 0.0 {
                let rrect = RRect::new_rect_xy(rect, radius, radius);
                canvas.draw_rrect(rrect, &paint);
            } else {
                canvas.draw_rect(rect, &paint);
            }
        });
    }

    /// Draw a drop shadow behind a rectangle.
    fn draw_shadow(
        &mut self,
        x: f32,
        y: f32,
        width: f32,
        height: f32,
        shadow: &crate::types::Shadow,
        border_radius: f32,
    ) {
        let mut paint = Paint::default();
        paint.set_style(PaintStyle::Fill);
        paint.set_anti_alias(true);
        paint.set_color(parse_color(&shadow.color));

        if let Some(filter) = shadow.make_blur_filter() {
            paint.set_mask_filter(filter);
        }

        // Offset rectangle for shadow
        let shadow_rect = Rect::from_xywh(
            x + shadow.offset_x,
            y + shadow.offset_y,
            width,
            height,
        );

        self.with_canvas(|canvas| {
            if border_radius > 0.0 {
                let rrect = RRect::new_rect_xy(shadow_rect, border_radius, border_radius);
                canvas.draw_rrect(rrect, &paint);
            } else {
                canvas.draw_rect(shadow_rect, &paint);
            }
        });
    }

    /// Stroke a rectangle outline with the current stroke style.
    pub fn stroke_rect(&mut self, x: f32, y: f32, width: f32, height: f32) {
        let rect = Rect::from_xywh(x, y, width, height);
        let paint = self.make_stroke_paint();
        let radius = self.current_style.border_radius;

        self.with_canvas(|canvas| {
            if radius > 0.0 {
                let rrect = RRect::new_rect_xy(rect, radius, radius);
                canvas.draw_rrect(rrect, &paint);
            } else {
                canvas.draw_rect(rect, &paint);
            }
        });
    }

    /// Translate the canvas origin.
    pub fn translate(&mut self, x: f32, y: f32) {
        self.with_canvas(|canvas| {
            canvas.translate((x, y));
        });
    }

    /// Scale the canvas.
    pub fn scale(&mut self, sx: f32, sy: f32) {
        self.with_canvas(|canvas| {
            canvas.scale((sx, sy));
        });
    }

    /// Set the clipping region.
    pub fn clip(&mut self, x: f32, y: f32, width: f32, height: f32) {
        let rect = Rect::from_xywh(x, y, width, height);
        self.with_canvas(|canvas| {
            canvas.clip_rect(rect, ClipOp::Intersect, true);
        });
    }

    /// Draw filled text at the given position.
    pub fn fill_text(&mut self, text: &str, x: f32, y: f32, max_width: Option<f32>) {
        let paint = self.make_fill_paint();
        self.draw_text_internal(text, x, y, max_width, &paint);
    }

    /// Draw stroked text at the given position.
    pub fn stroke_text(&mut self, text: &str, x: f32, y: f32, max_width: Option<f32>) {
        let paint = self.make_stroke_paint();
        self.draw_text_internal(text, x, y, max_width, &paint);
    }

    /// Measure the width of text with the current font (with fallback support).
    pub fn measure_text(&self, text: &str) -> f32 {
        if text.is_empty() {
            return 0.0;
        }

        let font_collection = get_font_collection();
        let paragraph_style = ParagraphStyle::new();

        let mut text_style = TextStyle::new();
        text_style.set_font_size(self.current_font.size());
        if let Some(ref family) = self.current_style.font_family {
            text_style.set_font_families(&[family.as_str()]);
        }

        let mut builder = ParagraphBuilder::new(&paragraph_style, font_collection);
        builder.push_style(&text_style);
        builder.add_text(text);

        let mut paragraph = builder.build();
        paragraph.layout(f32::MAX);

        paragraph.max_intrinsic_width()
    }

    /// Get metrics for the current font.
    pub fn get_font_metrics(&self) -> FontMetrics {
        get_metrics(&self.current_font)
    }

    /// Save the current canvas state.
    pub fn save(&mut self) {
        // Save style state
        self.state_stack.push(PainterState {
            style: self.current_style.clone(),
            font: self.current_font.clone(),
        });

        // Save canvas state
        self.with_canvas(|canvas| {
            canvas.save();
        });
    }

    /// Restore the previously saved canvas state.
    pub fn restore(&mut self) {
        // Restore style state
        if let Some(state) = self.state_stack.pop() {
            self.current_style = state.style;
            self.current_font = state.font;
        }

        // Restore canvas state
        self.with_canvas(|canvas| {
            canvas.restore();
        });
    }

    /// Set the current drawing style.
    pub fn set_style(&mut self, style: &Style) {
        // Only recreate font if font settings actually changed
        let font_changed = style.font_family != self.current_style.font_family
            || (style.font_size - self.current_style.font_size).abs() > 0.001;

        self.current_style = style.clone();

        if font_changed {
            let family = style.font_family.as_deref();
            let size = style.font_size;
            self.current_font = create_font(family, size);
        }
    }

    /// Get the current drawing style.
    pub fn get_style(&self) -> &Style {
        &self.current_style
    }

    /// Flush pending drawing operations.
    pub fn flush(&mut self) {
        // Note: actual flushing happens when swapping buffers
        // The surface's flush_and_submit is called separately
    }

    // ========== CircleCapable Methods ==========

    /// Fill a circle with the current fill style.
    pub fn fill_circle(&mut self, cx: f32, cy: f32, radius: f32) {
        let paint = self.make_fill_paint();
        self.with_canvas(|canvas| {
            canvas.draw_circle((cx, cy), radius, &paint);
        });
    }

    /// Stroke a circle outline with the current stroke style.
    pub fn stroke_circle(&mut self, cx: f32, cy: f32, radius: f32) {
        let paint = self.make_stroke_paint();
        self.with_canvas(|canvas| {
            canvas.draw_circle((cx, cy), radius, &paint);
        });
    }

    // ========== LocalImageCapable Methods ==========

    /// Draw an image from a local file.
    pub fn draw_image(
        &mut self,
        file_path: &str,
        x: f32,
        y: f32,
        width: f32,
        height: f32,
        use_cache: bool,
    ) -> Result<()> {
        let image = load_image(file_path, use_cache)?;
        let dest_rect = Rect::from_xywh(x, y, width, height);

        self.with_canvas(|canvas| {
            canvas.draw_image_rect(&image, None, dest_rect, &Paint::default());
        });

        Ok(())
    }

    /// Measure the size of an image from a local file.
    pub fn measure_image(&self, file_path: &str, use_cache: bool) -> Result<(i32, i32)> {
        measure_image(file_path, use_cache)
    }
}

// Internal helper methods
impl<'a> SkiaPainter<'a> {
    /// Access the canvas and run a closure.
    fn with_canvas<F>(&mut self, f: F)
    where
        F: FnOnce(&Canvas),
    {
        let canvas = self.surface.canvas();
        f(canvas);
    }

    /// Create a Paint for fill operations.
    fn make_fill_paint(&self) -> Paint {
        let mut paint = Paint::default();
        paint.set_style(PaintStyle::Fill);
        paint.set_anti_alias(true);

        if let Some(ref color_str) = self.current_style.fill_color {
            paint.set_color(parse_color(color_str));
        }

        paint
    }

    /// Create a Paint for stroke operations.
    fn make_stroke_paint(&self) -> Paint {
        let mut paint = Paint::default();
        paint.set_style(PaintStyle::Stroke);
        paint.set_anti_alias(true);
        paint.set_stroke_width(self.current_style.stroke_width);

        if let Some(ref color_str) = self.current_style.stroke_color {
            paint.set_color(parse_color(color_str));
        } else if let Some(ref color_str) = self.current_style.fill_color {
            // Fall back to fill color if no stroke color
            paint.set_color(parse_color(color_str));
        }

        paint
    }

    /// Internal text drawing with font fallback support using Paragraph.
    fn draw_text_internal(
        &mut self,
        text: &str,
        x: f32,
        y: f32,
        _max_width: Option<f32>,
        _paint: &Paint,
    ) {
        if text.is_empty() {
            return;
        }

        let font_collection = get_font_collection();
        let paragraph_style = ParagraphStyle::new();

        let mut text_style = TextStyle::new();
        text_style.set_font_size(self.current_font.size());

        // Set font family
        if let Some(ref family) = self.current_style.font_family {
            text_style.set_font_families(&[family.as_str()]);
        }

        // Set color from current style
        if let Some(ref color_str) = self.current_style.fill_color {
            text_style.set_color(parse_color(color_str));
        } else {
            text_style.set_color(Color::BLACK);
        }

        let mut builder = ParagraphBuilder::new(&paragraph_style, font_collection);
        builder.push_style(&text_style);
        builder.add_text(text);

        let mut paragraph = builder.build();
        paragraph.layout(f32::MAX);

        // Paragraph draws from top-left, but fill_text expects baseline position
        // Use the paragraph's own alphabetic baseline for accurate positioning
        let baseline = paragraph.alphabetic_baseline();

        self.with_canvas(|canvas| {
            paragraph.paint(canvas, (x, y - baseline));
        });
    }
}
