"""
Agent Hub Example - Demonstrates AgentHub for agent discovery and management.

Run with: uv run python skills/castella-agent-ui/examples/agent_hub.py

This creates a dashboard where you can:
- View connected agents
- Add new agents by URL
- Chat with selected agents
"""

from castella.agent import AgentHub
from castella.a2a import A2AClient, A2AConnectionError


def main():
    # Create agent hub
    hub = AgentHub(title="Agent Hub Dashboard")

    # Try to connect to some default agents
    default_agents = [
        "http://localhost:8080",
        "http://localhost:8081",
        "http://localhost:8082",
    ]

    connected = 0
    for url in default_agents:
        try:
            hub.add_agent(url)
            print(f"Connected to agent at {url}")
            connected += 1
        except A2AConnectionError:
            print(f"No agent at {url} (skipping)")

    print(f"\nStarting Agent Hub with {connected} connected agents")
    print("You can add more agents using the URL input in the UI")
    print()

    # Run the hub
    hub.run()


if __name__ == "__main__":
    main()
