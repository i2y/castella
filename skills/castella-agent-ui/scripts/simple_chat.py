"""
Simple Chat Example - Demonstrates AgentChat with custom handler.

Run with: uv run python skills/castella-agent-ui/examples/simple_chat.py
"""

from castella.agent import AgentChat


def echo_handler(message: str) -> str:
    """Simple echo handler that mirrors user input."""
    return f"You said: {message}"


def main():
    # Create chat with custom handler
    chat = AgentChat(
        handler=echo_handler,
        title="Echo Bot",
        system_message="Hello! I'm an echo bot. I'll repeat what you say!",
        placeholder="Type something...",
    )

    # Run the chat app
    chat.run()


if __name__ == "__main__":
    main()
