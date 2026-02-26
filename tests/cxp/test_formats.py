"""Tests for assistant format registry."""

from __future__ import annotations

from countersignal.cxp.formats import get_format, list_formats
from countersignal.cxp.models import AssistantFormat


class TestFormatRegistry:
    def test_list_formats_returns_three(self) -> None:
        formats = list_formats()
        assert len(formats) == 3

    def test_list_formats_returns_format_instances(self) -> None:
        formats = list_formats()
        for fmt in formats:
            assert isinstance(fmt, AssistantFormat)

    def test_get_claude_md(self) -> None:
        fmt = get_format("claude-md")
        assert fmt is not None
        assert fmt.id == "claude-md"
        assert fmt.filename == "CLAUDE.md"
        assert fmt.assistant == "Claude Code"
        assert fmt.syntax == "markdown"

    def test_get_cursorrules(self) -> None:
        fmt = get_format("cursorrules")
        assert fmt is not None
        assert fmt.id == "cursorrules"
        assert fmt.filename == ".cursorrules"
        assert fmt.assistant == "Cursor"
        assert fmt.syntax == "plaintext"

    def test_get_copilot_instructions(self) -> None:
        fmt = get_format("copilot-instructions")
        assert fmt is not None
        assert fmt.id == "copilot-instructions"
        assert fmt.filename == ".github/copilot-instructions.md"
        assert fmt.assistant == "GitHub Copilot"
        assert fmt.syntax == "markdown"

    def test_get_unknown_returns_none(self) -> None:
        assert get_format("nonexistent") is None
