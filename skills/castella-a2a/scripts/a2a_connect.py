"""
A2A Connection Example - Demonstrates connecting to an A2A agent.

Run with: uv run python skills/castella-a2a/examples/a2a_connect.py

Note: Requires a running A2A agent. See examples/a2a_server.py to run a test server.
"""

from castella.a2a import A2AClient, A2AConnectionError, A2AResponseError


def main():
    # Example agent URL (replace with actual agent)
    agent_url = "http://localhost:8080"

    print(f"Connecting to A2A agent at {agent_url}...")

    try:
        # Create client
        client = A2AClient(agent_url)

        # Display agent info
        print(f"\nConnected to: {client.name}")
        print(f"Description: {client.description}")
        print(f"Version: {client.version}")
        print(f"Streaming: {client.supports_streaming}")

        # List skills
        print("\nSkills:")
        for skill in client.skills:
            print(f"  - {skill.name}: {skill.description}")
            if skill.tags:
                print(f"    Tags: {', '.join(skill.tags)}")

        # Send a test query
        print("\nSending test query...")
        response = client.ask("Hello! What can you do?")
        print(f"Response: {response}")

    except A2AConnectionError as e:
        print(f"\nConnection failed: {e}")
        print("Make sure an A2A agent is running at the specified URL.")

    except A2AResponseError as e:
        print(f"\nAgent error: {e}")


if __name__ == "__main__":
    main()
