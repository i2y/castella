"""
Multi-Agent Chat Example - Demonstrates MultiAgentChat with multiple agents.

Run with: uv run python skills/castella-agent-ui/examples/multi_agent.py

Note: Requires running A2A agents on the specified ports.
For testing without agents, modify to use mock handlers.
"""

from castella.agent import MultiAgentChat
from castella.a2a import A2AClient, A2AConnectionError


def main():
    # Example agent URLs (replace with actual agents)
    agent_configs = {
        "weather": "http://localhost:8081",
        "travel": "http://localhost:8082",
        "restaurant": "http://localhost:8083",
    }

    # Try to connect to agents
    agents = {}
    for name, url in agent_configs.items():
        try:
            client = A2AClient(url)
            agents[name] = client
            print(f"Connected to {name} agent at {url}")
        except A2AConnectionError:
            print(f"Could not connect to {name} agent at {url}")

    if not agents:
        print("\nNo agents available. Please start some A2A agents first.")
        print("You can use mock agents for testing:")
        print("  uv run python examples/a2a_mock_server.py")
        return

    # Create multi-agent chat
    chat = MultiAgentChat(
        agents=agents,
        title="Multi-Agent Chat",
    )

    print(f"\nStarting chat with {len(agents)} agents...")
    chat.run()


if __name__ == "__main__":
    main()
