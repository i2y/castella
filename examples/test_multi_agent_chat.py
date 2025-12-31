"""Test MultiAgentChat with dummy A2A servers.

First run: python examples/dummy_a2a_server.py
Then run this script.
"""

from castella.agent import MultiAgentChat
from castella.a2a import A2AClient


def main():
    """Run MultiAgentChat with dummy agents."""
    print("Connecting to dummy A2A servers...")

    try:
        # Connect to dummy servers
        weather = A2AClient("http://localhost:8081")
        travel = A2AClient("http://localhost:8082")

        print(f"Connected to: {weather.name}, {travel.name}")

        # Create MultiAgentChat
        chat = MultiAgentChat({
            "weather": weather,
            "travel": travel,
        })

        print("Starting MultiAgentChat...")
        chat.run()

    except Exception as e:
        print(f"Error: {e}")
        print("\nMake sure dummy servers are running:")
        print("  python examples/dummy_a2a_server.py")


if __name__ == "__main__":
    main()
