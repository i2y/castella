"""AgentChat A2A Demo

This example demonstrates AgentChat connecting to an A2A agent.

First, start the weather agent server:
    uv run python examples/a2a_demo.py --server

Then run this demo:
    uv run python examples/agent_chat_a2a_demo.py

Or run standalone mode (no server needed):
    uv run python examples/agent_chat_a2a_demo.py --standalone
"""

import sys


def run_a2a_demo():
    """Run AgentChat connected to A2A agent."""
    from castella.agent import AgentChat

    print("Connecting to A2A agent at http://localhost:8080...")
    print("(Make sure the server is running: uv run python examples/a2a_demo.py --server)")
    print()

    try:
        # 3 lines to create a chat UI!
        chat = AgentChat.from_a2a(
            "http://localhost:8080",
            show_agent_card=False,  # Set to True to show agent card
        )
        chat.run()
    except Exception as e:
        print(f"Error: {e}")
        print()
        print("Could not connect to A2A agent.")
        print("Please start the server first:")
        print("  uv run python examples/a2a_demo.py --server")
        print()
        print("Or run standalone mode:")
        print("  uv run python examples/agent_chat_a2a_demo.py --standalone")


def run_standalone_demo():
    """Run AgentChat with a custom handler (no A2A server needed)."""
    from castella.agent import AgentChat

    def simple_handler(message: str) -> str:
        """Simple echo handler with some keywords."""
        msg_lower = message.lower()

        if "hello" in msg_lower or "hi" in msg_lower:
            return "Hello! I'm a simple demo bot. Try asking about 'weather' or 'time'."
        elif "weather" in msg_lower:
            return "The weather is **sunny** with a temperature of 22°C. Perfect for a walk!"
        elif "time" in msg_lower:
            from datetime import datetime
            now = datetime.now().strftime("%H:%M:%S")
            return f"The current time is **{now}**."
        elif "help" in msg_lower:
            return """# Available Commands

- **hello/hi** - Greeting
- **weather** - Get weather info
- **time** - Get current time
- **markdown** - See markdown demo
- **help** - Show this help"""
        elif "markdown" in msg_lower:
            return """# Markdown Demo

I can render **bold**, *italic*, and ~~strikethrough~~ text.

## Code Example

```python
def hello():
    print("Hello, World!")
```

## Lists

1. First item
2. Second item
3. Third item

Enjoy chatting!"""
        else:
            return f"You said: *{message}*\n\nTry asking about **weather**, **time**, or type **help**."

    # Create chat with custom handler
    chat = AgentChat(
        handler=simple_handler,
        title="Demo Bot",
        system_message="Welcome! I'm a demo bot. Type **help** to see available commands.",
    )
    chat.run()


def main():
    if "--standalone" in sys.argv:
        run_standalone_demo()
    else:
        run_a2a_demo()


if __name__ == "__main__":
    main()
