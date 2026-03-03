"""AGENTS.md format — cross-assistant standard."""

from __future__ import annotations

from countersignal.cxp.formats import register
from countersignal.cxp.models import AssistantFormat

AGENTS_MD = AssistantFormat(
    id="agents-md",
    filename="AGENTS.md",
    assistant="Multi-assistant",
    syntax="markdown",
)

register(AGENTS_MD)
