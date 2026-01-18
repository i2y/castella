"""Main window component for wrks.

This is the primary UI component that combines sidebar (projects, sessions, files, context)
with chat panel in a pycode-style layout.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from castella import (
    Box,
    Button,
    Column,
    ModalState,
    Row,
    ScrollState,
    Spacer,
    Text,
    Widget,
)
from castella.core import Component, ListState, SizePolicy, State
from castella.file_tree import FileTree, FileTreeState
from castella.markdown import Markdown
from castella.multiline_input import MultilineInput, MultilineInputState
from castella.theme import ThemeManager

from castella.wrks.sdk import WrksClient, ChatMessage, MessageRole, ToolCall, ToolStatus
from castella.wrks.storage import (
    Project,
    ProjectManager,
    SessionMetadata,
    MetadataStore,
)
from castella.wrks.storage.sessions import list_sessions
from castella.wrks.ui.cost_display import CostDisplay
from castella.wrks.ui.tool_display import ToolCallView, ToolApprovalModal


class MainWindow(Component):
    """Main application window with sidebar + chat layout.

    Layout:
    ┌────────────────────────────────────────────────────────┐
    │ Header: ☰ wrks   [project-name]   Cost: $0.02          │
    ├───────────┬────────────────────────────────────────────┤
    │ Sidebar   │ Chat Panel                                 │
    │           │                                            │
    │ Projects  │ [Messages...]                              │
    │ Sessions  │                                            │
    │ Files     │                                            │
    │ Context   │                                            │
    │           ├────────────────────────────────────────────┤
    │           │ [Input Area]                        [Send] │
    └───────────┴────────────────────────────────────────────┘
    """

    def __init__(self):
        """Initialize the main window."""
        super().__init__()

        # Project/session management
        self._project_manager = ProjectManager()
        self._metadata_store = MetadataStore()
        self._projects: ListState[Project] = ListState([])
        self._sessions: ListState[SessionMetadata] = ListState([])
        self._selected_project: State[Optional[Project]] = State(None)
        self._selected_session: State[Optional[SessionMetadata]] = State(None)

        # Messages and tool calls
        self._messages: ListState[ChatMessage] = ListState([])
        self._current_tools: ListState[ToolCall] = ListState([])
        self._context_files: ListState[dict[str, Any]] = ListState([])

        # FileTree state
        self._file_tree_state: Optional[FileTreeState] = None

        # Input state (don't attach)
        self._input_state = MultilineInputState("")

        # Scroll state (don't attach)
        self._chat_scroll_state = ScrollState()

        # SDK client state
        self._client: Optional[WrksClient] = None
        self._is_loading: State[bool] = State(False)
        self._streaming_text: State[str] = State("")
        self._total_cost: State[float] = State(0.0)
        self._session_id: State[Optional[str]] = State(None)
        self._pending_tool: State[Optional[ToolCall]] = State(None)

        # UI state
        self._sidebar_collapsed: State[bool] = State(False)
        self._approval_modal_state = ModalState()

        # Lazy state attachment flag
        self._states_attached = False

        # Load initial projects
        self._load_projects_initial()

    def _attach_states_if_needed(self) -> None:
        """Lazily attach states when view() is first called."""
        if not self._states_attached:
            self._projects.attach(self)
            self._sessions.attach(self)
            self._selected_project.attach(self)
            self._selected_session.attach(self)
            self._messages.attach(self)
            self._current_tools.attach(self)
            self._context_files.attach(self)
            self._is_loading.attach(self)
            self._streaming_text.attach(self)
            self._pending_tool.attach(self)
            self._sidebar_collapsed.attach(self)
            self._states_attached = True

    def _load_projects_initial(self) -> None:
        """Load projects initially without triggering notification."""
        favorites = self._metadata_store.get_favorites()
        projects = self._project_manager.list_projects(favorites=favorites)
        self._projects._list = projects

    def _refresh_projects(self) -> None:
        """Refresh the project list."""
        favorites = self._metadata_store.get_favorites()
        projects = self._project_manager.list_projects(favorites=favorites)
        self._projects.set(projects)

    def _select_project(self, project: Project) -> None:
        """Handle project selection."""
        self._selected_project.set(project)
        self._selected_session.set(None)

        # Initialize FileTree
        self._file_tree_state = FileTreeState(
            root_path=str(project.path),
            show_hidden=False,
            dirs_first=True,
        )

        # Load sessions
        sessions_path = self._project_manager.get_sessions_path(project)
        sessions = list_sessions(sessions_path)
        self._sessions.set(sessions)

        # Clear chat and show welcome message
        self._messages.set([])
        self._context_files.set([])
        self._current_tools.set([])
        self._client = None  # Reset client
        self._total_cost.set(0.0)
        self._session_id.set(None)

        self._add_system_message(
            f"Project: **{project.display_name}**\n\n"
            f"`{project.display_path}`\n\n"
            "Select a session to resume or start typing to begin a new session."
        )

    def _select_session(self, session: SessionMetadata) -> None:
        """Handle session selection (resume)."""
        self._selected_session.set(session)
        self._session_id.set(session.session_id)

        # Clear previous state
        self._messages.set([])
        self._current_tools.set([])
        self._context_files.set([])
        self._total_cost.set(0.0)

        # Reset client for new session
        self._client = None

        self._add_system_message(
            f"Resuming session: **{session.summary[:50]}**\n\n"
            f"Model: `{session.model or 'unknown'}`\n"
            f"Messages: {session.message_count}\n\n"
            "Type a message to continue this session."
        )

    def _toggle_favorite(self, project: Project) -> None:
        """Toggle favorite status for a project."""
        if project.is_favorite:
            self._metadata_store.remove_favorite(project.encoded_name)
        else:
            self._metadata_store.add_favorite(project.encoded_name)
        self._refresh_projects()

    def _on_file_select(self, path: Path) -> None:
        """Handle file selection in file tree - add to context."""
        path_str = str(path)

        # Check if already in context
        for ctx_file in self._context_files:
            if ctx_file["path"] == path_str:
                return

        # Get relative path for display
        project = self._selected_project()
        if project:
            try:
                rel_path = path.relative_to(project.path)
                name = str(rel_path)
            except ValueError:
                name = path.name
        else:
            name = path.name

        # Read file content
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
            # Truncate if too large
            max_size = 50000
            if len(content) > max_size:
                content = content[:max_size] + "\n\n... (truncated)"

            self._context_files.append({
                "path": path_str,
                "name": name,
                "content": content,
            })

        except Exception as e:
            self._add_system_message(f"Error reading file: {name}\n{e}")

    def _remove_context_file(self, path: str) -> None:
        """Remove a file from the context."""
        for i, ctx_file in enumerate(self._context_files):
            if ctx_file["path"] == path:
                del self._context_files[i]
                break

    def _toggle_sidebar(self) -> None:
        """Toggle sidebar visibility."""
        self._sidebar_collapsed.set(not self._sidebar_collapsed())

    def _add_system_message(self, content: str) -> None:
        """Add a system message to the chat."""
        self._messages.append(ChatMessage(
            role=MessageRole.SYSTEM,
            content=content,
        ))

    # SDK Client methods

    def _get_client(self) -> WrksClient:
        """Get or create the SDK client."""
        if self._client is None:
            project = self._selected_project()
            if project is None:
                raise RuntimeError("No project selected")

            session = self._selected_session()

            self._client = WrksClient(
                cwd=project.path,
                on_message=self._on_message_received,
                on_streaming_text=self._on_streaming_text_received,
                on_tool_use=self._on_tool_use,
                on_tool_result=self._on_tool_result,
                on_cost_update=self._on_cost_update,
                on_session_id=self._on_session_id,
                on_error=self._on_error,
                on_complete=self._on_complete,
                resume_session=session.session_id if session else None,
            )
        return self._client

    def _on_message_received(self, message: ChatMessage) -> None:
        """Handle complete message from SDK."""
        self._streaming_text.set("")
        self._messages.append(message)

    def _on_streaming_text_received(self, text: str) -> None:
        """Handle streaming text chunk."""
        self._streaming_text.set(text)

    def _on_tool_use(self, tool: ToolCall) -> None:
        """Handle tool use notification."""
        if tool.status == ToolStatus.PENDING:
            self._pending_tool.set(tool)
            self._approval_modal_state.open()
        else:
            self._current_tools.append(tool)

    def _on_tool_result(self, tool: ToolCall) -> None:
        """Handle tool completion."""
        tools = list(self._current_tools)
        for i, t in enumerate(tools):
            if t.id == tool.id:
                tools[i] = tool
                break
        self._current_tools.set(tools)

    def _on_cost_update(self, cost: float) -> None:
        """Handle cost update."""
        self._total_cost.set(cost)

    def _on_session_id(self, session_id: str) -> None:
        """Handle session ID notification."""
        self._session_id.set(session_id)

    def _on_error(self, error: Exception) -> None:
        """Handle error from SDK."""
        self._add_system_message(f"**Error:** {str(error)}")
        self._is_loading.set(False)

    def _on_complete(self) -> None:
        """Handle response completion."""
        self._is_loading.set(False)
        self._current_tools.set([])

    def _send_message(self) -> None:
        """Send the current input message."""
        text = self._input_state.value().strip()
        if not text or self._is_loading():
            return

        project = self._selected_project()
        if project is None:
            self._add_system_message("Please select a project first.")
            return

        # Build context
        context_parts = []
        if self._context_files:
            context_parts.append("**Context files:**\n")
            for ctx_file in self._context_files:
                context_parts.append(
                    f"\n`{ctx_file['name']}`:\n```\n{ctx_file['content']}\n```\n"
                )

        # Display message (without full context for cleaner UI)
        display_content = text
        if self._context_files:
            file_names = ", ".join(f"`{f['name']}`" for f in self._context_files)
            display_content = f"[Context: {file_names}]\n\n{text}"

        # Add user message to UI
        self._messages.append(ChatMessage(
            role=MessageRole.USER,
            content=display_content,
        ))

        # Build full message for agent
        if context_parts:
            full_message = "".join(context_parts) + "\n**User request:**\n" + text
        else:
            full_message = text

        # Clear input and set loading
        self._input_state.set("")
        self._is_loading.set(True)
        self._chat_scroll_state.y = 999999

        # Send to SDK
        client = self._get_client()
        client.send_message(full_message)

    def _handle_approve_tool(self) -> None:
        """Handle tool approval."""
        self._pending_tool.set(None)
        client = self._get_client()
        client.approve_tool()

    def _handle_reject_tool(self) -> None:
        """Handle tool rejection."""
        self._pending_tool.set(None)
        client = self._get_client()
        client.reject_tool()

    # View methods

    def view(self) -> Widget:
        """Build the main window view."""
        self._attach_states_if_needed()
        theme = ThemeManager().current

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

        main_content = Column(*elements).bg_color(theme.colors.bg_canvas)

        # Tool approval modal overlay
        pending = self._pending_tool()
        if pending:
            return Box(
                main_content,
                ToolApprovalModal(
                    tool_call=pending,
                    modal_state=self._approval_modal_state,
                    on_approve=self._handle_approve_tool,
                    on_reject=self._handle_reject_tool,
                ),
            )

        return main_content

    def _build_header(self, theme) -> Row:
        """Build the header bar."""
        project = self._selected_project()
        project_name = project.display_name if project else "No project"

        return (
            Row(
                Button("=").on_click(lambda _: self._toggle_sidebar()).fixed_size(36, 32),
                Spacer().fixed_width(8),
                Text("wrks", font_size=16)
                .text_color(theme.colors.text_primary)
                .fixed_height(24),
                Spacer().fixed_width(16),
                Text(project_name, font_size=14)
                .text_color(theme.colors.text_info)
                .fixed_height(24),
                Spacer(),
                CostDisplay(self._total_cost),
                Spacer().fixed_width(16),
            )
            .bg_color(theme.colors.bg_secondary)
            .fixed_height(44)
        )

    def _build_sidebar(self, theme) -> Column:
        """Build the sidebar with projects, sessions, files, and context.

        Each section shares height via flex (EXPANDING) and scrolls independently.
        """
        sections: list[Widget] = []

        # Projects section (always shown, flex height)
        sections.append(self._build_projects_section(theme))

        project = self._selected_project()
        if project:
            # Sessions section (flex height)
            sections.append(self._build_sessions_section(theme))

            # Files section (flex height)
            if self._file_tree_state:
                sections.append(self._build_files_section(theme))

        # Context section (flex height, only when files added)
        if self._context_files:
            sections.append(self._build_context_section(theme))

        return (
            Column(*sections)
            .bg_color(theme.colors.bg_secondary)
            .fixed_width(220)
        )

    def _build_projects_section(self, theme) -> Column:
        """Build the projects section of the sidebar."""
        # Header
        header = Row(
            Text("Projects", font_size=14)
            .text_color(theme.colors.text_primary)
            .fixed_height(24),
            Spacer(),
            Button("R")
            .on_click(lambda _: self._refresh_projects())
            .fixed_size(24, 24),
        ).fixed_height(28)

        # Content items
        content_items: list[Widget] = []
        selected_project = self._selected_project()

        for project in self._projects:
            star = "*" if project.is_favorite else " "
            is_selected = selected_project == project

            project_btn = (
                Button(project.display_name)
                .text_color(theme.colors.text_primary)
                .on_click(lambda _, p=project: self._select_project(p))
            )
            if is_selected:
                project_btn = project_btn.bg_color(theme.colors.bg_tertiary)

            content_items.append(
                Row(
                    Button(star)
                    .text_color(
                        theme.colors.text_warning if project.is_favorite
                        else theme.colors.border_secondary
                    )
                    .on_click(lambda _, p=project: self._toggle_favorite(p))
                    .fixed_size(20, 28),
                    project_btn,
                ).fixed_height(32)
            )

        if not self._projects:
            content_items.append(
                Text("No projects found", font_size=12)
                .text_color(theme.colors.border_secondary)
                .fixed_height(24)
            )

        # Scrollable content
        content = Column(*content_items, scrollable=True)

        return Column(header, content)

    def _build_sessions_section(self, theme) -> Column:
        """Build the sessions section of the sidebar."""
        # Header
        header = Row(
            Text("Sessions", font_size=14)
            .text_color(theme.colors.text_primary)
            .fixed_height(24),
            Spacer(),
            Button("+")
            .on_click(lambda _: self._start_new_session())
            .fixed_size(24, 24),
        ).fixed_height(28)

        # Content items
        content_items: list[Widget] = []
        selected_session = self._selected_session()

        for session in self._sessions:
            is_selected = selected_session and selected_session.session_id == session.session_id

            # Truncate summary
            summary = session.summary[:25]
            if len(session.summary) > 25:
                summary += "..."

            session_btn = (
                Button(f"{session.display_date}: {summary}")
                .text_color(theme.colors.text_primary)
                .on_click(lambda _, s=session: self._select_session(s))
                .fixed_height(28)
            )
            if is_selected:
                session_btn = session_btn.bg_color(theme.colors.bg_tertiary)

            content_items.append(session_btn)

        if not self._sessions:
            content_items.append(
                Text("No sessions yet", font_size=12)
                .text_color(theme.colors.border_secondary)
                .fixed_height(24)
            )

        # Scrollable content
        content = Column(*content_items, scrollable=True)

        return Column(header, content)

    def _start_new_session(self) -> None:
        """Start a new session (clear current session)."""
        self._selected_session.set(None)
        self._session_id.set(None)
        self._client = None
        self._messages.set([])
        self._current_tools.set([])
        self._context_files.set([])
        self._total_cost.set(0.0)

        project = self._selected_project()
        if project:
            self._add_system_message(
                f"New session in **{project.display_name}**\n\n"
                "Type a message to begin."
            )

    def _build_files_section(self, theme) -> Column:
        """Build the files section of the sidebar."""
        # Header
        header = Text("Files", font_size=14).text_color(theme.colors.text_primary).fixed_height(28)

        # FileTree has its own internal scrolling
        if self._file_tree_state:
            file_tree = FileTree(self._file_tree_state).on_file_select(self._on_file_select)
            return Column(header, file_tree)

        return Column(header)

    def _build_context_section(self, theme) -> Column:
        """Build the context files section of the sidebar."""
        # Header
        header = Text("Context", font_size=14).text_color(theme.colors.text_primary).fixed_height(28)

        # Content items
        content_items: list[Widget] = []
        for ctx_file in self._context_files:
            file_path = ctx_file["path"]
            content_items.append(
                Row(
                    Text(f"  {ctx_file['name']}", font_size=12)
                    .text_color(theme.colors.text_info)
                    .fixed_height(20),
                    Spacer(),
                    Button("x")
                    .on_click(lambda _, p=file_path: self._remove_context_file(p))
                    .fixed_size(20, 20),
                ).fixed_height(24)
            )

        # Scrollable content
        content = Column(*content_items, scrollable=True)

        return Column(header, content)

    def _build_chat_panel(self, theme) -> Column:
        """Build the chat panel with messages and input."""
        elements = []

        # Message list
        msg_widgets = self._build_messages(theme)

        # Streaming message
        streaming = self._streaming_text()
        if streaming:
            msg_widgets.append(self._build_streaming_message(streaming, theme))
            for tool in self._current_tools:
                msg_widgets.append(ToolCallView(tool))

        # Loading indicator
        if self._is_loading() and not streaming:
            msg_widgets.append(
                Text("Thinking...", font_size=12)
                .text_color(theme.colors.border_secondary)
                .height(40)
                .height_policy(SizePolicy.FIXED)
            )

        elements.append(
            Column(
                *msg_widgets,
                scrollable=True,
                scroll_state=self._chat_scroll_state,
            ).bg_color(theme.colors.bg_primary)
        )

        # Input area
        elements.append(self._build_input_area(theme))

        return Column(*elements)

    def _build_messages(self, theme) -> list[Widget]:
        """Build message widgets."""
        widgets: list[Widget] = []
        for message in self._messages:
            widgets.append(self._build_message(message, theme))
            widgets.append(Spacer().fixed_height(8))
        return widgets

    def _build_message(self, message: ChatMessage, theme) -> Box:
        """Build a single message widget."""
        if message.role == MessageRole.USER:
            bg_color = theme.colors.bg_tertiary
            role_label = "You"
            role_color = theme.colors.text_primary
        elif message.role == MessageRole.ASSISTANT:
            bg_color = theme.colors.bg_secondary
            role_label = "Assistant"
            role_color = theme.colors.text_info
        else:
            bg_color = theme.colors.bg_primary
            role_label = "System"
            role_color = theme.colors.text_warning

        content_widgets: list[Widget] = [
            Text(role_label, font_size=12)
            .text_color(role_color)
            .fixed_height(20),
            Markdown(message.content, base_font_size=14),
        ]

        # Add tool calls for assistant messages
        if message.role == MessageRole.ASSISTANT:
            for tool in message.tool_calls:
                content_widgets.append(ToolCallView(tool))

        return (
            Box(
                Column(*content_widgets).height_policy(SizePolicy.CONTENT)
            )
            .bg_color(bg_color)
            .height_policy(SizePolicy.CONTENT)
        )

    def _build_streaming_message(self, text: str, theme) -> Box:
        """Build a streaming message widget."""
        return (
            Box(
                Column(
                    Text("Assistant", font_size=12)
                    .text_color(theme.colors.text_info)
                    .fixed_height(20),
                    Markdown(text + "|", base_font_size=14),
                ).height_policy(SizePolicy.CONTENT)
            )
            .bg_color(theme.colors.bg_secondary)
            .height_policy(SizePolicy.CONTENT)
        )

    def _build_input_area(self, theme) -> Row:
        """Build the input area with text field and send button."""
        is_loading = self._is_loading()
        send_label = "..." if is_loading else "Send"

        return (
            Row(
                Spacer().fixed_width(8),
                MultilineInput(self._input_state, font_size=14, wrap=True)
                .height(50)
                .height_policy(SizePolicy.FIXED),
                Spacer().fixed_width(8),
                Button(send_label)
                .on_click(lambda _: self._send_message())
                .fixed_size(70, 40),
                Spacer().fixed_width(8),
            )
            .bg_color(theme.colors.bg_secondary)
            .fixed_height(66)
        )
