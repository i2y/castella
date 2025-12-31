"""All Widgets Demo - Comprehensive showcase of all Castella widgets.

This demo includes 29 widgets organized into 6 tabs:
- Basic: Text, SimpleText, MultilineText, Button
- Input: Input, MultilineInput, CheckBox, RadioButtons, Switch, Slider, DateTimeInput
- Layout: Column, Row, Box, Spacer
- Data: DataTable, Tree, FileTree, Modal, Markdown
- Media: NetImage
- Charts: BarChart, LineChart, PieChart, ScatterChart, AreaChart, StackedBarChart, GaugeChart
"""

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
    DateTimeInput,
    DateTimeInputState,
    FileTree,
    FileTreeState,
    Input,
    Kind,
    Markdown,
    Modal,
    ModalState,
    MultilineInput,
    MultilineInputState,
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
from castella.chart import (
    AreaChart,
    BarChart,
    CategoricalChartData,
    CategoricalSeries,
    GaugeChart,
    GaugeChartData,
    GaugeStyle,
    LineChart,
    NumericChartData,
    NumericSeries,
    PieChart,
    PointShape,
    ScatterChart,
    SeriesStyle,
    StackedBarChart,
)
from castella.frame import Frame
from castella.theme import ThemeManager


class AllWidgetsDemo(Component):
    """Main demo component showcasing all Castella widgets."""

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
        self._input_text = State("")  # Don't attach - Input manages
        self._multiline_state = MultilineInputState(
            "Type here...\nMultiple lines supported.\nWith scrolling!"
        )
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
        self._datetime_state = DateTimeInputState(
            value="2024-12-25T14:30:00",
            enable_date=True,
            enable_time=True,
        )
        self._datetime_state.attach(self)

        # Layout tab states
        self._z_top = State(3)
        self._z_top.attach(self)

        # Data tab states
        self._table_state = DataTableState(
            columns=[
                ColumnConfig(name="Name", width=100, sortable=True),
                ColumnConfig(name="Age", width=60, sortable=True),
                ColumnConfig(name="Country", width=100, sortable=True),
            ],
            rows=[
                ["Alice", 30, "Japan"],
                ["Bob", 25, "USA"],
                ["Charlie", 35, "UK"],
                ["Diana", 28, "Germany"],
                ["Eve", 32, "France"],
            ],
            selection_mode=SelectionMode.MULTI,
        )

        self._tree_state = TreeState(
            nodes=[
                TreeNode(
                    id="docs",
                    label="Documents",
                    icon="📁",
                    children=[
                        TreeNode(id="readme", label="README.md", icon="📄"),
                        TreeNode(id="license", label="LICENSE", icon="📄"),
                    ],
                ),
                TreeNode(
                    id="src",
                    label="Source",
                    icon="📁",
                    children=[
                        TreeNode(id="main", label="main.py", icon="🐍"),
                        TreeNode(id="utils", label="utils.py", icon="🐍"),
                    ],
                ),
            ],
            multi_select=False,
        )

        self._file_tree_state = FileTreeState(
            root_path=".",
            show_hidden=False,
            dirs_first=True,
        )

        self._modal_state = ModalState()
        self._modal_state.attach(self)

        self._status = State("Ready")
        self._status.attach(self)

        # ============================================================
        # Chart Data - Rich and Complex
        # ============================================================

        # --- BarChart Data: Regional Sales Comparison (3 years, 6 regions) ---
        self._bar_data = CategoricalChartData(title="Regional Sales Performance")
        self._bar_data.add_series(
            CategoricalSeries.from_values(
                name="2022",
                categories=["North America", "Europe", "Asia Pacific", "Latin America", "Middle East", "Africa"],
                values=[145, 132, 178, 67, 45, 38],
                style=SeriesStyle(color="#6366f1"),
            )
        )
        self._bar_data.add_series(
            CategoricalSeries.from_values(
                name="2023",
                categories=["North America", "Europe", "Asia Pacific", "Latin America", "Middle East", "Africa"],
                values=[162, 148, 195, 78, 52, 44],
                style=SeriesStyle(color="#22c55e"),
            )
        )
        self._bar_data.add_series(
            CategoricalSeries.from_values(
                name="2024",
                categories=["North America", "Europe", "Asia Pacific", "Latin America", "Middle East", "Africa"],
                values=[189, 167, 223, 92, 61, 53],
                style=SeriesStyle(color="#f59e0b"),
            )
        )

        # --- LineChart Data: Stock Price Movement (multiple stocks, 12 months) ---
        self._line_data = NumericChartData(title="Stock Price Movement (2024)")
        self._line_data.add_series(
            NumericSeries.from_y_values(
                name="TECH Corp",
                y_values=[150, 158, 162, 155, 168, 175, 182, 178, 190, 195, 188, 205],
                style=SeriesStyle(color="#3b82f6"),
            )
        )
        self._line_data.add_series(
            NumericSeries.from_y_values(
                name="HEALTH Inc",
                y_values=[85, 88, 92, 95, 91, 98, 102, 108, 105, 112, 118, 125],
                style=SeriesStyle(color="#22c55e"),
            )
        )
        self._line_data.add_series(
            NumericSeries.from_y_values(
                name="ENERGY Ltd",
                y_values=[72, 68, 75, 82, 78, 85, 80, 88, 92, 87, 95, 98],
                style=SeriesStyle(color="#ef4444"),
            )
        )

        # --- PieChart Data: Market Share (more segments) ---
        self._pie_data = CategoricalChartData(title="Browser Market Share 2024")
        self._pie_data.add_series(
            CategoricalSeries.from_values(
                name="Browsers",
                categories=["Chrome", "Safari", "Edge", "Firefox", "Opera", "Samsung", "Other"],
                values=[63.5, 19.8, 5.2, 2.8, 2.4, 2.3, 4.0],
            )
        )

        # --- Second PieChart: OS Market Share ---
        self._pie_data_2 = CategoricalChartData(title="Desktop OS Market Share")
        self._pie_data_2.add_series(
            CategoricalSeries.from_values(
                name="OS",
                categories=["Windows", "macOS", "Linux", "ChromeOS", "Other"],
                values=[72.1, 15.4, 4.2, 2.8, 5.5],
            )
        )

        # --- ScatterChart Data: Correlation Analysis (multiple datasets) ---
        self._scatter_data = NumericChartData(title="Height vs Weight Correlation")
        self._scatter_data.add_series(
            NumericSeries.from_values(
                name="Male",
                x_values=[165, 170, 175, 180, 185, 168, 172, 178, 182, 176, 169, 183, 177, 171, 179],
                y_values=[65, 72, 78, 85, 92, 68, 75, 82, 88, 79, 67, 90, 80, 73, 84],
                style=SeriesStyle(color="#3b82f6"),
            )
        )
        self._scatter_data.add_series(
            NumericSeries.from_values(
                name="Female",
                x_values=[155, 160, 165, 158, 162, 168, 157, 163, 159, 166, 161, 164, 156, 167, 170],
                y_values=[50, 55, 60, 52, 57, 65, 51, 58, 54, 62, 56, 59, 49, 63, 67],
                style=SeriesStyle(color="#ec4899"),
            )
        )

        # --- AreaChart Data: Website Traffic (multiple metrics) ---
        self._area_data = NumericChartData(title="Website Traffic Analysis")
        self._area_data.add_series(
            NumericSeries.from_y_values(
                name="Page Views",
                y_values=[12000, 15000, 14500, 18000, 22000, 19500, 25000, 28000, 26500, 31000, 35000, 38000],
                style=SeriesStyle(color="#06b6d4"),
            )
        )
        self._area_data.add_series(
            NumericSeries.from_y_values(
                name="Unique Visitors",
                y_values=[4500, 5200, 5000, 6200, 7500, 6800, 8500, 9200, 8800, 10500, 12000, 13500],
                style=SeriesStyle(color="#8b5cf6"),
            )
        )
        self._area_data.add_series(
            NumericSeries.from_y_values(
                name="Conversions",
                y_values=[450, 520, 480, 620, 750, 680, 850, 920, 880, 1050, 1200, 1350],
                style=SeriesStyle(color="#22c55e"),
            )
        )

        # --- StackedBarChart Data: Product Category Sales (4 products, 6 months) ---
        self._stacked_data = CategoricalChartData(title="Product Category Sales by Month")
        self._stacked_data.add_series(
            CategoricalSeries.from_values(
                name="Electronics",
                categories=["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
                values=[45, 52, 48, 61, 58, 67],
                style=SeriesStyle(color="#3b82f6"),
            )
        )
        self._stacked_data.add_series(
            CategoricalSeries.from_values(
                name="Clothing",
                categories=["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
                values=[32, 38, 42, 35, 48, 52],
                style=SeriesStyle(color="#22c55e"),
            )
        )
        self._stacked_data.add_series(
            CategoricalSeries.from_values(
                name="Home & Garden",
                categories=["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
                values=[18, 22, 28, 32, 38, 42],
                style=SeriesStyle(color="#f59e0b"),
            )
        )
        self._stacked_data.add_series(
            CategoricalSeries.from_values(
                name="Sports",
                categories=["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
                values=[15, 18, 22, 25, 30, 35],
                style=SeriesStyle(color="#ef4444"),
            )
        )

        # --- GaugeChart Data: System Metrics ---
        self._gauge_cpu = GaugeChartData(
            title="CPU Usage",
            value=67,
            min_value=0,
            max_value=100,
            value_format="{:.0f}%",
            thresholds=[(0.0, "#22c55e"), (0.6, "#f59e0b"), (0.85, "#ef4444")],
        )

        self._gauge_memory = GaugeChartData(
            title="Memory Usage",
            value=78,
            min_value=0,
            max_value=100,
            value_format="{:.0f}%",
            thresholds=[(0.0, "#22c55e"), (0.7, "#f59e0b"), (0.9, "#ef4444")],
        )

        self._gauge_disk = GaugeChartData(
            title="Disk Usage",
            value=45,
            min_value=0,
            max_value=100,
            value_format="{:.0f}%",
            thresholds=[(0.0, "#22c55e"), (0.75, "#f59e0b"), (0.9, "#ef4444")],
        )

        self._gauge_network = GaugeChartData(
            title="Network Load",
            value=32,
            min_value=0,
            max_value=100,
            value_format="{:.0f}%",
            thresholds=[(0.0, "#22c55e"), (0.5, "#f59e0b"), (0.8, "#ef4444")],
        )

    def view(self):
        theme = self._theme.current
        tab_id = self._tab_id()

        # Build ONLY the visible tab content (lazy building for performance)
        content = self._build_tab_content(theme, tab_id)

        # Build simple tab bar with buttons
        tab_bar = self._build_tab_bar(theme, tab_id)

        main_content = Column(
            Text("All Widgets Demo", font_size=20)
            .text_color(theme.colors.text_primary)
            .fixed_height(40),
            tab_bar,
            content,
            Row(
                Text(self._status(), font_size=12).text_color(theme.colors.fg),
                Spacer(),
                Button("Toggle Theme").on_click(self._toggle_theme),
            )
            .fixed_height(35),
        ).bg_color(theme.colors.bg_primary).z_index(1)

        # Modal overlay
        modal = Modal(
            content=Column(
                Text("Modal Dialog", font_size=16),
                MultilineText(
                    "This is a modal dialog.\nClick backdrop or button to close.",
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
        self._status.set(f"Theme: {mode} mode")

    def _build_tab_bar(self, theme, current_tab_id):
        """Build a simple button-based tab bar."""
        tabs = [
            ("basic", "Basic"),
            ("input", "Input"),
            ("layout", "Layout"),
            ("data", "Data"),
            ("media", "Media"),
            ("dashboard", "Dashboard"),
            ("bar", "Bar"),
            ("line", "Line/Area"),
            ("pie", "Pie/Scatter"),
            ("gauge", "Stacked/Gauge"),
        ]
        buttons = []
        for tid, label in tabs:
            # Highlight the selected tab with a different kind
            btn = Button(
                label,
                kind=Kind.INFO if tid == current_tab_id else Kind.NORMAL,
            ).on_click(lambda _, t=tid: self._tab_id.set(t))
            buttons.append(btn)
        return (
            Row(*buttons)
            .fixed_height(38)
            .bg_color(theme.colors.bg_secondary)
        )

    def _build_tab_content(self, theme, tab_id):
        """Build only the content for the selected tab (lazy building)."""
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
        elif tab_id == "dashboard":
            return self._build_dashboard_tab(theme)
        elif tab_id == "bar":
            return self._build_bar_chart_tab(theme)
        elif tab_id == "line":
            return self._build_line_area_tab(theme)
        elif tab_id == "pie":
            return self._build_pie_scatter_tab(theme)
        elif tab_id == "gauge":
            return self._build_stacked_gauge_tab(theme)
        else:
            return self._build_basic_tab(theme)

    def _build_basic_tab(self, theme):
        """Basic tab: Text, SimpleText, MultilineText, Button."""
        count = self._counter()

        if count > 0:
            kind, msg = Kind.SUCCESS, "Positive!"
        elif count < 0:
            kind, msg = Kind.DANGER, "Negative!"
        else:
            kind, msg = Kind.INFO, "Zero"

        return Column(
            # Text widget
            Text("Text Widget", font_size=16)
            .text_color(theme.colors.text_primary)
            .fixed_height(30),
            Text(f"Count: {count}", font_size=24)
            .text_color(theme.colors.text_info)
            .fixed_height(40),
            # SimpleText widget
            Text("SimpleText Widget:", font_size=14)
            .text_color(theme.colors.fg)
            .fixed_height(25),
            SimpleText(f"Simple text showing count = {count}")
            .fixed_height(25),
            # MultilineText widget
            Text("MultilineText Widget:", font_size=14)
            .text_color(theme.colors.fg)
            .fixed_height(25),
            MultilineText(f"Status: {msg}\nCount is {count}", font_size=12, kind=kind)
            .fixed_height(50),
            Spacer().fixed_height(10),
            # Button widgets with Kind styling
            Text("Button Widget (with Kind styling):", font_size=14)
            .text_color(theme.colors.fg)
            .fixed_height(25),
            Row(
                Button("-5", kind=Kind.DANGER).on_click(
                    lambda _: self._counter.set(self._counter() - 5)
                ),
                Button("-1").on_click(
                    lambda _: self._counter.set(self._counter() - 1)
                ),
                Button("0", kind=Kind.INFO).on_click(
                    lambda _: self._counter.set(0)
                ),
                Button("+1").on_click(
                    lambda _: self._counter.set(self._counter() + 1)
                ),
                Button("+5", kind=Kind.SUCCESS).on_click(
                    lambda _: self._counter.set(self._counter() + 5)
                ),
            )
            .fixed_height(40),
            Row(
                Button("Normal", kind=Kind.NORMAL),
                Button("Info", kind=Kind.INFO),
                Button("Success", kind=Kind.SUCCESS),
                Button("Warning", kind=Kind.WARNING),
                Button("Danger", kind=Kind.DANGER),
            )
            .fixed_height(40),
            Spacer(),
        ).bg_color(theme.colors.bg_secondary)

    def _build_input_tab(self, theme):
        """Input tab: Input, MultilineInput, CheckBox, RadioButtons, Switch, Slider, DateTimeInput."""
        return Column(
            # Input widget
            Text("Input Widget:", font_size=14)
            .text_color(theme.colors.fg)
            .fixed_height(25),
            Input(self._input_text())
            .on_change(lambda t: self._input_text.set(t))
            .fixed_height(35),
            # MultilineInput widget
            Text("MultilineInput Widget:", font_size=14)
            .text_color(theme.colors.fg)
            .fixed_height(25),
            MultilineInput(self._multiline_state, font_size=12, wrap=True)
            .fixed_height(80),
            Spacer().fixed_height(10),
            # CheckBox widgets
            Text("CheckBox Widget:", font_size=14)
            .text_color(theme.colors.fg)
            .fixed_height(25),
            Row(
                CheckBox(self._checkbox1)
                .on_change(lambda v: self._checkbox1.set(v))
                .fixed_size(25, 25),
                Text("Normal", font_size=12),
                Spacer().fixed_width(20),
                CheckBox(self._checkbox2, is_circle=True)
                .on_change(lambda v: self._checkbox2.set(v))
                .fixed_size(25, 25),
                Text("Circle", font_size=12),
                Spacer(),
            )
            .fixed_height(30),
            # RadioButtons widget
            Text("RadioButtons Widget:", font_size=14)
            .text_color(theme.colors.fg)
            .fixed_height(25),
            RadioButtons(self._radio_state).fixed_height(80),
            # Switch widget
            Text("Switch Widget:", font_size=14)
            .text_color(theme.colors.fg)
            .fixed_height(25),
            Row(
                Switch(self._switch_on())
                .on_change(lambda v: self._switch_on.set(v))
                .fixed_width(50),
                Text("ON" if self._switch_on() else "OFF", font_size=12),
                Spacer(),
            )
            .fixed_height(30),
            # Slider widget
            Text("Slider Widget:", font_size=14)
            .text_color(theme.colors.fg)
            .fixed_height(25),
            Row(
                Slider(self._slider_state).flex(1),
                Text(f"{self._slider_state.value():.0f}", font_size=12)
                .fixed_width(40),
            )
            .fixed_height(35),
            # DateTimeInput widget
            Text("DateTimeInput Widget:", font_size=14)
            .text_color(theme.colors.fg)
            .fixed_height(25),
            DateTimeInput(state=self._datetime_state, label="Select Date & Time")
            .height_policy(SizePolicy.EXPANDING),
            Text(
                f"Selected: {self._datetime_state.to_display_string() or 'None'}",
                font_size=11,
            )
            .text_color(theme.colors.fg)
            .fixed_height(25),
        ).bg_color(theme.colors.bg_secondary)

    def _build_layout_tab(self, theme):
        """Layout tab: Column, Row, Box, Spacer demonstration."""
        top = self._z_top()

        return Column(
            # Row with flex demonstration
            Text("Row with flex() - 1:2:1 proportion:", font_size=14)
            .text_color(theme.colors.fg)
            .fixed_height(25),
            Row(
                Button("1").flex(1),
                Button("2").flex(2),
                Button("1").flex(1),
            )
            .fixed_height(35),
            Spacer().fixed_height(15),
            # Nested layouts
            Text("Nested Column/Row layouts:", font_size=14)
            .text_color(theme.colors.fg)
            .fixed_height(25),
            Row(
                Column(
                    Button("A1").fixed_height(30),
                    Button("A2").fixed_height(30),
                ).fixed_width(100),
                Column(
                    Button("B1").fixed_height(30),
                    Button("B2").fixed_height(30),
                    Button("B3").fixed_height(30),
                ).fixed_width(100),
                Column(
                    Button("C1").fixed_height(30),
                ).fixed_width(100),
                Spacer(),
            )
            .fixed_height(100),
            Spacer().fixed_height(15),
            # Box with z-index
            Text("Box with z-index layering:", font_size=14)
            .text_color(theme.colors.fg)
            .fixed_height(25),
            Row(
                Button("Red Top", kind=Kind.DANGER).on_click(
                    lambda _: self._z_top.set(1)
                ),
                Button("Green Top", kind=Kind.SUCCESS).on_click(
                    lambda _: self._z_top.set(2)
                ),
                Button("Blue Top", kind=Kind.INFO).on_click(
                    lambda _: self._z_top.set(3)
                ),
            )
            .fixed_height(35),
            Box(
                MultilineText("R", font_size=14, kind=Kind.DANGER)
                .fixed_size(60, 50)
                .z_index(3 if top == 1 else 1),
                MultilineText("G", font_size=14, kind=Kind.SUCCESS)
                .fixed_size(60, 50)
                .z_index(3 if top == 2 else 2),
                MultilineText("B", font_size=14, kind=Kind.INFO)
                .fixed_size(60, 50)
                .z_index(3 if top == 3 else 1),
            )
            .fixed_height(55),
            Spacer().fixed_height(15),
            # Spacer demonstration
            Text("Spacer fills remaining space:", font_size=14)
            .text_color(theme.colors.fg)
            .fixed_height(25),
            Row(
                Button("Left"),
                Spacer(),
                Button("Right"),
            )
            .fixed_height(35),
            Spacer(),
        ).bg_color(theme.colors.bg_secondary)

    def _build_data_tab(self, theme):
        """Data tab: DataTable, Tree, FileTree, Modal, Markdown."""
        return Column(
            Row(
                # Left column: DataTable, Tree, FileTree - all expanding
                Column(
                    Text("DataTable Widget:", font_size=14)
                    .text_color(theme.colors.fg)
                    .fixed_height(25),
                    DataTable(self._table_state)
                    .on_cell_click(
                        lambda e: self._status.set(f"Clicked: {e.value}")
                    ),
                    Text("Tree Widget:", font_size=14)
                    .text_color(theme.colors.fg)
                    .fixed_height(25),
                    Tree(self._tree_state)
                    .on_select(lambda n: self._status.set(f"Selected: {n.label}")),
                    Text("FileTree Widget:", font_size=14)
                    .text_color(theme.colors.fg)
                    .fixed_height(25),
                    FileTree(self._file_tree_state)
                    .on_file_select(lambda p: self._status.set(f"File: {p.name}")),
                ).flex(1),
                # Right column: Markdown and Modal trigger
                Column(
                    Text("Markdown Widget:", font_size=14)
                    .text_color(theme.colors.fg)
                    .fixed_height(25),
                    Markdown(
                        """# Markdown Demo

**Bold** and *italic* text.

- List item 1
- List item 2

```python
def hello():
    print("Hello!")
```

> Blockquote text

| Col1 | Col2 |
|------|------|
| A    | B    |
""",
                        base_font_size=11,
                    ),
                    Text("Modal Widget:", font_size=14)
                    .text_color(theme.colors.fg)
                    .fixed_height(25),
                    Button("Open Modal").on_click(lambda _: self._modal_state.open())
                    .fixed_height(35),
                ).flex(1),
            ),
        ).bg_color(theme.colors.bg_secondary)

    def _build_media_tab(self, theme):
        """Media tab: NetImage widget."""
        return Column(
            Text("NetImage Widget:", font_size=14)
            .text_color(theme.colors.fg)
            .fixed_height(25),
            Text("Loading image from URL...", font_size=11)
            .text_color(theme.colors.fg)
            .fixed_height(20),
            NetImage("https://picsum.photos/400/300"),
            Text("NetImage supports various image formats from URLs.", font_size=12)
            .text_color(theme.colors.fg)
            .fixed_height(25),
        ).bg_color(theme.colors.bg_secondary)

    def _build_dashboard_tab(self, theme):
        """Dashboard tab: Multiple charts in a beautiful layout."""
        return Column(
            Row(
                Text("Analytics Dashboard", font_size=18)
                .text_color(theme.colors.text_primary),
                Spacer(),
                Button("Refresh All").on_click(self._refresh_dashboard),
            )
            .fixed_height(40),
            # Top row: Bar chart and Line chart
            Row(
                Column(
                    Text("Regional Sales", font_size=12)
                    .text_color(theme.colors.fg)
                    .fixed_height(20),
                    BarChart(self._bar_data, show_values=False, enable_tooltip=True),
                ),
                Column(
                    Text("Stock Trends", font_size=12)
                    .text_color(theme.colors.fg)
                    .fixed_height(20),
                    LineChart(self._line_data, smooth=True, show_points=True, enable_tooltip=True),
                ),
            ),
            # Middle row: Pie chart, Area chart, Scatter chart
            Row(
                Column(
                    Text("Browser Share", font_size=12)
                    .text_color(theme.colors.fg)
                    .fixed_height(20),
                    PieChart(self._pie_data, donut=True, inner_radius_ratio=0.5, enable_tooltip=True),
                ),
                Column(
                    Text("Traffic Growth", font_size=12)
                    .text_color(theme.colors.fg)
                    .fixed_height(20),
                    AreaChart(self._area_data, fill_opacity=0.3, enable_tooltip=True),
                ),
                Column(
                    Text("Correlation", font_size=12)
                    .text_color(theme.colors.fg)
                    .fixed_height(20),
                    ScatterChart(self._scatter_data, point_radius=6, enable_tooltip=True),
                ),
            ),
            # Bottom row: Stacked bar and Gauges
            Row(
                Column(
                    Text("Product Sales", font_size=12)
                    .text_color(theme.colors.fg)
                    .fixed_height(20),
                    StackedBarChart(self._stacked_data, enable_tooltip=True),
                ),
                Column(
                    Text("System Status", font_size=12)
                    .text_color(theme.colors.fg)
                    .fixed_height(20),
                    # 2x2 grid layout for gauges
                    Column(
                        Row(
                            GaugeChart(self._gauge_cpu, style=GaugeStyle.HALF_CIRCLE, arc_width=18),
                            GaugeChart(self._gauge_memory, style=GaugeStyle.HALF_CIRCLE, arc_width=18),
                        ),
                        Row(
                            GaugeChart(self._gauge_disk, style=GaugeStyle.HALF_CIRCLE, arc_width=18),
                            GaugeChart(self._gauge_network, style=GaugeStyle.HALF_CIRCLE, arc_width=18),
                        ),
                    ),
                ),
            ),
        ).bg_color(theme.colors.bg_secondary)

    def _refresh_dashboard(self, _):
        """Refresh all dashboard data using batch_update() for efficient updates."""
        import random

        # Use batch_update() context manager to batch multiple updates per chart data.
        # This allows using set_series() (which normally calls notify) while deferring
        # all notifications until the context exits - resulting in a single notify per object.

        # Bar chart data
        regions = ["North America", "Europe", "Asia Pacific", "Latin America", "Middle East", "Africa"]
        with self._bar_data.batch_update():
            self._bar_data.set_series([
                CategoricalSeries.from_values(
                    name="2022",
                    categories=regions,
                    values=[random.randint(50, 200) for _ in range(6)],
                    style=SeriesStyle(color="#6366f1"),
                ),
                CategoricalSeries.from_values(
                    name="2023",
                    categories=regions,
                    values=[random.randint(60, 220) for _ in range(6)],
                    style=SeriesStyle(color="#22c55e"),
                ),
                CategoricalSeries.from_values(
                    name="2024",
                    categories=regions,
                    values=[random.randint(70, 250) for _ in range(6)],
                    style=SeriesStyle(color="#f59e0b"),
                ),
            ])

        # Line chart data
        base_tech = random.randint(120, 180)
        base_health = random.randint(70, 100)
        base_energy = random.randint(60, 90)
        tech_values = [base_tech]
        health_values = [base_health]
        energy_values = [base_energy]
        for _ in range(11):
            tech_values.append(tech_values[-1] + random.randint(-15, 20))
            health_values.append(health_values[-1] + random.randint(-10, 15))
            energy_values.append(energy_values[-1] + random.randint(-12, 12))
        with self._line_data.batch_update():
            self._line_data.set_series([
                NumericSeries.from_y_values(name="TECH Corp", y_values=tech_values, style=SeriesStyle(color="#3b82f6")),
                NumericSeries.from_y_values(name="HEALTH Inc", y_values=health_values, style=SeriesStyle(color="#22c55e")),
                NumericSeries.from_y_values(name="ENERGY Ltd", y_values=energy_values, style=SeriesStyle(color="#ef4444")),
            ])

        # Area chart data
        base_pv = random.randint(10000, 15000)
        pv = [base_pv]
        uv = [int(base_pv * 0.35)]
        conv = [int(uv[0] * 0.1)]
        for _ in range(11):
            pv.append(int(pv[-1] * random.uniform(1.0, 1.15)))
            uv.append(int(pv[-1] * random.uniform(0.3, 0.4)))
            conv.append(int(uv[-1] * random.uniform(0.08, 0.12)))
        with self._area_data.batch_update():
            self._area_data.set_series([
                NumericSeries.from_y_values(name="Page Views", y_values=pv, style=SeriesStyle(color="#06b6d4")),
                NumericSeries.from_y_values(name="Unique Visitors", y_values=uv, style=SeriesStyle(color="#8b5cf6")),
                NumericSeries.from_y_values(name="Conversions", y_values=conv, style=SeriesStyle(color="#22c55e")),
            ])

        # Pie chart data
        browser_values = [random.uniform(5, 70) for _ in range(7)]
        browser_total = sum(browser_values)
        browser_values = [round(v / browser_total * 100, 1) for v in browser_values]
        os_values = [random.uniform(5, 80) for _ in range(5)]
        os_total = sum(os_values)
        os_values = [round(v / os_total * 100, 1) for v in os_values]
        with self._pie_data.batch_update():
            self._pie_data.set_series([
                CategoricalSeries.from_values(
                    name="Browsers",
                    categories=["Chrome", "Safari", "Edge", "Firefox", "Opera", "Samsung", "Other"],
                    values=browser_values,
                )
            ])
        with self._pie_data_2.batch_update():
            self._pie_data_2.set_series([
                CategoricalSeries.from_values(
                    name="OS",
                    categories=["Windows", "macOS", "Linux", "ChromeOS", "Other"],
                    values=os_values,
                )
            ])

        # Scatter chart data
        male_x = [random.randint(165, 190) for _ in range(15)]
        male_y = [int(x * 0.5 + random.randint(-10, 10)) for x in male_x]
        female_x = [random.randint(150, 175) for _ in range(15)]
        female_y = [int(x * 0.4 + random.randint(-8, 8)) for x in female_x]
        with self._scatter_data.batch_update():
            self._scatter_data.set_series([
                NumericSeries.from_values(name="Male", x_values=male_x, y_values=male_y, style=SeriesStyle(color="#3b82f6")),
                NumericSeries.from_values(name="Female", x_values=female_x, y_values=female_y, style=SeriesStyle(color="#ec4899")),
            ])

        # Stacked bar chart data
        categories = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"]
        with self._stacked_data.batch_update():
            self._stacked_data.set_series([
                CategoricalSeries.from_values(name="Electronics", categories=categories, values=[random.randint(30, 80) for _ in range(6)], style=SeriesStyle(color="#3b82f6")),
                CategoricalSeries.from_values(name="Clothing", categories=categories, values=[random.randint(20, 60) for _ in range(6)], style=SeriesStyle(color="#22c55e")),
                CategoricalSeries.from_values(name="Home & Garden", categories=categories, values=[random.randint(15, 50) for _ in range(6)], style=SeriesStyle(color="#f59e0b")),
                CategoricalSeries.from_values(name="Sports", categories=categories, values=[random.randint(10, 40) for _ in range(6)], style=SeriesStyle(color="#ef4444")),
            ])

        # Gauge chart data - use set_value() for efficient single-value updates
        self._gauge_cpu.set_value(random.randint(20, 95))
        self._gauge_memory.set_value(random.randint(30, 95))
        self._gauge_disk.set_value(random.randint(20, 90))
        self._gauge_network.set_value(random.randint(10, 85))

        # Single status update triggers one view() rebuild
        self._status.set("Dashboard refreshed!")

    def _build_bar_chart_tab(self, theme):
        """Bar Chart tab: Full-featured BarChart demonstration."""
        return Column(
            Row(
                Text("Bar Charts - Vertical & Horizontal", font_size=18)
                .text_color(theme.colors.text_primary),
                Spacer(),
                Button("Randomize Data").on_click(self._randomize_bar_data),
                Button("Toggle Series").on_click(self._toggle_bar_series),
            )
            .fixed_height(40),
            Row(
                # Vertical BarChart
                Column(
                    Text("Vertical Bar Chart", font_size=14)
                    .text_color(theme.colors.fg)
                    .fixed_height(22),
                    BarChart(
                        self._bar_data,
                        show_values=True,
                        enable_tooltip=True,
                    )
                    .on_click(lambda e: self._status.set(f"Clicked: {e.label} = {e.value}"))
                    .on_hover(lambda e: self._status.set(f"Hover: {e.label}")),
                ),
                # Horizontal BarChart
                Column(
                    Text("Horizontal Bar Chart", font_size=14)
                    .text_color(theme.colors.fg)
                    .fixed_height(22),
                    BarChart(
                        self._bar_data,
                        show_values=True,
                        enable_tooltip=True,
                        horizontal=True,
                    )
                    .on_click(lambda e: self._status.set(f"Clicked: {e.label} = {e.value}")),
                ),
            ),
        ).bg_color(theme.colors.bg_secondary)

    def _randomize_bar_data(self, _):
        """Randomize bar chart data."""
        import random
        regions = ["North America", "Europe", "Asia Pacific", "Latin America", "Middle East", "Africa"]
        self._bar_data.set_series([
            CategoricalSeries.from_values(
                name="2022",
                categories=regions,
                values=[random.randint(50, 200) for _ in range(6)],
                style=SeriesStyle(color="#6366f1"),
            ),
            CategoricalSeries.from_values(
                name="2023",
                categories=regions,
                values=[random.randint(60, 220) for _ in range(6)],
                style=SeriesStyle(color="#22c55e"),
            ),
            CategoricalSeries.from_values(
                name="2024",
                categories=regions,
                values=[random.randint(70, 250) for _ in range(6)],
                style=SeriesStyle(color="#f59e0b"),
            ),
        ])
        self._status.set("Bar chart data randomized!")

    def _toggle_bar_series(self, _):
        """Toggle visibility of bar chart series."""
        self._bar_data.toggle_series_visibility(0)
        self._status.set("Toggled 2022 series visibility")

    def _build_line_area_tab(self, theme):
        """Line & Area Chart tab: Stock prices and website traffic."""
        return Column(
            Row(
                Text("Line & Area Charts", font_size=18)
                .text_color(theme.colors.text_primary),
                Spacer(),
                Button("Randomize Line").on_click(self._randomize_line_data),
                Button("Randomize Area").on_click(self._randomize_area_data),
            )
            .fixed_height(40),
            # LineChart section
            Text(
                "Stock Price Movement - 3 companies over 12 months (smooth Catmull-Rom splines)",
                font_size=12,
            )
            .text_color(theme.colors.fg)
            .fixed_height(22),
            LineChart(
                self._line_data,
                smooth=True,
                show_points=True,
                enable_tooltip=True,
            )
            .on_click(lambda e: self._status.set(f"Point: {e.label} = ${e.value:.2f}")),
            # AreaChart section
            Text(
                "Website Traffic Analysis - Page views, visitors, and conversions over 12 months",
                font_size=12,
            )
            .text_color(theme.colors.fg)
            .fixed_height(22),
            AreaChart(
                self._area_data,
                fill_opacity=0.4,
                show_points=True,
                enable_tooltip=True,
            )
            .on_click(lambda e: self._status.set(f"Traffic: {e.value:,.0f}")),
        ).bg_color(theme.colors.bg_secondary)

    def _randomize_line_data(self, _):
        """Randomize line chart (stock) data."""
        import random
        base_tech = random.randint(120, 180)
        base_health = random.randint(70, 100)
        base_energy = random.randint(60, 90)

        tech_values = [base_tech]
        health_values = [base_health]
        energy_values = [base_energy]

        for _ in range(11):
            tech_values.append(tech_values[-1] + random.randint(-15, 20))
            health_values.append(health_values[-1] + random.randint(-10, 15))
            energy_values.append(energy_values[-1] + random.randint(-12, 12))

        self._line_data.set_series([
            NumericSeries.from_y_values(
                name="TECH Corp",
                y_values=tech_values,
                style=SeriesStyle(color="#3b82f6"),
            ),
            NumericSeries.from_y_values(
                name="HEALTH Inc",
                y_values=health_values,
                style=SeriesStyle(color="#22c55e"),
            ),
            NumericSeries.from_y_values(
                name="ENERGY Ltd",
                y_values=energy_values,
                style=SeriesStyle(color="#ef4444"),
            ),
        ])
        self._status.set("Stock price data randomized!")

    def _randomize_area_data(self, _):
        """Randomize area chart (traffic) data."""
        import random
        base_pv = random.randint(10000, 15000)
        base_uv = int(base_pv * 0.35)
        base_conv = int(base_uv * 0.1)

        pv = [base_pv]
        uv = [base_uv]
        conv = [base_conv]

        for _ in range(11):
            pv.append(int(pv[-1] * random.uniform(1.0, 1.15)))
            uv.append(int(pv[-1] * random.uniform(0.3, 0.4)))
            conv.append(int(uv[-1] * random.uniform(0.08, 0.12)))

        self._area_data.set_series([
            NumericSeries.from_y_values(
                name="Page Views",
                y_values=pv,
                style=SeriesStyle(color="#06b6d4"),
            ),
            NumericSeries.from_y_values(
                name="Unique Visitors",
                y_values=uv,
                style=SeriesStyle(color="#8b5cf6"),
            ),
            NumericSeries.from_y_values(
                name="Conversions",
                y_values=conv,
                style=SeriesStyle(color="#22c55e"),
            ),
        ])
        self._status.set("Website traffic data randomized!")

    def _build_pie_scatter_tab(self, theme):
        """Pie & Scatter Chart tab: Market share and correlation analysis."""
        return Column(
            Row(
                Text("Pie & Scatter Charts", font_size=18)
                .text_color(theme.colors.text_primary),
                Spacer(),
                Button("Randomize Pie Data").on_click(self._randomize_pie_data),
                Button("Randomize Scatter").on_click(self._randomize_scatter_data),
            )
            .fixed_height(40),
            # Two PieCharts - expanding
            Row(
                Column(
                    Text("Browser Market Share 2024 (Donut)", font_size=14)
                    .text_color(theme.colors.fg)
                    .fixed_height(25),
                    PieChart(
                        self._pie_data,
                        donut=True,
                        inner_radius_ratio=0.55,
                        show_labels=True,
                        show_percentages=True,
                        enable_tooltip=True,
                    ).on_click(lambda e: self._status.set(f"{e.label}: {e.value}%")),
                ),
                Column(
                    Text("Desktop OS Market Share (Pie)", font_size=14)
                    .text_color(theme.colors.fg)
                    .fixed_height(25),
                    PieChart(
                        self._pie_data_2,
                        donut=False,
                        show_labels=True,
                        show_percentages=True,
                        enable_tooltip=True,
                    ).on_click(lambda e: self._status.set(f"{e.label}: {e.value}%")),
                ),
            ),
            # ScatterChart section
            Text(
                "Height vs Weight Correlation - Male (blue) and Female (pink) datasets",
                font_size=12,
            )
            .text_color(theme.colors.fg)
            .fixed_height(22),
            ScatterChart(
                self._scatter_data,
                point_shape=PointShape.CIRCLE,
                point_radius=10,
                enable_tooltip=True,
            ).on_click(
                lambda e: self._status.set(f"Point: ({e.value:.0f} cm, {e.value:.0f} kg)")
            ),
        ).bg_color(theme.colors.bg_secondary)

    def _randomize_pie_data(self, _):
        """Randomize pie chart data."""
        import random
        # Browser market share
        values = [random.uniform(5, 70) for _ in range(7)]
        total = sum(values)
        values = [round(v / total * 100, 1) for v in values]
        self._pie_data.set_series([
            CategoricalSeries.from_values(
                name="Browsers",
                categories=["Chrome", "Safari", "Edge", "Firefox", "Opera", "Samsung", "Other"],
                values=values,
            )
        ])
        # OS market share
        values2 = [random.uniform(5, 80) for _ in range(5)]
        total2 = sum(values2)
        values2 = [round(v / total2 * 100, 1) for v in values2]
        self._pie_data_2.set_series([
            CategoricalSeries.from_values(
                name="OS",
                categories=["Windows", "macOS", "Linux", "ChromeOS", "Other"],
                values=values2,
            )
        ])
        self._status.set("Pie chart data randomized!")

    def _randomize_scatter_data(self, _):
        """Randomize scatter chart data."""
        import random
        male_x = [random.randint(165, 190) for _ in range(15)]
        male_y = [int(x * 0.5 + random.randint(-10, 10)) for x in male_x]
        female_x = [random.randint(150, 175) for _ in range(15)]
        female_y = [int(x * 0.4 + random.randint(-8, 8)) for x in female_x]
        self._scatter_data.set_series([
            NumericSeries.from_values(
                name="Male",
                x_values=male_x,
                y_values=male_y,
                style=SeriesStyle(color="#3b82f6"),
            ),
            NumericSeries.from_values(
                name="Female",
                x_values=female_x,
                y_values=female_y,
                style=SeriesStyle(color="#ec4899"),
            ),
        ])
        self._status.set("Scatter data randomized!")

    def _build_stacked_gauge_tab(self, theme):
        """Stacked Bar & Gauge Chart tab: Product sales and system metrics."""
        return Column(
            Row(
                Text("Stacked Bar & Gauge Charts", font_size=18)
                .text_color(theme.colors.text_primary),
                Spacer(),
                Button("Randomize Stacked").on_click(self._randomize_stacked_data),
                Button("Simulate Metrics").on_click(self._randomize_gauge_data),
            )
            .fixed_height(40),
            # StackedBarChart section
            Text(
                "Product Category Sales - 4 categories (Electronics, Clothing, Home, Sports) over 6 months",
                font_size=12,
            )
            .text_color(theme.colors.fg)
            .fixed_height(22),
            StackedBarChart(
                self._stacked_data,
                show_values=False,
                enable_tooltip=True,
            )
            .on_click(lambda e: self._status.set(f"{e.label}: ${e.value}K")),
            # GaugeCharts section - System Dashboard (2x2 grid)
            Text("System Metrics Dashboard", font_size=14)
            .text_color(theme.colors.fg)
            .fixed_height(25),
            Column(
                # Top row: CPU and Memory
                Row(
                    GaugeChart(
                        self._gauge_cpu,
                        style=GaugeStyle.HALF_CIRCLE,
                        arc_width=30,
                        show_ticks=True,
                    ),
                    GaugeChart(
                        self._gauge_memory,
                        style=GaugeStyle.HALF_CIRCLE,
                        arc_width=30,
                        show_ticks=True,
                    ),
                ),
                # Bottom row: Disk and Network
                Row(
                    GaugeChart(
                        self._gauge_disk,
                        style=GaugeStyle.HALF_CIRCLE,
                        arc_width=30,
                        show_ticks=True,
                    ),
                    GaugeChart(
                        self._gauge_network,
                        style=GaugeStyle.HALF_CIRCLE,
                        arc_width=30,
                        show_ticks=True,
                    ),
                ),
            ),
        ).bg_color(theme.colors.bg_secondary)

    def _randomize_stacked_data(self, _):
        """Randomize stacked bar chart data."""
        import random
        categories = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"]
        self._stacked_data.set_series([
            CategoricalSeries.from_values(
                name="Electronics",
                categories=categories,
                values=[random.randint(30, 80) for _ in range(6)],
                style=SeriesStyle(color="#3b82f6"),
            ),
            CategoricalSeries.from_values(
                name="Clothing",
                categories=categories,
                values=[random.randint(20, 60) for _ in range(6)],
                style=SeriesStyle(color="#22c55e"),
            ),
            CategoricalSeries.from_values(
                name="Home & Garden",
                categories=categories,
                values=[random.randint(15, 50) for _ in range(6)],
                style=SeriesStyle(color="#f59e0b"),
            ),
            CategoricalSeries.from_values(
                name="Sports",
                categories=categories,
                values=[random.randint(10, 40) for _ in range(6)],
                style=SeriesStyle(color="#ef4444"),
            ),
        ])
        self._status.set("Stacked bar data randomized!")

    def _randomize_gauge_data(self, _):
        """Simulate random system metrics."""
        import random
        # Use set_value() instead of creating new GaugeChartData objects
        # This preserves observer connections and reduces object churn
        self._gauge_cpu.set_value(random.randint(20, 95))
        self._gauge_memory.set_value(random.randint(30, 95))
        self._gauge_disk.set_value(random.randint(20, 90))
        self._gauge_network.set_value(random.randint(10, 85))
        self._status.set(f"Metrics: CPU={self._gauge_cpu.value}%, Mem={self._gauge_memory.value}%, Disk={self._gauge_disk.value}%, Net={self._gauge_network.value}%")


if __name__ == "__main__":
    App(
        Frame("All Widgets Demo - Castella", width=1400, height=900),
        AllWidgetsDemo(),
    ).run()
