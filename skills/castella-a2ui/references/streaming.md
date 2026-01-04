# A2UI Streaming and Transports

Progressive rendering with JSONL streams and various transport protocols.

## JSONL Format

A2UI messages stream as newline-delimited JSON:

```
{"beginRendering": {"surfaceId": "main", "root": "root"}}
{"updateComponents": {"surfaceId": "main", "components": [...]}}
{"updateComponents": {"surfaceId": "main", "components": [...]}}
{"updateDataModel": {"surfaceId": "main", "data": {...}}}
```

Each line is a complete JSON message.

## JSONLParser

Parse JSONL strings:

```python
from castella.a2ui import parse_jsonl_string

messages = parse_jsonl_string(jsonl_content)
for msg in messages:
    print(msg)  # Dict
```

## Streaming from File

```python
from castella.a2ui import A2UIRenderer

renderer = A2UIRenderer()

with open("ui.jsonl") as f:
    surface = renderer.handle_stream(
        f,
        on_update=lambda s: app.redraw()  # Called after each message
    )

widget = surface.root_widget
```

## SSE Transport

Server-Sent Events for HTTP streaming:

```python
from castella.a2ui import A2UIRenderer
from castella.a2ui.transports import sse_stream

renderer = A2UIRenderer()

async def main():
    stream = await sse_stream("http://agent.example.com/ui")
    surface = await renderer.handle_stream_async(stream)
    return surface.root_widget
```

**Requirements:**
```bash
uv sync --extra agent  # Includes httpx
```

## WebSocket Transport

Bidirectional WebSocket streaming:

```python
from castella.a2ui.transports import websocket_stream

async def main():
    stream = await websocket_stream("ws://agent.example.com/ui")
    surface = await renderer.handle_stream_async(stream)
```

**Requirements:**
```bash
pip install websockets
```

## Custom Stream

Create custom async generator:

```python
async def my_stream():
    async for chunk in some_source:
        yield chunk

surface = await renderer.handle_stream_async(my_stream())
```

## A2UIClient Streaming

Connect to A2A agents with streaming:

```python
from castella.a2ui import A2UIClient

client = A2UIClient("http://localhost:10002")

# Streaming response
async for update in client.send_stream("Tell me a story"):
    # update is surface with incremental changes
    app.redraw()
```

## Sync Stream Handling

For synchronous code:

```python
def stream_generator():
    for line in response.iter_lines():
        yield line.decode()

surface = renderer.handle_stream(
    stream_generator(),
    on_update=lambda s: print("Updated!")
)
```

## Progressive Rendering Pattern

```python
from castella import App
from castella.a2ui import A2UIRenderer, A2UIComponent
from castella.frame import Frame

renderer = A2UIRenderer()
app = None

def on_update(surface):
    if app:
        app.redraw()

async def start_stream():
    with open("stream.jsonl") as f:
        surface = renderer.handle_stream(f, on_update=on_update)
    return A2UIComponent(surface)

# Initialize with placeholder, update with stream
component = A2UIComponent(renderer.get_surface("default"))
app = App(Frame("Streaming", 800, 600), component)

# Start stream in background
import asyncio
asyncio.create_task(start_stream())

app.run()
```

## Error Handling

```python
from castella.a2ui import A2UIConnectionError, A2UIParseError

try:
    surface = await renderer.handle_stream_async(stream)
except A2UIConnectionError as e:
    print(f"Connection failed: {e}")
except A2UIParseError as e:
    print(f"Invalid JSONL: {e}")
```

## Performance Tips

1. **Batch component updates** - Send multiple components per `updateComponents`
2. **Use data binding** - `updateDataModel` is cheaper than `updateComponents`
3. **Minimize re-renders** - Group related updates in single message
4. **Buffer appropriately** - Don't send too many tiny messages

## SSE Server Example (Python)

Simple SSE server for testing:

```python
from flask import Flask, Response
import json
import time

app = Flask(__name__)

@app.route('/ui')
def stream_ui():
    def generate():
        yield f"data: {json.dumps({'beginRendering': {'surfaceId': 'main', 'root': 'root'}})}\n\n"

        components = [
            {"id": "root", "component": "Column", "children": {"explicitList": ["msg"]}},
            {"id": "msg", "component": "Text", "text": {"literalString": "Loading..."}}
        ]
        yield f"data: {json.dumps({'updateComponents': {'surfaceId': 'main', 'components': components}})}\n\n"

        time.sleep(1)

        yield f"data: {json.dumps({'updateDataModel': {'surfaceId': 'main', 'data': {'/status': 'Complete!'}}})}\n\n"

    return Response(generate(), mimetype='text/event-stream')

if __name__ == '__main__':
    app.run(port=8080)
```
