"""Castella iOS All Widgets Demo App.

Showcases all Castella widgets on iOS:
- Basic: Text, SimpleText, MultilineText, Button
- Input: Input, CheckBox, RadioButtons, Switch, Slider
- Layout: Column, Row, Box, Spacer
- Data: DataTable, Tree, Modal
- Media: NetImage
- Charts: BarChart, LineChart, PieChart, GaugeChart
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


nslog("=== Castella All Widgets Demo Starting ===")

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

print("=== Castella All Widgets Demo ===")

# Import Rubicon-ObjC for app delegate
from rubicon.objc import ObjCClass, objc_method
NSObject = ObjCClass("NSObject")

# Import Castella framework
print("Importing Castella framework...")
try:
    from castella import (
        App,
        Box,
        Button,
        CheckBox,
        Column,
        ColumnConfig,
        Component,
        DataTable,
        DataTableState,
        Input,
        Kind,
        Modal,
        ModalState,
        MultilineText,
        NetImage,
        RadioButtons,
        RadioButtonsState,
        Row,
        SelectionMode,
        SimpleText,
        SizePolicy,
        Slider,
        SliderState,
        Spacer,
        State,
        Switch,
        Text,
        Tree,
        TreeNode,
        TreeState,
    )
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
    from castella.theme import ThemeManager
    print(f"Castella imported! Frame class: {Frame}")
except ImportError as e:
    print(f"Castella import failed: {e}")
    import traceback
    traceback.print_exc()
    raise

# Store app reference to prevent garbage collection
_app = None
_frame = None


class AllWidgetsDemoApp(Component):
    """All Widgets Demo - iOS optimized version."""

    def __init__(self):
        super().__init__()
        self._theme = ThemeManager()

        # Tab navigation state
        self._tab_id = State("basic")
        self._tab_id.attach(self)

        # Basic tab states
        self._counter = State(0)
        self._counter.attach(self)

        # Input tab states
        self._input_text = State("")
        self._checkbox1 = State(False)
        self._checkbox1.attach(self)
        self._checkbox2 = State(True)
        self._checkbox2.attach(self)
        self._radio_state = RadioButtonsState(
            labels=["Option A", "Option B", "Option C"],
            selected_index=0,
        )
        self._radio_state.attach(self)
        self._switch_on = State(True)
        self._switch_on.attach(self)
        self._slider_state = SliderState(value=50, min_val=0, max_val=100)
        self._slider_state.attach(self)

        # Layout tab states
        self._z_top = State(3)
        self._z_top.attach(self)

        # Data tab states
        self._table_state = DataTableState(
            columns=[
                ColumnConfig(name="Name", width=80, sortable=True),
                ColumnConfig(name="Age", width=50, sortable=True),
                ColumnConfig(name="City", width=80, sortable=True),
            ],
            rows=[
                ["Alice", 30, "Tokyo"],
                ["Bob", 25, "NYC"],
                ["Carol", 35, "London"],
                ["Dave", 28, "Paris"],
            ],
            selection_mode=SelectionMode.SINGLE,
        )

        self._tree_state = TreeState(
            nodes=[
                TreeNode(
                    id="docs",
                    label="Documents",
                    icon="📁",
                    children=[
                        TreeNode(id="readme", label="README", icon="📄"),
                        TreeNode(id="license", label="LICENSE", icon="📄"),
                    ],
                ),
                TreeNode(
                    id="src",
                    label="Source",
                    icon="📁",
                    children=[
                        TreeNode(id="main", label="main.py", icon="🐍"),
                    ],
                ),
            ],
            multi_select=False,
        )

        self._modal_state = ModalState()
        self._modal_state.attach(self)

        self._status = State("Ready")
        self._status.attach(self)

        # Chart data
        self._init_chart_data()

        print("AllWidgetsDemoApp initialized")

    def _init_chart_data(self):
        """Initialize chart data."""
        # Bar Chart
        self._bar_data = CategoricalChartData(title="Sales")
        self._bar_data.add_series(
            CategoricalSeries.from_values(
                name="2024",
                categories=["Q1", "Q2", "Q3", "Q4"],
                values=[120, 150, 130, 180],
                style=SeriesStyle(color="#3b82f6"),
            )
        )

        # Line Chart
        self._line_data = NumericChartData(title="Trend")
        self._line_data.add_series(
            NumericSeries.from_y_values(
                name="Revenue",
                y_values=[50, 65, 80, 72, 90, 105],
                style=SeriesStyle(color="#22c55e"),
            )
        )

        # Pie Chart
        self._pie_data = CategoricalChartData(title="Share")
        self._pie_data.add_series(
            CategoricalSeries.from_values(
                name="Market",
                categories=["A", "B", "C", "D"],
                values=[40, 30, 20, 10],
            )
        )

        # Gauge Chart
        self._gauge_data = GaugeChartData(
            title="CPU",
            value=65,
            min_value=0,
            max_value=100,
            value_format="{:.0f}%",
            thresholds=[(0.0, "#22c55e"), (0.6, "#f59e0b"), (0.85, "#ef4444")],
        )

    def view(self):
        """Build the UI tree."""
        theme = self._theme.current
        tab_id = self._tab_id()

        # Build tab content
        content = self._build_tab_content(theme, tab_id)

        # Build tab bar (scrollable horizontal)
        tab_bar = self._build_tab_bar(theme, tab_id)

        # Main layout
        main_content = Column(
            # Top padding for safe area
            Spacer().fixed_height(10),

            # Header
            Row(
                Spacer(),
                Text("All Widgets Demo", font_size=20)
                .text_color(theme.colors.text_primary)
                .fit_content()
                .erase_border(),
                Spacer(),
            ).fixed_height(40),

            # Tab bar
            tab_bar,

            # Content
            content,

            # Status bar
            Row(
                Text(self._status(), font_size=11)
                .text_color(theme.colors.fg)
                .fit_content(),
                Spacer(),
                Button("Theme").on_click(self._toggle_theme).fixed_height(36),
            ).fixed_height(40),
        ).bg_color(theme.colors.bg_primary).z_index(1)

        # Modal overlay
        modal = Modal(
            content=Column(
                Text("Modal Dialog", font_size=16),
                MultilineText(
                    "This is a modal dialog.\nTap backdrop or button to close.",
                    font_size=12,
                ),
                Spacer(),
                Button("Close").on_click(lambda _: self._modal_state.close()),
            ),
            state=self._modal_state,
            title="Modal Demo",
        )

        return Box(main_content, modal)

    def _toggle_theme(self, _):
        self._theme.toggle_dark_mode()
        mode = "Dark" if self._theme.current.is_dark else "Light"
        self._status.set(f"Theme: {mode}")

    def _build_tab_bar(self, theme, current_tab_id):
        """Build scrollable tab bar."""
        tabs = [
            ("basic", "Basic"),
            ("input", "Input"),
            ("layout", "Layout"),
            ("data", "Data"),
            ("media", "Media"),
            ("charts", "Charts"),
        ]
        buttons = []
        for tid, label in tabs:
            btn = Button(
                label,
                kind=Kind.INFO if tid == current_tab_id else Kind.NORMAL,
            ).on_click(lambda _, t=tid: self._tab_id.set(t)).fixed_size(70, 40)
            buttons.append(btn)
        return Row(*buttons, scrollable=True).fixed_height(44).bg_color(theme.colors.bg_secondary)

    def _build_tab_content(self, theme, tab_id):
        """Build content for selected tab."""
        if tab_id == "basic":
            return self._build_basic_tab(theme)
        elif tab_id == "input":
            return self._build_input_tab(theme)
        elif tab_id == "layout":
            return self._build_layout_tab(theme)
        elif tab_id == "data":
            return self._build_data_tab(theme)
        elif tab_id == "media":
            return self._build_media_tab(theme)
        elif tab_id == "charts":
            return self._build_charts_tab(theme)
        return self._build_basic_tab(theme)

    def _build_basic_tab(self, theme):
        """Basic tab: Text, Button."""
        count = self._counter()

        if count > 0:
            kind, msg = Kind.SUCCESS, "Positive!"
        elif count < 0:
            kind, msg = Kind.DANGER, "Negative!"
        else:
            kind, msg = Kind.INFO, "Zero"

        return Column(
            Spacer().fixed_height(10),

            Text("Text Widget", font_size=14)
            .text_color(theme.colors.fg)
            .fixed_height(25),

            Text(f"Count: {count}", font_size=24)
            .text_color(theme.colors.text_info)
            .fixed_height(40),

            Text("SimpleText:", font_size=14)
            .text_color(theme.colors.fg)
            .fixed_height(25),

            SimpleText(f"Simple text: count = {count}")
            .fixed_height(25),

            Text("MultilineText:", font_size=14)
            .text_color(theme.colors.fg)
            .fixed_height(25),

            MultilineText(f"Status: {msg}\nCount is {count}", font_size=12, kind=kind)
            .fixed_height(50),

            Spacer().fixed_height(15),

            Text("Buttons:", font_size=14)
            .text_color(theme.colors.fg)
            .fixed_height(25),

            Row(
                Button("-5", kind=Kind.DANGER).on_click(
                    lambda _: self._counter.set(self._counter() - 5)
                ).fixed_height(44),
                Button("-1").on_click(
                    lambda _: self._counter.set(self._counter() - 1)
                ).fixed_height(44),
                Button("0", kind=Kind.INFO).on_click(
                    lambda _: self._counter.set(0)
                ).fixed_height(44),
                Button("+1").on_click(
                    lambda _: self._counter.set(self._counter() + 1)
                ).fixed_height(44),
                Button("+5", kind=Kind.SUCCESS).on_click(
                    lambda _: self._counter.set(self._counter() + 5)
                ).fixed_height(44),
            ).fixed_height(48),

            Spacer().fixed_height(20),
        ).bg_color(theme.colors.bg_secondary)

    def _build_input_tab(self, theme):
        """Input tab: Input, CheckBox, RadioButtons, Switch, Slider."""
        return Column(
            Spacer().fixed_height(10),

            Text("Input Widget:", font_size=14)
            .text_color(theme.colors.fg)
            .fixed_height(25),

            Input(self._input_text())
            .on_change(lambda t: self._input_text.set(t))
            .fixed_height(40),

            Spacer().fixed_height(15),

            Text("CheckBox:", font_size=14)
            .text_color(theme.colors.fg)
            .fixed_height(25),

            Row(
                CheckBox(self._checkbox1)
                .on_change(lambda v: self._checkbox1.set(v))
                .fixed_size(30, 30),
                Text("Normal", font_size=12).fixed_width(60),
                Spacer().fixed_width(20),
                CheckBox(self._checkbox2, is_circle=True)
                .on_change(lambda v: self._checkbox2.set(v))
                .fixed_size(30, 30),
                Text("Circle", font_size=12).fixed_width(60),
                Spacer(),
            ).fixed_height(35),

            Spacer().fixed_height(15),

            Text("RadioButtons:", font_size=14)
            .text_color(theme.colors.fg)
            .fixed_height(25),

            RadioButtons(self._radio_state).fixed_height(90),

            Spacer().fixed_height(15),

            Text("Switch:", font_size=14)
            .text_color(theme.colors.fg)
            .fixed_height(25),

            Row(
                Switch(self._switch_on())
                .on_change(lambda v: self._switch_on.set(v))
                .fixed_width(55),
                Text("ON" if self._switch_on() else "OFF", font_size=12).fixed_width(40),
                Spacer(),
            ).fixed_height(35),

            Spacer().fixed_height(15),

            Text("Slider:", font_size=14)
            .text_color(theme.colors.fg)
            .fixed_height(25),

            Row(
                Slider(self._slider_state).flex(1),
                Text(f"{self._slider_state.value():.0f}", font_size=12).fixed_width(40),
            ).fixed_height(40),

            Spacer().fixed_height(20),
        ).bg_color(theme.colors.bg_secondary)

    def _build_layout_tab(self, theme):
        """Layout tab: Column, Row, Box, Spacer."""
        top = self._z_top()

        return Column(
            Spacer().fixed_height(10),

            Text("Row with flex (1:2:1):", font_size=14)
            .text_color(theme.colors.fg)
            .fixed_height(25),

            Row(
                Button("1").flex(1).fixed_height(40),
                Button("2").flex(2).fixed_height(40),
                Button("1").flex(1).fixed_height(40),
            ).fixed_height(44),

            Spacer().fixed_height(15),

            Text("Nested layouts:", font_size=14)
            .text_color(theme.colors.fg)
            .fixed_height(25),

            Row(
                Column(
                    Button("A1").fixed_height(35),
                    Button("A2").fixed_height(35),
                ).fixed_width(90),
                Column(
                    Button("B1").fixed_height(35),
                    Button("B2").fixed_height(35),
                    Button("B3").fixed_height(35),
                ).fixed_width(90),
                Column(
                    Button("C1").fixed_height(35),
                ).fixed_width(90),
                Spacer(),
            ).fixed_height(110),

            Spacer().fixed_height(15),

            Text("Box with z-index:", font_size=14)
            .text_color(theme.colors.fg)
            .fixed_height(25),

            Row(
                Button("R Top", kind=Kind.DANGER).on_click(
                    lambda _: self._z_top.set(1)
                ).fixed_height(40),
                Button("G Top", kind=Kind.SUCCESS).on_click(
                    lambda _: self._z_top.set(2)
                ).fixed_height(40),
                Button("B Top", kind=Kind.INFO).on_click(
                    lambda _: self._z_top.set(3)
                ).fixed_height(40),
            ).fixed_height(44),

            Box(
                MultilineText("R", font_size=14, kind=Kind.DANGER)
                .fixed_size(55, 45)
                .z_index(3 if top == 1 else 1),
                MultilineText("G", font_size=14, kind=Kind.SUCCESS)
                .fixed_size(55, 45)
                .z_index(3 if top == 2 else 2),
                MultilineText("B", font_size=14, kind=Kind.INFO)
                .fixed_size(55, 45)
                .z_index(3 if top == 3 else 1),
            ).fixed_height(50),

            Spacer().fixed_height(20),
        ).bg_color(theme.colors.bg_secondary)

    def _build_data_tab(self, theme):
        """Data tab: DataTable, Tree, Modal."""
        return Column(
            Spacer().fixed_height(10),

            Text("DataTable:", font_size=14)
            .text_color(theme.colors.fg)
            .fixed_height(25),

            DataTable(self._table_state)
            .on_cell_click(lambda e: self._status.set(f"Cell: {e.value}"))
            .fixed_height(150),

            Spacer().fixed_height(15),

            Text("Tree:", font_size=14)
            .text_color(theme.colors.fg)
            .fixed_height(25),

            Tree(self._tree_state)
            .on_select(lambda n: self._status.set(f"Selected: {n.label}"))
            .fixed_height(120),

            Spacer().fixed_height(15),

            Text("MultilineText (formatted):", font_size=14)
            .text_color(theme.colors.fg)
            .fixed_height(25),

            MultilineText(
                "Heading\n\nBold and italic text.\n- Item 1\n- Item 2\n\nprint('Hello!')",
                font_size=11,
            ).fixed_height(120),

            Spacer().fixed_height(15),

            Button("Open Modal").on_click(lambda _: self._modal_state.open())
            .fixed_height(44),

            Spacer().fixed_height(20),
        ).bg_color(theme.colors.bg_secondary)

    def _build_media_tab(self, theme):
        """Media tab: NetImage."""
        return Column(
            Spacer().fixed_height(10),

            Text("NetImage:", font_size=14)
            .text_color(theme.colors.fg)
            .fixed_height(25),

            Text("Loading from URL...", font_size=11)
            .text_color(theme.colors.fg)
            .fixed_height(20),

            NetImage("https://picsum.photos/300/200"),

            Text("Images loaded via HTTPS", font_size=12)
            .text_color(theme.colors.fg)
            .fixed_height(25),

            Spacer().fixed_height(20),
        ).bg_color(theme.colors.bg_secondary)

    def _build_charts_tab(self, theme):
        """Charts tab: BarChart, LineChart, PieChart, GaugeChart."""
        return Column(
            Spacer().fixed_height(5),

            Row(
                Column(
                    Text("Bar", font_size=11).text_color(theme.colors.fg).fixed_height(18),
                    BarChart(self._bar_data, show_values=False),
                ),
                Column(
                    Text("Line", font_size=11).text_color(theme.colors.fg).fixed_height(18),
                    LineChart(self._line_data, smooth=True),
                ),
            ),

            Spacer().fixed_height(5),

            Row(
                Column(
                    Text("Pie", font_size=11).text_color(theme.colors.fg).fixed_height(18),
                    PieChart(self._pie_data, donut=True, inner_radius_ratio=0.4),
                ),
                Column(
                    Text("Gauge", font_size=11).text_color(theme.colors.fg).fixed_height(18),
                    GaugeChart(self._gauge_data, style=GaugeStyle.HALF_CIRCLE, arc_width=20),
                ),
            ),

            Row(
                Spacer(),
                Button("Update").on_click(self._update_charts).fixed_height(40),
                Spacer(),
            ).fixed_height(44),

            Spacer().fixed_height(20),
        ).bg_color(theme.colors.bg_secondary)

    def _update_charts(self, _):
        """Update chart data with random values."""
        import random

        # Update bar chart
        self._bar_data.set_series([
            CategoricalSeries.from_values(
                name="2024",
                categories=["Q1", "Q2", "Q3", "Q4"],
                values=[random.randint(80, 200) for _ in range(4)],
                style=SeriesStyle(color="#3b82f6"),
            )
        ])

        # Update line chart
        self._line_data.set_series([
            NumericSeries.from_y_values(
                name="Revenue",
                y_values=[random.randint(40, 120) for _ in range(6)],
                style=SeriesStyle(color="#22c55e"),
            )
        ])

        # Update pie chart
        values = [random.randint(10, 50) for _ in range(4)]
        self._pie_data.set_series([
            CategoricalSeries.from_values(
                name="Market",
                categories=["A", "B", "C", "D"],
                values=values,
            )
        ])

        # Update gauge
        self._gauge_data.set_value(random.randint(10, 95))

        self._status.set("Charts updated!")


class PythonAppDelegate(NSObject):
    """iOS App Delegate for Castella All Widgets Demo."""

    @objc_method
    def application_didFinishLaunchingWithOptions_(
        self, application, launchOptions
    ) -> bool:
        """Called when app finishes launching."""
        nslog("=" * 50)
        nslog("PythonAppDelegate: Launching All Widgets Demo")
        nslog("=" * 50)

        global _app, _frame

        try:
            nslog("Creating Frame...")
            _frame = Frame("Castella All Widgets Demo")
            nslog(f"Frame created: {_frame}")

            nslog("Creating AllWidgetsDemoApp component...")
            demo_app = AllWidgetsDemoApp()

            nslog("Creating Castella App...")
            _app = App(_frame, demo_app)

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

            nslog("All Widgets demo started successfully!")
            return True

        except Exception as e:
            nslog(f"Error starting app: {e}")
            import traceback
            traceback.print_exc()
            return False


def main():
    """Entry point for the iOS app."""
    print("=" * 50)
    print("main() called - Castella All Widgets Demo")
    print("=" * 50)
    print("Waiting for PythonAppDelegate...")
