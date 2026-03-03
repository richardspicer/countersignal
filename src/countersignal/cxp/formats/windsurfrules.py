""".windsurfrules format for Windsurf."""

from __future__ import annotations

from countersignal.cxp.formats import register
from countersignal.cxp.models import AssistantFormat

WINDSURFRULES = AssistantFormat(
    id="windsurfrules",
    filename=".windsurfrules",
    assistant="Windsurf",
    syntax="plaintext",
)

register(WINDSURFRULES)
