"""Castella iOS Charts Demo App.

Showcases various chart widgets on iOS:
- BarChart
- LineChart
- PieChart
- GaugeChart
- AreaChart
- ScatterChart
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


nslog("=== Castella Charts Demo Starting ===")

# Fix locale issue on iOS
_original_setlocale = _locale_module.setlocale


def _patched_setlocale(category, locale_str=""):
    try:
        return _original_setlocale(category, locale_str)
    except _locale_module.Error:
        try:
            return _original_setlocale(category, "C")
        except _locale_module.Error:
            return _original_setlocale(category, None)


_locale_module.setlocale = _patched_setlocale
sys.modules["locale"] = _locale_module

print("=== Castella Charts Demo ===")

# Import Rubicon-ObjC for app delegate
from rubicon.objc import ObjCClass, objc_method
NSObject = ObjCClass("NSObject")

# Import Castella framework
print("Importing Castella framework...")
try:
    from castella import App, Component, State, Column, Row, Text, Button, Spacer
    from castella.core import SizePolicy
    from castella.frame import Frame
    from castella.chart import (
        BarChart,
        LineChart,
        PieChart,
        GaugeChart,
        GaugeStyle,
        GaugeChartData,
        CategoricalChartData,
        CategoricalSeries,
        NumericChartData,
        NumericSeries,
        SeriesStyle,
    )
    print(f"Castella imported! Frame class: {Frame}")
except ImportError as e:
    print(f"Castella import failed: {e}")
    import traceback
    traceback.print_exc()
    raise

# Store app reference to prevent garbage collection
_app = None
_frame = None


class ChartsDemoApp(Component):
    """Charts demo with multiple chart types."""

    def __init__(self):
        super().__init__()
        self._chart_index = State(0)
        self._chart_index.attach(self)

        # Chart names for navigation
        self._chart_names = ["Bar", "Line", "Pie", "Gauge"]

        # Initialize chart data
        self._init_chart_data()
        print("ChartsDemoApp initialized")

    def _init_chart_data(self):
        """Initialize all chart data."""
        # Bar Chart Data - Sales by Region
        self._bar_data = CategoricalChartData(title="Sales by Region")
        self._bar_data.add_series(
            CategoricalSeries.from_values(
                name="2024",
                categories=["North", "South", "East", "West"],
                values=[120, 95, 150, 80],
                style=SeriesStyle(color="#3b82f6"),
            )
        )

        # Line Chart Data - Monthly Trend
        self._line_data = NumericChartData(title="Monthly Trend")
        self._line_data.add_series(
            NumericSeries.from_y_values(
                name="Revenue",
                y_values=[50, 65, 80, 72, 90, 105, 95, 110, 125, 115, 130, 145],
                style=SeriesStyle(color="#22c55e"),
            )
        )
        self._line_data.add_series(
            NumericSeries.from_y_values(
                name="Expenses",
                y_values=[40, 45, 55, 50, 60, 70, 65, 75, 85, 80, 90, 100],
                style=SeriesStyle(color="#ef4444"),
            )
        )

        # Pie Chart Data - Market Share
        self._pie_data = CategoricalChartData(title="Market Share")
        self._pie_data.add_series(
            CategoricalSeries.from_values(
                name="Share",
                categories=["Product A", "Product B", "Product C", "Others"],
                values=[45, 25, 20, 10],
            )
        )

        # Gauge Chart Data - Performance
        self._gauge_data = GaugeChartData(
            title="CPU Usage",
            value=67,
            min_value=0,
            max_value=100,
            value_format="{:.0f}%",
            thresholds=[
                (0.0, "#22c55e"),   # Green 0-50%
                (0.5, "#f59e0b"),   # Yellow 50-80%
                (0.8, "#ef4444"),   # Red 80-100%
            ],
        )

    def _next_chart(self, event):
        """Switch to next chart."""
        idx = (self._chart_index() + 1) % len(self._chart_names)
        self._chart_index.set(idx)
        print(f"Switched to chart: {self._chart_names[idx]}")

    def _prev_chart(self, event):
        """Switch to previous chart."""
        idx = (self._chart_index() - 1) % len(self._chart_names)
        self._chart_index.set(idx)
        print(f"Switched to chart: {self._chart_names[idx]}")

    def _update_gauge(self, event):
        """Update gauge with random value."""
        import random
        new_value = random.randint(0, 100)
        self._gauge_data.set_value(new_value)
        print(f"Gauge updated to: {new_value}")

    def view(self):
        """Build the UI tree."""
        idx = self._chart_index()
        chart_name = self._chart_names[idx]
        print(f"[VIEW] Building chart view: {chart_name}")

        # Build the current chart
        if idx == 0:
            chart = BarChart(self._bar_data, show_values=True)
        elif idx == 1:
            chart = LineChart(self._line_data, smooth=True, show_points=True)
        elif idx == 2:
            chart = PieChart(self._pie_data, donut=True, inner_radius_ratio=0.4)
        else:
            chart = GaugeChart(
                self._gauge_data,
                style=GaugeStyle.HALF_CIRCLE,
                arc_width=25,
                show_ticks=True,
            )

        # Navigation buttons
        nav_row = Row(
            Spacer(),
            Button("<").on_click(self._prev_chart).fixed_size(60, 44),
            Spacer().fixed_width(20),
            Text(chart_name).font_size(20).text_color("#FFFFFF").fixed_size(80, 44).erase_border(),
            Spacer().fixed_width(20),
            Button(">").on_click(self._next_chart).fixed_size(60, 44),
            Spacer(),
        ).height(50).height_policy(SizePolicy.FIXED)

        # Extra button for gauge
        action_row = Row(
            Spacer(),
            Button("Update").on_click(self._update_gauge).fixed_size(100, 44) if idx == 3 else Spacer().fixed_width(100),
            Spacer(),
        ).height(50).height_policy(SizePolicy.FIXED)

        tree = Column(
            Spacer().fixed_height(10),

            # Header
            Row(
                Spacer(),
                Text("Castella Charts").font_size(28).text_color("#9ECE6A").fit_content().erase_border(),
                Spacer(),
            ).height(35).height_policy(SizePolicy.FIXED),

            Spacer().fixed_height(10),

            # Navigation
            nav_row,

            Spacer().fixed_height(10),

            # Chart area
            chart,

            Spacer().fixed_height(10),

            # Action row
            action_row,

            # Info
            Row(
                Spacer(),
                Text("Tap arrows to navigate").font_size(12).text_color("#565F89").fit_content().erase_border(),
                Spacer(),
            ).height(20).height_policy(SizePolicy.FIXED),

            Spacer(),
        )
        return tree


class PythonAppDelegate(NSObject):
    """iOS App Delegate for Castella Charts Demo."""

    @objc_method
    def application_didFinishLaunchingWithOptions_(
        self, application, launchOptions
    ) -> bool:
        """Called when app finishes launching."""
        nslog("=" * 50)
        nslog("PythonAppDelegate: Launching Charts Demo")
        nslog("=" * 50)

        global _app, _frame

        try:
            nslog("Creating Frame...")
            _frame = Frame("Castella Charts Demo")
            nslog(f"Frame created: {_frame}")

            nslog("Creating ChartsDemoApp component...")
            charts_app = ChartsDemoApp()

            nslog("Creating Castella App...")
            _app = App(_frame, charts_app)

            nslog("Registering callbacks...")
            _frame.on_mouse_down(_app.mouse_down)
            _frame.on_mouse_up(_app.mouse_up)
            _frame.on_mouse_wheel(_app.mouse_wheel)
            _frame.on_cursor_pos(_app.cursor_pos)
            _frame.on_input_char(_app.input_char)
            _frame.on_input_key(_app.input_key)
            _frame.on_redraw(_app.redraw)
            nslog("Callbacks registered")

            nslog("Starting frame...")
            _frame.start(application)

            nslog("Charts demo started successfully!")
            return True

        except Exception as e:
            nslog(f"Error starting app: {e}")
            import traceback
            traceback.print_exc()
            return False


def main():
    """Entry point for the iOS app."""
    print("=" * 50)
    print("main() called - Castella Charts Demo")
    print("=" * 50)
    print("Waiting for PythonAppDelegate...")
