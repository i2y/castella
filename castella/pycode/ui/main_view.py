"""Main view for pycode.

This is the primary UI component that combines chat, tools, and file browsing.
"""

from __future__ import annotations

import base64
import threading
from pathlib import Path
from typing import TYPE_CHECKING, Any

from castella import Box, Button, Column, Image, Row, ScrollState, Spacer, Text
from castella.core import Component, ListState, SizePolicy, State
from castella.file_tree import FileTree, FileTreeState
from castella.markdown import Markdown
from castella.multiline_input import MultilineInput, MultilineInputState

# Supported image extensions
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"}

if TYPE_CHECKING:
    from castella.pycode.agent.coding_agent import CodingAgent, MockCodingAgent
    from castella.pycode.config import Config


class MainView(Component):
    """Main view component for pycode.

    Combines:
    - Sidebar with file tree, context files, and tool history
    - Chat panel with message history
    - Input area for user messages
    """

    def __init__(
        self,
        config: "Config",
        agent: "CodingAgent | MockCodingAgent",
    ):
        """Initialize the main view.

        Args:
            config: Application configuration
            agent: The coding agent instance
        """
        super().__init__()
        self._config = config
        self._agent = agent

        # Message history (reactive)
        self._messages: ListState[dict[str, Any]] = ListState([])
        self._messages.attach(self)

        # Tool usage history (reactive)
        self._tool_calls: ListState[dict[str, Any]] = ListState([])
        self._tool_calls.attach(self)

        # Context files - files added to the conversation context
        # Each entry: {"path": str, "content": str, "name": str}
        self._context_files: ListState[dict[str, Any]] = ListState([])
        self._context_files.attach(self)

        # Input state
        self._input_state = MultilineInputState("")

        # Scroll state (don't attach - preserves position)
        self._scroll_state = ScrollState()

        # Loading state
        self._is_loading = State(False)
        self._is_loading.attach(self)

        # Current response being streamed
        self._streaming_response = State("")
        self._streaming_response.attach(self)

        # File tree state
        self._file_tree_state = FileTreeState(
            root_path=str(config.cwd),
            show_hidden=False,
            dirs_first=True,
        )

        # Sidebar collapsed state
        self._sidebar_collapsed = State(False)
        self._sidebar_collapsed.attach(self)

        # Add welcome message
        self._messages.append(
            {
                "role": "system",
                "content": f"Welcome to **pycode**! I'm your AI coding assistant.\n\n"
                f"Working directory: `{config.cwd}`\n"
                f"Model: `{agent.model}`\n\n"
                "Click files in the sidebar to add them to context.\n"
                "How can I help you today?",
            }
        )

    def _on_tool_use(self, name: str, args: dict[str, Any]) -> None:
        """Callback when a tool is invoked."""
        self._tool_calls.append(
            {
                "name": name,
                "args": args,
                "status": "running",
                "result": None,
            }
        )

    def _on_tool_result(self, name: str, result: str) -> None:
        """Callback when a tool completes."""
        # Update the last tool call with the same name
        for i in range(len(self._tool_calls) - 1, -1, -1):
            if (
                self._tool_calls[i]["name"] == name
                and self._tool_calls[i]["status"] == "running"
            ):
                call = self._tool_calls[i].copy()
                call["status"] = "completed"
                call["result"] = result
                self._tool_calls[i] = call
                break

    def _send_message(self, event=None) -> None:
        """Handle sending a message."""
        text = self._input_state.value().strip()
        if not text or self._is_loading():
            return

        # Separate text and image context files
        text_files = []
        image_files = []
        for ctx_file in self._context_files:
            file_type = ctx_file.get("type", "text")
            if file_type == "image":
                image_files.append(ctx_file)
            else:
                text_files.append(ctx_file)

        # Build context for text files
        context_parts = []
        if text_files:
            context_parts.append("**Context files:**\n")
            for ctx_file in text_files:
                context_parts.append(
                    f"\n`{ctx_file['name']}`:\n```\n{ctx_file['content']}\n```\n"
                )

        # Display message (without context for cleaner UI)
        display_content = text
        if self._context_files:
            file_names = ", ".join(f"`{f['name']}`" for f in self._context_files)
            display_content = f"[Context: {file_names}]\n\n{text}"

        # Add user message to UI
        self._messages.append(
            {
                "role": "user",
                "content": display_content,
            }
        )

        # Build full message for agent (with file contents)
        if context_parts:
            full_message = "".join(context_parts) + "\n**User request:**\n" + text
        else:
            full_message = text

        # Add image descriptions to the message
        if image_files:
            image_desc = "\n\n**Images provided:**\n"
            for img in image_files:
                image_desc += f"- `{img['name']}`\n"
            full_message += image_desc

        # Prepare image data for multimodal models
        image_data_list = []
        for img in image_files:
            try:
                img_path = Path(img["path"])
                img_bytes = img_path.read_bytes()
                img_base64 = base64.b64encode(img_bytes).decode("utf-8")
                # Determine MIME type
                ext = img_path.suffix.lower()
                mime_map = {
                    ".png": "image/png",
                    ".jpg": "image/jpeg",
                    ".jpeg": "image/jpeg",
                    ".gif": "image/gif",
                    ".webp": "image/webp",
                    ".bmp": "image/bmp",
                }
                mime_type = mime_map.get(ext, "image/png")
                image_data_list.append(
                    {
                        "name": img["name"],
                        "base64": img_base64,
                        "mime_type": mime_type,
                    }
                )
            except Exception:
                pass  # Skip failed images

        # Clear input
        self._input_state.set("")

        # Set loading state
        self._is_loading.set(True)
        self._streaming_response.set("")

        # Scroll to bottom
        self._scroll_state.y = 999999

        # Run agent in background thread
        def run_agent():
            try:
                from castella.pycode.agent.coding_agent import CodingDeps

                deps = CodingDeps(
                    cwd=self._config.cwd,
                    on_tool_use=self._on_tool_use,
                    on_tool_result=self._on_tool_result,
                )

                # Run synchronously for now (streaming TBD)
                # Pass images if available
                response = self._agent.run_sync(
                    full_message,
                    deps,
                    images=image_data_list if image_data_list else None,
                )

                # Update UI on main thread
                self._scroll_state.y = 999999
                self._messages.append(
                    {
                        "role": "assistant",
                        "content": response,
                    }
                )

            except Exception as e:
                self._scroll_state.y = 999999
                self._messages.append(
                    {
                        "role": "system",
                        "content": f"**Error:** {e}",
                    }
                )
            finally:
                self._is_loading.set(False)
                self._streaming_response.set("")

        thread = threading.Thread(target=run_agent, daemon=True)
        thread.start()

    def _on_file_select(self, path: Path) -> None:
        """Handle file selection in file tree - add file to context."""
        # Check if file is already in context
        path_str = str(path)
        for ctx_file in self._context_files:
            if ctx_file["path"] == path_str:
                # Already in context, don't add again
                return

        # Get relative path for display
        try:
            rel_path = path.relative_to(self._config.cwd)
            name = str(rel_path)
        except ValueError:
            name = path.name

        # Check if it's an image file
        ext = path.suffix.lower()
        if ext in IMAGE_EXTENSIONS:
            # Store as image (path only, no content)
            self._context_files.append(
                {
                    "path": path_str,
                    "name": name,
                    "type": "image",
                    "content": None,
                }
            )
            return

        # Read text file content
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
            # Truncate if too large
            max_size = 50000  # ~50KB
            if len(content) > max_size:
                content = content[:max_size] + "\n\n... (truncated)"

            self._context_files.append(
                {
                    "path": path_str,
                    "name": name,
                    "type": "text",
                    "content": content,
                }
            )

        except Exception as e:
            # Show error in chat
            self._messages.append(
                {
                    "role": "system",
                    "content": f"**Error reading file:** {path.name}\n{e}",
                }
            )

    def _remove_context_file(self, path: str) -> None:
        """Remove a file from the context."""
        for i, ctx_file in enumerate(self._context_files):
            if ctx_file["path"] == path:
                del self._context_files[i]
                break

    def _toggle_sidebar(self, event=None) -> None:
        """Toggle sidebar visibility."""
        self._sidebar_collapsed.set(not self._sidebar_collapsed())

    def _clear_chat(self, event=None) -> None:
        """Clear chat history and context files."""
        self._messages.set(
            [
                {
                    "role": "system",
                    "content": f"Chat cleared. Working directory: `{self._config.cwd}`\n\n"
                    "Click files in the sidebar to add them to context.",
                }
            ]
        )
        self._tool_calls.set([])
        self._context_files.set([])
        self._agent.clear_history()

    def view(self):
        from castella.theme import ThemeManager

        theme = ThemeManager().current

        # Build main layout
        elements = []

        # Header bar
        elements.append(self._build_header(theme))

        # Main content area (sidebar + chat)
        content_row = []

        # Sidebar (collapsible)
        if not self._sidebar_collapsed():
            content_row.append(self._build_sidebar(theme))

        # Chat panel
        content_row.append(self._build_chat_panel(theme))

        elements.append(Row(*content_row))

        return Column(*elements).bg_color(theme.colors.bg_canvas)

    def _build_header(self, theme) -> Box:
        """Build the header bar."""
        return (
            Box(
                Row(
                    Button("☰").on_click(self._toggle_sidebar).fixed_size(36, 28),
                    Text("pycode", font_size=16)
                    .text_color(theme.colors.text_primary)
                    .fixed_height(24),
                    Spacer(),
                    Text(self._agent.model, font_size=12)
                    .text_color(theme.colors.text_info)
                    .fixed_height(20),
                    Button("Clear").on_click(self._clear_chat).fixed_size(60, 28),
                ).fixed_height(36)
            )
            .bg_color(theme.colors.bg_secondary)
            .fixed_height(44)
        )

    def _build_sidebar(self, theme) -> Column:
        """Build the sidebar with context files, file tree, and tools."""
        elements = []

        # Context files section (always show if there are files)
        if self._context_files:
            elements.append(
                Text("Context", font_size=14)
                .text_color(theme.colors.text_primary)
                .fixed_height(24)
            )

            for ctx_file in self._context_files:
                file_path = ctx_file["path"]
                file_type = ctx_file.get("type", "text")

                if file_type == "image":
                    # Show image thumbnail
                    elements.append(
                        Row(
                            Text(f"🖼️ {ctx_file['name']}", font_size=12)
                            .text_color(theme.colors.text_info)
                            .fixed_height(20),
                            Spacer(),
                            Button("×")
                            .on_click(
                                lambda _, p=file_path: self._remove_context_file(p)
                            )
                            .fixed_size(20, 20),
                        ).fixed_height(24)
                    )
                    # Add thumbnail
                    elements.append(Image(file_path).fixed_size(180, 100))
                    elements.append(Spacer().fixed_height(4))
                else:
                    # Text file - just show name
                    file_row = Row(
                        Text(f"📄 {ctx_file['name']}", font_size=12)
                        .text_color(theme.colors.text_info)
                        .fixed_height(20),
                        Spacer(),
                        Button("×")
                        .on_click(lambda _, p=file_path: self._remove_context_file(p))
                        .fixed_size(20, 20),
                    ).fixed_height(24)
                    elements.append(file_row)

            elements.append(Spacer().fixed_height(8))

        # File tree section
        elements.append(
            Text("Files", font_size=14)
            .text_color(theme.colors.text_primary)
            .fixed_height(24)
        )

        file_tree = FileTree(self._file_tree_state).on_file_select(self._on_file_select)
        elements.append(file_tree)

        # Tool calls section
        if self._tool_calls:
            elements.append(
                Text("Recent Tools", font_size=14)
                .text_color(theme.colors.text_primary)
                .fixed_height(24)
            )

            # Show last 5 tool calls
            for call in list(self._tool_calls)[-5:]:
                status_icon = "✓" if call["status"] == "completed" else "..."
                elements.append(
                    Text(f"{status_icon} {call['name']}", font_size=12)
                    .text_color(
                        theme.colors.text_success
                        if call["status"] == "completed"
                        else theme.colors.text_warning
                    )
                    .fixed_height(20)
                )

        return Column(*elements).bg_color(theme.colors.bg_secondary).fixed_width(200)

    def _build_chat_panel(self, theme) -> Column:
        """Build the chat panel with messages and input."""
        elements = []

        # Message list
        msg_widgets = self._build_messages(theme)

        # Loading indicator
        if self._is_loading():
            streaming_text = self._streaming_response()
            if streaming_text:
                msg_widgets.append(
                    self._build_message_widget("assistant", streaming_text + "▌", theme)
                )
            else:
                msg_widgets.append(
                    Box(
                        Text("Thinking...", font_size=14)
                        .text_color(theme.colors.text_info)
                        .fixed_height(24)
                    )
                    .bg_color(theme.colors.bg_secondary)
                    .height_policy(SizePolicy.CONTENT)
                )

        elements.append(
            Column(
                *msg_widgets,
                scrollable=True,
                scroll_state=self._scroll_state,
            ).bg_color(theme.colors.bg_primary)
        )

        # Input area
        elements.append(self._build_input_area(theme))

        return Column(*elements)

    def _build_messages(self, theme) -> list:
        """Build message widgets."""
        widgets = []
        for msg in self._messages:
            widgets.append(
                self._build_message_widget(msg["role"], msg["content"], theme)
            )
            widgets.append(Spacer().fixed_height(8))
        return widgets

    def _build_message_widget(self, role: str, content: str, theme) -> Box:
        """Build a single message widget."""
        # Role-based styling
        if role == "user":
            bg_color = theme.colors.bg_tertiary
            role_label = "You"
            role_color = theme.colors.text_primary
        elif role == "assistant":
            bg_color = theme.colors.bg_secondary
            role_label = "Assistant"
            role_color = theme.colors.text_info
        else:
            bg_color = theme.colors.bg_primary
            role_label = "System"
            role_color = theme.colors.text_warning

        return (
            Box(
                Column(
                    Text(role_label, font_size=14)
                    .text_color(role_color)
                    .fixed_height(20),
                    Markdown(content, base_font_size=14),
                ).height_policy(SizePolicy.CONTENT)
            )
            .bg_color(bg_color)
            .height_policy(SizePolicy.CONTENT)
        )

    def _build_input_area(self, theme) -> Row:
        """Build the input area with text field and send button."""
        send_label = "..." if self._is_loading() else "Send"

        return (
            Row(
                MultilineInput(
                    self._input_state,
                    font_size=14,
                    wrap=True,
                ).fixed_height(40),
                Button(send_label).on_click(self._send_message).fixed_size(70, 40),
            )
            .bg_color(theme.colors.bg_secondary)
            .fixed_height(56)
        )
