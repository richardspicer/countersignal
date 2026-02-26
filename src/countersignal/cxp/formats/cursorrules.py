""".cursorrules format for Cursor."""

from __future__ import annotations

from countersignal.cxp.formats import register
from countersignal.cxp.models import AssistantFormat

CURSORRULES = AssistantFormat(
    id="cursorrules",
    filename=".cursorrules",
    assistant="Cursor",
    syntax="plaintext",
)

register(CURSORRULES)
