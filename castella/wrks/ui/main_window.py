"""Main window component for wrks.

This is the primary UI component that combines sidebar (projects, sessions, files, context)
with tabbed chat panels for parallel session support.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from castella import (
    Box,
    Button,
    Column,
    ModalState,
    Row,
    Spacer,
    Text,
    Widget,
)
from castella.core import Component, ListState, SizePolicy, State
from castella.file_tree import FileTree, FileTreeState
from castella.markdown import Markdown
from castella.multiline_input import MultilineInput
from castella.theme import ThemeManager

from castella.wrks.config import get_config
from castella.wrks.sdk import WrksClient, ChatMessage, MessageRole, ToolCall, ToolStatus
from castella.wrks.storage import (
    Project,
    ProjectManager,
    SessionMetadata,
    MetadataStore,
    load_session_messages,
)
from castella.wrks.storage.sessions import list_sessions
from castella.wrks.ui.cost_display import CostDisplay
from castella.wrks.ui.session_state import ActiveSession
from castella.wrks.ui.tool_display import ToolCallView, ToolApprovalModal
from castella.wrks.ui.diff_view import DiffView, is_diff_output

# Maximum number of past messages to load when opening a session
HISTORY_LIMIT = 20


def _shorten_model_name(model: str) -> str:
    """Shorten model name for display.

    Examples:
        claude-opus-4-5-20251101 -> opus-4.5
        claude-sonnet-4-5-20251101 -> sonnet-4.5
        claude-3-5-haiku-20241022 -> haiku-3.5
    """
    if "opus-4" in model:
        return "opus-4.5"
    elif "sonnet-4" in model:
        return "sonnet-4.5"
    elif "haiku" in model:
        return "haiku-3.5"
    elif "opus" in model:
        return "opus"
    elif "sonnet" in model:
        return "sonnet"
    return model


def _extract_diff_blocks(content: str) -> list[tuple[str, str]]:
    """Extract diff blocks from message content.

    Returns list of tuples: ("text", content) or ("diff", diff_content)
    Returns empty list if no diff blocks found.
    """
    import re

    # Look for diff blocks in code fences (```diff or ````diff or just raw diff)
    parts: list[tuple[str, str]] = []

    # Pattern to match code blocks with 3 or 4 backticks
    code_block_pattern = re.compile(r'(`{3,4})(\w*)\n(.*?)\1', re.DOTALL)

    last_end = 0
    found_diff = False

    for match in code_block_pattern.finditer(content):
        # Add text before this code block
        text_before = content[last_end:match.start()]
        if text_before.strip():
            parts.append(("text", text_before))

        lang = match.group(2).lower()
        code_content = match.group(3)

        # Check if it's a diff block or looks like diff
        if lang == "diff" or (not lang and _looks_like_diff(code_content)):
            parts.append(("diff", code_content))
            found_diff = True
        else:
            # Keep as text (will be rendered by Markdown)
            parts.append(("text", match.group(0)))

        last_end = match.end()

    # Add remaining text
    if last_end < len(content):
        remaining = content[last_end:]
        # Check if remaining content looks like raw diff
        if _looks_like_diff(remaining):
            parts.append(("diff", remaining))
            found_diff = True
        elif remaining.strip():
            parts.append(("text", remaining))

    return parts if found_diff else []


def _looks_like_diff(text: str) -> bool:
    """Check if text looks like diff output."""
    lines = text.strip().split("\n")[:15]
    if not lines:
        return False

    diff_indicators = 0
    for line in lines:
        if line.startswith("diff --git"):
            return True
        if line.startswith("--- ") or line.startswith("+++ "):
            diff_indicators += 1
        if line.startswith("@@") and "@@" in line[2:]:
            diff_indicators += 1
        if line.startswith("+") or line.startswith("-"):
            diff_indicators += 0.5

    return diff_indicators >= 3


class MainWindow(Component):
    """Main application window with sidebar + tabbed chat layout.

    Supports parallel sessions via tabs.

    Layout:
    ┌────────────────────────────────────────────────────────────┐
    │ Header: ☰ wrks                            Total: $0.05     │
    ├───────────┬────────────────────────────────────────────────┤
    │ Sidebar   │ [proj1/session1] [proj2/new] [+]    ← Tabs     │
    │           ├────────────────────────────────────────────────┤
    │ Projects  │                                                │
    │ Sessions  │ Chat content for selected tab...               │
    │ Files     │                                                │
    │ Context   │                                                │
    │           ├────────────────────────────────────────────────┤
    │           │ [Input...]                              [Send] │
    └───────────┴────────────────────────────────────────────────┘
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

        # FileTree state (shared for sidebar display)
        self._file_tree_state: Optional[FileTreeState] = None

        # Active sessions (tabs)
        self._active_sessions: ListState[ActiveSession] = ListState([])
        self._current_session_id: State[Optional[str]] = State(None)

        # Total cost across all sessions
        self._total_cost: State[float] = State(0.0)

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
            self._active_sessions.attach(self)
            self._current_session_id.attach(self)
            self._sidebar_collapsed.attach(self)
            self._states_attached = True

    def _get_current_session(self) -> Optional[ActiveSession]:
        """Get the currently active session tab."""
        session_id = self._current_session_id()
        if session_id is None:
            return None
        for session in self._active_sessions:
            if session.id == session_id:
                return session
        return None

    def _load_projects_initial(self) -> None:
        """Load projects initially without triggering notification."""
        favorites = self._metadata_store.get_favorites()
        projects = self._project_manager.list_projects(favorites=favorites)
        # Use list methods directly to avoid notify (no observers attached yet)
        self._projects.clear()
        list.extend(self._projects, projects)

    def _refresh_projects(self) -> None:
        """Refresh the project list."""
        favorites = self._metadata_store.get_favorites()
        projects = self._project_manager.list_projects(favorites=favorites)
        self._projects.set(projects)

    def _select_project(self, project: Project) -> None:
        """Handle project selection in sidebar."""
        self._selected_project.set(project)

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

    def _toggle_favorite(self, project: Project) -> None:
        """Toggle favorite status for a project."""
        if project.is_favorite:
            self._metadata_store.remove_favorite(project.encoded_name)
        else:
            self._metadata_store.add_favorite(project.encoded_name)
        self._refresh_projects()

    def _open_session_tab(
        self,
        project: Project,
        session_metadata: Optional[SessionMetadata] = None,
    ) -> None:
        """Open a session in a new tab or switch to existing tab."""
        # Check if this session is already open
        for active in self._active_sessions:
            if (active.project == project and
                active.session_metadata == session_metadata):
                # Switch to existing tab
                self._current_session_id.set(active.id)
                return

        # Create new active session
        new_session = ActiveSession(
            project=project,
            session_metadata=session_metadata,
        )
        new_session.attach_states(self)

        # Set session ID if resuming
        if session_metadata:
            new_session.session_id.set(session_metadata.session_id)

        # Add welcome message
        new_session.messages.append(ChatMessage(
            role=MessageRole.SYSTEM,
            content=self._get_welcome_message(project, session_metadata),
        ))

        # Load past messages if resuming a session (limit to most recent N)
        if session_metadata and session_metadata.file_path.exists():
            past_messages = load_session_messages(
                session_metadata.file_path, limit=HISTORY_LIMIT
            )
            for msg in past_messages:
                role = MessageRole.USER if msg.role == "user" else MessageRole.ASSISTANT
                new_session.messages.append(ChatMessage(
                    role=role,
                    content=msg.content,
                    model_name=msg.model_name,
                ))
            # Scroll to bottom after loading past messages
            new_session.scroll_state.y = 999999

        # Add to active sessions and switch to it
        self._active_sessions.append(new_session)
        self._current_session_id.set(new_session.id)

    def _close_session_tab(self, session_id: str) -> None:
        """Close a session tab."""
        for i, session in enumerate(self._active_sessions):
            if session.id == session_id:
                # Detach states before removing
                session.detach_states(self)

                # Remove from list
                del self._active_sessions[i]

                # If this was the current tab, switch to another
                if self._current_session_id() == session_id:
                    if self._active_sessions:
                        self._current_session_id.set(self._active_sessions[-1].id)
                    else:
                        self._current_session_id.set(None)
                break

    def _switch_to_tab(self, session_id: str) -> None:
        """Switch to a specific tab."""
        self._current_session_id.set(session_id)

    def _get_welcome_message(
        self,
        project: Project,
        session_metadata: Optional[SessionMetadata],
    ) -> str:
        """Get the welcome message for a session."""
        if session_metadata:
            return (
                f"Resuming session: **{session_metadata.summary[:50]}**\n\n"
                f"Project: `{project.display_path}`\n"
                f"Model: `{session_metadata.model or 'unknown'}`\n\n"
                "Type a message to continue."
            )
        return (
            f"New session in **{project.display_name}**\n\n"
            f"`{project.display_path}`\n\n"
            "Type a message to begin."
        )

    def _on_file_select(self, path: Path) -> None:
        """Handle file selection in file tree - add to current session's context."""
        session = self._get_current_session()
        if session is None:
            return

        path_str = str(path)

        # Check if already in context
        for ctx_file in session.context_files:
            if ctx_file["path"] == path_str:
                return

        # Get relative path for display
        if session.project:
            try:
                rel_path = path.relative_to(session.project.path)
                name = str(rel_path)
            except ValueError:
                name = path.name
        else:
            name = path.name

        # Read file content
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
            max_size = 50000
            if len(content) > max_size:
                content = content[:max_size] + "\n\n... (truncated)"

            session.context_files.append({
                "path": path_str,
                "name": name,
                "content": content,
            })
        except Exception as e:
            session.messages.append(ChatMessage(
                role=MessageRole.SYSTEM,
                content=f"Error reading file: {name}\n{e}",
            ))

    def _remove_context_file(self, path: str) -> None:
        """Remove a file from the current session's context."""
        session = self._get_current_session()
        if session is None:
            return

        for i, ctx_file in enumerate(session.context_files):
            if ctx_file["path"] == path:
                del session.context_files[i]
                break

    def _toggle_sidebar(self) -> None:
        """Toggle sidebar visibility."""
        self._sidebar_collapsed.set(not self._sidebar_collapsed())

    # SDK Client methods

    def _get_client(self, session: ActiveSession) -> WrksClient:
        """Get or create the SDK client for a session."""
        if session.client is None:
            if session.project is None:
                raise RuntimeError("No project for session")

            config = get_config()
            session.client = WrksClient(
                cwd=session.project.path,
                on_message=lambda msg: self._on_message_received(session, msg),
                on_streaming_text=lambda text: self._on_streaming_text(session, text),
                on_tool_use=lambda tool: self._on_tool_use(session, tool),
                on_tool_result=lambda tool: self._on_tool_result(session, tool),
                on_cost_update=lambda cost: self._on_cost_update(session, cost),
                on_session_id=lambda sid: self._on_session_id(session, sid),
                on_error=lambda err: self._on_error(session, err),
                on_complete=lambda: self._on_complete(session),
                resume_session=(
                    session.session_metadata.session_id
                    if session.session_metadata else None
                ),
                model=config.model,
            )
        return session.client

    def _on_message_received(self, session: ActiveSession, message: ChatMessage) -> None:
        """Handle complete message from SDK."""
        session.streaming_text.set("")
        session.messages.append(message)

    def _on_streaming_text(self, session: ActiveSession, text: str) -> None:
        """Handle streaming text chunk."""
        session.streaming_text.set(text)

    def _on_tool_use(self, session: ActiveSession, tool: ToolCall) -> None:
        """Handle tool use notification."""
        if tool.status == ToolStatus.PENDING:
            session.pending_tool.set(tool)
            self._approval_modal_state.open()
        else:
            session.current_tools.append(tool)

    def _on_tool_result(self, session: ActiveSession, tool: ToolCall) -> None:
        """Handle tool completion."""
        tools = list(session.current_tools)
        for i, t in enumerate(tools):
            if t.id == tool.id:
                tools[i] = tool
                break
        session.current_tools.set(tools)

    def _on_cost_update(self, session: ActiveSession, cost: float) -> None:
        """Handle cost update."""
        old_cost = session.total_cost()
        session.total_cost.set(cost)

        # Update total cost
        delta = cost - old_cost
        self._total_cost.set(self._total_cost() + delta)

    def _on_session_id(self, session: ActiveSession, session_id: str) -> None:
        """Handle session ID notification."""
        session.session_id.set(session_id)

    def _on_error(self, session: ActiveSession, error: Exception) -> None:
        """Handle error from SDK."""
        session.messages.append(ChatMessage(
            role=MessageRole.SYSTEM,
            content=f"**Error:** {str(error)}",
        ))
        session.is_loading.set(False)

    def _on_complete(self, session: ActiveSession) -> None:
        """Handle response completion."""
        session.is_loading.set(False)
        session.current_tools.set([])

    def _send_message(self) -> None:
        """Send the current input message."""
        session = self._get_current_session()
        if session is None:
            return

        text = session.input_state.value().strip()
        if not text or session.is_loading():
            return

        # Build context
        context_parts = []
        if session.context_files:
            context_parts.append("**Context files:**\n")
            for ctx_file in session.context_files:
                context_parts.append(
                    f"\n`{ctx_file['name']}`:\n```\n{ctx_file['content']}\n```\n"
                )

        # Display message
        display_content = text
        if session.context_files:
            file_names = ", ".join(f"`{f['name']}`" for f in session.context_files)
            display_content = f"[Context: {file_names}]\n\n{text}"

        session.messages.append(ChatMessage(
            role=MessageRole.USER,
            content=display_content,
        ))

        # Build full message
        if context_parts:
            full_message = "".join(context_parts) + "\n**User request:**\n" + text
        else:
            full_message = text

        # Clear input and set loading
        session.input_state.set("")
        session.is_loading.set(True)
        session.scroll_state.y = 999999

        # Send to SDK
        client = self._get_client(session)
        client.send_message(full_message)

    def _handle_approve_tool(self) -> None:
        """Handle tool approval."""
        session = self._get_current_session()
        if session is None:
            return

        session.pending_tool.set(None)
        client = self._get_client(session)
        client.approve_tool()

    def _handle_reject_tool(self) -> None:
        """Handle tool rejection."""
        session = self._get_current_session()
        if session is None:
            return

        session.pending_tool.set(None)
        client = self._get_client(session)
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

        # Chat panel with tabs
        content_row.append(self._build_tabbed_chat_panel(theme))

        elements.append(Row(*content_row))

        main_content = Column(*elements).bg_color(theme.colors.bg_canvas)

        # Tool approval modal overlay
        session = self._get_current_session()
        if session:
            pending = session.pending_tool()
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
        config = get_config()
        model_label = f"Model: {config.model}"

        return (
            Row(
                Button("=").on_click(lambda _: self._toggle_sidebar()).fixed_size(36, 32),
                Spacer().fixed_width(8),
                Text("wrks", font_size=16)
                .text_color(theme.colors.text_primary)
                .fixed_height(24),
                Spacer().fixed_width(16),
                Text(model_label, font_size=12)
                .text_color(theme.colors.border_secondary)
                .fixed_height(20),
                Spacer(),
                Text("Total:", font_size=12)
                .text_color(theme.colors.border_secondary)
                .fixed_height(20),
                Spacer().fixed_width(4),
                CostDisplay(self._total_cost),
                Spacer().fixed_width(16),
            )
            .bg_color(theme.colors.bg_secondary)
            .fixed_height(44)
        )

    def _build_sidebar(self, theme) -> Column:
        """Build the sidebar with projects, sessions, files, and context."""
        sections: list[Widget] = []

        # Projects section
        sections.append(self._build_projects_section(theme))

        project = self._selected_project()
        if project:
            # Sessions section
            sections.append(self._build_sessions_section(theme))

            # Files section
            if self._file_tree_state:
                sections.append(self._build_files_section(theme))

        # Context section (from current session)
        session = self._get_current_session()
        if session and session.context_files:
            sections.append(self._build_context_section(theme, session))

        return (
            Column(*sections)
            .bg_color(theme.colors.bg_secondary)
            .fixed_width(220)
        )

    def _build_projects_section(self, theme) -> Column:
        """Build the projects section of the sidebar."""
        header = Row(
            Text("Projects", font_size=14)
            .text_color(theme.colors.text_primary)
            .fixed_height(24),
            Spacer(),
            Button("R")
            .on_click(lambda _: self._refresh_projects())
            .fixed_size(24, 24),
        ).fixed_height(28)

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

        content = Column(*content_items, scrollable=True)
        return Column(header, content)

    def _build_sessions_section(self, theme) -> Column:
        """Build the sessions section of the sidebar."""
        project = self._selected_project()

        header = Row(
            Text("Sessions", font_size=14)
            .text_color(theme.colors.text_primary)
            .fixed_height(24),
            Spacer(),
            Button("+")
            .on_click(lambda _: self._open_session_tab(project) if project else None)
            .fixed_size(24, 24),
        ).fixed_height(28)

        content_items: list[Widget] = []

        for session in self._sessions:
            summary = session.summary[:20]
            if len(session.summary) > 20:
                summary += "..."

            # Double-click behavior simulated via single click to open tab
            session_btn = (
                Button(f"{session.display_date}: {summary}")
                .text_color(theme.colors.text_primary)
                .on_click(lambda _, s=session, p=project: self._open_session_tab(p, s))
                .fixed_height(28)
            )
            content_items.append(session_btn)

        if not self._sessions:
            content_items.append(
                Text("No sessions yet", font_size=12)
                .text_color(theme.colors.border_secondary)
                .fixed_height(24)
            )

        content = Column(*content_items, scrollable=True)
        return Column(header, content)

    def _build_files_section(self, theme) -> Column:
        """Build the files section of the sidebar."""
        header = Text("Files", font_size=14).text_color(theme.colors.text_primary).fixed_height(28)

        if self._file_tree_state:
            file_tree = FileTree(self._file_tree_state).on_file_select(self._on_file_select)
            return Column(header, file_tree)

        return Column(header)

    def _build_context_section(self, theme, session: ActiveSession) -> Column:
        """Build the context files section for a session."""
        header = Text("Context", font_size=14).text_color(theme.colors.text_primary).fixed_height(28)

        content_items: list[Widget] = []
        for ctx_file in session.context_files:
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

        content = Column(*content_items, scrollable=True)
        return Column(header, content)

    def _build_tabbed_chat_panel(self, theme) -> Column:
        """Build the chat panel with session tabs."""
        elements = []

        # Tab bar
        elements.append(self._build_tab_bar(theme))

        # Chat content for current session
        session = self._get_current_session()
        if session:
            elements.append(self._build_chat_content(theme, session))
            elements.append(self._build_input_area(theme, session))
        else:
            # No active session - show placeholder
            elements.append(
                Column(
                    Spacer(),
                    Text("Select a project and session to start", font_size=14)
                    .text_color(theme.colors.border_secondary),
                    Spacer(),
                ).bg_color(theme.colors.bg_primary)
            )

        return Column(*elements)

    def _build_tab_bar(self, theme) -> Row:
        """Build the session tabs bar."""
        tabs: list[Widget] = []

        current_id = self._current_session_id()

        for session in self._active_sessions:
            is_active = session.id == current_id

            # Tab button with close
            tab_bg = theme.colors.bg_primary if is_active else theme.colors.bg_tertiary
            tab_text_color = theme.colors.text_primary  # Always use primary for visibility

            tab = (
                Row(
                    Button(session.tab_name)
                    .text_color(tab_text_color)
                    .bg_color(tab_bg)
                    .on_click(lambda _, sid=session.id: self._switch_to_tab(sid))
                    .fixed_height(28)
                    .fit_content_width(),
                    Button("x")
                    .text_color(theme.colors.text_primary)
                    .on_click(lambda _, sid=session.id: self._close_session_tab(sid))
                    .fixed_size(20, 28),
                )
                .fixed_height(32)
                .fit_content_width()
            )

            tabs.append(tab)

        # Add new tab button (if a project is selected)
        project = self._selected_project()
        if project:
            tabs.append(
                Button("+")
                .text_color(theme.colors.text_primary)
                .on_click(lambda _: self._open_session_tab(project))
                .fixed_size(32, 28)
            )

        return (
            Row(*tabs, scrollable=True)
            .bg_color(theme.colors.bg_secondary)
            .fixed_height(36)
        )

    def _build_chat_content(self, theme, session: ActiveSession) -> Column:
        """Build the chat content for a session."""
        msg_widgets = self._build_messages(theme, session)

        # Streaming message
        streaming = session.streaming_text()
        if streaming:
            msg_widgets.append(self._build_streaming_message(streaming, theme))

        # Show current tools (during streaming or while tools are running)
        for tool in session.current_tools:
            tool_view = ToolCallView(tool)
            tool_view.height_policy(SizePolicy.CONTENT)
            msg_widgets.append(tool_view)

        # Loading indicator
        if session.is_loading() and not streaming and not session.current_tools:
            msg_widgets.append(
                Text("Thinking...", font_size=12)
                .text_color(theme.colors.border_secondary)
                .height(40)
                .height_policy(SizePolicy.FIXED)
            )

        return (
            Column(
                *msg_widgets,
                scrollable=True,
                scroll_state=session.scroll_state,
            )
            .bg_color(theme.colors.bg_primary)
        )

    def _build_messages(self, theme, session: ActiveSession) -> list[Widget]:
        """Build message widgets for a session."""
        widgets: list[Widget] = []
        for message in session.messages:
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

        # Build header row with role label and model name (for assistant)
        header_items: list[Widget] = [
            Text(role_label, font_size=12)
            .text_color(role_color)
            .fit_content(),
        ]

        # Add model name for assistant messages
        if message.role == MessageRole.ASSISTANT and message.model_name:
            short_model = _shorten_model_name(message.model_name)
            header_items.append(Spacer().fixed_width(8))
            header_items.append(
                Text(short_model, font_size=11)
                .text_color(theme.colors.text_info)
                .fit_content()
            )

        content_widgets: list[Widget] = [
            Row(*header_items).fixed_height(20).height_policy(SizePolicy.FIXED),
        ]

        # Check if message contains diff output and render appropriately
        content = message.content
        diff_parts = _extract_diff_blocks(content)

        if diff_parts:
            for part_type, part_content in diff_parts:
                if part_type == "diff":
                    diff_view = DiffView(part_content)
                    diff_view.height_policy(SizePolicy.CONTENT)
                    content_widgets.append(diff_view)
                elif part_content.strip():
                    content_widgets.append(Markdown(part_content, base_font_size=14))
        else:
            content_widgets.append(Markdown(content, base_font_size=14))

        if message.role == MessageRole.ASSISTANT:
            for tool in message.tool_calls:
                tool_view = ToolCallView(tool)
                tool_view.height_policy(SizePolicy.CONTENT)
                content_widgets.append(tool_view)

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

    def _build_input_area(self, theme, session: ActiveSession) -> Row:
        """Build the input area for a session."""
        is_loading = session.is_loading()
        send_label = "..." if is_loading else "Send"

        return (
            Row(
                Spacer().fixed_width(8),
                MultilineInput(session.input_state, font_size=14, wrap=True)
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
