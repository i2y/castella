"""A2A Protocol Demo

This example demonstrates A2A (Agent-to-Agent) protocol integration:

1. A2A Server: Uses python-a2a directly (Castella focuses on UI layer)
2. A2A Client: Uses python-a2a directly for protocol handling
3. Castella UI: AgentCardView displays agent information

Castella's value-add for A2A:
- AgentCardView: Display agent cards in Desktop/Web/Terminal
- A2UIRenderer: Render A2UI JSON responses as Castella widgets
- (Coming soon) AgentChat: Full chat UI for agent interaction

Run the server (python-a2a):
    uv run python examples/a2a_demo.py --server

Run the client (python-a2a):
    uv run python examples/a2a_demo.py --client

Run the UI demo (Castella AgentCardView):
    uv run python examples/a2a_demo.py
"""

import sys


def run_server():
    """Run a sample A2A server using python-a2a directly."""
    from python_a2a import A2AServer, TaskState, TaskStatus, run_server, skill

    class WeatherAgent(A2AServer):
        """A sample weather agent."""

        @skill(
            name="get_weather",
            description="Get current weather for a location",
            tags=["weather", "current"],
            examples=["What's the weather in Tokyo?"],
        )
        def get_weather(self, location: str = "unknown") -> str:
            return f"Weather in {location}: Sunny, 22°C, Humidity 45%"

        @skill(
            name="forecast",
            description="Get weather forecast for a location",
            tags=["weather", "forecast"],
            examples=["3-day forecast for London"],
        )
        def forecast(self, location: str = "unknown") -> str:
            return f"Forecast for {location}: Sunny → Cloudy → Rainy over the next 3 days"

        @skill(
            name="alerts",
            description="Get weather alerts for a region",
            tags=["weather", "alerts", "emergency"],
        )
        def alerts(self, region: str = "your area") -> str:
            return f"No active weather alerts in {region}"

        def handle_task(self, task):
            """Handle incoming tasks and route to appropriate skill."""
            # Extract message text from task
            message_data = task.message or {}
            content = message_data.get("content", {})
            text = content.get("text", "") if isinstance(content, dict) else str(content)

            # Simple keyword-based routing
            text_lower = text.lower()
            if "forecast" in text_lower:
                response = self.forecast()
            elif "alert" in text_lower:
                response = self.alerts()
            elif "weather" in text_lower:
                response = self.get_weather()
            else:
                response = self.get_weather()

            # Set task response
            task.artifacts = [{"parts": [{"type": "text", "text": response}]}]
            task.status = TaskStatus(state=TaskState.COMPLETED)
            return task

    weather_agent = WeatherAgent(
        name="Weather Agent",
        description="Provides weather information including current conditions, forecasts, and alerts",
        version="1.0.0",
        url="http://localhost:8080",
    )

    print("Starting Weather Agent...")
    print("Connect with: A2AClient('http://localhost:8080')")
    run_server(weather_agent, port=8080)


def run_client():
    """Run a sample A2A client using python-a2a directly."""
    from python_a2a import A2AClient

    print("Connecting to A2A agent at http://localhost:8080...")

    try:
        client = A2AClient("http://localhost:8080")
        card = client.agent_card
        print(f"Connected to: {card.name}")
        print(f"Description: {card.description}")
        print(f"Version: {card.version}")
        print(f"Skills: {[s.name for s in card.skills]}")
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
    from castella import App, Column, Text
    from castella.a2a.types import AgentCard, AgentSkill
    from castella.agent import AgentCardView
    from castella.frame import Frame

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
        .fixed_height(32),
        Text("Connected Agents:")
        .text_color(theme.colors.text_info)
        .fixed_height(24),
        AgentCardView(weather_card, show_url=True),
        AgentCardView(travel_card, show_url=True),
    )

    App(Frame("A2A Demo", 800, 600), ui).run()


def main():
    if "--server" in sys.argv:
        run_server()
    elif "--client" in sys.argv:
        run_client()
    else:
        run_ui_demo()


if __name__ == "__main__":
    main()
