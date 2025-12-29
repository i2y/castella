"""Mock A2UI Server - SSE Streaming Demo

A simple FastAPI server that streams A2UI components via Server-Sent Events.
This demonstrates how an AI agent might progressively send UI updates.

Requirements:
    pip install fastapi uvicorn

Run the server:
    uv run python examples/a2ui_mock_server.py

Then run the client:
    uv run python examples/a2ui_sse_client_demo.py
"""

import asyncio
import json
import random
from datetime import datetime

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

app = FastAPI(title="Mock A2UI Server", version="0.1.0")

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def create_weather_ui(city: str) -> list[dict]:
    """Generate A2UI components for a weather display."""
    temp = random.randint(15, 30)
    conditions = random.choice(["Sunny", "Cloudy", "Rainy", "Partly Cloudy"])
    humidity = random.randint(40, 80)

    return [
        {"beginRendering": {"surfaceId": "weather", "root": "root"}},
        {
            "updateComponents": {
                "surfaceId": "weather",
                "components": [
                    {
                        "id": "root",
                        "component": "Column",
                        "children": {"explicitList": ["header", "card", "footer"]},
                    }
                ],
            }
        },
        {
            "updateComponents": {
                "surfaceId": "weather",
                "components": [
                    {
                        "id": "header",
                        "component": "Text",
                        "text": {"literalString": f"Weather in {city}"},
                        "usageHint": "h1",
                    }
                ],
            }
        },
        {
            "updateComponents": {
                "surfaceId": "weather",
                "components": [
                    {
                        "id": "card",
                        "component": "Card",
                        "children": {"explicitList": ["card_content"]},
                    }
                ],
            }
        },
        {
            "updateComponents": {
                "surfaceId": "weather",
                "components": [
                    {
                        "id": "card_content",
                        "component": "Column",
                        "children": {
                            "explicitList": ["temp", "conditions", "humidity", "divider", "details"]
                        },
                    }
                ],
            }
        },
        {
            "updateComponents": {
                "surfaceId": "weather",
                "components": [
                    {
                        "id": "temp",
                        "component": "Text",
                        "text": {"literalString": f"{temp}°C"},
                        "usageHint": "h2",
                    }
                ],
            }
        },
        {
            "updateComponents": {
                "surfaceId": "weather",
                "components": [
                    {
                        "id": "conditions",
                        "component": "Text",
                        "text": {"literalString": conditions},
                        "usageHint": "body",
                    }
                ],
            }
        },
        {
            "updateComponents": {
                "surfaceId": "weather",
                "components": [
                    {
                        "id": "humidity",
                        "component": "Text",
                        "text": {"literalString": f"Humidity: {humidity}%"},
                        "usageHint": "caption",
                    }
                ],
            }
        },
        {
            "updateComponents": {
                "surfaceId": "weather",
                "components": [
                    {
                        "id": "divider",
                        "component": "Divider",
                        "orientation": "horizontal",
                    }
                ],
            }
        },
        {
            "updateComponents": {
                "surfaceId": "weather",
                "components": [
                    {
                        "id": "details",
                        "component": "Markdown",
                        "content": {
                            "literalString": f"""### Forecast Details

- **Temperature**: {temp}°C ({int(temp * 9/5 + 32)}°F)
- **Conditions**: {conditions}
- **Humidity**: {humidity}%
- **Updated**: {datetime.now().strftime("%H:%M:%S")}

*Data provided by Mock Weather API*
"""
                        },
                        "baseFontSize": 13,
                    }
                ],
            }
        },
        {
            "updateComponents": {
                "surfaceId": "weather",
                "components": [
                    {
                        "id": "footer",
                        "component": "Row",
                        "children": {"explicitList": ["refresh_btn", "close_btn"]},
                    }
                ],
            }
        },
        {
            "updateComponents": {
                "surfaceId": "weather",
                "components": [
                    {
                        "id": "refresh_btn",
                        "component": "Button",
                        "text": {"literalString": "Refresh"},
                        "action": {"name": "refresh", "context": []},
                    },
                    {
                        "id": "close_btn",
                        "component": "Button",
                        "text": {"literalString": "Close"},
                        "action": {"name": "close", "context": []},
                    },
                ],
            }
        },
    ]


def create_form_ui() -> list[dict]:
    """Generate A2UI components for a simple form."""
    return [
        {"beginRendering": {"surfaceId": "form", "root": "root"}},
        {
            "updateComponents": {
                "surfaceId": "form",
                "components": [
                    {
                        "id": "root",
                        "component": "Column",
                        "children": {"explicitList": ["title", "form_card"]},
                    }
                ],
            }
        },
        {
            "updateComponents": {
                "surfaceId": "form",
                "components": [
                    {
                        "id": "title",
                        "component": "Text",
                        "text": {"literalString": "Contact Form"},
                        "usageHint": "h1",
                    }
                ],
            }
        },
        {
            "updateComponents": {
                "surfaceId": "form",
                "components": [
                    {
                        "id": "form_card",
                        "component": "Card",
                        "children": {"explicitList": ["form_fields"]},
                    }
                ],
            }
        },
        {
            "updateComponents": {
                "surfaceId": "form",
                "components": [
                    {
                        "id": "form_fields",
                        "component": "Column",
                        "children": {
                            "explicitList": [
                                "name_label",
                                "name_input",
                                "email_label",
                                "email_input",
                                "message_label",
                                "message_input",
                                "agree_check",
                                "submit_btn",
                            ]
                        },
                    }
                ],
            }
        },
        {
            "updateComponents": {
                "surfaceId": "form",
                "components": [
                    {"id": "name_label", "component": "Text", "text": {"literalString": "Name:"}, "usageHint": "caption"},
                    {"id": "name_input", "component": "TextField", "text": {"literalString": ""}, "usageHint": "text"},
                ],
            }
        },
        {
            "updateComponents": {
                "surfaceId": "form",
                "components": [
                    {"id": "email_label", "component": "Text", "text": {"literalString": "Email:"}, "usageHint": "caption"},
                    {"id": "email_input", "component": "TextField", "text": {"literalString": ""}, "usageHint": "email"},
                ],
            }
        },
        {
            "updateComponents": {
                "surfaceId": "form",
                "components": [
                    {"id": "message_label", "component": "Text", "text": {"literalString": "Message:"}, "usageHint": "caption"},
                    {"id": "message_input", "component": "TextField", "text": {"literalString": ""}, "usageHint": "multiline"},
                ],
            }
        },
        {
            "updateComponents": {
                "surfaceId": "form",
                "components": [
                    {
                        "id": "agree_check",
                        "component": "CheckBox",
                        "label": {"literalString": "I agree to the terms"},
                        "checked": {"literalBoolean": False},
                    }
                ],
            }
        },
        {
            "updateComponents": {
                "surfaceId": "form",
                "components": [
                    {
                        "id": "submit_btn",
                        "component": "Button",
                        "text": {"literalString": "Submit"},
                        "action": {"name": "submit_form", "context": []},
                    }
                ],
            }
        },
    ]


@app.get("/")
async def root():
    """API info."""
    return {
        "name": "Mock A2UI Server",
        "version": "0.1.0",
        "endpoints": {
            "/ui/weather": "Weather display (SSE)",
            "/ui/form": "Contact form (SSE)",
        },
    }


@app.get("/ui/weather")
async def weather_ui(city: str = Query(default="Tokyo")):
    """Stream a weather UI via SSE."""

    async def generate():
        messages = create_weather_ui(city)
        for msg in messages:
            # SSE format: "data: <json>\n\n"
            yield f"data: {json.dumps(msg)}\n\n"
            await asyncio.sleep(0.15)  # Simulate progressive generation

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )


@app.get("/ui/form")
async def form_ui():
    """Stream a contact form UI via SSE."""

    async def generate():
        messages = create_form_ui()
        for msg in messages:
            yield f"data: {json.dumps(msg)}\n\n"
            await asyncio.sleep(0.1)  # Simulate progressive generation

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )


if __name__ == "__main__":
    import uvicorn

    print("Starting Mock A2UI Server...")
    print("Endpoints:")
    print("  - http://localhost:8080/ui/weather?city=Tokyo")
    print("  - http://localhost:8080/ui/form")
    print()
    uvicorn.run(app, host="0.0.0.0", port=8080)
