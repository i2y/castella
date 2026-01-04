"""
A2A Async Example - Demonstrates async and streaming communication.

Run with: uv run python skills/castella-a2a/examples/a2a_async.py

Note: Requires a running A2A agent with streaming support.
"""

import asyncio
from castella.a2a import A2AClient, A2AConnectionError, A2AResponseError


async def basic_async():
    """Basic async request."""
    client = A2AClient("http://localhost:8080")

    print("Sending async request...")
    response = await client.ask_async("What is the meaning of life?")
    print(f"Response: {response}")


async def streaming_example():
    """Streaming response example."""
    client = A2AClient("http://localhost:8080")

    if not client.supports_streaming:
        print("Agent does not support streaming, using fallback...")
        response = await client.ask_async("Tell me a short story")
        print(response)
        return

    print("Streaming response:")
    async for chunk in client.ask_stream("Tell me a short story"):
        print(chunk, end="", flush=True)
    print()  # Newline at end


async def parallel_requests():
    """Send multiple requests in parallel."""
    client = A2AClient("http://localhost:8080")

    queries = [
        "What is Python?",
        "What is JavaScript?",
        "What is Rust?",
    ]

    print("Sending parallel requests...")

    tasks = [client.ask_async(q) for q in queries]
    responses = await asyncio.gather(*tasks, return_exceptions=True)

    for query, response in zip(queries, responses):
        if isinstance(response, Exception):
            print(f"Q: {query}\nA: Error - {response}\n")
        else:
            print(f"Q: {query}\nA: {response}\n")


async def main():
    try:
        print("=== Basic Async ===")
        await basic_async()

        print("\n=== Streaming ===")
        await streaming_example()

        print("\n=== Parallel Requests ===")
        await parallel_requests()

    except A2AConnectionError as e:
        print(f"Connection failed: {e}")
        print("Make sure an A2A agent is running at http://localhost:8080")

    except A2AResponseError as e:
        print(f"Agent error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
