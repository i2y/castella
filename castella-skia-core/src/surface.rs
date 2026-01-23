//! Platform-specific surface management for castella-skia-core.
//!
//! This module provides Surface creation for different platforms:
//! - Desktop (OpenGL)
//! - iOS (Metal)
//! - Android (Vulkan) - TODO

use skia_safe::{ColorType, EncodedImageFormat, Surface as SkiaSurface};
use std::cell::RefCell;
use std::fs::File;
use std::io::Write;

use crate::error::{Error, Result};

// Platform-specific imports for GPU
#[cfg(not(any(target_os = "ios", target_os = "android")))]
use skia_safe::gpu::{self, gl::FramebufferInfo, SurfaceOrigin};

#[cfg(target_os = "ios")]
use skia_safe::gpu::{self, mtl, SurfaceOrigin};

// Thread-local DirectContext cache (Skia GPU contexts are thread-bound)
#[cfg(not(any(target_os = "ios", target_os = "android")))]
thread_local! {
    static GL_CONTEXT: RefCell<Option<gpu::DirectContext>> = const { RefCell::new(None) };
}

/// Load OpenGL function by name using glXGetProcAddress (Linux/WSL2).
/// This is needed because Skia's Interface::new_native() may fail on WSL2
/// where GL symbols aren't exposed via standard dlsym.
#[cfg(target_os = "linux")]
fn load_gl_function(name: &str) -> *const std::ffi::c_void {
    use std::ffi::CString;
    use std::sync::OnceLock;

    // Type for glXGetProcAddress/glXGetProcAddressARB
    type GlXGetProcAddressFn = unsafe extern "C" fn(*const u8) -> *const std::ffi::c_void;

    static GLX_GET_PROC_ADDRESS: OnceLock<Option<GlXGetProcAddressFn>> = OnceLock::new();

    let get_proc_address = GLX_GET_PROC_ADDRESS.get_or_init(|| {
        // Load libGL dynamically
        let lib = unsafe { libc::dlopen(b"libGL.so.1\0".as_ptr() as *const _, libc::RTLD_LAZY | libc::RTLD_GLOBAL) };
        if lib.is_null() {
            return None;
        }

        // Try glXGetProcAddressARB first (more widely available), then glXGetProcAddress
        let proc_addr = unsafe {
            let addr = libc::dlsym(lib, b"glXGetProcAddressARB\0".as_ptr() as *const _);
            if !addr.is_null() {
                addr
            } else {
                libc::dlsym(lib, b"glXGetProcAddress\0".as_ptr() as *const _)
            }
        };

        if proc_addr.is_null() {
            None
        } else {
            Some(unsafe { std::mem::transmute(proc_addr) })
        }
    });

    if let Some(glx_get_proc_address) = get_proc_address {
        let c_name = CString::new(name).unwrap();
        unsafe { glx_get_proc_address(c_name.as_ptr() as *const u8) }
    } else {
        std::ptr::null()
    }
}

// Thread-local Metal DirectContext cache for iOS
#[cfg(target_os = "ios")]
thread_local! {
    static METAL_CONTEXT: RefCell<Option<gpu::DirectContext>> = const { RefCell::new(None) };
}

/// A wrapper around skia_safe::Surface that can be created from different backends.
/// Note: Surface is not Send-safe because Skia GPU resources are tied to the thread.
pub struct Surface {
    pub(crate) inner: SkiaSurface,
    pub(crate) context: Option<gpu::DirectContext>,
    width: i32,
    height: i32,
}

impl Surface {
    // ============ Common Methods (All Platforms) ============

    /// Create a raster (CPU) surface for testing.
    pub fn new_raster(width: i32, height: i32) -> Result<Self> {
        let surface = skia_safe::surfaces::raster_n32_premul((width, height))
            .ok_or(Error::RasterSurfaceError)?;

        Ok(Self {
            inner: surface,
            context: None,
            width,
            height,
        })
    }

    /// Get the width of the surface.
    pub fn width(&self) -> i32 {
        self.width
    }

    /// Get the height of the surface.
    pub fn height(&self) -> i32 {
        self.height
    }

    /// Get the canvas for drawing.
    pub fn canvas(&mut self) -> &skia_safe::Canvas {
        self.inner.canvas()
    }

    /// Flush and submit pending GPU operations.
    pub fn flush_and_submit(&mut self) {
        if let Some(ref mut context) = self.context {
            context.flush_and_submit();
        }
    }

    /// Save the surface to a PNG file.
    /// Useful for debugging and testing.
    pub fn save_png(&mut self, path: &str) -> Result<()> {
        let image = self.inner.image_snapshot();
        let data = image.encode(None, EncodedImageFormat::PNG, None)
            .ok_or(Error::PngEncodeError)?;

        let mut file = File::create(path)
            .map_err(Error::FileCreateError)?;

        file.write_all(data.as_bytes())
            .map_err(Error::FileWriteError)?;

        Ok(())
    }

    /// Get the surface pixel data as RGBA bytes.
    /// This is useful for transferring rendered content to other systems (e.g., UIImageView on iOS).
    ///
    /// Returns a Vec<u8> containing RGBA pixel data in row-major order.
    pub fn get_rgba_data(&mut self) -> Result<Vec<u8>> {
        use skia_safe::{ImageInfo, AlphaType};

        let image_info = ImageInfo::new(
            (self.width, self.height),
            ColorType::RGBA8888,
            AlphaType::Premul,
            None,
        );

        let row_bytes = self.width as usize * 4;  // 4 bytes per pixel (RGBA)
        let total_bytes = row_bytes * self.height as usize;
        let mut pixels = vec![0u8; total_bytes];

        let success = self.inner.read_pixels(
            &image_info,
            &mut pixels,
            row_bytes,
            (0, 0),
        );

        if !success {
            return Err(Error::ReadPixelsError);
        }

        Ok(pixels)
    }

    /// Get the surface pixel data as PNG bytes.
    /// This is more efficient for iOS as CGImage can be created directly from PNG data.
    pub fn get_png_data(&mut self) -> Result<Vec<u8>> {
        let image = self.inner.image_snapshot();
        let data = image.encode(None, EncodedImageFormat::PNG, None)
            .ok_or(Error::PngEncodeError)?;

        Ok(data.as_bytes().to_vec())
    }

    // ============ Desktop (OpenGL) Methods ============

    /// Create a Surface from an OpenGL context.
    ///
    /// This should be called after the OpenGL context is made current.
    /// The DirectContext is cached and reused across surface creations for performance.
    ///
    /// # Arguments
    /// * `width` - Framebuffer width in pixels
    /// * `height` - Framebuffer height in pixels
    /// * `sample_count` - MSAA sample count (0 for no MSAA)
    /// * `stencil_bits` - Stencil buffer bits (typically 0 or 8)
    /// * `framebuffer_id` - OpenGL framebuffer ID (0 for default)
    #[cfg(not(any(target_os = "ios", target_os = "android")))]
    pub fn from_gl_context(
        width: i32,
        height: i32,
        sample_count: usize,
        stencil_bits: usize,
        framebuffer_id: u32,
    ) -> Result<Self> {
        // Get or create the DirectContext (cached for performance)
        let context = GL_CONTEXT.with(|cell| {
            cell.borrow_mut().take()
        });

        let mut context = if let Some(ctx) = context {
            ctx
        } else {
            // Create GPU context from current OpenGL context
            // Try new_native() first, fall back to custom loader for WSL2/Linux compatibility
            let interface = gpu::gl::Interface::new_native()
                .or_else(|| {
                    // On Linux (especially WSL2), new_native() may fail because Skia
                    // can't find GL functions via dlsym. Use glXGetProcAddress instead.
                    #[cfg(target_os = "linux")]
                    {
                        gpu::gl::Interface::new_load_with(|name| {
                            load_gl_function(name)
                        })
                    }
                    #[cfg(not(target_os = "linux"))]
                    {
                        None
                    }
                })
                .ok_or(Error::OpenGLInterfaceError)?;

            gpu::direct_contexts::make_gl(interface, None)
                .ok_or(Error::DirectContextError)?
        };

        // Create backend render target
        let fb_info = FramebufferInfo {
            fboid: framebuffer_id,
            format: gpu::gl::Format::RGBA8.into(),
            ..Default::default()
        };

        let backend_render_target = gpu::backend_render_targets::make_gl(
            (width, height),
            sample_count,
            stencil_bits,
            fb_info,
        );

        // Create surface from backend render target
        let surface = gpu::surfaces::wrap_backend_render_target(
            &mut context,
            &backend_render_target,
            SurfaceOrigin::BottomLeft,
            ColorType::RGBA8888,
            None,
            None,
        )
        .ok_or(Error::SurfaceCreationError)?;

        Ok(Self {
            inner: surface,
            context: Some(context),
            width,
            height,
        })
    }

    /// Resize the surface without recreating the DirectContext.
    /// This is faster and avoids flickering during window resize.
    #[cfg(not(any(target_os = "ios", target_os = "android")))]
    pub fn resize(
        &mut self,
        width: i32,
        height: i32,
        sample_count: usize,
        stencil_bits: usize,
        framebuffer_id: u32,
    ) -> Result<()> {
        // Reuse existing context
        let context = self.context.as_mut()
            .ok_or(Error::NoDirectContext)?;

        // Create backend render target with new size
        let fb_info = FramebufferInfo {
            fboid: framebuffer_id,
            format: gpu::gl::Format::RGBA8.into(),
            ..Default::default()
        };

        let backend_render_target = gpu::backend_render_targets::make_gl(
            (width, height),
            sample_count,
            stencil_bits,
            fb_info,
        );

        // Create new surface from backend render target
        let surface = gpu::surfaces::wrap_backend_render_target(
            context,
            &backend_render_target,
            SurfaceOrigin::BottomLeft,
            ColorType::RGBA8888,
            None,
            None,
        )
        .ok_or(Error::SurfaceCreationError)?;

        self.inner = surface;
        self.width = width;
        self.height = height;

        Ok(())
    }

    // ============ iOS (Metal) Methods ============

    /// Create a Surface from Metal device and command queue pointers.
    ///
    /// This creates a Metal-backed Skia surface for iOS rendering.
    /// The DirectContext is cached and reused across surface creations for performance.
    ///
    /// # Arguments
    /// * `device_ptr` - Raw pointer to MTLDevice (from Rubicon-ObjC)
    /// * `queue_ptr` - Raw pointer to MTLCommandQueue (from Rubicon-ObjC)
    /// * `width` - Surface width in pixels
    /// * `height` - Surface height in pixels
    ///
    /// # Safety
    /// The caller must ensure the device and queue pointers are valid Metal objects.
    #[cfg(target_os = "ios")]
    pub fn from_metal(
        device_ptr: usize,
        queue_ptr: usize,
        width: i32,
        height: i32,
    ) -> Result<Self> {
        // Get or create the DirectContext (cached for performance)
        let context = METAL_CONTEXT.with(|cell| {
            cell.borrow_mut().take()
        });

        let mut context = if let Some(ctx) = context {
            ctx
        } else {
            // Create Skia DirectContext for Metal using the provided device and queue
            let backend = unsafe {
                mtl::BackendContext::new(
                    device_ptr as mtl::Handle,
                    queue_ptr as mtl::Handle,
                )
            };

            gpu::direct_contexts::make_metal(&backend, None)
                .ok_or(Error::MetalContextError)?
        };

        // Create a render target surface
        let image_info = skia_safe::ImageInfo::new(
            (width, height),
            ColorType::BGRA8888,  // Metal prefers BGRA
            skia_safe::AlphaType::Premul,
            None,
        );

        let surface = gpu::surfaces::render_target(
            &mut context,
            skia_safe::Budgeted::Yes,
            &image_info,
            Some(1),  // sample count
            SurfaceOrigin::TopLeft,  // iOS uses top-left origin
            None,
            false,
            None,
        )
        .ok_or(Error::MetalSurfaceError)?;

        Ok(Self {
            inner: surface,
            context: Some(context),
            width,
            height,
        })
    }

    /// Resize the Metal surface without recreating the DirectContext.
    #[cfg(target_os = "ios")]
    pub fn resize_metal(
        &mut self,
        width: i32,
        height: i32,
    ) -> Result<()> {
        // Reuse existing context
        let context = self.context.as_mut()
            .ok_or(Error::NoDirectContext)?;

        let image_info = skia_safe::ImageInfo::new(
            (width, height),
            ColorType::BGRA8888,
            skia_safe::AlphaType::Premul,
            None,
        );

        let surface = gpu::surfaces::render_target(
            context,
            skia_safe::Budgeted::Yes,
            &image_info,
            Some(1),
            SurfaceOrigin::TopLeft,
            None,
            false,
            None,
        )
        .ok_or(Error::MetalSurfaceError)?;

        self.inner = surface;
        self.width = width;
        self.height = height;

        Ok(())
    }

    // ============ Android (Vulkan) Methods - TODO ============

    /// Create a Surface from a Vulkan surface.
    /// This will be implemented when Vulkan backend support is added.
    #[cfg(target_os = "android")]
    pub fn from_vulkan(_surface_ptr: usize, _width: i32, _height: i32) -> Result<Self> {
        Err(Error::VulkanNotImplemented)
    }
}

// ============ Drop Implementation (Platform-Specific) ============

#[cfg(not(any(target_os = "ios", target_os = "android")))]
impl Drop for Surface {
    fn drop(&mut self) {
        // Return the OpenGL context to the cache for reuse
        if let Some(context) = self.context.take() {
            GL_CONTEXT.with(|cell| {
                *cell.borrow_mut() = Some(context);
            });
        }
    }
}

#[cfg(target_os = "ios")]
impl Drop for Surface {
    fn drop(&mut self) {
        // Return the Metal context to the cache for reuse
        if let Some(context) = self.context.take() {
            METAL_CONTEXT.with(|cell| {
                *cell.borrow_mut() = Some(context);
            });
        }
    }
}

#[cfg(target_os = "android")]
impl Drop for Surface {
    fn drop(&mut self) {
        // Android: TODO - will need Vulkan context caching
        // For now, just drop the context
    }
}
