"""CLAUDE.md format for Claude Code."""

from __future__ import annotations

from countersignal.cxp.formats import register
from countersignal.cxp.models import AssistantFormat

CLAUDE_MD = AssistantFormat(
    id="claude-md",
    filename="CLAUDE.md",
    assistant="Claude Code",
    syntax="markdown",
)

register(CLAUDE_MD)
