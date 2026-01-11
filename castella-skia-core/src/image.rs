//! Image loading and caching for castella-skia-core.

use skia_safe::{Data, Image};
use std::collections::HashMap;
use std::fs;
use std::sync::Mutex;

use crate::error::{Error, Result};

/// Thread-safe image cache.
static IMAGE_CACHE: Mutex<Option<HashMap<String, Image>>> = Mutex::new(None);

fn get_cache() -> std::sync::MutexGuard<'static, Option<HashMap<String, Image>>> {
    IMAGE_CACHE.lock().unwrap()
}

fn ensure_cache() {
    let mut cache = get_cache();
    if cache.is_none() {
        *cache = Some(HashMap::new());
    }
}

/// Load an image from a file path.
pub fn load_image(path: &str, use_cache: bool) -> Result<Image> {
    ensure_cache();

    // Check cache first
    if use_cache {
        let cache = get_cache();
        if let Some(ref cache_map) = *cache {
            if let Some(img) = cache_map.get(path) {
                return Ok(img.clone());
            }
        }
    }

    // Load from file
    let bytes = fs::read(path)
        .map_err(|e| Error::ImageReadError {
            path: path.to_string(),
            source: e,
        })?;

    let data = Data::new_copy(&bytes);
    let image = Image::from_encoded(data)
        .ok_or_else(|| Error::ImageDecodeError(path.to_string()))?;

    // Store in cache
    if use_cache {
        let mut cache = get_cache();
        if let Some(ref mut cache_map) = *cache {
            cache_map.insert(path.to_string(), image.clone());
        }
    }

    Ok(image)
}

/// Get the size of an image from a file path.
pub fn measure_image(path: &str, use_cache: bool) -> Result<(i32, i32)> {
    let image = load_image(path, use_cache)?;
    Ok((image.width(), image.height()))
}

/// Load an image from bytes.
pub fn load_image_from_bytes(bytes: &[u8]) -> Result<Image> {
    let data = Data::new_copy(bytes);
    Image::from_encoded(data)
        .ok_or(Error::ImageBytesDecodeError)
}

/// Clear the image cache.
pub fn clear_image_cache() {
    let mut cache = get_cache();
    if let Some(ref mut cache_map) = *cache {
        cache_map.clear();
    }
}
