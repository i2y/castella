//! Error types for castella-skia-core.

use thiserror::Error;

/// Errors that can occur in castella-skia-core.
#[derive(Error, Debug)]
pub enum Error {
    #[error("Failed to create OpenGL interface. Is OpenGL context current?")]
    OpenGLInterfaceError,

    #[error("Failed to create Skia DirectContext")]
    DirectContextError,

    #[error("Failed to create Skia Surface")]
    SurfaceCreationError,

    #[error("Failed to create Metal DirectContext")]
    MetalContextError,

    #[error("Failed to create Metal Surface")]
    MetalSurfaceError,

    #[error("No DirectContext available for resize")]
    NoDirectContext,

    #[error("Failed to create raster surface")]
    RasterSurfaceError,

    #[error("Failed to encode image as PNG")]
    PngEncodeError,

    #[error("Failed to create file: {0}")]
    FileCreateError(std::io::Error),

    #[error("Failed to write file: {0}")]
    FileWriteError(std::io::Error),

    #[error("Failed to read pixels from surface")]
    ReadPixelsError,

    #[error("Failed to read image file '{path}': {source}")]
    ImageReadError {
        path: String,
        source: std::io::Error,
    },

    #[error("Failed to decode image file '{0}'")]
    ImageDecodeError(String),

    #[error("Failed to decode image from bytes")]
    ImageBytesDecodeError,

    #[error("Vulkan backend not yet implemented")]
    VulkanNotImplemented,
}

/// Result type for castella-skia-core operations.
pub type Result<T> = std::result::Result<T, Error>;
