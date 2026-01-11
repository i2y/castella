"""iOS Frame implementation using Rubicon-ObjC and castella-skia Metal.

This module provides the Frame implementation for iOS, using:
- Rubicon-ObjC for UIKit integration
- castella-skia with Metal backend for rendering
- CADisplayLink for vsync-aligned frame updates
- UIGestureRecognizers for touch handling

The current implementation uses an offscreen rendering approach:
1. Render to an offscreen Metal surface via Skia
2. Convert RGBA data to CGImage via CoreGraphics
3. Display via UIImageView

This is simpler to implement and works reliably. A future optimization
could render directly to CAMetalLayer's drawable for better performance.

Requirements:
- iOS 13.0+ (for UIWindowScene)
- castella-skia with Metal backend
- rubicon-objc

Note: This requires pydantic-core to be built for iOS, which is
not yet available. See examples/ios_test_app for a Pydantic-free
test implementation.

Usage:
    This Frame is automatically selected when running on iOS via Briefcase.
    The Frame Dispatcher (castella/frame/__init__.py) handles detection.
"""

from __future__ import annotations

import ctypes
from typing import TYPE_CHECKING, Any, Optional

from castella.frame.base import BaseFrame
from castella.models.geometry import Point, Size
from castella.models.events import (
    InputCharEvent,
    InputKeyEvent,
    KeyAction,
    KeyCode,
    MouseEvent,
    WheelEvent,
)

if TYPE_CHECKING:
    from castella.protocols.painter import BasePainter

# UIKit imports via Rubicon-ObjC
try:
    from rubicon.objc import ObjCClass, objc_method, SEL
    from rubicon.objc.runtime import send_message, objc_id
    from rubicon.objc.api import ObjCInstance
    from rubicon.objc.types import CGRect, CGPoint, CGSize

    # UIKit classes
    UIApplication = ObjCClass("UIApplication")
    UIWindow = ObjCClass("UIWindow")
    UIView = ObjCClass("UIView")
    UIViewController = ObjCClass("UIViewController")
    UIScreen = ObjCClass("UIScreen")
    UIImageView = ObjCClass("UIImageView")
    UIImage = ObjCClass("UIImage")
    UIColor = ObjCClass("UIColor")
    NSObject = ObjCClass("NSObject")
    UIPasteboard = ObjCClass("UIPasteboard")

    # Gesture recognizers
    UITapGestureRecognizer = ObjCClass("UITapGestureRecognizer")
    UIPanGestureRecognizer = ObjCClass("UIPanGestureRecognizer")
    UIPinchGestureRecognizer = ObjCClass("UIPinchGestureRecognizer")

    # Text input
    UITextField = ObjCClass("UITextField")
    NSNotificationCenter = ObjCClass("NSNotificationCenter")

    # QuartzCore / RunLoop
    CADisplayLink = ObjCClass("CADisplayLink")
    NSRunLoop = ObjCClass("NSRunLoop")

    _RUBICON_AVAILABLE = True
except ImportError:
    _RUBICON_AVAILABLE = False

# castella-skia import
try:
    import castella_skia
    from castella import rust_skia_painter as painter_module

    _CASTELLA_SKIA_AVAILABLE = True
except ImportError:
    _CASTELLA_SKIA_AVAILABLE = False

# CoreGraphics constants
_kCGImageAlphaPremultipliedLast = 1
_kCGBitmapByteOrder32Big = 4 << 12


class iOSFrame(BaseFrame):
    """iOS Frame using Metal backend via castella-skia.

    This Frame implementation integrates with iOS UIKit via Rubicon-ObjC
    and uses castella-skia's Metal backend for GPU-accelerated rendering.

    The current implementation uses offscreen rendering:
    1. Skia renders to an offscreen Metal texture
    2. Pixel data is converted to CGImage via CoreGraphics
    3. UIImageView displays the result

    Touch events are translated to Castella MouseEvent format:
    - UITapGestureRecognizer -> mouse_down + mouse_up
    - UIPanGestureRecognizer -> mouse_down, cursor_pos (drag), mouse_up
    - UIPinchGestureRecognizer -> wheel_event (for zoom)

    Features:
    - CADisplayLink for vsync-aligned 60fps updates
    - UIWindowScene support (iOS 13+)
    - Clipboard via UIPasteboard
    """

    # Class-level state to prevent garbage collection
    _instance: Optional["iOSFrame"] = None
    _gesture_handlers: list = []
    _display_link_handler: Any = None
    _display_link: Any = None
    _keyboard_input_view: Any = None
    _hidden_text_field: Any = None
    _text_field_delegate: Any = None
    _current_text: str = ""  # Track current text for change detection

    def __init__(
        self, title: str = "Castella", width: float = 0, height: float = 0
    ) -> None:
        """Initialize the iOS Frame.

        Args:
            title: Window title (used for accessibility)
            width: Ignored on iOS - uses screen width
            height: Ignored on iOS - uses screen height
        """
        if not _RUBICON_AVAILABLE:
            raise RuntimeError(
                "Rubicon-ObjC is required for iOS support. "
                "Install with: pip install rubicon-objc"
            )
        if not _CASTELLA_SKIA_AVAILABLE:
            raise RuntimeError(
                "castella-skia is required for iOS support. "
                "Ensure castella-skia wheel is installed for iOS target."
            )

        # iOS uses full screen size in POINTS (not pixels)
        screen = UIScreen.mainScreen
        bounds = screen.bounds
        self._scale: float = screen.scale
        self._point_width: float = bounds.size.width
        self._point_height: float = bounds.size.height

        # Use POINT dimensions for frame size so layout matches screen coordinates
        super().__init__(title, int(self._point_width), int(self._point_height))

        self._window: Any = None
        self._main_view: Any = None
        self._image_view: Any = None
        self._metal_device: Any = None
        self._metal_queue: Any = None

        # Rendering state
        self._surface: Any = None
        self._painter: Any = None
        self._needs_redraw: bool = True
        self._rgba_buffer: Any = None  # Keep reference to prevent GC

        # CoreGraphics framework
        self._cg = ctypes.CDLL(
            "/System/Library/Frameworks/CoreGraphics.framework/CoreGraphics"
        )
        self._setup_cg_functions()

        # Touch state
        self._is_dragging: bool = False
        self._last_touch_pos: Point = Point(x=0, y=0)

        # Safe area insets (populated in _setup_window)
        self._safe_area_top: float = 0.0
        self._safe_area_bottom: float = 0.0
        self._safe_area_left: float = 0.0
        self._safe_area_right: float = 0.0
        self._safe_width: float = self._point_width
        self._safe_height: float = self._point_height

        # Store instance reference for gesture handlers
        iOSFrame._instance = self

    def _setup_cg_functions(self) -> None:
        """Set up CoreGraphics function signatures for RGBA to CGImage conversion."""
        cg = self._cg

        cg.CGDataProviderCreateWithData.argtypes = [
            ctypes.c_void_p,
            ctypes.c_void_p,
            ctypes.c_size_t,
            ctypes.c_void_p,
        ]
        cg.CGDataProviderCreateWithData.restype = ctypes.c_void_p

        cg.CGColorSpaceCreateDeviceRGB.argtypes = []
        cg.CGColorSpaceCreateDeviceRGB.restype = ctypes.c_void_p

        cg.CGImageCreate.argtypes = [
            ctypes.c_size_t,
            ctypes.c_size_t,
            ctypes.c_size_t,
            ctypes.c_size_t,
            ctypes.c_size_t,
            ctypes.c_void_p,
            ctypes.c_uint32,
            ctypes.c_void_p,
            ctypes.c_void_p,
            ctypes.c_bool,
            ctypes.c_int,
        ]
        cg.CGImageCreate.restype = ctypes.c_void_p

        cg.CGDataProviderRelease.argtypes = [ctypes.c_void_p]
        cg.CGDataProviderRelease.restype = None

        cg.CGColorSpaceRelease.argtypes = [ctypes.c_void_p]
        cg.CGColorSpaceRelease.restype = None

        cg.CGImageRelease.argtypes = [ctypes.c_void_p]
        cg.CGImageRelease.restype = None

    def _setup_window(self, application: Any = None) -> None:
        """Create UIWindow and view hierarchy.

        Args:
            application: UIApplication instance (optional, for UIWindowScene)
        """
        screen = UIScreen.mainScreen
        bounds = screen.bounds

        # Get UIWindowScene (iOS 13+)
        window_scene = None
        if application is not None:
            try:
                scenes = application.connectedScenes
                if scenes:
                    # NSSet - use anyObject() to get first item
                    scene = scenes.anyObject()
                    if scene and "UIWindowScene" in str(scene.objc_class.name):
                        window_scene = scene
            except Exception:
                pass

        # Create window
        if window_scene:
            self._window = UIWindow.alloc().initWithWindowScene_(window_scene)
        else:
            self._window = UIWindow.alloc().initWithFrame_(bounds)

        # Create main view (full screen)
        self._main_view = UIView.alloc().initWithFrame_(bounds)
        self._main_view.backgroundColor = UIColor.blackColor

        # Setup view controller and window first to get safe area insets
        vc = UIViewController.alloc().init()
        vc.view = self._main_view
        self._window.rootViewController = vc
        self._window.makeKeyAndVisible()

        # Get safe area insets from the window (iOS 11+)
        # Need to access after makeKeyAndVisible for correct values
        try:
            insets = self._window.safeAreaInsets
            self._safe_area_top = insets.top
            self._safe_area_bottom = insets.bottom
            self._safe_area_left = insets.left
            self._safe_area_right = insets.right
        except Exception:
            # Fallback: assume status bar height of 20pt
            self._safe_area_top = 20.0
            self._safe_area_bottom = 0.0
            self._safe_area_left = 0.0
            self._safe_area_right = 0.0

        # Calculate safe area frame
        safe_x = self._safe_area_left
        safe_y = self._safe_area_top
        safe_width = bounds.size.width - self._safe_area_left - self._safe_area_right
        safe_height = bounds.size.height - self._safe_area_top - self._safe_area_bottom

        # Create UIImageView for Skia rendering output (within safe area)
        safe_frame = CGRect(CGPoint(safe_x, safe_y), CGSize(safe_width, safe_height))
        self._image_view = UIImageView.alloc().initWithFrame_(safe_frame)
        self._image_view.contentMode = 1  # UIViewContentModeScaleAspectFit
        self._image_view.backgroundColor = UIColor.blackColor
        self._image_view.userInteractionEnabled = True  # Required for gestures
        self._main_view.addSubview_(self._image_view)

        # Store safe area dimensions for surface creation
        self._safe_width = safe_width
        self._safe_height = safe_height

        # Setup gesture recognizers
        self._setup_gesture_recognizers()

        # Setup keyboard input view (for text input)
        self._setup_keyboard_input_view()

    def _setup_gesture_recognizers(self) -> None:
        """Set up touch gesture recognizers on the image view."""
        # Clear previous handlers
        iOSFrame._gesture_handlers = []

        # Tap recognizer
        tap_handler = _create_tap_handler_class().alloc().init()
        iOSFrame._gesture_handlers.append(tap_handler)
        tap_recognizer = UITapGestureRecognizer.alloc().initWithTarget_action_(
            tap_handler, SEL("handleTap:")
        )
        self._image_view.addGestureRecognizer_(tap_recognizer)

        # Pan recognizer (for drag events)
        pan_handler = _create_pan_handler_class().alloc().init()
        iOSFrame._gesture_handlers.append(pan_handler)
        pan_recognizer = UIPanGestureRecognizer.alloc().initWithTarget_action_(
            pan_handler, SEL("handlePan:")
        )
        self._image_view.addGestureRecognizer_(pan_recognizer)

        # Pinch recognizer (for wheel/zoom events)
        pinch_handler = _create_pinch_handler_class().alloc().init()
        iOSFrame._gesture_handlers.append(pinch_handler)
        pinch_recognizer = UIPinchGestureRecognizer.alloc().initWithTarget_action_(
            pinch_handler, SEL("handlePinch:")
        )
        self._image_view.addGestureRecognizer_(pinch_recognizer)

    def _setup_keyboard_input_view(self) -> None:
        """Set up hidden UITextField for keyboard input with full IME support.

        UITextField provides complete IME (Input Method Editor) support for
        Japanese, Chinese, Korean, and other languages that require composition.
        """
        # Create hidden UITextField
        text_field = UITextField.alloc().initWithFrame_(
            CGRect(CGPoint(0, 0), CGSize(1, 1))
        )
        text_field.backgroundColor = UIColor.clearColor
        text_field.alpha = 0.0  # Invisible
        text_field.autocorrectionType = 1  # UITextAutocorrectionTypeNo
        text_field.autocapitalizationType = 0  # UITextAutocapitalizationTypeNone

        # Add to view hierarchy
        self._main_view.addSubview_(text_field)

        # Set up text change notification observer
        TextFieldObserverClass = _create_text_field_observer_class()
        observer = TextFieldObserverClass.alloc().init()

        # Register for text change notifications
        notification_center = NSNotificationCenter.defaultCenter
        notification_center.addObserver_selector_name_object_(
            observer,
            SEL("textFieldDidChange:"),
            "UITextFieldTextDidChangeNotification",
            text_field,
        )

        # Store references to prevent garbage collection
        iOSFrame._hidden_text_field = text_field
        iOSFrame._text_field_delegate = observer
        iOSFrame._current_text = ""

        # Also keep the UIKeyInput view as fallback
        KeyboardInputViewClass = _create_keyboard_input_view_class()
        keyboard_view = KeyboardInputViewClass.alloc().initWithFrame_(
            CGRect(CGPoint(0, 0), CGSize(1, 1))
        )
        keyboard_view.backgroundColor = UIColor.clearColor
        keyboard_view.alpha = 0.0
        self._main_view.addSubview_(keyboard_view)
        iOSFrame._keyboard_input_view = keyboard_view

    def show_keyboard(self, initial_text: str = "") -> None:
        """Show the iOS keyboard for text input.

        Args:
            initial_text: Initial text to populate the hidden text field with.
                         This should match the current text in the Castella Input.
        """
        if iOSFrame._hidden_text_field:
            # Set initial text and track it
            iOSFrame._hidden_text_field.text = initial_text
            iOSFrame._current_text = initial_text
            iOSFrame._hidden_text_field.becomeFirstResponder()

    def hide_keyboard(self) -> None:
        """Hide the iOS keyboard."""
        if iOSFrame._hidden_text_field:
            iOSFrame._hidden_text_field.resignFirstResponder()

    def _handle_text_field_change(self, new_text: str) -> None:
        """Handle text changes from UITextField - compute diff and forward to Castella.

        This method computes the difference between the old and new text,
        then sends appropriate input events to Castella.
        """
        old_text = iOSFrame._current_text
        iOSFrame._current_text = new_text

        # Simple diff: find common prefix and suffix
        # Then determine what was deleted and what was inserted
        if new_text == old_text:
            return

        # Find common prefix length
        prefix_len = 0
        min_len = min(len(old_text), len(new_text))
        while prefix_len < min_len and old_text[prefix_len] == new_text[prefix_len]:
            prefix_len += 1

        # Find common suffix length (from the end, but not overlapping with prefix)
        suffix_len = 0
        while (
            suffix_len < min_len - prefix_len
            and old_text[-(suffix_len + 1)] == new_text[-(suffix_len + 1)]
        ):
            suffix_len += 1

        # Characters deleted from old_text
        deleted_count = len(old_text) - prefix_len - suffix_len
        # Characters inserted in new_text
        if suffix_len > 0:
            inserted_text = new_text[prefix_len:-suffix_len]
        else:
            inserted_text = new_text[prefix_len:]

        # Send backspace events for deleted characters
        for _ in range(deleted_count):
            self._callback_on_input_key(
                InputKeyEvent(
                    key=KeyCode.BACKSPACE,
                    action=KeyAction.PRESS,
                    scancode=0,
                    mods=0,
                )
            )

        # Send character events for inserted text
        for char in inserted_text:
            if char == "\n":
                self._callback_on_input_key(
                    InputKeyEvent(
                        key=KeyCode.ENTER,
                        action=KeyAction.PRESS,
                        scancode=0,
                        mods=0,
                    )
                )
            else:
                self._callback_on_input_char(InputCharEvent(char=char))

        self._needs_redraw = True

    def _handle_text_input(self, text: str) -> None:
        """Handle text input from keyboard - forward to Castella."""
        for char in text:
            self._callback_on_input_char(InputCharEvent(char=char))
        self._needs_redraw = True

    def _handle_backspace(self) -> None:
        """Handle backspace key - forward to Castella."""
        self._callback_on_input_key(
            InputKeyEvent(
                key=KeyCode.BACKSPACE,
                action=KeyAction.PRESS,
                scancode=0,
                mods=0,
            )
        )
        self._needs_redraw = True

    def _handle_return_key(self) -> None:
        """Handle return/enter key - forward to Castella."""
        self._callback_on_input_key(
            InputKeyEvent(
                key=KeyCode.ENTER,
                action=KeyAction.PRESS,
                scancode=0,
                mods=0,
            )
        )
        self._needs_redraw = True

    def _setup_metal(self) -> None:
        """Initialize Metal device and command queue."""
        metal = ctypes.CDLL("/System/Library/Frameworks/Metal.framework/Metal")
        metal.MTLCreateSystemDefaultDevice.restype = ctypes.c_void_p

        device_ptr = metal.MTLCreateSystemDefaultDevice()
        if not device_ptr or device_ptr == 0:
            raise RuntimeError("Failed to create Metal device")

        self._metal_device = ObjCInstance(device_ptr)
        self._metal_queue = self._metal_device.newCommandQueue()

    def _update_surface_and_painter(self) -> None:
        """Create/recreate the Skia surface for the current size."""
        if self._metal_device is None:
            self._setup_metal()

        device_ptr = self._metal_device.ptr.value
        queue_ptr = self._metal_queue.ptr.value

        # Create Skia surface with Metal backend (use safe area dimensions)
        self._surface = castella_skia.Surface.from_metal(
            device_ptr, queue_ptr, int(self._safe_width), int(self._safe_height)
        )
        self._painter = painter_module.Painter(self, self._surface)

        # Update frame size to match safe area
        self._width = int(self._safe_width)
        self._height = int(self._safe_height)

    def _setup_display_link(self) -> None:
        """Set up CADisplayLink for vsync-aligned 60fps rendering."""
        handler = _create_display_link_handler_class().alloc().init()
        iOSFrame._display_link_handler = handler

        display_link = CADisplayLink.displayLinkWithTarget_selector_(
            handler, SEL("onDisplayLink:")
        )
        iOSFrame._display_link = display_link

        # Add to main run loop with default mode
        # Note: kCFRunLoopDefaultMode works; kCFRunLoopCommonModes doesn't work
        # with rubicon-objc on iOS. Using default mode is sufficient for our use.
        main_run_loop = NSRunLoop.mainRunLoop
        display_link.addToRunLoop_forMode_(main_run_loop, "kCFRunLoopDefaultMode")

    def _render_to_image_view(self) -> None:
        """Convert Skia surface RGBA data to UIImage and display."""
        if self._surface is None or self._image_view is None:
            return

        try:
            # Get RGBA data from surface
            rgba_data = self._surface.get_rgba_data()
            width = self._surface.width
            height = self._surface.height

            # Create data buffer
            rgba_bytes = bytes(rgba_data)
            data_buffer = (ctypes.c_char * len(rgba_bytes)).from_buffer_copy(rgba_bytes)
            self._rgba_buffer = data_buffer  # Keep reference to prevent GC

            # Create CGImage via CoreGraphics
            cg = self._cg
            provider = cg.CGDataProviderCreateWithData(
                None, ctypes.addressof(data_buffer), len(rgba_bytes), None
            )
            color_space = cg.CGColorSpaceCreateDeviceRGB()
            bitmap_info = _kCGImageAlphaPremultipliedLast | _kCGBitmapByteOrder32Big

            cg_image = cg.CGImageCreate(
                width,
                height,
                8,
                32,
                width * 4,
                color_space,
                bitmap_info,
                provider,
                None,
                False,
                0,
            )

            if cg_image:
                # Create UIImage from CGImage
                cg_image_ref = ctypes.cast(cg_image, objc_id)
                image = send_message(
                    UIImage,
                    "imageWithCGImage:",
                    cg_image_ref,
                    restype=objc_id,
                    argtypes=[ctypes.c_void_p],
                )
                if image:
                    self._image_view.image = ObjCInstance(image)

                cg.CGImageRelease(cg_image)

            cg.CGDataProviderRelease(provider)
            cg.CGColorSpaceRelease(color_space)

        except Exception as e:
            print(f"Warning: Failed to render to image view: {e}")

    def _signal_main_thread(self) -> None:
        """Signal main thread that an update is pending."""
        self._needs_redraw = True
        # CADisplayLink will handle the redraw on the next frame

    def _handle_display_link(self) -> None:
        """Called on each display refresh by CADisplayLink."""
        # Process pending updates from background threads
        self._process_pending_updates()

        # Render if needed
        if self._needs_redraw:
            self._needs_redraw = False
            self._callback_on_redraw(self._painter, True)  # force=True to ensure redraw
            self.flush()
            self._render_to_image_view()

    # ========== Touch Event Handlers ==========

    def _handle_tap(self, x: float, y: float) -> None:
        """Handle tap gesture -> mouse down + up."""
        pos = Point(x=x, y=y)
        self._callback_on_mouse_down(MouseEvent(pos=pos))
        self._callback_on_mouse_up(MouseEvent(pos=pos))
        self._needs_redraw = True

    def _handle_pan_began(self, x: float, y: float) -> None:
        """Handle pan began -> mouse down."""
        self._is_dragging = True
        self._last_touch_pos = Point(x=x, y=y)
        self._callback_on_mouse_down(MouseEvent(pos=self._last_touch_pos))
        self._needs_redraw = True

    def _handle_pan_changed(self, x: float, y: float) -> None:
        """Handle pan changed -> cursor pos (drag)."""
        pos = Point(x=x, y=y)
        self._last_touch_pos = pos
        self._callback_on_cursor_pos(MouseEvent(pos=pos))
        self._needs_redraw = True

    def _handle_pan_ended(self, x: float, y: float) -> None:
        """Handle pan ended -> mouse up."""
        self._is_dragging = False
        pos = Point(x=x, y=y)
        self._callback_on_mouse_up(MouseEvent(pos=pos))
        self._needs_redraw = True

    def _handle_pinch(self, scale: float, x: float, y: float) -> None:
        """Handle pinch gesture -> wheel event."""
        # Convert pinch scale to wheel delta
        delta = (scale - 1.0) * 100
        self._callback_on_mouse_wheel(
            WheelEvent(pos=Point(x=x, y=y), x_offset=0, y_offset=delta)
        )
        self._needs_redraw = True

    # ========== Abstract Method Implementations ==========

    def get_painter(self) -> "BasePainter":
        """Get the painter for this frame."""
        return self._painter

    def get_size(self) -> Size:
        """Get the current frame size (in points)."""
        return self._size

    def flush(self) -> None:
        """Flush pending drawing operations to screen."""
        if self._painter:
            self._painter.flush()
        if self._surface:
            self._surface.flush_and_submit()

    def clear(self) -> None:
        """Clear the frame."""
        if self._painter:
            self._painter.clear_all()

    def run(self) -> None:
        """Start the iOS application.

        Note: On iOS, the app lifecycle is managed by UIKit. This method
        sets up the UI but doesn't start a run loop - that's handled by
        UIApplicationMain via Briefcase.

        For proper iOS integration, call start() from your app delegate's
        application:didFinishLaunchingWithOptions: method.
        """
        # Get the shared application
        app = UIApplication.sharedApplication
        self.start(app)

    def start(self, application: Any) -> None:
        """Initialize the frame after app launch.

        This should be called from the app delegate's
        application:didFinishLaunchingWithOptions: method.

        Args:
            application: The UIApplication instance
        """
        # Setup UI
        self._setup_window(application)
        self._update_surface_and_painter()

        # Initial draw BEFORE starting display link
        self._needs_redraw = False
        self._callback_on_redraw(self._painter, True)
        self.flush()
        self._render_to_image_view()

        # Start display link AFTER initial draw
        self._setup_display_link()

    # ========== Clipboard ==========

    def get_clipboard_text(self) -> str:
        """Get text from iOS clipboard."""
        try:
            pasteboard = UIPasteboard.generalPasteboard
            text = pasteboard.string
            return str(text) if text else ""
        except Exception:
            raise NotImplementedError("Clipboard not available on this iOS version")

    def set_clipboard_text(self, text: str) -> None:
        """Set text to iOS clipboard."""
        try:
            pasteboard = UIPasteboard.generalPasteboard
            pasteboard.string = text
        except Exception:
            raise NotImplementedError("Clipboard not available on this iOS version")


# ========== Gesture Handler Class Factories ==========


def _create_tap_handler_class():
    """Create a tap gesture handler class."""

    class TapHandler(NSObject):
        @objc_method
        def handleTap_(self, gesture_recognizer) -> None:
            frame = iOSFrame._instance
            if frame:
                view = gesture_recognizer.view
                location = gesture_recognizer.locationInView_(view)
                frame._handle_tap(location.x, location.y)

    return TapHandler


def _create_pan_handler_class():
    """Create a pan gesture handler class."""

    class PanHandler(NSObject):
        @objc_method
        def handlePan_(self, gesture_recognizer) -> None:
            frame = iOSFrame._instance
            if not frame:
                return

            view = gesture_recognizer.view
            location = gesture_recognizer.locationInView_(view)
            state = gesture_recognizer.state

            # UIGestureRecognizerState: 1=Began, 2=Changed, 3=Ended, 4=Cancelled
            if state == 1:
                frame._handle_pan_began(location.x, location.y)
            elif state == 2:
                frame._handle_pan_changed(location.x, location.y)
            elif state in (3, 4):
                frame._handle_pan_ended(location.x, location.y)

    return PanHandler


def _create_pinch_handler_class():
    """Create a pinch gesture handler class."""

    class PinchHandler(NSObject):
        @objc_method
        def handlePinch_(self, gesture_recognizer) -> None:
            frame = iOSFrame._instance
            if not frame:
                return

            view = gesture_recognizer.view
            location = gesture_recognizer.locationInView_(view)
            scale = gesture_recognizer.scale

            # Only handle the change state
            if gesture_recognizer.state == 2:  # Changed
                frame._handle_pinch(scale, location.x, location.y)
                # Reset scale to get delta changes
                gesture_recognizer.scale = 1.0

    return PinchHandler


def _create_display_link_handler_class():
    """Create a CADisplayLink handler class."""

    class DisplayLinkHandler(NSObject):
        @objc_method
        def onDisplayLink_(self, display_link) -> None:
            frame = iOSFrame._instance
            if frame:
                frame._handle_display_link()

    return DisplayLinkHandler


def _create_text_field_observer_class():
    """Create an observer class for UITextField text change notifications.

    This class observes UITextFieldTextDidChangeNotification and forwards
    text changes to the iOSFrame for processing.
    """

    class TextFieldObserver(NSObject):
        @objc_method
        def textFieldDidChange_(self, notification) -> None:
            """Called when the UITextField's text changes."""
            frame = iOSFrame._instance
            if frame:
                # Get the text field from the notification
                text_field = notification.object
                if text_field:
                    # Get current text (may be None)
                    text = text_field.text
                    new_text = str(text) if text else ""
                    frame._handle_text_field_change(new_text)

    return TextFieldObserver


def _create_keyboard_input_view_class():
    """Create a UIView subclass that implements UIKeyInput protocol for keyboard input.

    UIKeyInput is a protocol that allows a view to receive keyboard input.
    The key methods are:
    - insertText: called when characters are typed
    - deleteBackward: called when backspace is pressed
    - hasText: property indicating if there's text (always returns True for us)

    rubicon-objc requires explicit protocol declaration via protocols=[...].
    See: https://rubicon-objc.readthedocs.io/en/stable/topics/protocols.html
    """
    from rubicon.objc import ObjCProtocol

    # Get the UIKeyInput protocol
    UIKeyInput = ObjCProtocol("UIKeyInput")

    class KeyboardInputView(UIView, protocols=[UIKeyInput]):
        # UIKeyInput protocol implementation

        @objc_method
        def canBecomeFirstResponder(self) -> bool:
            """Allow this view to become first responder (show keyboard)."""
            return True

        @objc_method
        def hasText(self) -> bool:
            """UIKeyInput protocol: indicate if there's text.

            We always return True so backspace is always forwarded.
            """
            return True

        @objc_method
        def insertText_(self, text) -> None:
            """UIKeyInput protocol: handle character insertion."""
            frame = iOSFrame._instance
            if frame:
                # Convert ObjC NSString to Python string
                text_str = str(text)

                # Check for return key (sent as newline character)
                if text_str == "\n":
                    frame._handle_return_key()
                else:
                    frame._handle_text_input(text_str)

        @objc_method
        def deleteBackward(self) -> None:
            """UIKeyInput protocol: handle backspace."""
            frame = iOSFrame._instance
            if frame:
                frame._handle_backspace()

    return KeyboardInputView


# Alias for Frame Dispatcher compatibility
Frame = iOSFrame
