"""Agent Card View component for Castella.

This module provides a UI component for displaying A2A Agent Card information.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from castella.box import Box
from castella.column import Column
from castella.core import Component, SizePolicy, State
from castella.row import Row
from castella.text import Text

if TYPE_CHECKING:
    from castella.a2a.types import AgentCard, AgentSkill


class SkillBadge(Component):
    """A badge displaying a single skill."""

    def __init__(self, skill: "AgentSkill"):
        super().__init__()
        self._skill = skill

    def view(self):
        from castella.theme import ThemeManager

        theme = ThemeManager().current

        return (
            Box(
                Text(self._skill.name, font_size=14)
                .text_color(theme.colors.text_primary)
                .fixed_height(20)
            )
            .bg_color(theme.colors.bg_tertiary)
            .fixed_height(28)
            .fixed_width(100)
        )


class AgentCardView(Component):
    """Display an A2A Agent Card.

    This component shows the agent's name, description, version,
    and available skills in a card layout.

    Example:
        from castella.agent import AgentCardView
        from castella.a2a import A2AClient

        client = A2AClient("http://agent.example.com")
        card = AgentCardView(client.agent_card)
        run_app(card)
    """

    def __init__(
        self,
        agent_card: "AgentCard",
        show_skills: bool = True,
        show_url: bool = False,
        compact: bool = False,
    ):
        """Initialize the Agent Card View.

        Args:
            agent_card: The AgentCard to display
            show_skills: Whether to show the skills section
            show_url: Whether to show the agent URL
            compact: Use compact layout
        """
        super().__init__()
        self._card = agent_card
        self._show_skills = show_skills
        self._show_url = show_url
        self._compact = compact
        self._expanded = State(True)
        self._expanded.attach(self)

    def view(self):
        from castella.theme import ThemeManager

        theme = ThemeManager().current

        # Header with name and version
        header = Row(
            Text(self._card.name, font_size=16)
            .text_color(theme.colors.text_primary)
            .fixed_height(24),
            Text(f"v{self._card.version}", font_size=14)
            .text_color(theme.colors.text_info)
            .fixed_height(20),
        ).fixed_height(30)

        # Description
        description = (
            Text(self._card.description or "No description", font_size=14)
            .text_color(theme.colors.text_info)
            .fixed_height(20)
        )

        # Build content list
        content = [header, description]

        # URL (optional)
        if self._show_url and self._card.url:
            url_text = (
                Text(f"URL: {self._card.url}", font_size=12)
                .text_color(theme.colors.text_info)
                .fixed_height(18)
            )
            content.append(url_text)

        # Skills section (optional)
        if self._show_skills and self._card.skills:
            skills_header = (
                Text(f"Skills ({len(self._card.skills)})", font_size=14)
                .text_color(theme.colors.text_primary)
                .fixed_height(20)
            )
            content.append(skills_header)

            # Create skill badges in rows
            skills_row = Row(
                *[SkillBadge(s) for s in self._card.skills[:5]],  # Limit to 5
            ).fixed_height(32)
            content.append(skills_row)

            # Show remaining count if more than 5
            if len(self._card.skills) > 5:
                more_text = (
                    Text(f"+{len(self._card.skills) - 5} more skills", font_size=12)
                    .text_color(theme.colors.text_info)
                    .fixed_height(16)
                )
                content.append(more_text)

        # Wrap in a card box
        return (
            Box(Column(*content).height_policy(SizePolicy.CONTENT))
            .bg_color(theme.colors.bg_secondary)
            .border_color(theme.colors.border_primary)
            .height_policy(SizePolicy.CONTENT)
        )


class AgentListView(Component):
    """Display a list of A2A agents.

    Example:
        from castella.agent import AgentListView
        from castella.a2a import A2AClient

        clients = [
            A2AClient("http://agent1.example.com"),
            A2AClient("http://agent2.example.com"),
        ]
        list_view = AgentListView([c.agent_card for c in clients])
        run_app(list_view)
    """

    def __init__(
        self,
        agent_cards: list["AgentCard"],
        on_select: callable = None,
    ):
        """Initialize the Agent List View.

        Args:
            agent_cards: List of AgentCards to display
            on_select: Callback when an agent is selected
        """
        super().__init__()
        self._cards = agent_cards
        self._on_select = on_select
        self._selected_index = State(-1)
        self._selected_index.attach(self)

    def view(self):
        from castella.theme import ThemeManager

        theme = ThemeManager().current

        if not self._cards:
            return (
                Text("No agents found", font_size=14)
                .text_color(theme.colors.text_info)
                .fixed_height(40)
            )

        items = []
        for i, card in enumerate(self._cards):
            card_view = AgentCardView(card, compact=True, show_skills=False)
            items.append(card_view)

        return Column(*items, scrollable=True)
