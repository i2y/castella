"""Tree widget example.

Demonstrates the Tree widget with:
- Hierarchical data display
- Custom icons
- Expand/collapse functionality
- Single and multi-selection modes
"""

from castella import App, Tree, TreeState, TreeNode, Column, Row, Button, Text
from castella.frame import Frame


def main():
    # Create tree data with custom icons
    nodes = [
        TreeNode(
            id="documents",
            label="Documents",
            icon="📁",
            children=[
                TreeNode(id="readme", label="README.md", icon="📄"),
                TreeNode(id="license", label="LICENSE", icon="📄"),
                TreeNode(
                    id="reports",
                    label="Reports",
                    icon="📁",
                    children=[
                        TreeNode(id="q1", label="Q1 Report.pdf", icon="📊"),
                        TreeNode(id="q2", label="Q2 Report.pdf", icon="📊"),
                    ],
                ),
            ],
        ),
        TreeNode(
            id="source",
            label="Source",
            icon="📁",
            children=[
                TreeNode(id="main", label="main.py", icon="🐍"),
                TreeNode(id="utils", label="utils.py", icon="🐍"),
                TreeNode(
                    id="tests",
                    label="tests",
                    icon="📁",
                    children=[
                        TreeNode(id="test_main", label="test_main.py", icon="🧪"),
                        TreeNode(id="test_utils", label="test_utils.py", icon="🧪"),
                    ],
                ),
            ],
        ),
        TreeNode(
            id="config",
            label="Configuration",
            icon="⚙️",
            children=[
                TreeNode(id="settings", label="settings.json", icon="📝"),
                TreeNode(id="env", label=".env", icon="🔐"),
            ],
        ),
    ]

    # Create tree state (single-select mode)
    state = TreeState(nodes, multi_select=False)

    # Status display
    status_text = Text("Select a node", font_size=14)

    def on_select(node: TreeNode):
        icon = node.icon or ""
        status_text._text = f"Selected: {icon} {node.label} (id={node.id})"
        status_text.update()

    def on_expand(node: TreeNode):
        print(f"Expanded: {node.label}")

    def on_collapse(node: TreeNode):
        print(f"Collapsed: {node.label}")

    # Create tree widget
    tree = (
        Tree(state)
        .on_select(on_select)
        .on_expand(on_expand)
        .on_collapse(on_collapse)
    )

    # Control buttons
    def expand_all(_):
        tree.expand_all()

    def collapse_all(_):
        tree.collapse_all()

    def toggle_multi_select(_):
        current = state.is_multi_select()
        state.set_multi_select(not current)
        mode = "Multi-select" if not current else "Single-select"
        status_text._text = f"Mode: {mode}"
        status_text.update()

    controls = Row(
        Button("Expand All").on_click(expand_all),
        Button("Collapse All").on_click(collapse_all),
        Button("Toggle Multi-select").on_click(toggle_multi_select),
    ).fixed_height(40)

    # Main layout
    content = Column(
        Text("Tree Widget Demo", font_size=18)
        .fixed_height(30),
        controls,
        tree,
        status_text.fixed_height(30),
    )

    App(Frame("Tree Demo", 500, 600), content).run()


if __name__ == "__main__":
    main()
