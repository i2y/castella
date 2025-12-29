"""Test AgentHub with dummy A2A servers.

First run: python examples/dummy_a2a_server.py
Then run this script.
"""

from castella import App
from castella.agent import AgentHub
from castella.a2a import A2AClient
from castella.frame import Frame


def main():
    """Run AgentHub with dummy agents."""
    print("Connecting to dummy A2A servers...")

    try:
        # Create AgentHub and add agents
        hub = AgentHub(title="Agent Hub Demo")

        # Connect to dummy servers
        hub.add_agent("http://localhost:8081")  # Weather
        hub.add_agent("http://localhost:8082")  # Travel
        hub.add_agent("http://localhost:8083")  # Echo

        print("Starting AgentHub...")
        hub.run()

    except Exception as e:
        print(f"Error: {e}")
        print("\nMake sure dummy servers are running:")
        print("  python examples/dummy_a2a_server.py")


if __name__ == "__main__":
    main()
