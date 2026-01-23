#!/usr/bin/env python3
"""Debug script for WSL2 OpenGL/Skia issues."""

import sys
import faulthandler

# Enable faulthandler to print stack trace on segfault
faulthandler.enable()

print("=== WSL2 OpenGL Debug ===")
print(f"Python: {sys.version}")

# Step 1: SDL3 import
print("\n[1] Importing SDL3...")
try:
    import sdl3
    print("    OK")
except ImportError as e:
    print(f"    FAILED: {e}")
    sys.exit(1)

# Step 2: castella_skia import
print("\n[2] Importing castella_skia...")
try:
    import castella_skia
    print("    OK")
except ImportError as e:
    print(f"    FAILED: {e}")
    sys.exit(1)

# Step 3: PyOpenGL import
print("\n[3] Importing PyOpenGL...")
try:
    from OpenGL import GL
    print("    OK")
except ImportError as e:
    print(f"    FAILED: {e}")

# Step 4: SDL init
print("\n[4] SDL_Init...")
from ctypes import byref, c_int

if not sdl3.SDL_Init(sdl3.SDL_INIT_VIDEO):
    print(f"    FAILED: {sdl3.SDL_GetError().decode()}")
    sys.exit(1)
print("    OK")

# Step 5: Load GL library
print("\n[5] SDL_GL_LoadLibrary...")
if not sdl3.SDL_GL_LoadLibrary(None):
    print(f"    FAILED: {sdl3.SDL_GetError().decode()}")
    sys.exit(1)
print("    OK")

# Step 6: Set GL attributes
print("\n[6] Setting GL attributes...")
sdl3.SDL_GL_SetAttribute(sdl3.SDL_GL_CONTEXT_MAJOR_VERSION, 3)
sdl3.SDL_GL_SetAttribute(sdl3.SDL_GL_CONTEXT_MINOR_VERSION, 2)
sdl3.SDL_GL_SetAttribute(sdl3.SDL_GL_CONTEXT_PROFILE_MASK, sdl3.SDL_GL_CONTEXT_PROFILE_CORE)
sdl3.SDL_GL_SetAttribute(sdl3.SDL_GL_STENCIL_SIZE, 8)
print("    OK")

# Step 7: Create window
print("\n[7] Creating window...")
window = sdl3.SDL_CreateWindow(b"Debug Test", 400, 300, sdl3.SDL_WINDOW_OPENGL)
if not window:
    print(f"    FAILED: {sdl3.SDL_GetError().decode()}")
    sys.exit(1)
print(f"    OK (window={window})")

# Step 8: Create GL context
print("\n[8] Creating GL context...")
gl_ctx = sdl3.SDL_GL_CreateContext(window)
if not gl_ctx:
    print(f"    FAILED: {sdl3.SDL_GetError().decode()}")
    sys.exit(1)
print(f"    OK (context={gl_ctx})")

# Step 9: Make current
print("\n[9] Making GL context current...")
if not sdl3.SDL_GL_MakeCurrent(window, gl_ctx):
    print(f"    FAILED: {sdl3.SDL_GetError().decode()}")
    sys.exit(1)
print("    OK")

# Step 10: Check OpenGL info via PyOpenGL
print("\n[10] OpenGL info (via PyOpenGL)...")
try:
    from OpenGL import GL
    vendor = GL.glGetString(GL.GL_VENDOR)
    renderer = GL.glGetString(GL.GL_RENDERER)
    version = GL.glGetString(GL.GL_VERSION)
    print(f"    Vendor: {vendor.decode() if vendor else 'N/A'}")
    print(f"    Renderer: {renderer.decode() if renderer else 'N/A'}")
    print(f"    Version: {version.decode() if version else 'N/A'}")
except Exception as e:
    print(f"    FAILED: {e}")

# Step 11: Create Skia surface
print("\n[11] Creating Skia Surface from GL context...", flush=True)
try:
    print("    Calling from_gl_context...", flush=True)
    surface = castella_skia.Surface.from_gl_context(400, 300, 0, 8, 0)
    print("    Surface object created", flush=True)
    w = surface.width()
    print(f"    width={w}", flush=True)
    h = surface.height()
    print(f"    height={h}", flush=True)
    print(f"    OK (size={w}x{h})", flush=True)
except Exception as e:
    print(f"    FAILED: {e}", flush=True)
    sdl3.SDL_Quit()
    sys.exit(1)

# Step 11.5: Immediately test flush
print("\n[11.5] Testing immediate flush_and_submit...", flush=True)
try:
    surface.flush_and_submit()
    print("    OK", flush=True)
except Exception as e:
    print(f"    FAILED: {e}", flush=True)

# Step 12: Test drawing
print("\n[12] Testing Skia drawing...")
try:
    # SkiaPainter requires Py<Surface>, so we use the surface directly
    # Just test that we can access the canvas
    print("    Skipping direct draw test (API requires Python binding context)")
    print("    Testing flush_and_submit instead...")
    surface.flush_and_submit()
    print("    OK")
except Exception as e:
    print(f"    FAILED: {e}")

# Step 13: GL flush
print("\n[13] GL flush...")
try:
    GL.glFlush()
    print("    OK")
except Exception as e:
    print(f"    FAILED: {e}")

# Cleanup
print("\n[14] Cleanup...")
sdl3.SDL_Quit()
print("    OK")

print("\n=== Debug Complete ===")
