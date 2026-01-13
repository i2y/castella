"""Castella iOS Test App - Full Castella Framework Test.

This tests the complete Castella framework on iOS:
- Frame Dispatcher automatically selects iOSFrame
- Component model with State for reactivity
- Pydantic models for geometry and events
- castella-skia Metal backend for GPU rendering

Features:
- Counter component with tap interaction
- Full Castella widget tree
- Theme support
- Animation via CADisplayLink
"""

import sys
import locale as _locale_module
import ctypes

# Direct NSLog access for debugging
_foundation = ctypes.CDLL("/System/Library/Frameworks/Foundation.framework/Foundation")
_objc = ctypes.CDLL("/usr/lib/libobjc.A.dylib")

def nslog(msg):
    """Log directly to NSLog."""
    try:
        _objc.objc_getClass.restype = ctypes.c_void_p
        _objc.sel_registerName.restype = ctypes.c_void_p
        _objc.objc_msgSend.restype = ctypes.c_void_p
        _objc.objc_msgSend.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p]

        NSString = _objc.objc_getClass(b"NSString")
        sel = _objc.sel_registerName(b"stringWithUTF8String:")
        ns_str = _objc.objc_msgSend(NSString, sel, msg.encode('utf-8'))

        _foundation.NSLog.argtypes = [ctypes.c_void_p]
        _foundation.NSLog(ns_str)
    except Exception as e:
        print(f"NSLog error: {e}")

nslog("=== Castella iOS Test Starting ===")

# Import std-nslog to redirect stdout/stderr to NSLog
# (std_nslog replaces sys.stdout/stderr on import)
try:
    import std_nslog
    nslog("std_nslog loaded - stdout/stderr redirected to NSLog")
except ImportError as e:
    nslog(f"std_nslog not available: {e}")
except Exception as e:
    nslog(f"std_nslog error: {e}")

# Fix locale issue on iOS by patching the module itself
_original_setlocale = _locale_module.setlocale


def _patched_setlocale(category, locale_str=""):
    """Patched setlocale that handles iOS locale issues."""
    try:
        return _original_setlocale(category, locale_str)
    except _locale_module.Error:
        try:
            return _original_setlocale(category, "C")
        except _locale_module.Error:
            return _original_setlocale(category, None)


_locale_module.setlocale = _patched_setlocale
sys.modules["locale"] = _locale_module

print("=== Castella iOS Test: Full Framework ===")

# Import Rubicon-ObjC for app delegate
from rubicon.objc import ObjCClass, objc_method
NSObject = ObjCClass("NSObject")

# Import Castella framework
print("Importing Castella framework...")
try:
    from castella import App, Component, State, Column, Row, Box, Text, Button, Spacer
    from castella.core import SizePolicy
    from castella.frame import Frame
    from castella.progressbar import ProgressBar, ProgressBarState
    print(f"Castella imported! Frame class: {Frame}")
except ImportError as e:
    print(f"Castella import failed: {e}")
    import traceback
    traceback.print_exc()
    raise

# Store app reference to prevent garbage collection
_app = None
_frame = None


class CounterApp(Component):
    """Counter app with complex UI using Castella Component model."""

    def __init__(self):
        super().__init__()
        self._count = State(0)
        self._count.attach(self)
        # Progress bar state (0-100)
        self._progress = ProgressBarState(value=50, min_val=0, max_val=100)
        print(f"CounterApp initialized with count: {self._count()}")

    def _increment(self, event):
        """Handle increment button tap."""
        print(f"Increment button tapped! Current: {self._count()}")
        self._count += 1
        # Update progress based on count
        self._progress.set(min(100, max(0, 50 + self._count() * 10)))
        print(f"New count: {self._count()}")

    def _decrement(self, event):
        """Handle decrement button tap."""
        print(f"Decrement button tapped! Current: {self._count()}")
        self._count -= 1
        self._progress.set(min(100, max(0, 50 + self._count() * 10)))
        print(f"New count: {self._count()}")

    def _reset(self, event):
        """Handle reset button tap."""
        print("Reset button tapped!")
        self._count.set(0)
        self._progress.set(50)

    def view(self):
        """Build the UI tree."""
        count = self._count()
        print(f"[VIEW] CounterApp.view() called, count={count}")

        # Button row with center positioning
        button_row = Row(
            Spacer(),
            Button("-").on_click(self._decrement).fixed_size(70, 50),
            Spacer().fixed_width(15),
            Button("Reset").on_click(self._reset).fixed_size(90, 50),
            Spacer().fixed_width(15),
            Button("+").on_click(self._increment).fixed_size(70, 50),
            Spacer(),
        ).height(50).height_policy(SizePolicy.FIXED)

        # Progress bar section
        progress_section = Column(
            Row(Spacer(), Text("Progress").font_size(14).text_color("#565F89").fit_content().erase_border(), Spacer())
                .height(20).height_policy(SizePolicy.FIXED),
            Spacer().fixed_height(8),
            ProgressBar(self._progress)
                .track_color("#1a1b26")
                .fill_color("#9ece6a")
                .fixed_height(16),
        ).height(50).height_policy(SizePolicy.FIXED)

        tree = Column(
            Spacer().fixed_height(20),

            # Header
            Row(
                Spacer(),
                Text("Castella iOS").font_size(32).text_color("#FFFFFF").fit_content().erase_border(),
                Spacer(),
            ).height(40).height_policy(SizePolicy.FIXED),

            Spacer().fixed_height(30),

            # Counter display
            Row(
                Spacer(),
                Text(str(count)).font_size(80).text_color("#9ECE6A").fit_content().erase_border(),
                Spacer(),
            ).height(90).height_policy(SizePolicy.FIXED),

            Spacer().fixed_height(30),

            # Button row
            button_row,

            Spacer().fixed_height(40),

            # Progress bar
            progress_section,

            Spacer().fixed_height(30),

            # Info section
            Row(
                Spacer(),
                Text("iOSFrame + Metal + Pydantic").font_size(14).text_color("#7DCFFF").fit_content().erase_border(),
                Spacer(),
            ).height(20).height_policy(SizePolicy.FIXED),

            # Fill remaining space
            Spacer(),
        )
        print(f"[VIEW] Created widget tree: {tree}")
        return tree


class PythonAppDelegate(NSObject):
    """iOS App Delegate for Castella."""

    @objc_method
    def application_didFinishLaunchingWithOptions_(
        self, application, launchOptions
    ) -> bool:
        """Called when app finishes launching."""
        nslog("=" * 50)
        nslog("PythonAppDelegate: Launching Castella App")
        nslog("=" * 50)

        global _app, _frame

        try:
            # Create Frame (iOSFrame will be auto-selected by dispatcher)
            nslog("Creating Frame...")
            _frame = Frame("Castella iOS Test")
            nslog(f"Frame created: {_frame}")

            # Create app with counter component
            nslog("Creating CounterApp component...")
            counter = CounterApp()

            nslog("Creating Castella App...")
            _app = App(_frame, counter)

            # Register all callbacks from App to Frame
            nslog("Registering callbacks...")
            _frame.on_mouse_down(_app.mouse_down)
            _frame.on_mouse_up(_app.mouse_up)
            _frame.on_mouse_wheel(_app.mouse_wheel)
            _frame.on_cursor_pos(_app.cursor_pos)
            _frame.on_input_char(_app.input_char)
            _frame.on_input_key(_app.input_key)
            _frame.on_redraw(_app.redraw)
            nslog("Callbacks registered")

            # Start the frame (initializes Metal, creates window, etc.)
            nslog("Starting frame...")
            _frame.start(application)

            nslog("Castella app started successfully!")
            return True

        except Exception as e:
            nslog(f"Error starting Castella app: {e}")
            import traceback
            traceback.print_exc()
            return False


def main():
    """Entry point for the iOS app."""
    print("=" * 50)
    print("main() called - Castella iOS Full Framework Test")
    print("=" * 50)
    print("Waiting for PythonAppDelegate to be called by iOS...")
