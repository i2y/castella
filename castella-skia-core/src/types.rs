//! Type definitions for castella-skia-core.
//! These types are pure Rust and can be wrapped by any FFI (PyO3, magnus, napi-rs, etc.).

use skia_safe::MaskFilter;

/// A 2D point.
#[derive(Clone, Copy, Debug, Default, PartialEq)]
pub struct Point {
    pub x: f32,
    pub y: f32,
}

impl Point {
    pub fn new(x: f32, y: f32) -> Self {
        Self { x, y }
    }
}

/// A 2D size.
#[derive(Clone, Copy, Debug, Default, PartialEq)]
pub struct Size {
    pub width: f32,
    pub height: f32,
}

impl Size {
    pub fn new(width: f32, height: f32) -> Self {
        Self { width, height }
    }
}

/// A rectangle defined by origin point and size.
#[derive(Clone, Copy, Debug, Default, PartialEq)]
pub struct Rect {
    pub x: f32,
    pub y: f32,
    pub width: f32,
    pub height: f32,
}

impl Rect {
    pub fn new(x: f32, y: f32, width: f32, height: f32) -> Self {
        Self { x, y, width, height }
    }

    pub fn from_xywh(x: f32, y: f32, width: f32, height: f32) -> Self {
        Self::new(x, y, width, height)
    }
}

/// A circle defined by center point and radius.
#[derive(Clone, Copy, Debug, Default, PartialEq)]
pub struct Circle {
    pub cx: f32,
    pub cy: f32,
    pub radius: f32,
}

impl Circle {
    pub fn new(cx: f32, cy: f32, radius: f32) -> Self {
        Self { cx, cy, radius }
    }
}

/// Font metrics returned from get_font_metrics().
#[derive(Clone, Debug, Default, PartialEq)]
pub struct FontMetrics {
    /// The recommended distance above the baseline.
    pub ascent: f32,
    /// The recommended distance below the baseline.
    pub descent: f32,
    /// The recommended distance between lines.
    pub leading: f32,
    /// The height of the font (ascent + descent).
    pub height: f32,
}

impl FontMetrics {
    pub fn new(ascent: f32, descent: f32, leading: f32) -> Self {
        Self {
            ascent,
            descent,
            leading,
            height: ascent.abs() + descent.abs(),
        }
    }
}

/// Drop shadow configuration.
#[derive(Clone, Debug)]
pub struct Shadow {
    /// Shadow color (CSS hex format, e.g., "#00000080")
    pub color: String,
    /// Horizontal offset
    pub offset_x: f32,
    /// Vertical offset
    pub offset_y: f32,
    /// Blur radius
    pub blur_radius: f32,
}

impl Shadow {
    pub fn new(color: impl Into<String>, offset_x: f32, offset_y: f32, blur_radius: f32) -> Self {
        Self {
            color: color.into(),
            offset_x,
            offset_y,
            blur_radius,
        }
    }

    /// Create a MaskFilter for the shadow blur effect.
    pub fn make_blur_filter(&self) -> Option<MaskFilter> {
        if self.blur_radius > 0.0 {
            MaskFilter::blur(skia_safe::BlurStyle::Normal, self.blur_radius / 2.0, false)
        } else {
            None
        }
    }
}

/// Drawing style configuration.
#[derive(Clone, Debug)]
pub struct Style {
    // Fill style
    pub fill_color: Option<String>,

    // Stroke style
    pub stroke_color: Option<String>,
    pub stroke_width: f32,

    // Font settings
    pub font_family: Option<String>,
    pub font_size: f32,

    // Border radius for rounded rectangles
    pub border_radius: f32,

    // Drop shadow
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

impl Style {
    pub fn new() -> Self {
        Self::default()
    }

    pub fn with_fill_color(mut self, color: impl Into<String>) -> Self {
        self.fill_color = Some(color.into());
        self
    }

    pub fn with_stroke_color(mut self, color: impl Into<String>) -> Self {
        self.stroke_color = Some(color.into());
        self
    }

    pub fn with_stroke_width(mut self, width: f32) -> Self {
        self.stroke_width = width;
        self
    }

    pub fn with_font_family(mut self, family: impl Into<String>) -> Self {
        self.font_family = Some(family.into());
        self
    }

    pub fn with_font_size(mut self, size: f32) -> Self {
        self.font_size = size;
        self
    }

    pub fn with_border_radius(mut self, radius: f32) -> Self {
        self.border_radius = radius;
        self
    }

    pub fn with_shadow(mut self, shadow: Shadow) -> Self {
        self.shadow = Some(shadow);
        self
    }
}

/// Parse a CSS color string (e.g., "#RRGGBB" or "#RRGGBBAA") to skia Color.
pub fn parse_color(color_str: &str) -> skia_safe::Color {
    let s = color_str.trim_start_matches('#');

    match s.len() {
        6 => {
            // #RRGGBB
            let r = u8::from_str_radix(&s[0..2], 16).unwrap_or(0);
            let g = u8::from_str_radix(&s[2..4], 16).unwrap_or(0);
            let b = u8::from_str_radix(&s[4..6], 16).unwrap_or(0);
            skia_safe::Color::from_rgb(r, g, b)
        }
        8 => {
            // #RRGGBBAA
            let r = u8::from_str_radix(&s[0..2], 16).unwrap_or(0);
            let g = u8::from_str_radix(&s[2..4], 16).unwrap_or(0);
            let b = u8::from_str_radix(&s[4..6], 16).unwrap_or(0);
            let a = u8::from_str_radix(&s[6..8], 16).unwrap_or(255);
            skia_safe::Color::from_argb(a, r, g, b)
        }
        _ => skia_safe::Color::BLACK,
    }
}
