"""Simple iOS test app using Rubicon-ObjC.

This tests the basic UIKit integration that ios_frame.py will use.
"""

from rubicon.objc import ObjCClass, objc_method

# UIKit classes
UIApplication = ObjCClass("UIApplication")
UIWindow = ObjCClass("UIWindow")
UIViewController = ObjCClass("UIViewController")
UILabel = ObjCClass("UILabel")
UIButton = ObjCClass("UIButton")
UIScreen = ObjCClass("UIScreen")
UIColor = ObjCClass("UIColor")
NSObject = ObjCClass("NSObject")


class PythonAppDelegate(NSObject):
    """iOS App Delegate - named PythonAppDelegate for Briefcase compatibility."""

    @objc_method
    def application_didFinishLaunchingWithOptions_(
        self, application, launchOptions
    ) -> bool:
        """Called when app finishes launching."""
        print("App launched!")

        # Get screen bounds
        screen = UIScreen.mainScreen
        bounds = screen.bounds

        # Create window
        self.window = UIWindow.alloc().initWithFrame_(bounds)

        # Create view controller
        vc = UIViewController.alloc().init()

        # Create a label
        label = UILabel.alloc().initWithFrame_(
            ((50, 100), (bounds.size.width - 100, 50))
        )
        label.text = "Castella iOS Test"
        label.textAlignment = 1  # Center
        label.textColor = UIColor.whiteColor

        # Create counter label
        self.counter_label = UILabel.alloc().initWithFrame_(
            ((50, 200), (bounds.size.width - 100, 100))
        )
        self.counter_label.text = "0"
        self.counter_label.textAlignment = 1
        self.counter_label.font = self.counter_label.font.fontWithSize_(72)
        self.counter_label.textColor = UIColor.whiteColor
        self.counter = 0

        # Create increment button
        button = UIButton.buttonWithType_(1)  # UIButtonTypeSystem
        button.frame = ((50, 350), (bounds.size.width - 100, 50))
        button.setTitle_forState_("Tap to Increment", 0)
        button.addTarget_action_forControlEvents_(
            self, "buttonTapped", 1 << 6  # UIControlEventTouchUpInside
        )

        # Add views
        vc.view.backgroundColor = UIColor.blackColor
        vc.view.addSubview_(label)
        vc.view.addSubview_(self.counter_label)
        vc.view.addSubview_(button)

        # Setup window
        self.window.rootViewController = vc
        self.window.makeKeyAndVisible()

        return True

    @objc_method
    def buttonTapped(self):
        """Handle button tap."""
        self.counter += 1
        self.counter_label.text = str(self.counter)
        print(f"Counter: {self.counter}")


def main():
    """Entry point for the iOS app."""
    print("Starting Castella iOS Test...")
    # Force the class to be registered with the Objective-C runtime
    # by accessing it before Briefcase bootstrap looks for it
    _ = PythonAppDelegate
    print(f"PythonAppDelegate class registered: {PythonAppDelegate}")
    # Note: UIApplicationMain is called by the Briefcase bootstrap
