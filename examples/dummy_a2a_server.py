"""Dummy A2A servers for testing MultiAgentChat and AgentHub.

Run this first, then run test_multi_agent_chat.py or test_agent_hub.py
in a separate terminal.

Usage:
    python examples/dummy_a2a_server.py
"""

import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
import json


class DummyA2AHandler(BaseHTTPRequestHandler):
    """Simple HTTP handler that responds to A2A requests."""

    # Class-level config set by server
    agent_name = "Dummy Agent"
    agent_description = "A dummy agent for testing"
    agent_port = 8080

    def do_GET(self):
        """Handle GET requests for agent card."""
        if self.path == "/.well-known/agent.json":
            self._send_agent_card()
        else:
            self.send_error(404)

    def do_POST(self):
        """Handle POST requests for messages."""
        if self.path == "/":
            self._handle_message()
        else:
            self.send_error(404)

    def _send_agent_card(self):
        """Send the agent card."""
        agent_card = {
            "name": self.agent_name,
            "description": self.agent_description,
            "version": "1.0.0",
            "url": f"http://localhost:{self.agent_port}",
            "capabilities": {
                "streaming": False,
                "pushNotifications": False,
            },
            "skills": [
                {
                    "name": "chat",
                    "description": "General conversation",
                }
            ],
        }
        self._send_json(agent_card)

    def _handle_message(self):
        """Handle incoming message and send response."""
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8")

        try:
            data = json.loads(body) if body else {}
            message = data.get("message", {})
            content = message.get("content", "")

            # Generate response based on agent type
            if "weather" in self.agent_name.lower():
                response = f"Weather update: It's sunny and 22°C. You asked: {content}"
            elif "travel" in self.agent_name.lower():
                response = f"Travel info: Great destinations await! You asked: {content}"
            elif "echo" in self.agent_name.lower():
                response = f"Echo: {content}"
            else:
                response = f"[{self.agent_name}] Received: {content}"

            response_data = {
                "message": {
                    "role": "agent",
                    "content": response,
                }
            }
            self._send_json(response_data)
        except Exception as e:
            self.send_error(500, str(e))

    def _send_json(self, data):
        """Send JSON response."""
        body = json.dumps(data).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", len(body))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        """Override to add agent name to log."""
        print(f"[{self.agent_name}] {args[0]}")


def create_handler(name: str, description: str, port: int):
    """Create a handler class with custom agent info."""

    class CustomHandler(DummyA2AHandler):
        agent_name = name
        agent_description = description
        agent_port = port

    return CustomHandler


def run_server(port: int, name: str, description: str):
    """Run a single A2A server."""
    handler = create_handler(name, description, port)
    server = HTTPServer(("localhost", port), handler)
    print(f"Starting {name} on http://localhost:{port}")
    server.serve_forever()


def main():
    """Start multiple dummy A2A servers."""
    servers = [
        (8081, "Weather Agent", "Provides weather information"),
        (8082, "Travel Agent", "Provides travel recommendations"),
        (8083, "Echo Agent", "Echoes your messages back"),
    ]

    threads = []
    for port, name, description in servers:
        t = threading.Thread(target=run_server, args=(port, name, description), daemon=True)
        t.start()
        threads.append(t)

    print("\n" + "=" * 50)
    print("Dummy A2A servers running:")
    for port, name, _ in servers:
        print(f"  - {name}: http://localhost:{port}")
    print("=" * 50)
    print("\nPress Ctrl+C to stop\n")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")


if __name__ == "__main__":
    main()
