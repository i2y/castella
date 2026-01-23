#!/usr/bin/env python3
"""Debug script for WSL2 OpenGL/Skia issues."""

import sys

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
print("\n[11] Creating Skia Surface from GL context...")
try:
    surface = castella_skia.Surface.from_gl_context(400, 300, 0, 8, 0)
    print(f"    OK (size={surface.width()}x{surface.height()})")
except Exception as e:
    print(f"    FAILED: {e}")
    sdl3.SDL_Quit()
    sys.exit(1)

# Step 12: Test drawing
print("\n[12] Testing Skia drawing...")
try:
    painter = castella_skia.SkiaPainter(surface)
    painter.fill_rect(10, 10, 100, 100, 0xFF0000FF)  # Red rectangle
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
