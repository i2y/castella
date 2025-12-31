"""Test MCP client that connects to the Castella MCP server.

This script demonstrates how an AI agent can interact with a Castella
UI via the Model Context Protocol.
"""

import json
import subprocess
import sys
import time
import threading
from queue import Queue, Empty


def send_message(proc, message):
    """Send a JSON-RPC message to the MCP server."""
    json_str = json.dumps(message)
    proc.stdin.write(json_str + "\n")
    proc.stdin.flush()


def read_responses(proc, queue, stop_event):
    """Read responses from the MCP server in a background thread."""
    while not stop_event.is_set():
        try:
            line = proc.stdout.readline()
            if line:
                try:
                    response = json.loads(line.strip())
                    queue.put(response)
                except json.JSONDecodeError:
                    pass
        except Exception:
            break


def wait_for_response(queue, timeout=5.0):
    """Wait for a response from the queue."""
    try:
        return queue.get(timeout=timeout)
    except Empty:
        return None


def main():
    print("=" * 60)
    print("Castella MCP Client Test")
    print("=" * 60)
    print()

    # Start the MCP demo as a subprocess
    print("Starting MCP server...")
    proc = subprocess.Popen(
        [sys.executable, "examples/mcp_demo.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )

    # Give the server time to start
    time.sleep(2)
    print("MCP server started!")
    print()

    # Set up response reader
    response_queue = Queue()
    stop_event = threading.Event()
    reader_thread = threading.Thread(
        target=read_responses, args=(proc, response_queue, stop_event)
    )
    reader_thread.daemon = True
    reader_thread.start()

    try:
        # Initialize the MCP connection
        print("Step 1: Initialize MCP connection")
        print("-" * 40)
        init_message = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test-client", "version": "1.0.0"},
            },
        }
        send_message(proc, init_message)
        time.sleep(0.5)

        response = wait_for_response(response_queue, timeout=2.0)
        if response:
            print(f"Response: {json.dumps(response, indent=2)}")
        else:
            print("No response received (server might be running in GUI mode)")
        print()

        # List available tools
        print("Step 2: List available tools")
        print("-" * 40)
        tools_message = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {},
        }
        send_message(proc, tools_message)
        time.sleep(0.5)

        response = wait_for_response(response_queue, timeout=2.0)
        if response and "result" in response:
            tools = response["result"].get("tools", [])
            print(f"Available tools ({len(tools)}):")
            for tool in tools:
                print(f"  - {tool['name']}: {tool.get('description', '')[:50]}...")
        else:
            print("No tools response")
        print()

        # List resources
        print("Step 3: List available resources")
        print("-" * 40)
        resources_message = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "resources/list",
            "params": {},
        }
        send_message(proc, resources_message)
        time.sleep(0.5)

        response = wait_for_response(response_queue, timeout=2.0)
        if response and "result" in response:
            resources = response["result"].get("resources", [])
            print(f"Available resources ({len(resources)}):")
            for res in resources:
                print(f"  - {res['uri']}: {res.get('name', '')}")
        else:
            print("No resources response")
        print()

        # Call list_actionable tool
        print("Step 4: Call list_actionable() tool")
        print("-" * 40)
        call_message = {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {
                "name": "list_actionable",
                "arguments": {},
            },
        }
        send_message(proc, call_message)
        time.sleep(0.5)

        response = wait_for_response(response_queue, timeout=2.0)
        if response and "result" in response:
            content = response["result"].get("content", [])
            if content:
                data = json.loads(content[0].get("text", "[]"))
                if isinstance(data, list):
                    print(f"Interactive elements ({len(data)}):")
                    for elem in data:
                        if isinstance(elem, dict):
                            print(f"  - {elem['id']}: {elem['type']} ({elem.get('label', 'no label')})")
                        else:
                            print(f"  - {elem}")
                elif isinstance(data, dict):
                    print(f"Interactive elements ({len(data)}):")
                    for elem_id, elem in data.items():
                        if isinstance(elem, dict):
                            print(f"  - {elem.get('id', elem_id)}: {elem.get('type', 'unknown')}")
                        else:
                            print(f"  - {elem_id}: {elem}")
        else:
            print("No response from list_actionable")
        print()

        # Try clicking a button
        print("Step 5: Click 'increment-btn'")
        print("-" * 40)
        click_message = {
            "jsonrpc": "2.0",
            "id": 5,
            "method": "tools/call",
            "params": {
                "name": "click",
                "arguments": {"element_id": "increment-btn"},
            },
        }
        send_message(proc, click_message)
        time.sleep(0.5)

        response = wait_for_response(response_queue, timeout=2.0)
        if response and "result" in response:
            content = response["result"].get("content", [])
            if content:
                result = json.loads(content[0].get("text", "{}"))
                print(f"Click result: {result}")
        else:
            print("No response from click")
        print()

        print("=" * 60)
        print("Test complete! The GUI window should still be visible.")
        print("Close the window to exit.")
        print("=" * 60)

        # Wait for the GUI to close
        proc.wait()

    except KeyboardInterrupt:
        print("\nInterrupted by user")
    finally:
        stop_event.set()
        proc.terminate()
        proc.wait()


if __name__ == "__main__":
    main()
