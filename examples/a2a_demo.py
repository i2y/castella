"""A2A Protocol Demo

This example demonstrates A2A (Agent-to-Agent) protocol integration:
1. Creating an A2A server (agent)
2. Connecting to an A2A agent
3. Displaying agent information with AgentCardView

Run the server:
    uv run python examples/a2a_demo.py --server

Run the client:
    uv run python examples/a2a_demo.py --client

Run the UI demo (uses mock data):
    uv run python examples/a2a_demo.py
"""

import sys


def run_server():
    """Run a sample A2A server."""
    from castella.a2a import A2AServer, skill

    class WeatherAgent(A2AServer):
        """A sample weather agent."""

        @skill(
            name="get_weather",
            description="Get current weather for a location",
            tags=["weather", "current"],
            examples=["What's the weather in Tokyo?"],
        )
        def get_weather(self, message: str) -> str:
            # Extract location from message (simple implementation)
            return "Weather: Sunny, 22°C, Humidity 45%"

        @skill(
            name="forecast",
            description="Get weather forecast for a location",
            tags=["weather", "forecast"],
            examples=["3-day forecast for London"],
        )
        def forecast(self, message: str) -> str:
            return "Forecast: Sunny → Cloudy → Rainy over the next 3 days"

        @skill(
            name="alerts",
            description="Get weather alerts for a region",
            tags=["weather", "alerts", "emergency"],
        )
        def alerts(self, message: str) -> str:
            return "No active weather alerts"

    agent = WeatherAgent(
        name="Weather Agent",
        description="Provides weather information including current conditions, forecasts, and alerts",
        version="1.0.0",
    )

    print("Starting Weather Agent...")
    print("Connect with: A2AClient('http://localhost:8080')")
    agent.run(port=8080)


def run_client():
    """Run a sample A2A client."""
    from castella.a2a import A2AClient

    print("Connecting to A2A agent at http://localhost:8080...")

    try:
        client = A2AClient("http://localhost:8080")
        print(f"Connected to: {client.name}")
        print(f"Description: {client.description}")
        print(f"Version: {client.version}")
        print(f"Skills: {[s.name for s in client.skills]}")
        print()

        # Ask questions
        print("Asking: What's the weather?")
        response = client.ask("What's the weather?")
        print(f"Response: {response}")
        print()

        print("Asking: 3-day forecast")
        response = client.ask("forecast for 3 days")
        print(f"Response: {response}")

    except Exception as e:
        print(f"Error: {e}")
        print("Make sure the server is running: python examples/a2a_demo.py --server")


def run_ui_demo():
    """Run UI demo with mock agent card."""
    from castella import run_app
    from castella.a2a.types import AgentCard, AgentSkill
    from castella.agent import AgentCardView
    from castella.column import Column
    from castella.core import SizePolicy
    from castella.text import Text

    # Create mock agent cards for demo
    weather_card = AgentCard(
        name="Weather Agent",
        description="Provides weather information including current conditions, forecasts, and alerts",
        version="1.0.0",
        url="http://localhost:8080",
        skills=[
            AgentSkill(
                id="get_weather",
                name="get_weather",
                description="Get current weather",
                tags=["weather", "current"],
            ),
            AgentSkill(
                id="forecast",
                name="forecast",
                description="Get weather forecast",
                tags=["weather", "forecast"],
            ),
            AgentSkill(
                id="alerts",
                name="alerts",
                description="Get weather alerts",
                tags=["weather", "alerts"],
            ),
        ],
    )

    travel_card = AgentCard(
        name="Travel Agent",
        description="Helps plan travel itineraries and book accommodations",
        version="2.1.0",
        url="http://travel.example.com",
        skills=[
            AgentSkill(
                id="plan_trip",
                name="plan_trip",
                description="Plan a travel itinerary",
                tags=["travel", "planning"],
            ),
            AgentSkill(
                id="book_hotel",
                name="book_hotel",
                description="Book hotel accommodations",
                tags=["travel", "booking"],
            ),
        ],
    )

    # Create UI
    from castella.theme import ThemeManager

    theme = ThemeManager().current

    ui = Column(
        Text("A2A Agent Cards Demo")
        .text_color(theme.colors.text_primary)
        .height(32)
        .height_policy(SizePolicy.FIXED),
        Text("Connected Agents:")
        .text_color(theme.colors.text_secondary)
        .height(24)
        .height_policy(SizePolicy.FIXED),
        AgentCardView(weather_card, show_url=True),
        AgentCardView(travel_card, show_url=True),
    )

    run_app(ui, title="A2A Demo")


def main():
    if "--server" in sys.argv:
        run_server()
    elif "--client" in sys.argv:
        run_client()
    else:
        run_ui_demo()


if __name__ == "__main__":
    main()
