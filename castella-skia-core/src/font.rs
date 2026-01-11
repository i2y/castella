//! Font management for castella-skia-core.

use skia_safe::{Font, FontMgr, FontStyle, GlyphId, Typeface};
use std::collections::HashMap;
use std::sync::Mutex;

use crate::types::FontMetrics;

/// Global typeface cache (thread-safe).
static TYPEFACE_CACHE: Mutex<Option<HashMap<String, Typeface>>> = Mutex::new(None);

/// Cache for emoji typeface (lazily initialized).
static EMOJI_TYPEFACE_CACHE: Mutex<Option<Option<Typeface>>> = Mutex::new(None);

/// Get the default font manager.
pub fn get_font_manager() -> FontMgr {
    FontMgr::default()
}

/// Create a typeface from a font family name.
/// Falls back to the default typeface if the family is not found.
/// Results are cached for performance.
pub fn create_typeface(family: Option<&str>) -> Option<Typeface> {
    let cache_key = family.unwrap_or("__default__").to_string();

    // Check cache first
    {
        let cache = TYPEFACE_CACHE.lock().unwrap();
        if let Some(ref map) = *cache {
            if let Some(typeface) = map.get(&cache_key) {
                return Some(typeface.clone());
            }
        }
    }

    // Not in cache, create typeface
    let typeface = create_typeface_uncached(family);

    // Store in cache
    if let Some(ref tf) = typeface {
        let mut cache = TYPEFACE_CACHE.lock().unwrap();
        if cache.is_none() {
            *cache = Some(HashMap::new());
        }
        if let Some(ref mut map) = *cache {
            map.insert(cache_key, tf.clone());
        }
    }

    typeface
}

/// Create a typeface without caching (internal use).
fn create_typeface_uncached(family: Option<&str>) -> Option<Typeface> {
    let mgr = get_font_manager();

    if let Some(family_name) = family {
        // Try to match the font family
        if let Some(typeface) = mgr.match_family_style(family_name, FontStyle::normal()) {
            return Some(typeface);
        }
    }

    // Fallback: try common system fonts
    let fallback_families = [
        "Noto Sans",
        "Noto Sans CJK JP",
        "Hiragino Sans",
        "Hiragino Kaku Gothic ProN",
        "Yu Gothic",
        "Meiryo",
        "Microsoft YaHei",
        "PingFang SC",
        "SF Pro",
        "Segoe UI",
        "Roboto",
        "Arial",
        "Helvetica",
    ];

    for fallback in fallback_families.iter() {
        if let Some(typeface) = mgr.match_family_style(fallback, FontStyle::normal()) {
            return Some(typeface);
        }
    }

    // Ultimate fallback: use legacy family names
    mgr.legacy_make_typeface(None, FontStyle::normal())
}

/// Create a Font with the given typeface and size.
pub fn create_font(family: Option<&str>, size: f32) -> Font {
    if let Some(typeface) = create_typeface(family) {
        Font::from_typeface(typeface, size)
    } else {
        // Absolute fallback - create font with default size, then set size
        let mut font = Font::default();
        font.set_size(size);
        font
    }
}

/// Get font metrics from a Font.
pub fn get_metrics(font: &Font) -> FontMetrics {
    let (_, metrics) = font.metrics();
    FontMetrics::new(
        metrics.ascent.abs(),
        metrics.descent.abs(),
        metrics.leading,
    )
}

/// Check if a typeface has a glyph for the given character.
pub fn has_glyph(typeface: &Typeface, ch: char) -> bool {
    let glyph_id: GlyphId = typeface.unichar_to_glyph(ch as i32);
    glyph_id != 0
}

/// Find a fallback typeface that can render the given character.
pub fn find_fallback_typeface(ch: char, style: FontStyle) -> Option<Typeface> {
    let mgr = get_font_manager();
    // Use matchFamilyStyleCharacter to find a font that can render this character
    // Empty string means search all system fonts
    mgr.match_family_style_character("", style, &["ja", "en"], ch as i32)
}

/// Check if a character is a color emoji that needs Apple Color Emoji font.
/// Only includes characters that are actually colorful emoji, not general symbols.
#[inline]
fn is_likely_emoji(ch: char) -> bool {
    let cp = ch as u32;
    // Only true color emoji ranges (not symbols that should use text fonts)
    (0x1F300..=0x1F5FF).contains(&cp) ||  // Misc Symbols and Pictographs
    (0x1F600..=0x1F64F).contains(&cp) ||  // Emoticons (faces)
    (0x1F680..=0x1F6FF).contains(&cp) ||  // Transport and Map Symbols
    (0x1F700..=0x1F77F).contains(&cp) ||  // Alchemical Symbols
    (0x1F780..=0x1F7FF).contains(&cp) ||  // Geometric Shapes Extended
    (0x1F800..=0x1F8FF).contains(&cp) ||  // Supplemental Arrows-C
    (0x1F900..=0x1F9FF).contains(&cp) ||  // Supplemental Symbols and Pictographs
    (0x1FA00..=0x1FA6F).contains(&cp) ||  // Chess Symbols
    (0x1FA70..=0x1FAFF).contains(&cp) ||  // Symbols and Pictographs Extended-A
    (0x1F1E0..=0x1F1FF).contains(&cp)     // Regional Indicator Symbols (Flags)
}

/// Get cached emoji typeface, initializing if needed.
fn get_emoji_typeface() -> Option<Typeface> {
    // Check cache first
    {
        let cache = EMOJI_TYPEFACE_CACHE.lock().unwrap();
        if let Some(ref cached) = *cache {
            return cached.clone();
        }
    }

    // Not cached, find emoji font using a common emoji character
    let mgr = get_font_manager();
    let emoji_tf = mgr.match_family_style_character(
        "",
        FontStyle::normal(),
        &["en"],
        '🎉' as i32,
    );

    // Cache the result
    {
        let mut cache = EMOJI_TYPEFACE_CACHE.lock().unwrap();
        *cache = Some(emoji_tf.clone());
    }

    emoji_tf
}

/// A text segment with its typeface.
pub struct TextSegment {
    pub text: String,
    pub typeface: Typeface,
}

/// Debug function to check font fallback for a character.
/// Returns (character, codepoint, has_glyph_in_primary, fallback_family_name)
pub fn debug_font_fallback(ch: char, primary_family: &str) -> (char, u32, bool, String) {
    let mgr = get_font_manager();
    let style = FontStyle::normal();

    let has_glyph_primary = if !primary_family.is_empty() {
        if let Some(primary_tf) = mgr.match_family_style(primary_family, style) {
            has_glyph(&primary_tf, ch)
        } else {
            false
        }
    } else {
        false
    };

    let fallback_name = if let Some(tf) = find_fallback_typeface(ch, style) {
        tf.family_name()
    } else {
        "NONE".to_string()
    };

    (ch, ch as u32, has_glyph_primary, fallback_name)
}

/// Debug function to segment text and show which font each segment uses.
/// Returns Vec<(text_segment, font_family_name)>
pub fn debug_segment_text(text: &str, primary_family: &str) -> Vec<(String, String)> {
    let mgr = get_font_manager();
    let style = FontStyle::normal();

    let primary_typeface = if !primary_family.is_empty() {
        mgr.match_family_style(primary_family, style)
    } else {
        None
    };

    let segments = segment_text_by_font(text, primary_typeface.as_ref(), style);

    segments
        .into_iter()
        .map(|seg| (seg.text, seg.typeface.family_name()))
        .collect()
}

/// Check if text contains any emoji characters.
#[inline]
fn contains_emoji(text: &str) -> bool {
    text.chars().any(is_likely_emoji)
}

/// Segment text by font availability, grouping consecutive characters
/// that can be rendered by the same font.
///
/// Optimized: Only segments if emoji are present. Otherwise returns single segment.
pub fn segment_text_by_font(
    text: &str,
    primary_typeface: Option<&Typeface>,
    _style: FontStyle,
) -> Vec<TextSegment> {
    if text.is_empty() {
        return Vec::new();
    }

    // Fast path: no emoji, return single segment with primary font
    if !contains_emoji(text) {
        let typeface = primary_typeface.cloned()
            .unwrap_or_else(|| get_font_manager().legacy_make_typeface(None, FontStyle::normal()).unwrap());
        return vec![TextSegment {
            text: text.to_string(),
            typeface,
        }];
    }

    // Slow path: has emoji, need to segment
    let emoji_typeface = get_emoji_typeface();
    let default_typeface = primary_typeface.cloned()
        .unwrap_or_else(|| get_font_manager().legacy_make_typeface(None, FontStyle::normal()).unwrap());

    let mut segments: Vec<TextSegment> = Vec::new();
    let mut current_text = String::new();
    let mut current_is_emoji = false;

    for ch in text.chars() {
        let is_emoji = is_likely_emoji(ch);

        if is_emoji != current_is_emoji && !current_text.is_empty() {
            // Type changed, flush current segment
            let typeface = if current_is_emoji {
                emoji_typeface.clone().unwrap_or_else(|| default_typeface.clone())
            } else {
                default_typeface.clone()
            };

            segments.push(TextSegment {
                text: std::mem::take(&mut current_text),
                typeface,
            });
        }

        current_is_emoji = is_emoji;
        current_text.push(ch);
    }

    // Flush remaining segment
    if !current_text.is_empty() {
        let typeface = if current_is_emoji {
            emoji_typeface.clone().unwrap_or_else(|| default_typeface.clone())
        } else {
            default_typeface.clone()
        };

        segments.push(TextSegment {
            text: current_text,
            typeface,
        });
    }

    segments
}
