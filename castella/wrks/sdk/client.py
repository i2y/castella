"""WrksClient - Threading wrapper for Claude Agent SDK."""

import asyncio
import os
import threading
import uuid
from pathlib import Path
from typing import Any, Callable, Optional

from castella.wrks.sdk.types import ChatMessage, MessageRole, ToolCall, ToolStatus


class WrksClient:
    """Client wrapper for Claude Agent SDK with threading support.

    This client runs the async SDK in a background thread and provides
    callbacks for UI updates.
    """

    def __init__(
        self,
        cwd: Path,
        on_message: Optional[Callable[[ChatMessage], None]] = None,
        on_streaming_text: Optional[Callable[[str], None]] = None,
        on_tool_use: Optional[Callable[[ToolCall], None]] = None,
        on_tool_result: Optional[Callable[[ToolCall], None]] = None,
        on_cost_update: Optional[Callable[[float], None]] = None,
        on_session_id: Optional[Callable[[str], None]] = None,
        on_error: Optional[Callable[[Exception], None]] = None,
        on_complete: Optional[Callable[[], None]] = None,
        resume_session: Optional[str] = None,
        fork_session: bool = False,
        model: str = "haiku",
    ):
        """Initialize the client.

        Args:
            cwd: Working directory for the agent
            on_message: Called when a complete message is received
            on_streaming_text: Called with streaming text chunks
            on_tool_use: Called when a tool is about to be used
            on_tool_result: Called when a tool completes
            on_cost_update: Called with updated cost
            on_session_id: Called with the session ID
            on_error: Called when an error occurs
            on_complete: Called when the response is complete
            resume_session: Session ID to resume
            fork_session: If True, fork the resumed session
            model: Model to use (haiku, sonnet, opus)
        """
        self._cwd = cwd
        self._model = model
        self._on_message = on_message
        self._on_streaming_text = on_streaming_text
        self._on_tool_use = on_tool_use
        self._on_tool_result = on_tool_result
        self._on_cost_update = on_cost_update
        self._on_session_id = on_session_id
        self._on_error = on_error
        self._on_complete = on_complete
        self._resume_session = resume_session
        self._fork_session = fork_session

        self._session_id: Optional[str] = None
        self._total_cost: float = 0.0
        self._is_running = False
        self._current_thread: Optional[threading.Thread] = None

        # For tool approval
        self._pending_tool: Optional[ToolCall] = None
        self._tool_approval_event: Optional[asyncio.Event] = None
        self._tool_approved: bool = False

    @property
    def session_id(self) -> Optional[str]:
        """Get the current session ID."""
        return self._session_id

    @property
    def total_cost(self) -> float:
        """Get the total cost in USD."""
        return self._total_cost

    @property
    def is_running(self) -> bool:
        """Check if a query is currently running."""
        return self._is_running

    def send_message(self, prompt: str) -> None:
        """Send a message to the agent.

        This starts a background thread to run the async SDK.

        Args:
            prompt: The user's message
        """
        if self._is_running:
            return

        self._is_running = True

        def run_async():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(self._async_query(prompt))
            except Exception as e:
                if self._on_error:
                    self._on_error(e)
            finally:
                self._is_running = False
                loop.close()
                if self._on_complete:
                    self._on_complete()

        self._current_thread = threading.Thread(target=run_async, daemon=True)
        self._current_thread.start()

    async def _async_query(self, prompt: str) -> None:
        """Run the actual async query."""
        try:
            from claude_agent_sdk import (
                ClaudeSDKClient,
                ClaudeAgentOptions,
                AssistantMessage,
                TextBlock,
                ToolUseBlock,
                ToolResultBlock,
                ResultMessage,
            )
            from claude_agent_sdk.types import (
                PermissionResultAllow,
                PermissionResultDeny,
            )
        except ImportError:
            raise ImportError(
                "claude-agent-sdk is required. Install with: uv sync --extra wrks"
            )

        # Create approval event for tool callbacks
        self._tool_approval_event = asyncio.Event()

        async def can_use_tool(tool_name: str, input_data: dict, context: Any) -> Any:
            """Callback for tool approval."""
            tool_call = ToolCall(
                id=str(uuid.uuid4()),
                name=tool_name,
                arguments=input_data,
                status=ToolStatus.PENDING,
            )
            self._pending_tool = tool_call

            if self._on_tool_use:
                self._on_tool_use(tool_call)

            # Wait for approval
            self._tool_approval_event.clear()
            await self._tool_approval_event.wait()

            if self._tool_approved:
                tool_call.status = ToolStatus.APPROVED
                return PermissionResultAllow(updated_input=input_data)
            else:
                tool_call.status = ToolStatus.REJECTED
                return PermissionResultDeny(
                    message="User rejected the tool call",
                    interrupt=False,
                )

        options = ClaudeAgentOptions(
            cwd=str(self._cwd),
            include_partial_messages=True,
            can_use_tool=can_use_tool,
            permission_mode="default",
            model=self._model,
            env=dict(os.environ),  # Pass current environment to subprocess
        )

        if self._resume_session:
            options.resume = self._resume_session
            if self._fork_session:
                options.fork_session = True

        current_text = ""

        async with ClaudeSDKClient(options) as client:
            await client.query(prompt)

            async for message in client.receive_response():
                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, TextBlock):
                            # Streaming text
                            new_text = block.text
                            if new_text != current_text:
                                current_text = new_text
                                if self._on_streaming_text:
                                    self._on_streaming_text(current_text)

                        elif isinstance(block, ToolUseBlock):
                            # Tool is being used (after approval)
                            tool_call = ToolCall(
                                id=block.id,
                                name=block.name,
                                arguments=block.input,
                                status=ToolStatus.RUNNING,
                            )
                            if self._on_tool_use:
                                self._on_tool_use(tool_call)

                        elif isinstance(block, ToolResultBlock):
                            # Tool completed
                            if self._pending_tool and self._pending_tool.name:
                                self._pending_tool.result = str(block.content)
                                self._pending_tool.status = ToolStatus.COMPLETED
                                if self._on_tool_result:
                                    self._on_tool_result(self._pending_tool)

                elif isinstance(message, ResultMessage):
                    # Final result
                    self._session_id = message.session_id
                    if self._on_session_id:
                        self._on_session_id(message.session_id)

                    if message.total_cost_usd:
                        self._total_cost += message.total_cost_usd
                        if self._on_cost_update:
                            self._on_cost_update(self._total_cost)

                    # Create final message
                    if current_text and self._on_message:
                        final_message = ChatMessage(
                            role=MessageRole.ASSISTANT,
                            content=current_text,
                            is_streaming=False,
                            cost_usd=message.total_cost_usd,
                        )
                        self._on_message(final_message)

    def approve_tool(self) -> None:
        """Approve the pending tool call."""
        self._tool_approved = True
        if self._tool_approval_event:
            self._tool_approval_event.set()

    def reject_tool(self) -> None:
        """Reject the pending tool call."""
        self._tool_approved = False
        if self._tool_approval_event:
            self._tool_approval_event.set()

    def stop(self) -> None:
        """Stop the current query."""
        # The SDK doesn't have a direct cancel mechanism
        # Setting is_running to False will prevent further processing
        self._is_running = False
        # Also trigger any waiting approval to unblock
        if self._tool_approval_event:
            self._tool_approval_event.set()
