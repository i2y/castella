# A2A Streaming Responses

Handle streaming responses from A2A agents.

## Check Streaming Support

```python
from castella.a2a import A2AClient

client = A2AClient("http://agent.example.com")

if client.supports_streaming:
    print("Agent supports streaming")
else:
    print("Streaming not supported")
```

## Async Streaming

Use `ask_stream()` for streaming responses:

```python
async def stream_response():
    client = A2AClient("http://agent.example.com")

    async for chunk in client.ask_stream("Tell me a story"):
        print(chunk, end="", flush=True)

    print()  # Newline at end
```

## Streaming with Progress

```python
async def stream_with_progress(query: str):
    client = A2AClient("http://agent.example.com")

    full_response = []

    async for chunk in client.ask_stream(query):
        full_response.append(chunk)
        # Update UI with partial response
        update_display("".join(full_response))

    return "".join(full_response)
```

## Fallback Pattern

Handle agents that don't support streaming:

```python
async def ask_with_fallback(client: A2AClient, query: str) -> str:
    if client.supports_streaming:
        chunks = []
        async for chunk in client.ask_stream(query):
            chunks.append(chunk)
            yield chunk
        return "".join(chunks)
    else:
        response = await client.ask_async(query)
        yield response
        return response
```

## Streaming in Chat UI

Integration with ChatContainer:

```python
from castella.agent import ChatMessageData
from castella.a2a import A2AClient

async def handle_message(client: A2AClient, messages: ListState, query: str):
    # Add user message
    messages.append(ChatMessageData(role="user", content=query))

    # Add placeholder for assistant
    messages.append(ChatMessageData(role="assistant", content=""))

    if client.supports_streaming:
        full_response = []
        async for chunk in client.ask_stream(query):
            full_response.append(chunk)
            # Update last message
            messages[-1] = ChatMessageData(
                role="assistant",
                content="".join(full_response)
            )
    else:
        response = await client.ask_async(query)
        messages[-1] = ChatMessageData(role="assistant", content=response)
```

## Error Handling in Streams

```python
from castella.a2a import A2AConnectionError, A2AResponseError

async def safe_stream(client: A2AClient, query: str):
    try:
        async for chunk in client.ask_stream(query):
            yield chunk
    except A2AConnectionError as e:
        yield f"\n\n[Connection lost: {e}]"
    except A2AResponseError as e:
        yield f"\n\n[Error: {e}]"
```

## Cancellation

Cancel streaming mid-response:

```python
import asyncio

async def cancellable_stream(client: A2AClient, query: str):
    task = asyncio.create_task(stream_response(client, query))

    try:
        result = await asyncio.wait_for(task, timeout=30.0)
        return result
    except asyncio.TimeoutError:
        task.cancel()
        return "Response timed out"
    except asyncio.CancelledError:
        return "Response cancelled"
```

## Streaming with A2UI

Combine streaming with A2UI progressive rendering:

```python
from castella.a2ui import A2UIClient

client = A2UIClient("http://agent.example.com")

# Stream UI updates
async for surface in client.send_stream("Show me restaurants"):
    # surface contains incremental UI updates
    app.redraw()
```

## Performance Tips

1. **Buffer appropriately** - Don't yield too frequently
   ```python
   buffer = []
   async for chunk in client.ask_stream(query):
       buffer.append(chunk)
       if len(buffer) >= 10:  # Batch updates
           yield "".join(buffer)
           buffer = []
   ```

2. **Use async context** - Keep UI responsive
   ```python
   async def background_stream():
       async for chunk in client.ask_stream(query):
           await update_ui(chunk)
   ```

3. **Handle backpressure** - Don't overwhelm UI
   ```python
   async for chunk in client.ask_stream(query):
       await ui_update_queue.put(chunk)
   ```
