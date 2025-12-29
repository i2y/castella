"""A2UI Streaming Demo - Progressive Rendering Example

This example demonstrates A2UI streaming capabilities:
- JSONL parsing
- Progressive rendering with beginRendering/updateComponents
- Simulated streaming (for demo without external server)

The demo simulates an agent progressively building a UI, showing how
components appear as they stream in.

Run with:
    uv run python examples/a2ui_streaming_demo.py
"""

import time
from io import StringIO

from castella import App
from castella.a2ui import A2UIRenderer, UserAction
from castella.frame import Frame


def create_streaming_jsonl() -> str:
    """Create a JSONL stream that progressively builds a UI.

    This simulates what an AI agent might output when generating UI.
    Each line is a separate JSON message.
    """
    return """{"beginRendering": {"surfaceId": "main", "root": "root"}}
{"updateComponents": {"surfaceId": "main", "components": [{"id": "root", "component": "Column", "children": {"explicitList": ["header", "content", "footer"]}}]}}
{"updateComponents": {"surfaceId": "main", "components": [{"id": "header", "component": "Text", "text": {"literalString": "Progressive UI Demo"}, "usageHint": "h1"}]}}
{"updateComponents": {"surfaceId": "main", "components": [{"id": "content", "component": "Card", "children": {"explicitList": ["card_content"]}}]}}
{"updateComponents": {"surfaceId": "main", "components": [{"id": "card_content", "component": "Column", "children": {"explicitList": ["intro", "features"]}}]}}
{"updateComponents": {"surfaceId": "main", "components": [{"id": "intro", "component": "Markdown", "content": {"literalString": "## Welcome\\n\\nThis UI was built **progressively** from a JSONL stream.\\n\\nEach component arrived in a separate message."}, "baseFontSize": 14}]}}
{"updateComponents": {"surfaceId": "main", "components": [{"id": "features", "component": "Column", "children": {"explicitList": ["f1", "f2", "f3"]}}]}}
{"updateComponents": {"surfaceId": "main", "components": [{"id": "f1", "component": "Text", "text": {"literalString": "- JSONL streaming support"}}]}}
{"updateComponents": {"surfaceId": "main", "components": [{"id": "f2", "component": "Text", "text": {"literalString": "- Progressive rendering"}}]}}
{"updateComponents": {"surfaceId": "main", "components": [{"id": "f3", "component": "Text", "text": {"literalString": "- SSE/WebSocket transports"}}]}}
{"updateComponents": {"surfaceId": "main", "components": [{"id": "footer", "component": "Row", "children": {"explicitList": ["status", "action_btn"]}}]}}
{"updateComponents": {"surfaceId": "main", "components": [{"id": "status", "component": "Text", "text": {"literalString": "Stream complete!"}, "usageHint": "caption"}]}}
{"updateComponents": {"surfaceId": "main", "components": [{"id": "action_btn", "component": "Button", "text": {"literalString": "Acknowledge"}, "action": {"name": "acknowledge", "context": []}}]}}
"""


def demo_jsonl_parsing():
    """Demo 1: Parse JSONL string directly."""
    print("=" * 60)
    print("Demo 1: JSONL String Parsing")
    print("=" * 60)

    def on_action(action: UserAction):
        print(f"Action: {action.name}")
        print(f"  Source: {action.source_component_id}")

    renderer = A2UIRenderer(on_action=on_action)
    jsonl_content = create_streaming_jsonl()

    # Count messages
    message_count = 0

    def on_update(surface):
        nonlocal message_count
        message_count += 1
        print(f"  Message {message_count}: Surface updated")

    print("\nProcessing JSONL stream...")
    surface = renderer.handle_jsonl(jsonl_content, on_update=on_update)

    if surface:
        print(f"\nSurface created: {surface.surface_id}")
        print(f"Total messages processed: {message_count}")
        return surface.root_widget

    return None


def demo_stream_iterator():
    """Demo 2: Parse from file-like iterator."""
    print("\n" + "=" * 60)
    print("Demo 2: Stream Iterator (File-like)")
    print("=" * 60)

    renderer = A2UIRenderer()
    jsonl_content = create_streaming_jsonl()

    # Simulate file-like object
    stream = StringIO(jsonl_content)

    print("\nProcessing stream...")
    surface = renderer.handle_stream(
        stream, on_update=lambda s: print(f"  Updated: {s.surface_id}")
    )

    if surface:
        print(f"\nSurface created: {surface.surface_id}")
        return surface.root_widget

    return None


def demo_progressive_simulation():
    """Demo 3: Simulate real-time progressive rendering."""
    print("\n" + "=" * 60)
    print("Demo 3: Progressive Rendering Simulation")
    print("=" * 60)

    renderer = A2UIRenderer()
    jsonl_content = create_streaming_jsonl()
    lines = jsonl_content.strip().split("\n")

    print("\nSimulating progressive message arrival...")

    for i, line in enumerate(lines):
        # Simulate network delay
        time.sleep(0.1)

        # Process single message
        surface = renderer.handle_jsonl(line + "\n")

        status = "created" if surface else "pending"
        print(f"  [{i + 1}/{len(lines)}] {status}")

    surface = renderer.get_surface("main")
    if surface:
        print(f"\nFinal surface ready: {surface.surface_id}")
        return surface.root_widget

    return None


def main():
    """Run the streaming demo with GUI."""
    print("A2UI Streaming Demo")
    print("==================")

    # Run demos and get the final widget
    demo_jsonl_parsing()
    demo_stream_iterator()
    widget = demo_progressive_simulation()

    if widget:
        print("\n" + "=" * 60)
        print("Launching GUI...")
        print("=" * 60)
        App(Frame("A2UI Streaming Demo", 800, 600), widget).run()
    else:
        print("Failed to create widget")


def main_simple():
    """Simplified demo - just render the streamed UI."""

    def on_action(action: UserAction):
        print(f"Action: {action.name} from {action.source_component_id}")

    renderer = A2UIRenderer(on_action=on_action)

    # Parse JSONL and render
    jsonl = create_streaming_jsonl()
    surface = renderer.handle_jsonl(jsonl)

    if surface:
        App(Frame("A2UI Streaming Demo", 800, 600), surface.root_widget).run()


if __name__ == "__main__":
    # Use main() for full demo with console output
    # Use main_simple() for just the GUI
    main()
